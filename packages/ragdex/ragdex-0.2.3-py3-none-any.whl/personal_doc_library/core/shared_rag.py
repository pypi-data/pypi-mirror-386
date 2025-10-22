#!/usr/bin/env python3
"""
Shared RAG System for Personal Document Library
Common functionality used by both MCP server and background indexer
"""

from langchain_community.document_loaders import (
    PyPDFLoader,
    UnstructuredWordDocumentLoader,
    UnstructuredEPubLoader,
    UnstructuredPowerPointLoader
)
from langchain.schema import Document
import pypdf
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
# from langchain_community.llms import Ollama  # Removed for direct RAG results
import os
import logging
import torch
import hashlib
import json
import time
import subprocess
import shutil
import shlex
from datetime import datetime
from pathlib import Path
import fcntl
from contextlib import contextmanager
from .config import config
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeoutError
import psutil
import threading
from collections import OrderedDict
import difflib

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class IndexLock:
    """File-based locking to prevent simultaneous indexing with stale lock detection"""
    def __init__(self, lock_file="/tmp/spiritual_library_index.lock", stale_timeout_minutes=30):
        self.lock_file = lock_file
        self.lock_fd = None
        self.stale_timeout_minutes = stale_timeout_minutes
        self.update_thread = None
        self.stop_update = threading.Event()
        # Clean stale locks on initialization
        self.clean_stale_lock()
    
    def is_lock_stale(self):
        """Check if existing lock file is from a dead process or too old"""
        if not os.path.exists(self.lock_file):
            return False
        
        try:
            # Check file age
            mtime = os.path.getmtime(self.lock_file)
            age_minutes = (time.time() - mtime) / 60
            
            if age_minutes > self.stale_timeout_minutes:
                logger.info(f"Lock file is {age_minutes:.1f} minutes old, considering stale")
                return True
            
            # Check if process is alive
            with open(self.lock_file, 'r') as f:
                lines = f.readlines()
                if lines:
                    pid = int(lines[0].strip())
                    try:
                        # Signal 0 checks if process exists without sending signal
                        os.kill(pid, 0)
                        return False  # Process is alive
                    except ProcessLookupError:
                        logger.info(f"Lock held by dead process {pid}")
                        return True  # Process is dead
                    except PermissionError:
                        # Process exists but we can't signal it
                        return False
        except Exception as e:
            logger.warning(f"Error checking lock status: {e}")
            return True  # Consider stale if we can't check properly
    
    def clean_stale_lock(self):
        """Remove stale lock files from dead processes"""
        if self.is_lock_stale():
            try:
                os.remove(self.lock_file)
                logger.info("Cleaned up stale lock file")
            except Exception as e:
                logger.warning(f"Could not remove stale lock: {e}")
    
    def get_lock_info(self):
        """Get information about current lock holder"""
        if not os.path.exists(self.lock_file):
            return None
        
        try:
            with open(self.lock_file, 'r') as f:
                lines = f.readlines()
                if len(lines) >= 2:
                    pid = int(lines[0].strip())
                    timestamp = lines[1].strip()
                    
                    # Check if process is alive
                    try:
                        os.kill(pid, 0)
                        alive = True
                    except:
                        alive = False
                    
                    return {
                        "pid": pid,
                        "timestamp": timestamp,
                        "alive": alive,
                        "age_minutes": (time.time() - os.path.getmtime(self.lock_file)) / 60
                    }
        except:
            pass
        return None
    
    def start_periodic_update(self):
        """Start background thread to update lock timestamp"""
        def update_loop():
            while not self.stop_update.is_set():
                try:
                    # Only update the modification time - don't try to rewrite content
                    # since the file is already exclusively locked by the main process
                    if os.path.exists(self.lock_file):
                        os.utime(self.lock_file, None)
                    else:
                        # If lock file doesn't exist, the lock was released
                        break
                except Exception as e:
                    logger.warning(f"Failed to update lock timestamp: {e}")
                # Wait 30 seconds or until stop signal
                self.stop_update.wait(30)
        
        self.update_thread = threading.Thread(target=update_loop, daemon=True)
        self.update_thread.start()
        logger.info("Started lock periodic update thread")
    
    def stop_periodic_update(self):
        """Stop the periodic update thread"""
        if self.update_thread and self.update_thread.is_alive():
            self.stop_update.set()
            self.update_thread.join(timeout=1)
            logger.info("Stopped lock periodic update thread")
    
    @contextmanager
    def acquire(self, blocking=False):
        """Acquire index lock with context manager"""
        # Clean stale locks before attempting
        self.clean_stale_lock()
        
        # Open lock file with restricted permissions (owner read/write only)
        self.lock_fd = os.open(self.lock_file, os.O_CREAT | os.O_WRONLY, 0o600)
        self.lock_fd = os.fdopen(self.lock_fd, 'w')
        lock_acquired = False
        try:
            if blocking:
                fcntl.flock(self.lock_fd, fcntl.LOCK_EX)
            else:
                fcntl.flock(self.lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            lock_acquired = True
            self.lock_fd.write(f"{os.getpid()}\n{datetime.now().isoformat()}")
            self.lock_fd.flush()
            # Start periodic update thread
            self.start_periodic_update()
            yield
        except IOError:
            if self.lock_fd:
                self.lock_fd.close()
                self.lock_fd = None  # Set to None after closing
            logger.warning("Could not acquire index lock - another process may be indexing")
            raise
        finally:
            # Stop periodic update thread
            self.stop_periodic_update()
            if self.lock_fd and lock_acquired:
                try:
                    fcntl.flock(self.lock_fd, fcntl.LOCK_UN)
                except:
                    pass
                self.lock_fd.close()
                try:
                    os.remove(self.lock_file)
                except:
                    pass

class PDFCleaner:
    """Handles PDF cleaning for problematic files"""
    
    @staticmethod
    def clean_pdf(input_path, output_path, timeout_minutes=30):
        """Clean a PDF using Ghostscript with security validation"""
        try:
            # Validate paths to prevent command injection
            input_path = os.path.abspath(input_path)
            output_path = os.path.abspath(output_path)
            
            if not os.path.exists(input_path):
                raise ValueError(f"Input file does not exist: {input_path}")
            
            logger.info(f"Cleaning {os.path.basename(input_path)}...")
            
            cmd = [
                'gs', '-dBATCH', '-dNOPAUSE', '-q',
                '-sDEVICE=pdfwrite', '-dCompatibilityLevel=1.4',
                '-dPDFSETTINGS=/ebook', '-dCompressFonts=true',
                '-dSubsetFonts=true', '-dOptimize=true',
                '-dColorImageResolution=150',
                f'-sOutputFile={output_path}', input_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, 
                                  timeout=timeout_minutes * 60)
            
            if result.returncode == 0 and os.path.exists(output_path) and os.path.getsize(output_path) > 0:
                logger.info(f"Successfully cleaned {os.path.basename(input_path)}")
                return True
            return False
            
        except subprocess.TimeoutExpired:
            logger.error(f"Timeout cleaning PDF after {timeout_minutes} minutes")
            return False
        except Exception as e:
            logger.error(f"Error cleaning PDF: {e}")
            return False

class OCRPDFLoader:
    """PDF loader with OCR capability for scanned documents"""
    
    def __init__(self, file_path):
        self.file_path = file_path
    
    def needs_ocr(self):
        """Check if PDF needs OCR by analyzing text content"""
        try:
            import pypdf
            with open(self.file_path, 'rb') as file:
                pdf_reader = pypdf.PdfReader(file, strict=False)
                total_pages = len(pdf_reader.pages)
                
                # Sample first 10 pages to check for text
                sample_pages = min(10, total_pages)
                text_pages = 0
                
                for i in range(sample_pages):
                    try:
                        text = pdf_reader.pages[i].extract_text()
                        if text and len(text.strip()) > 50:  # More than 50 chars of text
                            text_pages += 1
                    except:
                        continue
                
                # If less than 20% of sampled pages have text, likely needs OCR
                text_ratio = text_pages / sample_pages if sample_pages > 0 else 0
                logger.info(f"PDF text analysis: {text_pages}/{sample_pages} pages have text (ratio: {text_ratio:.2f})")
                
                return text_ratio < 0.2
        except Exception as e:
            logger.error(f"Error checking if PDF needs OCR: {e}")
            return False
    
    def perform_ocr(self, output_path=None):
        """Perform OCR on the PDF using ocrmypdf"""
        if output_path is None:
            output_path = self.file_path + ".ocr.pdf"
        
        try:
            # Validate paths to prevent command injection
            input_file = os.path.abspath(self.file_path)
            output_file = os.path.abspath(output_path)
            
            if not os.path.exists(input_file):
                raise ValueError(f"Input file does not exist: {input_file}")
                
            logger.info(f"Performing OCR on {os.path.basename(input_file)}...")
            
            cmd = [
                'ocrmypdf',
                '--skip-text',     # Skip pages that already have text
                '--optimize', '1', # Optimize output size
                '--output-type', 'pdf',  # Regular PDF output to avoid color space issues
                '--tesseract-timeout', '300',  # 5 min timeout per page
                input_file,
                output_file
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=3600)  # 1 hour timeout
            
            if result.returncode == 0 and os.path.exists(output_path):
                logger.info(f"OCR completed successfully: {output_path}")
                return output_path
            else:
                logger.error(f"OCR failed: {result.stderr}")
                return None
                
        except subprocess.TimeoutExpired:
            logger.error("OCR timeout after 1 hour")
            return None
        except Exception as e:
            logger.error(f"OCR error: {e}")
            return None
    
    def load(self):
        """Load PDF, performing OCR if needed"""
        # First check if OCR is needed
        if self.needs_ocr():
            logger.info(f"PDF appears to be scanned, performing OCR...")
            
            # Create OCR output path
            ocr_dir = os.path.join(os.path.dirname(self.file_path), ".ocr_cache")
            os.makedirs(ocr_dir, exist_ok=True)
            ocr_path = os.path.join(ocr_dir, os.path.basename(self.file_path) + ".ocr.pdf")
            
            # Check if we already have an OCR'd version
            if os.path.exists(ocr_path) and os.path.getmtime(ocr_path) > os.path.getmtime(self.file_path):
                logger.info(f"Using cached OCR version: {ocr_path}")
                # Use FastPDFLoader on the OCR'd version
                return FastPDFLoader(ocr_path).load()
            
            # Perform OCR
            ocr_result = self.perform_ocr(ocr_path)
            if ocr_result:
                # Use FastPDFLoader on the OCR'd version
                return FastPDFLoader(ocr_result).load()
            else:
                logger.warning("OCR failed, falling back to regular extraction")
        
        # Use appropriate loader based on file size
        file_size_mb = os.path.getsize(self.file_path) / (1024 * 1024)
        if file_size_mb > 200:  # Files over 200MB
            return UltraLargePDFLoader(self.file_path).load()
        else:
            return FastPDFLoader(self.file_path).load()

class UltraLargePDFLoader:
    """Special PDF loader for extremely large files (>200MB) with aggressive memory management"""
    
    def __init__(self, file_path):
        self.file_path = file_path
        # Increase chunk size for better throughput
        self.chunk_size = 200  # Process 200 pages at a time for better performance
    
    def load(self):
        """Load ultra-large PDF in small chunks to avoid memory issues"""
        documents = []
        file_size_mb = os.path.getsize(self.file_path) / (1024 * 1024)
        logger.info(f"UltraLargePDFLoader processing {os.path.basename(self.file_path)} ({file_size_mb:.1f}MB)")
        
        try:
            import pypdf
            import gc  # For garbage collection
            import signal
            from contextlib import contextmanager
            
            # Parallel processing support for ultra-large files
            from concurrent.futures import ThreadPoolExecutor, as_completed
            import multiprocessing
            
            # Timeout context manager for chunk processing
            @contextmanager
            def timeout(seconds):
                def timeout_handler(signum, frame):
                    raise TimeoutError(f"Chunk processing timed out after {seconds} seconds")
                
                # Set the signal handler and alarm
                old_handler = signal.signal(signal.SIGALRM, timeout_handler)
                signal.alarm(seconds)
                try:
                    yield
                finally:
                    signal.alarm(0)
                    signal.signal(signal.SIGALRM, old_handler)
            
            # First pass - just get page count
            with open(self.file_path, 'rb') as file:
                pdf_reader = pypdf.PdfReader(file, strict=False)
                total_pages = len(pdf_reader.pages)
                logger.info(f"PDF has {total_pages} pages")
            
            # Process chunks in parallel for better performance
            successful_chunks = 0
            failed_chunks = 0
            chunk_timeout_seconds = 180  # 3 minutes per chunk
            
            # Determine optimal workers based on CPU cores
            max_workers = min(4, multiprocessing.cpu_count())
            logger.info(f"Using {max_workers} parallel workers for ultra-large PDF")
            
            def process_chunk(chunk_start, chunk_end):
                """Process a single chunk of pages"""
                chunk_docs = []
                try:
                    # Re-open file for each chunk to avoid memory buildup
                    with open(self.file_path, 'rb') as file:
                        pdf_reader = pypdf.PdfReader(file, strict=False)
                        
                        for page_num in range(chunk_start, chunk_end):
                            try:
                                page = pdf_reader.pages[page_num]
                                text = page.extract_text()
                                if text and text.strip():
                                    doc = Document(
                                        page_content=text,
                                        metadata={
                                            'source': self.file_path,
                                            'page': page_num
                                        }
                                    )
                                    chunk_docs.append(doc)
                            except Exception as e:
                                # Log but continue - we expect many errors with corrupted PDFs
                                if page_num % 100 == 0:  # Only log every 100th page
                                    logger.debug(f"Error on page {page_num}: {str(e)[:100]}")
                                continue
                    
                    # Force garbage collection after processing
                    gc.collect()
                    return chunk_docs
                except Exception as e:
                    logger.warning(f"Chunk {chunk_start}-{chunk_end} failed: {e}")
                    return []
            
            # Process chunks in parallel
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                futures = {}
                for chunk_start in range(0, total_pages, self.chunk_size):
                    chunk_end = min(chunk_start + self.chunk_size, total_pages)
                    logger.info(f"Submitting chunk: pages {chunk_start}-{chunk_end}")
                    future = executor.submit(process_chunk, chunk_start, chunk_end)
                    futures[future] = (chunk_start, chunk_end)
                
                # Collect results as they complete
                for future in as_completed(futures):
                    chunk_start, chunk_end = futures[future]
                    try:
                        chunk_docs = future.result(timeout=chunk_timeout_seconds)
                        documents.extend(chunk_docs)
                        successful_chunks += 1
                        logger.info(f"Completed chunk {chunk_start}-{chunk_end}: {len(chunk_docs)} pages extracted")
                    
                    except Exception as e:
                        logger.warning(f"Failed chunk {chunk_start}-{chunk_end}: {e}")
                        failed_chunks += 1
                        if failed_chunks > 5:  # Allow more failures for parallel processing
                            logger.error(f"Too many chunk failures ({failed_chunks}), continuing with partial extraction")
            
            logger.info(f"UltraLargePDFLoader extracted {len(documents)} pages from {total_pages} total pages")
            
            # If we got very little content, it might be a scanned PDF
            if len(documents) < total_pages * 0.1:  # Less than 10% of pages have text
                logger.warning(f"Very low text extraction rate ({len(documents)}/{total_pages}). May be a scanned PDF.")
            
            return documents
            
        except Exception as e:
            logger.error(f"UltraLargePDFLoader fatal error: {e}")
            return []

class FastPDFLoader:
    """Fast PDF loader using pypdf with parallel processing for large files"""
    
    def __init__(self, file_path):
        self.file_path = file_path
    
    def _extract_page_batch(self, pdf_reader, start_page, end_page):
        """Extract text from a batch of pages"""
        documents = []
        for page_num in range(start_page, min(end_page, len(pdf_reader.pages))):
            try:
                page = pdf_reader.pages[page_num]
                text = page.extract_text()
                if text.strip():  # Only add non-empty pages
                    doc = Document(
                        page_content=text,
                        metadata={
                            'source': self.file_path,
                            'page': page_num
                        }
                    )
                    documents.append(doc)
            except Exception as e:
                logger.warning(f"Error extracting page {page_num}: {e}")
                continue
        return documents
    
    def load(self):
        """Load PDF and return list of Document objects"""
        documents = []
        logger.info(f"FastPDFLoader starting to load {os.path.basename(self.file_path)}")
        
        try:
            # Check file size to determine processing strategy
            file_size_mb = os.path.getsize(self.file_path) / (1024 * 1024)
            
            with open(self.file_path, 'rb') as file:
                pdf_reader = pypdf.PdfReader(file, strict=False)
                total_pages = len(pdf_reader.pages)
                logger.info(f"PDF has {total_pages} pages, size: {file_size_mb:.1f}MB")
                
                # For large PDFs (>50MB or >500 pages), use parallel processing
                if file_size_mb > 50 or total_pages > 500:
                    logger.info(f"Using parallel processing for large PDF ({total_pages} pages)")
                    batch_size = 200  # Process 200 pages per batch for better throughput
                    
                    from concurrent.futures import ThreadPoolExecutor, as_completed
                    import multiprocessing
                    # Use more workers based on CPU cores
                    max_workers = min(8, max(4, multiprocessing.cpu_count()))
                    logger.info(f"Using {max_workers} workers for parallel PDF extraction")
                    with ThreadPoolExecutor(max_workers=max_workers) as executor:
                        # Submit batch jobs
                        futures = []
                        for start_page in range(0, total_pages, batch_size):
                            end_page = start_page + batch_size
                            future = executor.submit(self._extract_page_batch, pdf_reader, start_page, end_page)
                            futures.append((start_page, future))
                        
                        # Collect results in order
                        batch_results = {}
                        for start_page, future in futures:
                            try:
                                # Increased timeout: 5 minutes per batch for large PDFs
                                # This allows processing to continue as long as progress is being made
                                batch_docs = future.result(timeout=300)  # 5 minutes timeout per batch
                                batch_results[start_page] = batch_docs
                                logger.info(f"Processed pages {start_page}-{start_page+batch_size}")
                            except Exception as e:
                                logger.error(f"Error processing batch starting at page {start_page}: {e}")
                        
                        # Combine results in order
                        for start_page in sorted(batch_results.keys()):
                            documents.extend(batch_results[start_page])
                else:
                    # Process small PDFs sequentially
                    for page_num, page in enumerate(pdf_reader.pages):
                        try:
                            text = page.extract_text()
                            if text.strip():  # Only add non-empty pages
                                doc = Document(
                                    page_content=text,
                                    metadata={
                                        'source': self.file_path,
                                        'page': page_num
                                    }
                                )
                                documents.append(doc)
                        except Exception as e:
                            logger.warning(f"Error extracting page {page_num}: {e}")
                            continue
                        
            logger.info(f"FastPDFLoader extracted {len(documents)} pages from {os.path.basename(self.file_path)}")
            
            # For large PDFs with extraction issues, be more lenient
            if not documents and file_size_mb > 100:
                logger.warning(f"Large PDF {os.path.basename(self.file_path)} had no successful page extractions")
                # Try one more time with a simpler approach - just get any text we can
                try:
                    emergency_text = []
                    for i, page in enumerate(pdf_reader.pages[:10]):  # Try first 10 pages
                        try:
                            text = page.extract_text()
                            if text and text.strip():
                                emergency_text.append(text)
                        except:
                            continue
                    
                    if emergency_text:
                        logger.info(f"Emergency extraction got {len(emergency_text)} pages of content")
                        combined_text = "\n\n".join(emergency_text)
                        return [Document(
                            page_content=combined_text, 
                            metadata={"source": self.file_path, "page": "0-9", "extraction": "emergency"}
                        )]
                except Exception as e:
                    logger.error(f"Emergency extraction also failed: {e}")
            
            return documents
            
        except Exception as e:
            logger.error(f"FastPDFLoader error loading {self.file_path}: {e}")
            # Fall back to PyPDFLoader if pypdf fails
            logger.info("Falling back to PyPDFLoader...")
            return PyPDFLoader(self.file_path).load()

class MOBILoader:
    """MOBI/AZW/AZW3 ebook loader using Calibre's ebook-convert"""
    
    def __init__(self, file_path):
        self.file_path = file_path
    
    def load(self):
        """Load and extract text from MOBI file using Calibre"""
        try:
            from langchain.schema import Document
            import subprocess
            import tempfile
            
            logger.info(f"Loading MOBI file: {os.path.basename(self.file_path)}")
            
            # Check if Calibre's ebook-convert is available
            calibre_convert = "/Applications/calibre.app/Contents/MacOS/ebook-convert"
            if not os.path.exists(calibre_convert):
                # Try to find ebook-convert in PATH
                result = subprocess.run(['which', 'ebook-convert'], capture_output=True, text=True)
                if result.returncode == 0:
                    calibre_convert = result.stdout.strip()
                else:
                    logger.warning("Calibre's ebook-convert not found, falling back to basic extraction")
                    calibre_convert = None
            
            documents = []
            
            # Try using Calibre's ebook-convert if available
            if calibre_convert:
                try:
                    # Create a temporary text file for output
                    with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as tmp_file:
                        tmp_path = tmp_file.name
                    
                    # Convert MOBI to text using Calibre
                    cmd = [calibre_convert, self.file_path, tmp_path]
                    result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
                    
                    if result.returncode == 0:
                        # Read the converted text
                        with open(tmp_path, 'r', encoding='utf-8', errors='ignore') as f:
                            text = f.read()
                        
                        if text.strip():
                            doc = Document(
                                page_content=text,
                                metadata={
                                    'source': self.file_path,
                                    'file_type': os.path.splitext(self.file_path)[1].lower()[1:]  # Remove the dot
                                }
                            )
                            documents.append(doc)
                            logger.info(f"Successfully converted MOBI using Calibre")
                    else:
                        logger.warning(f"Calibre conversion failed: {result.stderr}")
                    
                    # Clean up temp file
                    try:
                        os.unlink(tmp_path)
                    except:
                        pass
                        
                except Exception as e:
                    logger.warning(f"Error using Calibre: {e}")
            
            # If Calibre failed or wasn't available, try the mobi library
            if not documents:
                try:
                    import mobi
                    tempdir = mobi.extract(self.file_path)
                except (ImportError, Exception) as e:
                    # If mobi library fails, try a simpler approach
                    logger.warning(f"MOBI extraction failed: {e}")
                    tempdir = None
                
                # Find the main HTML content
                html_files = []
                if tempdir:
                    for root, dirs, files in os.walk(tempdir):
                        for file in files:
                            if file.endswith('.html') or file.endswith('.htm'):
                                html_files.append(os.path.join(root, file))
                
                for html_file in html_files:
                    try:
                        # Read HTML content
                        with open(html_file, 'r', encoding='utf-8', errors='ignore') as f:
                            html_content = f.read()
                        
                        # Convert HTML to plain text
                        from bs4 import BeautifulSoup
                        soup = BeautifulSoup(html_content, 'html.parser')
                        
                        # Remove script and style elements
                        for script in soup(["script", "style"]):
                            script.decompose()
                        
                        # Get text
                        text = soup.get_text()
                        
                        # Clean up whitespace
                        lines = (line.strip() for line in text.splitlines())
                        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
                        text = ' '.join(chunk for chunk in chunks if chunk)
                        
                        if text.strip():
                            doc = Document(
                                page_content=text,
                                metadata={
                                    'source': self.file_path,
                                    'file_type': 'mobi'
                                }
                            )
                            documents.append(doc)
                            
                    except Exception as e:
                        logger.warning(f"Error processing HTML file {html_file}: {e}")
                        continue
            
                # Clean up temp directory
                if tempdir:
                    import shutil
                    try:
                        shutil.rmtree(tempdir)
                    except:
                        pass
            
            if not documents:
                # If mobi extraction failed, try as a simple text file
                logger.warning("MOBI extraction produced no content, trying simple text extraction")
                with open(self.file_path, 'rb') as f:
                    content = f.read()
                    # Try to decode as UTF-8, ignoring errors
                    text = content.decode('utf-8', errors='ignore')
                    # Remove null bytes and other control characters
                    text = ''.join(char for char in text if char.isprintable() or char.isspace())
                    if text.strip():
                        doc = Document(
                            page_content=text,
                            metadata={
                                'source': self.file_path,
                                'file_type': 'mobi'
                            }
                        )
                        documents.append(doc)
            
            logger.info(f"Successfully loaded MOBI file with {len(documents)} document(s)")
            return documents
            
        except Exception as e:
            logger.error(f"Error loading MOBI file {self.file_path}: {e}")
            # As a last resort, try UnstructuredFileLoader
            try:
                from langchain_community.document_loaders import UnstructuredFileLoader
                logger.info("Falling back to UnstructuredFileLoader for MOBI")
                return UnstructuredFileLoader(self.file_path).load()
            except Exception as e2:
                logger.error(f"UnstructuredFileLoader also failed: {e2}")
                return []

class SharedRAG:
    """Core RAG functionality shared between server and monitor"""
    
    def __init__(self, books_directory=None, db_directory=None):
        # Use config system if no explicit paths provided
        self.books_directory = books_directory if books_directory is not None else str(config.books_directory)
        self.db_directory = db_directory if db_directory is not None else str(config.db_directory)
        
        # Ensure directories exist
        config.ensure_directories()
        
        logger.info(f"SharedRAG initialized with books_directory: {self.books_directory}")
        logger.info(f"SharedRAG initialized with db_directory: {self.db_directory}")
        
        self.index_file = os.path.join(self.db_directory, "book_index.json")
        self.status_file = os.path.join(self.db_directory, "index_status.json")
        self.failed_pdfs_file = os.path.join(self.db_directory, "failed_pdfs.json")
        self.book_index = self.load_book_index()
        self.lock = IndexLock()
        
        # Thread safety for parallel processing
        import threading
        self._index_lock = threading.Lock()  # For book_index updates
        self._status_lock = threading.Lock()  # For status file updates
        
        # LRU cache for search results to prevent memory leaks
        self._search_cache = OrderedDict()
        self._cache_ttl = 300  # 5 minutes TTL
        self._max_cache_size = 50  # Maximum number of cached queries
        
        # Initialize embeddings
        logger.info("Initializing embeddings...")
        device = 'mps' if hasattr(torch, 'backends') and hasattr(torch.backends, 'mps') and torch.backends.mps.is_available() else 'cpu'
        
        # BACKUP: Original 384-dim model was "sentence-transformers/all-MiniLM-L6-v2"
        # Switching to original 768-dim model to match existing database
        self.embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-mpnet-base-v2",
            model_kwargs={'device': device},
            encode_kwargs={'normalize_embeddings': True}
        )
        
        # LLM initialization removed - using direct RAG results
        # logger.info("Initializing Ollama LLM...")
        # self.llm = Ollama(model="llama3.3:70b")
        
        # Initialize or load vector store
        self.vectorstore = self.initialize_vectorstore()
    
    def load_book_index(self):
        """Load the book index from disk"""
        if os.path.exists(self.index_file):
            try:
                with open(self.index_file, 'r') as f:
                    return json.load(f)
            except:
                return {}
        return {}
    
    def save_book_index(self):
        """Save the book index to disk (thread-safe)"""
        os.makedirs(self.db_directory, exist_ok=True)
        with self._index_lock:
            with open(self.index_file, 'w') as f:
                json.dump(self.book_index, f, indent=2)
    
    def update_status(self, status, details=None):
        """Update indexing status file (thread-safe)"""
        status_data = {
            "status": status,
            "timestamp": datetime.now().isoformat(),
            "details": details or {}
        }
        with self._status_lock:
            with open(self.status_file, 'w') as f:
                json.dump(status_data, f, indent=2)
    
    def get_indexing_status(self):
        """Get current indexing status"""
        if os.path.exists(self.status_file):
            try:
                with open(self.status_file, 'r') as f:
                    return json.load(f)
            except:
                pass
        return {"status": "idle", "timestamp": datetime.now().isoformat()}
    
    def get_status(self):
        """Legacy method name for backward compatibility"""
        return self.get_indexing_status()
    
    def get_lock_status(self):
        """Get detailed lock status"""
        return self.lock.get_lock_info()
    
    def update_progress(self, stage, current_page=None, total_pages=None, chunks_generated=None, current_file=None):
        """Update detailed progress tracking"""
        progress_file = os.path.join(self.db_directory, "indexing_progress.json")
        
        # Get memory usage
        try:
            process = psutil.Process()
            memory_mb = process.memory_info().rss / (1024 * 1024)
        except:
            memory_mb = 0
        
        progress_data = {
            "timestamp": datetime.now().isoformat(),
            "stage": stage,  # loading, extracting, chunking, embedding
            "current_page": current_page,
            "total_pages": total_pages,
            "chunks_generated": chunks_generated,
            "memory_mb": round(memory_mb, 1),
            "current_file": current_file or self.get_status().get('details', {}).get('current_file')
        }
        
        try:
            with open(progress_file, 'w') as f:
                json.dump(progress_data, f, indent=2)
        except Exception as e:
            logger.warning(f"Could not update progress: {e}")
    
    def is_process_healthy(self):
        """Check if the indexing process is healthy"""
        progress_file = os.path.join(self.db_directory, "indexing_progress.json")
        
        # Check if progress file exists
        if not os.path.exists(progress_file):
            return True  # No active indexing
        
        try:
            with open(progress_file, 'r') as f:
                progress = json.load(f)
            
            # Check timestamp age
            timestamp = datetime.fromisoformat(progress['timestamp'])
            age_seconds = (datetime.now() - timestamp).total_seconds()
            
            # If no update for more than 2 minutes, might be stuck
            if age_seconds > 120:
                logger.warning(f"Progress hasn't been updated for {age_seconds:.0f} seconds")
                return False
            
            # Check memory usage trends
            memory_mb = progress.get('memory_mb', 0)
            if memory_mb > 8000:  # More than 8GB
                logger.warning(f"High memory usage: {memory_mb:.0f} MB")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error checking process health: {e}")
            return True  # Assume healthy on error
    
    def get_file_hash(self, filepath):
        """Calculate MD5 hash of a file"""
        hash_md5 = hashlib.md5()
        with open(filepath, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    
    def initialize_vectorstore(self):
        """Initialize or load the vector store"""
        if os.path.exists(self.db_directory) and os.path.exists(os.path.join(self.db_directory, "chroma.sqlite3")):
            logger.info("Loading existing vector store...")
            return Chroma(
                persist_directory=self.db_directory,
                embedding_function=self.embeddings
            )
        else:
            logger.info("Creating new vector store...")
            os.makedirs(self.db_directory, exist_ok=True)
            return Chroma(
                embedding_function=self.embeddings,
                persist_directory=self.db_directory
            )
    
    def index_emails(self):
        """Index emails from Apple Mail and Outlook"""
        logger.info("Starting email indexing...")

        # Import email loaders
        try:
            from ..loaders.emlx_loader import EMLXLoader
            from ..loaders.outlook_loader import OutlookLocalLoader
            from ..loaders.email_loaders import EmailFilterConfig
        except ImportError as e:
            logger.error(f"Could not import email loaders: {e}")
            return 0

        # Create email filter configuration from environment
        filter_config = EmailFilterConfig({
            'max_age_days': int(os.getenv('PERSONAL_LIBRARY_EMAIL_MAX_AGE_DAYS', '365')),
            'excluded_folders': os.getenv('PERSONAL_LIBRARY_EMAIL_EXCLUDED_FOLDERS', 'Spam,Junk,Trash,Deleted Items,Drafts').split(','),
            'included_folders': os.getenv('PERSONAL_LIBRARY_EMAIL_INCLUDED_FOLDERS', '').split(',') if os.getenv('PERSONAL_LIBRARY_EMAIL_INCLUDED_FOLDERS') else [],
            'important_senders': os.getenv('PERSONAL_LIBRARY_EMAIL_IMPORTANT_SENDERS', '').split(',') if os.getenv('PERSONAL_LIBRARY_EMAIL_IMPORTANT_SENDERS') else []
        })

        all_email_documents = []
        email_sources = os.getenv('PERSONAL_LIBRARY_EMAIL_SOURCES', 'apple_mail').split(',')

        # Index Apple Mail if enabled
        if 'apple_mail' in email_sources:
            try:
                logger.info("Indexing Apple Mail emails...")
                emlx_loader = EMLXLoader(filter_config=filter_config)
                apple_mail_docs = emlx_loader.load()
                all_email_documents.extend(apple_mail_docs)
                logger.info(f"Indexed {len(apple_mail_docs)} Apple Mail emails")
            except Exception as e:
                logger.error(f"Error indexing Apple Mail: {e}")

        # Index Outlook if enabled
        if 'outlook_local' in email_sources:
            try:
                logger.info("Indexing Outlook emails...")
                olm_path = os.getenv('PERSONAL_LIBRARY_OUTLOOK_OLM_PATH')
                outlook_loader = OutlookLocalLoader(olm_path=olm_path, filter_config=filter_config)
                outlook_docs = outlook_loader.load()
                all_email_documents.extend(outlook_docs)
                logger.info(f"Indexed {len(outlook_docs)} Outlook emails")
            except Exception as e:
                logger.error(f"Error indexing Outlook: {e}")

        # Add emails to vector store if any were found
        if all_email_documents:
            logger.info(f"Adding {len(all_email_documents)} total email documents to vector store...")

            # Split emails into chunks if needed
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=1200,
                chunk_overlap=150
            )
            split_email_docs = text_splitter.split_documents(all_email_documents)

            # Add to vector store
            if self.vector_store is None:
                # Create new vector store
                self.vector_store = Chroma.from_documents(
                    documents=split_email_docs,
                    embedding=self.embeddings,
                    persist_directory=self.persist_directory
                )
            else:
                # Add to existing vector store
                self.vector_store.add_documents(split_email_docs)

            logger.info(f"Successfully indexed {len(all_email_documents)} emails")

        return len(all_email_documents)

    def find_new_or_modified_documents(self):
        """Find documents that need indexing (PDFs, Word docs, EPUBs)"""
        if not os.path.exists(self.books_directory):
            return []
        
        # Supported file extensions (including email formats)
        supported_extensions = ('.pdf', '.docx', '.doc', '.epub', '.mobi', '.azw', '.azw3', '.pptx', '.ppt', '.emlx', '.eml', '.olm')
        documents_to_index = []
        
        for root, dirs, files in os.walk(self.books_directory):
            # Skip .ocr_cache directories to prevent recursive processing
            if '.ocr_cache' in dirs:
                dirs.remove('.ocr_cache')
            
            # Also skip if current directory is within .ocr_cache
            if '.ocr_cache' in root:
                continue
                
            for file in files:
                if file.lower().endswith(supported_extensions):
                    filepath = os.path.join(root, file)
                    rel_path = os.path.relpath(filepath, self.books_directory)
                    
                    # Skip files that are already marked as failed
                    if self.is_document_failed(rel_path):
                        logger.debug(f"Skipping failed document: {rel_path}")
                        continue
                    
                    # Skip files that have OCR versions
                    if self.is_document_skipped(rel_path):
                        logger.debug(f"Skipping document with OCR version: {rel_path}")
                        continue
                    
                    file_hash = self.get_file_hash(filepath)
                    
                    if rel_path not in self.book_index or self.book_index[rel_path].get('hash') != file_hash:
                        documents_to_index.append((filepath, rel_path))
        
        return documents_to_index
    
    def find_new_or_modified_pdfs(self):
        """Legacy method - now calls find_new_or_modified_documents for backward compatibility"""
        return self.find_new_or_modified_documents()
    
    def get_document_loader(self, filepath):
        """Get the appropriate document loader based on file extension"""
        file_ext = os.path.splitext(filepath)[1].lower()
        
        if file_ext == '.pdf':
            return OCRPDFLoader(filepath)  # Use OCR-enabled PDF loader
        elif file_ext in ['.docx', '.doc']:
            return UnstructuredWordDocumentLoader(filepath)
        elif file_ext == '.epub':
            return UnstructuredEPubLoader(filepath)
        elif file_ext in ['.mobi', '.azw', '.azw3']:
            # Use custom MOBI loader for MOBI/Kindle formats
            return MOBILoader(filepath)
        elif file_ext in ['.pptx', '.ppt']:
            return UnstructuredPowerPointLoader(filepath)
        else:
            raise ValueError(f"Unsupported file type: {file_ext}")
    
    def get_document_type(self, filepath):
        """Get a human-readable document type from file extension"""
        file_ext = os.path.splitext(filepath)[1].lower()
        
        type_mapping = {
            '.pdf': 'PDF',
            '.docx': 'Word Document',
            '.doc': 'Word Document',
            '.epub': 'EPUB Book',
            '.mobi': 'MOBI Book',
            '.azw': 'Kindle Book',
            '.azw3': 'Kindle Book (AZW3)',
            '.pptx': 'PowerPoint Presentation',
            '.ppt': 'PowerPoint Presentation'
        }
        
        return type_mapping.get(file_ext, 'Document')
    
    def process_document_with_timeout(self, filepath, rel_path=None, timeout_minutes=60):
        """Process any supported document with timeout protection"""
        # For very large files, increase timeout proportionally
        file_size_mb = os.path.getsize(filepath) / (1024 * 1024)
        
        # Scale timeout based on file size - allow more time for larger files
        # Approximately 1 minute per 10MB for ultra-large files
        if file_size_mb > 500:
            timeout_minutes = max(60, int(file_size_mb / 10))
            logger.info(f"Ultra-large file ({file_size_mb:.1f}MB), using extended timeout of {timeout_minutes} minutes")
        elif file_size_mb > 200:
            timeout_minutes = max(30, int(file_size_mb / 15))
            logger.info(f"Large file ({file_size_mb:.1f}MB), using timeout of {timeout_minutes} minutes")
        
        with ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(self.process_document, filepath, rel_path)
            try:
                return future.result(timeout=timeout_minutes * 60)
            except FutureTimeoutError:
                logger.error(f"Processing timeout after {timeout_minutes} minutes for {filepath}")
                # Always record the failure so we can skip it next time
                self.handle_failed_document(filepath, f"Processing timeout after {timeout_minutes} minutes - file size: {file_size_mb:.1f}MB")
                return False
            except Exception as e:
                logger.error(f"Error in thread: {e}")
                return False
    
    def process_pdf_with_timeout(self, filepath, rel_path=None, timeout_minutes=30):
        """Legacy method - now calls process_document_with_timeout for backward compatibility"""
        return self.process_document_with_timeout(filepath, rel_path, timeout_minutes)
    
    def prepare_file_for_processing(self, filepath, rel_path):
        """Prepare file for processing, handling CloudDocs permission issues"""
        # Check if this is a CloudDocs file
        if "Mobile Documents/com~apple~CloudDocs" in filepath:
            logger.info(f"CloudDocs file detected, creating accessible copy: {rel_path}")
            
            # Create temp directory for CloudDocs files
            temp_dir = os.path.join(self.db_directory, "temp_cloudocs")
            os.makedirs(temp_dir, exist_ok=True)
            
            # Create safe filename from rel_path
            safe_filename = rel_path.replace("/", "_").replace(" ", "_")
            temp_filepath = os.path.join(temp_dir, safe_filename)
            
            try:
                # Copy file to accessible location
                shutil.copy2(filepath, temp_filepath)
                logger.info(f"Created temporary copy at: {temp_filepath}")
                return temp_filepath
            except Exception as e:
                logger.error(f"Failed to copy CloudDocs file: {e}")
                # Fall back to original path and let the error happen
                return filepath
        else:
            # Regular file, use as-is
            return filepath
    
    def cleanup_temp_file(self, working_filepath, original_filepath):
        """Clean up temporary file if it was created"""
        if working_filepath != original_filepath:
            try:
                os.remove(working_filepath)
                logger.debug(f"Cleaned up temporary file: {working_filepath}")
            except Exception as e:
                logger.warning(f"Could not clean up temporary file {working_filepath}: {e}")
    
    def process_document(self, filepath, rel_path=None):
        """Process any supported document and add it to the index"""
        if not rel_path:
            rel_path = os.path.relpath(filepath, self.books_directory)
        
        working_filepath = filepath  # Initialize to original path
        
        try:
            doc_type = self.get_document_type(filepath)
            logger.info(f"Processing {doc_type}: {rel_path}")
            
            # Update status but preserve any existing details like progress
            try:
                with open(self.status_file, 'r') as f:
                    current_status = json.load(f)
                    existing_details = current_status.get('details', {})
            except:
                existing_details = {}
            
            # Preserve critical progress fields if they exist
            preserved_fields = ['progress', 'success', 'failed', 'percentage', 'parallel_workers']
            preserved_data = {}
            for field in preserved_fields:
                if field in existing_details:
                    preserved_data[field] = existing_details[field]
            
            # Update current file while preserving progress tracking
            preserved_data['current_file'] = rel_path
            self.update_status("indexing", preserved_data)
            self.update_progress("starting", current_file=rel_path)
            
            # Check file size before processing
            file_size_mb = os.path.getsize(filepath) / (1024 * 1024)
            if file_size_mb > 2048:  # Skip files larger than 2GB (2048MB)
                logger.warning(f"Skipping {rel_path}: File too large ({file_size_mb:.1f}MB)")
                self.handle_failed_document(filepath, f"File too large: {file_size_mb:.1f}MB")
                return False
            
            # Handle CloudDocs permission issue by copying to temp location if needed
            working_filepath = self.prepare_file_for_processing(filepath, rel_path)
            
            # Load the document using appropriate loader with timeout protection
            self.update_progress("loading", current_file=rel_path)
            logger.info(f"Loading {doc_type}: {rel_path} ({file_size_mb:.1f}MB)")
            
            # Set timeout based on file size
            # Small files (<10MB): 3 minutes (180 seconds)
            # Medium files (10-50MB): 6 minutes (360 seconds)  
            # Large files (50-200MB): 15 minutes (900 seconds)
            # Very large files (200-300MB): 30 minutes (1800 seconds)
            # Huge files (>300MB): 120 minutes for extremely large documents
            # Special case for ultra-large documents like 40k page PDFs
            if file_size_mb < 10:
                timeout_seconds = 180  # 3 minutes
            elif file_size_mb < 50:
                timeout_seconds = 360  # 6 minutes
            elif file_size_mb < 200:
                timeout_seconds = 900  # 15 minutes
            elif file_size_mb < 300:
                timeout_seconds = 1800  # 30 minutes
            else:
                # For very large files, estimate based on pages if possible
                # Allow up to 2 hours for massive documents
                timeout_seconds = 7200  # 120 minutes for files >300MB
            
            logger.info(f"Processing with {timeout_seconds}s timeout for {file_size_mb:.1f}MB file")
            
            # Use threading to implement timeout with progress monitoring
            import threading
            import queue
            import time
            
            result_queue = queue.Queue()
            exception_queue = queue.Queue()
            progress_file = os.path.join(self.db_directory, "indexing_progress.json")
            
            def load_with_timeout():
                try:
                    # Get file extension for cleanup check
                    file_ext = os.path.splitext(working_filepath)[1].lower()
                    
                    loader = self.get_document_loader(working_filepath)
                    docs = loader.load()
                    
                    # EPUB file descriptor cleanup
                    # EPUBs can leave many file descriptors open, so we need to ensure cleanup
                    if file_ext == '.epub':
                        import gc
                        # Force garbage collection to close any lingering file handles
                        gc.collect()
                        # If the loader has any cleanup methods, call them
                        if hasattr(loader, 'close'):
                            loader.close()
                        if hasattr(loader, '__del__'):
                            try:
                                loader.__del__()
                            except:
                                pass
                    
                    result_queue.put(docs)
                except Exception as e:
                    exception_queue.put(e)
            
            # Start the loading in a separate thread
            load_thread = threading.Thread(target=load_with_timeout)
            load_thread.daemon = True
            load_thread.start()
            
            # Monitor progress with adaptive timeout
            start_time = time.time()
            last_progress_time = start_time
            last_progress_value = None
            extensions_granted = 0
            max_extensions = 5  # Allow up to 5 extensions
            
            # Calculate extension time based on file size
            # Small files: 5 minutes extension
            # Medium files: 10 minutes extension
            # Large files: 15 minutes extension
            # Very large/Huge files: 20 minutes extension
            if file_size_mb < 10:
                extension_time = 300  # 5 minutes
            elif file_size_mb < 50:
                extension_time = 600  # 10 minutes
            elif file_size_mb < 200:
                extension_time = 900  # 15 minutes
            else:
                extension_time = 1200  # 20 minutes
            
            while load_thread.is_alive():
                elapsed = time.time() - start_time
                time_since_progress = time.time() - last_progress_time
                
                # Check progress every 10 seconds, ensuring non-negative sleep
                remaining_time = timeout_seconds - elapsed
                time.sleep(min(10, max(0, remaining_time)))
                
                # Read current progress
                try:
                    if os.path.exists(progress_file):
                        with open(progress_file, 'r') as f:
                            progress_data = json.load(f)
                            current_progress = progress_data.get('chunks_generated') or progress_data.get('current_page')
                            
                            # Check if progress has been made
                            if current_progress and current_progress != last_progress_value:
                                logger.info(f"Progress detected: {current_progress} (was {last_progress_value})")
                                last_progress_value = current_progress
                                last_progress_time = time.time()
                except:
                    pass  # Ignore errors reading progress
                
                # Check if we should timeout
                if elapsed > timeout_seconds:
                    # Check if progress was made recently (within last 5 minutes for continuous extension)
                    if time_since_progress < 300 and extensions_granted < max_extensions:
                        extensions_granted += 1
                        timeout_seconds += extension_time
                        logger.info(f"Extending timeout by {extension_time/60:.0f} minutes due to recent progress (extension {extensions_granted}/{max_extensions}, total time: {timeout_seconds/60:.0f} minutes)")
                    else:
                        # No recent progress or max extensions reached
                        logger.error(f"Timeout after {elapsed:.0f}s loading {rel_path} ({file_size_mb:.1f}MB)")
                        if extensions_granted > 0:
                            logger.info(f"Granted {extensions_granted} extensions but no recent progress in {time_since_progress/60:.1f} minutes")
                        # Try to terminate the thread cleanly if possible
                        # Note: Thread termination in Python is limited, but we can try to signal it
                        self.handle_failed_document(filepath, f"Timeout after {elapsed:.0f}s - file may be corrupted or too complex")
                        return False
                
                if not load_thread.is_alive():
                    break
            
            # Check for exceptions
            if not exception_queue.empty():
                error = exception_queue.get()
                raise error
            
            # Get the result
            if result_queue.empty():
                raise Exception("No result from document loader")
            
            documents = result_queue.get()
            
            if not documents:
                raise Exception(f"No content extracted from {doc_type}")
            
            # For non-PDF documents, we don't have page count, so use document count
            total_sections = len(documents)
            logger.info(f"Loaded {total_sections} sections from {rel_path}")
            self.update_progress("extracting", total_pages=total_sections, current_file=rel_path)
            
            # Split into chunks with optimized parameters
            logger.info(f"Splitting {rel_path} into chunks...")
            self.update_progress("chunking", total_pages=total_sections, current_file=rel_path)
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=1200,  # Slightly larger chunks for better context
                chunk_overlap=150,  # Less overlap for efficiency
                separators=["\n\n", "\n", ". ", " ", ""],
                length_function=len
            )
            
            chunks = text_splitter.split_documents(documents)
            logger.info(f"Created {len(chunks)} chunks from {rel_path}")
            self.update_progress("chunking", total_pages=total_sections, chunks_generated=len(chunks), current_file=rel_path)
            
            # Add metadata
            for chunk in chunks:
                chunk.metadata['book'] = os.path.basename(filepath)
                chunk.metadata['document_type'] = doc_type
                chunk.metadata['indexed_at'] = datetime.now().isoformat()
                
                # Categorize content
                content = chunk.page_content.lower()
                if any(word in content for word in ['meditation', 'mindfulness', 'breath', 'breathing']):
                    chunk.metadata['type'] = 'practice'
                elif any(word in content for word in ['energy', 'chakra', 'healing', 'aura']):
                    chunk.metadata['type'] = 'energy_work'
                elif any(word in content for word in ['conscious', 'awareness', 'enlighten', 'spiritual']):
                    chunk.metadata['type'] = 'philosophy'
                else:
                    chunk.metadata['type'] = 'general'
            
            # Remove old chunks if re-indexing
            if rel_path in self.book_index:
                self.remove_book_by_path(rel_path, skip_save=True)
            
            # Add to vector store with batch optimization
            logger.info(f"Adding {len(chunks)} chunks to vector store...")
            self.update_progress("embedding", total_pages=total_sections, chunks_generated=len(chunks), current_file=rel_path)
            
            # Add in batches for better performance
            batch_size = 100
            for i in range(0, len(chunks), batch_size):
                batch = chunks[i:i + batch_size]
                self.vectorstore.add_documents(batch)
                if i + batch_size < len(chunks):
                    self.update_progress("embedding", total_pages=total_sections, 
                                       chunks_generated=len(chunks), 
                                       current_file=rel_path,
                                       current_page=f"Batch {i//batch_size + 1}/{(len(chunks) + batch_size - 1)//batch_size}")
            
            self.vectorstore.persist()
            self.update_progress("completed", total_pages=total_sections, chunks_generated=len(chunks), current_file=rel_path)
            
            # Update index (thread-safe)
            with self._index_lock:
                self.book_index[rel_path] = {
                    'hash': self.get_file_hash(filepath),
                    'chunks': len(chunks),
                    'pages': total_sections,  # For non-PDFs, this represents sections/documents
                    'document_type': doc_type,
                    'indexed_at': datetime.now().isoformat()
                }
            self.save_book_index()
            
            logger.info(f"Successfully indexed {rel_path}: {len(chunks)} chunks from {total_sections} sections")
            
            # Remove from failed list if it was previously failed
            self.remove_from_failed_list(rel_path)
            
            # Clean up temporary file if it was created
            self.cleanup_temp_file(working_filepath, filepath)
            
            # Force garbage collection to free memory
            import gc
            gc.collect()
            
            return True
            
        except Exception as e:
            logger.error(f"Error processing {filepath}: {str(e)}")
            self.handle_failed_document(filepath, str(e))
            
            # Clean up temporary file if it was created
            self.cleanup_temp_file(working_filepath, filepath)
            
            # Force garbage collection even on error
            import gc
            gc.collect()
            
            return False
    
    def process_pdf(self, filepath, rel_path=None):
        """Legacy method - now calls process_document for backward compatibility"""
        return self.process_document(filepath, rel_path)
    
    def _update_failed_list_with_lock(self, update_func):
        """
        Thread-safe update of failed_pdfs.json with file locking.
        update_func receives the current dict and should return the updated dict.
        """
        lock_file = self.failed_pdfs_file + '.lock'
        max_retries = 10
        retry_delay = 0.1
        
        for attempt in range(max_retries):
            try:
                # Create or open lock file
                lock_fd = os.open(lock_file, os.O_CREAT | os.O_WRONLY)
                
                try:
                    # Acquire exclusive lock (blocking with timeout via retries)
                    fcntl.flock(lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
                    
                    # Read current content
                    failed_docs = {}
                    if os.path.exists(self.failed_pdfs_file):
                        try:
                            with open(self.failed_pdfs_file, 'r') as f:
                                failed_docs = json.load(f)
                        except:
                            pass
                    
                    # Apply the update
                    updated_docs = update_func(failed_docs)
                    
                    # Write back atomically
                    temp_file = self.failed_pdfs_file + '.tmp'
                    with open(temp_file, 'w') as f:
                        json.dump(updated_docs, f, indent=2)
                    
                    # Atomic rename
                    os.rename(temp_file, self.failed_pdfs_file)
                    
                    # Release lock
                    fcntl.flock(lock_fd, fcntl.LOCK_UN)
                    os.close(lock_fd)
                    
                    return True
                    
                except BlockingIOError:
                    # Lock is held by another process, retry
                    os.close(lock_fd)
                    if attempt < max_retries - 1:
                        time.sleep(retry_delay)
                        retry_delay *= 2  # Exponential backoff
                    else:
                        logger.warning(f"Could not acquire lock for failed_pdfs.json after {max_retries} attempts")
                        return False
                        
            except Exception as e:
                logger.error(f"Error updating failed list: {e}")
                if 'lock_fd' in locals():
                    try:
                        os.close(lock_fd)
                    except:
                        pass
                return False
        
        return False
    
    def handle_failed_document(self, filepath, error_msg):
        """Handle a document that failed to index by attempting to clean it (PDFs only)"""
        # Use full path as key to avoid collisions
        # This fixes the issue where only basename was used, causing failures to overwrite each other
        rel_path = os.path.relpath(filepath, self.books_directory) if hasattr(self, 'books_directory') else filepath
        
        # Only attempt cleaning for PDFs
        if not filepath.lower().endswith('.pdf'):
            # For non-PDF documents, just log the failure
            def update_failed(failed_docs):
                # Use relative path as key to avoid collisions
                failed_docs[rel_path] = {
                    "error": error_msg,
                    "cleaned": False,
                    "failed_at": datetime.now().isoformat(),
                    "full_path": filepath
                }
                return failed_docs
            
            self._update_failed_list_with_lock(update_failed)
            
            return False
        
        # For PDFs, attempt cleaning
        return self.handle_failed_pdf(filepath, error_msg)
    
    def remove_from_failed_list(self, rel_path):
        """Remove a document from the failed list if it exists"""
        try:
            if not os.path.exists(self.failed_pdfs_file):
                return
            
            with open(self.failed_pdfs_file, 'r') as f:
                failed_docs = json.load(f)
            
            # Try different variations of the path
            doc_name = os.path.basename(rel_path)
            variations = [
                rel_path,
                doc_name,
                os.path.join(self.books_directory, rel_path)
            ]
            
            removed = False
            for variation in variations:
                if variation in failed_docs:
                    del failed_docs[variation]
                    removed = True
                    logger.info(f"Removed {variation} from failed list after successful indexing")
            
            if removed:
                def update_removed(current_docs):
                    return failed_docs  # Use the already modified failed_docs
                self._update_failed_list_with_lock(update_removed)
                    
        except Exception as e:
            # Don't let this error stop the indexing process
            logger.debug(f"Could not remove from failed list: {e}")
    
    def handle_failed_pdf(self, filepath, error_msg):
        """Handle a PDF that failed to index by attempting to clean it"""
        # Use relative path to avoid collisions
        rel_path = os.path.relpath(filepath, self.books_directory) if hasattr(self, 'books_directory') else filepath
        pdf_name = os.path.basename(filepath)
        
        # Load failed PDFs log
        failed_pdfs = {}
        if os.path.exists(self.failed_pdfs_file):
            try:
                with open(self.failed_pdfs_file, 'r') as f:
                    failed_pdfs = json.load(f)
            except:
                pass
        
        # Don't retry if already cleaned
        if rel_path in failed_pdfs and failed_pdfs[rel_path].get("cleaned", False):
            return False
        
        logger.info(f"Attempting to clean failed PDF: {pdf_name}")
        
        # Create tmp directory in db_directory (not in books directory)
        tmp_dir = os.path.join(self.db_directory, "tmp_cleaned_pdfs")
        os.makedirs(tmp_dir, exist_ok=True)
        
        # Paths
        temp_cleaned = os.path.join(tmp_dir, pdf_name + ".cleaned")
        
        # Try to clean
        if PDFCleaner.clean_pdf(filepath, temp_cleaned):
            try:
                # Don't replace the original file - just try indexing the cleaned version
                logger.info(f"Successfully cleaned {pdf_name}. Trying to index cleaned version.")
                
                # Try indexing the cleaned file directly
                result = self.process_pdf(temp_cleaned, rel_path=os.path.relpath(filepath, self.books_directory))
                
                if result:
                    # If indexing succeeded, we can optionally replace the original
                    # For now, just mark it as cleaned successfully
                    failed_pdfs[rel_path] = {
                        "error": error_msg,
                        "cleaned": True,
                        "cleaned_at": datetime.now().isoformat(),
                        "indexed_cleaned": True,
                        "full_path": filepath
                    }
                else:
                    # Cleaned but still failed to index
                    failed_pdfs[rel_path] = {
                        "error": error_msg,
                        "cleaned": True,
                        "cleaned_at": datetime.now().isoformat(),
                        "indexed_cleaned": False,
                        "final_error": "Cleaned but still failed to index",
                        "full_path": filepath
                    }
                
                def update_cleaned(current_docs):
                    # Merge our updates into current state
                    current_docs.update(failed_pdfs)
                    return current_docs
                self._update_failed_list_with_lock(update_cleaned)
                
                # Clean up the temp file
                try:
                    os.remove(temp_cleaned)
                except:
                    pass
                
                return result
                
            except Exception as e:
                logger.error(f"Error during cleaning process: {e}")
        else:
            # Record failure
            failed_pdfs[rel_path] = {
                "error": error_msg,
                "cleaned": False,
                "attempted_at": datetime.now().isoformat(),
                "full_path": filepath
            }
            def update_attempted(current_docs):
                # Merge our updates into current state
                current_docs[rel_path] = failed_pdfs[rel_path]
                return current_docs
            self._update_failed_list_with_lock(update_attempted)
        
        return False
    
    def is_document_failed(self, rel_path):
        """Check if a document is in the failed list"""
        if os.path.exists(self.failed_pdfs_file):
            try:
                with open(self.failed_pdfs_file, 'r') as f:
                    failed_docs = json.load(f)
                    # Check both relative path and basename for backward compatibility
                    return rel_path in failed_docs or os.path.basename(rel_path) in failed_docs
            except:
                pass
        return False
    
    def is_document_skipped(self, rel_path):
        """Check if a document is in the skip list (has OCR version)"""
        skip_list_file = os.path.join(self.db_directory, 'skip_list.json')
        if os.path.exists(skip_list_file):
            try:
                with open(skip_list_file, 'r') as f:
                    skip_list = json.load(f)
                    # Check both relative path and basename
                    return rel_path in skip_list or os.path.basename(rel_path) in skip_list
            except:
                pass
        return False
    
    def remove_book_by_path(self, rel_path, skip_save=False):
        """Remove a book from the index by relative path"""
        if rel_path not in self.book_index:
            return
        
        try:
            # Delete from vector store
            book_name = os.path.basename(rel_path)
            collection = self.vectorstore._collection
            collection.delete(where={"book": book_name})
            
            # Remove from index (thread-safe)
            with self._index_lock:
                del self.book_index[rel_path]
            if not skip_save:
                self.save_book_index()
            
            logger.info(f"Removed {rel_path} from index")
        except Exception as e:
            logger.error(f"Error removing {rel_path}: {str(e)}")
    
    def search(self, query, k=10, filter_type=None, synthesize=False):
        """Search the vector store with caching"""
        if not self.vectorstore:
            return []
        
        # Create cache key
        cache_key = f"{query}:{k}:{filter_type}"
        
        # Check cache
        if cache_key in self._search_cache:
            cached_result, timestamp = self._search_cache[cache_key]
            if time.time() - timestamp < self._cache_ttl:
                logger.debug(f"Cache hit for query: {query[:50]}...")
                # Move to end (most recently used)
                self._search_cache.move_to_end(cache_key)
                return cached_result
            else:
                # Remove expired entry
                del self._search_cache[cache_key]
        
        try:
            search_kwargs = {"k": min(k, self.vectorstore._collection.count() or 1)}
            if filter_type:
                search_kwargs["filter"] = {"type": filter_type}
            
            results = self.vectorstore.similarity_search_with_score(
                query, **search_kwargs
            )
            
            formatted_results = []
            for doc, score in results:
                formatted_results.append({
                    "content": doc.page_content,
                    "source": doc.metadata.get('book', 'Unknown'),
                    "page": doc.metadata.get('page', 'Unknown'),
                    "type": doc.metadata.get('type', 'general'),
                    "relevance_score": float(score)
                })
            
            # Cache the results
            self._search_cache[cache_key] = (formatted_results, time.time())
            
            # Enforce max cache size (LRU eviction)
            while len(self._search_cache) > self._max_cache_size:
                # Remove oldest item (first in OrderedDict)
                self._search_cache.popitem(last=False)
            
            # Also clean expired entries periodically
            if len(self._search_cache) > self._max_cache_size // 2:
                current_time = time.time()
                expired_keys = [
                    k for k, (_, timestamp) in self._search_cache.items()
                    if current_time - timestamp >= self._cache_ttl
                ]
                for k in expired_keys:
                    del self._search_cache[k]
            
            # Always return direct results (synthesis removed)
            return formatted_results
            
        except Exception as e:
            logger.error(f"Search error: {str(e)}")
            return []
    
    def synthesize_results(self, query, context_chunks):
        """Stub method - synthesis now handled by Claude"""
        # This method is kept for backward compatibility but no longer used
        # Claude will synthesize the raw results directly
        return "Direct results provided - synthesis to be done by Claude for article writing."

    def find_book_by_fuzzy_match(self, book_pattern, cutoff=0.6):
        """Find book(s) using fuzzy matching

        Args:
            book_pattern: Partial or fuzzy book name to match
            cutoff: Similarity threshold (0.0-1.0), default 0.6

        Returns:
            tuple: (matched_books, exact_match_found, similarity_scores)
        """
        book_pattern_lower = book_pattern.lower()
        all_books = list(self.book_index.keys())

        # First try exact substring match (case-insensitive)
        exact_matches = []
        for book_path in all_books:
            book_path_lower = book_path.lower()
            book_name_lower = os.path.basename(book_path).lower()

            # Try exact match on full path or just filename
            if book_pattern_lower == book_path_lower or book_pattern_lower == book_name_lower:
                return ([book_path], True, {book_path: 1.0})

            # Try exact match with .pdf/.docx extension added
            if (book_pattern_lower + '.pdf' == book_name_lower or
                book_pattern_lower + '.docx' == book_name_lower or
                book_pattern_lower + '.doc' == book_name_lower or
                book_pattern_lower + '.epub' == book_name_lower):
                return ([book_path], True, {book_path: 1.0})

            # Substring match
            if book_pattern_lower in book_path_lower or book_pattern_lower in book_name_lower:
                exact_matches.append(book_path)

        if exact_matches:
            if len(exact_matches) == 1:
                return (exact_matches, True, {exact_matches[0]: 0.9})
            else:
                # Multiple substring matches - return all with high scores
                return (exact_matches, False, {path: 0.9 for path in exact_matches})

        # No exact matches, use fuzzy matching
        # Create a list of book names (without directory path) for better matching
        book_names = [os.path.basename(path) for path in all_books]

        # Use difflib to find close matches
        close_matches = difflib.get_close_matches(
            book_pattern,
            book_names,
            n=5,  # Return up to 5 matches
            cutoff=cutoff
        )

        if not close_matches:
            # Try again with just the pattern against basenames (case-insensitive)
            close_matches = difflib.get_close_matches(
                book_pattern_lower,
                [name.lower() for name in book_names],
                n=5,
                cutoff=cutoff
            )

            # Map back to original book names
            if close_matches:
                close_matches = [
                    book_names[i] for i, name in enumerate([n.lower() for n in book_names])
                    if name in close_matches
                ]

        # Map matched names back to full paths and calculate similarity scores
        matched_books = []
        similarity_scores = {}

        for matched_name in close_matches:
            for book_path in all_books:
                if os.path.basename(book_path) == matched_name or os.path.basename(book_path).lower() == matched_name.lower():
                    matched_books.append(book_path)
                    # Calculate similarity score
                    score = difflib.SequenceMatcher(
                        None,
                        book_pattern_lower,
                        os.path.basename(book_path).lower()
                    ).ratio()
                    similarity_scores[book_path] = score
                    break

        # Sort by similarity score (highest first)
        matched_books.sort(key=lambda x: similarity_scores.get(x, 0), reverse=True)

        return (matched_books, False, similarity_scores)

    def extract_pages(self, book_pattern, pages):
        """Extract specific pages from a book (or chunks for non-PDF documents)

        Args:
            book_pattern: Partial or fuzzy book name to match (uses fuzzy matching)
            pages: Can be:
                - int: Single page number (or chunk index for non-PDFs)
                - list[int]: List of page numbers (or chunk indices)
                - str: Page range like "10-15" (or chunk range for non-PDFs)

        Returns:
            dict with book info and extracted pages/chunks
        """
        # Use fuzzy matching to find the book
        matching_books, exact_match, similarity_scores = self.find_book_by_fuzzy_match(book_pattern, cutoff=0.6)

        if not matching_books:
            return {
                "error": f"No books found matching '{book_pattern}'",
                "suggestion": "Try using a different part of the book name or check spelling",
                "available_books": list(self.book_index.keys())[:10]  # Show first 10 as suggestions
            }

        if len(matching_books) > 1:
            # Sort by similarity and show top matches with scores
            matches_with_scores = [
                {
                    "book": book,
                    "similarity": f"{similarity_scores.get(book, 0):.2%}"
                }
                for book in matching_books[:5]  # Show top 5
            ]
            return {
                "error": f"Multiple books match '{book_pattern}'. Please be more specific.",
                "matching_books": matches_with_scores,
                "suggestion": "Use a more specific part of the book name"
            }

        book_path = matching_books[0]
        book_name = os.path.basename(book_path)
        book_info = self.book_index.get(book_path, {})
        doc_type = book_info.get('document_type', 'Unknown')

        # Check if this is a PDF with actual page numbers
        is_pdf = book_path.lower().endswith('.pdf')

        # Parse page/chunk numbers
        if isinstance(pages, int):
            page_list = [pages]
        elif isinstance(pages, list):
            page_list = pages
        elif isinstance(pages, str) and '-' in pages:
            try:
                start, end = map(int, pages.split('-'))
                page_list = list(range(start, end + 1))
            except:
                return {"error": f"Invalid page range format: '{pages}'. Use format like '10-15'"}
        else:
            return {"error": f"Invalid pages format: {pages}"}

        # Query vector store for pages/chunks from this specific book
        extracted_pages = {}

        if self.vectorstore:
            if is_pdf:
                # PDFs: Extract by page number
                for page_num in page_list:
                    try:
                        # Get all chunks from this page using ChromaDB's filter syntax
                        results = self.vectorstore._collection.get(
                            where={"$and": [
                                {"book": {"$eq": book_name}},
                                {"page": {"$eq": page_num}}
                            ]},
                            include=["documents", "metadatas"]
                        )

                        if results and results['documents']:
                            # Combine chunks from the same page
                            page_content = "\n".join(results['documents'])
                            extracted_pages[page_num] = {
                                "content": page_content,
                                "chunks": len(results['documents'])
                            }
                        else:
                            # Try alternative query method
                            search_results = self.vectorstore.similarity_search(
                                f"page {page_num}",
                                k=10,
                                filter={"book": book_name}
                            )

                            page_chunks = []
                            for doc in search_results:
                                if doc.metadata.get('page') == page_num:
                                    page_chunks.append(doc.page_content)

                            if page_chunks:
                                extracted_pages[page_num] = {
                                    "content": "\n".join(page_chunks),
                                    "chunks": len(page_chunks)
                                }
                            else:
                                extracted_pages[page_num] = {
                                    "content": f"Page {page_num} not found in index",
                                    "chunks": 0
                                }

                    except Exception as e:
                        logger.error(f"Error extracting page {page_num}: {str(e)}")
                        extracted_pages[page_num] = {
                            "content": f"Error extracting page: {str(e)}",
                            "chunks": 0
                        }
            else:
                # Non-PDFs (Word, EPUB, etc.): Extract by chunk index
                try:
                    # Get all chunks from this book
                    results = self.vectorstore._collection.get(
                        where={"book": {"$eq": book_name}},
                        include=["documents", "metadatas"]
                    )

                    if results and results['documents']:
                        all_chunks = results['documents']
                        total_chunks = len(all_chunks)

                        # Extract requested chunks (treating page numbers as chunk indices)
                        for chunk_idx in page_list:
                            # Convert 1-based page number to 0-based chunk index
                            array_idx = chunk_idx - 1

                            if 0 <= array_idx < total_chunks:
                                extracted_pages[chunk_idx] = {
                                    "content": all_chunks[array_idx],
                                    "chunks": 1,
                                    "note": f"Chunk {chunk_idx} of {total_chunks} (no page numbers available for {doc_type})"
                                }
                            else:
                                extracted_pages[chunk_idx] = {
                                    "content": f"Chunk {chunk_idx} not found (document has {total_chunks} chunks total)",
                                    "chunks": 0
                                }
                    else:
                        for chunk_idx in page_list:
                            extracted_pages[chunk_idx] = {
                                "content": "No chunks found in index for this document",
                                "chunks": 0
                            }

                except Exception as e:
                    logger.error(f"Error extracting chunks: {str(e)}")
                    for chunk_idx in page_list:
                        extracted_pages[chunk_idx] = {
                            "content": f"Error extracting chunk: {str(e)}",
                            "chunks": 0
                        }

        result = {
            "book": book_name,
            "book_path": book_path,
            "document_type": doc_type,
            "is_pdf": is_pdf,
            "requested_pages": page_list,
            "extracted_pages": extracted_pages,
            "total_pages_found": len([p for p in extracted_pages.values() if p['chunks'] > 0])
        }

        # Add informative message for non-PDFs
        if not is_pdf:
            total_chunks = book_info.get('chunks', 0)
            result["note"] = f"This is a {doc_type} with {total_chunks} chunks (no page numbers). Requested 'pages' are treated as chunk indices."

        return result
    
    def get_stats(self):
        """Get library statistics"""
        stats = {
            "total_books": len(self.book_index),
            "total_chunks": 0,
            "categories": {},
            "failed_books": 0,
            "cleaned_books": 0,
            "indexing_status": self.get_indexing_status()
        }
        
        # Count chunks
        for info in self.book_index.values():
            stats["total_chunks"] += info.get("chunks", 0)
        
        # Get category breakdown from vector store
        try:
            if self.vectorstore:
                all_docs = self.vectorstore.get()
                if all_docs and 'metadatas' in all_docs:
                    for metadata in all_docs['metadatas']:
                        if 'type' in metadata:
                            cat_type = metadata['type']
                            stats['categories'][cat_type] = stats['categories'].get(cat_type, 0) + 1
        except:
            pass
        
        # Count failed/cleaned PDFs
        if os.path.exists(self.failed_pdfs_file):
            try:
                with open(self.failed_pdfs_file, 'r') as f:
                    failed_pdfs = json.load(f)
                    stats["failed_books"] = len(failed_pdfs)
                    stats["cleaned_books"] = len([f for f in failed_pdfs.values() if f.get("cleaned", False)])
            except:
                pass
        
        return stats
    
    def get_book_pages(self, book_pattern):
        """Get all page numbers available in the index for a specific book

        Args:
            book_pattern: Partial or fuzzy book name to match (uses fuzzy matching)

        Returns:
            dict with book info and available page numbers
        """
        # Use fuzzy matching to find the book
        matching_books, exact_match, similarity_scores = self.find_book_by_fuzzy_match(book_pattern, cutoff=0.6)

        if not matching_books:
            return {
                "error": f"No books found matching '{book_pattern}'",
                "suggestion": "Try using a different part of the book name or check spelling",
                "available_books": list(self.book_index.keys())[:10]  # Show first 10 as suggestions
            }

        if len(matching_books) > 1:
            # Sort by similarity and show top matches with scores
            matches_with_scores = [
                {
                    "book": book,
                    "similarity": f"{similarity_scores.get(book, 0):.2%}"
                }
                for book in matching_books[:5]  # Show top 5
            ]
            return {
                "error": f"Multiple books match '{book_pattern}'. Please be more specific.",
                "matching_books": matches_with_scores,
                "suggestion": "Use a more specific part of the book name"
            }

        book_path = matching_books[0]
        book_info = self.book_index[book_path]
        book_name = os.path.basename(book_path)

        # Get all page numbers from the database
        try:
            # Query for all documents from this book
            results = self.vectorstore._collection.get(
                where={"book": {"$eq": book_name}},
                include=["metadatas", "ids"]
            )

            # Extract unique page numbers
            page_numbers = set()
            for metadata in results.get('metadatas', []):
                if metadata and 'page' in metadata:
                    page_numbers.add(metadata['page'])

            return {
                "book": book_name,
                "book_path": book_path,
                "total_pages": len(page_numbers),
                "total_chunks": len(results.get('ids', [])),
                "page_numbers": sorted(list(page_numbers))
            }

        except Exception as e:
            logger.error(f"Error getting pages for book '{book_pattern}': {e}")
            return {
                "error": f"Error retrieving pages: {str(e)}",
                "book": book_name,
                "book_path": book_path
            }