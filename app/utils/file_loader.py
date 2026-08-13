import logging
import os
import hashlib
from typing import Optional, Tuple
from pathlib import Path
from html.parser import HTMLParser


logger = logging.getLogger(__name__)


class _HTMLTextParser(HTMLParser):
    """Minimal stdlib HTML → text extractor (fallback when bs4 missing).

    Mirrors the BeautifulSoup behaviour: drops scripts/styles/nav, keeps block
    elements (paragraphs, list items, table rows, headings) as paragraphs and
    captures the <title>.
    """
    BLOCK_TAGS = {
        'p', 'div', 'tr', 'li', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
        'pre', 'blockquote', 'table', 'section', 'article',
    }
    SKIP_TAGS = {'script', 'style', 'noscript', 'template', 'svg'}

    def __init__(self):
        super().__init__()
        self.parts = []
        self.pending = []
        self.skip_depth = 0
        self.title = None
        self._in_title = False
        self._title_parts = []

    def handle_starttag(self, tag, attrs):
        if tag in self.SKIP_TAGS:
            self.skip_depth += 1
        elif tag == 'title':
            self._in_title = True
            self._title_parts = []
        elif tag in self.BLOCK_TAGS:
            self._flush()

    def handle_endtag(self, tag):
        if tag in self.SKIP_TAGS:
            self.skip_depth = max(0, self.skip_depth - 1)
        elif tag == 'title':
            self._in_title = False
            self.title = ' '.join(self._title_parts).strip()
        elif tag in self.BLOCK_TAGS:
            self._flush()

    def handle_data(self, data):
        if self.skip_depth:
            return
        if self._in_title:
            if data.strip():
                self._title_parts.append(data.strip())
        elif data.strip():
            self.pending.append(data.strip())

    def _flush(self):
        if self.pending:
            self.parts.append(' '.join(self.pending))
            self.pending = []


class FileLoader:
    """Extract text from various file formats"""
    
    @staticmethod
    def extract_text(file_path: str) -> Tuple[str, dict]:
        """
        Extract text from a file.
        Returns (text_content, metadata)
        """
        
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        # Get file info
        file_info = {
            "filename": file_path.name,
            "file_size": file_path.stat().st_size,
            "file_type": file_path.suffix.lower(),
            "last_modified": file_path.stat().st_mtime
        }
        
        # Extract based on file type
        suffix = file_path.suffix.lower()
        
        if suffix == '.pdf':
            text = FileLoader._extract_pdf(file_path)
        elif suffix == '.docx':
            text = FileLoader._extract_docx(file_path)
        elif suffix in ['.md', '.markdown']:
            text = FileLoader._extract_markdown(file_path)
        elif suffix in ['.txt', '.text']:
            text = FileLoader._extract_text(file_path)
        elif suffix == '.csv':
            text = FileLoader._extract_csv(file_path)
        elif suffix == '.xlsx':
            text = FileLoader._extract_xlsx(file_path)
        elif suffix == '.pptx':
            text = FileLoader._extract_pptx(file_path)
        elif suffix == '.rtf':
            text = FileLoader._extract_rtf(file_path)
        elif suffix in ['.html', '.htm']:
            text = FileLoader._extract_html_bytes(file_path.read_bytes())
        elif suffix == '.zip':
            text = FileLoader._extract_zip(file_path.read_bytes(), file_path.name, depth=0)
        else:
            supported = ', '.join(sorted([
                '.pdf', '.docx', '.md', '.markdown',
                '.txt', '.text', '.csv', '.xlsx', '.pptx', '.rtf',
                '.html', '.htm', '.zip'
            ]))
            raise ValueError(f"Unsupported file type: {suffix}. Supported types: {supported}")
        
        return text, file_info
    
    @staticmethod
    def _extract_pdf(file_path: Path) -> str:
        """Extract text from PDF"""
        try:
            from pypdf import PdfReader
            
            reader = PdfReader(str(file_path))
            text_parts = []
            
            for page_num, page in enumerate(reader.pages, 1):
                page_text = page.extract_text()
                if page_text:
                    text_parts.append(f"[Page {page_num}]\n{page_text}")
            
            return "\n\n".join(text_parts)
            
        except Exception as e:
            logger.error(f"PDF extraction failed: {e}")
            raise
    
    @staticmethod
    def _extract_docx(file_path: Path) -> str:
        """Extract text from Word document"""
        try:
            from docx import Document
            
            doc = Document(str(file_path))
            text_parts = []
            
            for para in doc.paragraphs:
                if para.text.strip():
                    text_parts.append(para.text)
            
            # Also extract tables
            for table in doc.tables:
                for row in table.rows:
                    row_text = " | ".join(cell.text for cell in row.cells)
                    if row_text.strip():
                        text_parts.append(row_text)
            
            return "\n".join(text_parts)
            
        except Exception as e:
            logger.error(f"DOCX extraction failed: {e}")
            raise
    
    @staticmethod
    def _read_text_file(file_path: Path) -> str:
        """Read a text file with encoding fallbacks"""
        for encoding in ('utf-8-sig', 'utf-8', 'latin-1'):
            try:
                with open(file_path, 'r', encoding=encoding) as f:
                    return f.read()
            except (UnicodeDecodeError, UnicodeError):
                continue
        with open(file_path, 'r', encoding='latin-1', errors='replace') as f:
            return f.read()
    
    @staticmethod
    def _extract_markdown(file_path: Path) -> str:
        """Extract text from Markdown"""
        return FileLoader._read_text_file(file_path)
    
    @staticmethod
    def _extract_text(file_path: Path) -> str:
        """Extract text from plain text file"""
        return FileLoader._read_text_file(file_path)
    
    @staticmethod
    def _extract_csv(file_path: Path) -> str:
        """Extract text from CSV"""
        return FileLoader._extract_csv_bytes(file_path.read_bytes())
    
    @staticmethod
    def _extract_xlsx(file_path: Path) -> str:
        """Extract text from Excel workbook"""
        try:
            from openpyxl import load_workbook
            
            wb = load_workbook(str(file_path), read_only=True, data_only=True)
            text_parts = []
            
            for sheet in wb.worksheets:
                text_parts.append(f"[Sheet: {sheet.title}]")
                for row in sheet.iter_rows(values_only=True):
                    cells = [str(c).strip() if c is not None else "" for c in row]
                    if any(cells):
                        text_parts.append(" | ".join(cells))
            
            wb.close()
            return "\n".join(text_parts)
            
        except Exception as e:
            logger.error(f"XLSX extraction failed: {e}")
            raise
    
    @staticmethod
    def _extract_pptx(file_path: Path) -> str:
        """Extract text from PowerPoint presentation"""
        try:
            from pptx import Presentation
            
            prs = Presentation(str(file_path))
            text_parts = []
            
            for slide_num, slide in enumerate(prs.slides, 1):
                text_parts.append(f"[Slide {slide_num}]")
                for shape in slide.shapes:
                    if shape.has_text_frame:
                        for para in shape.text_frame.paragraphs:
                            text = "".join(run.text for run in para.runs)
                            if text.strip():
                                text_parts.append(text)
                    if shape.has_table:
                        for row in shape.table.rows:
                            cells = [cell.text.strip() for cell in row.cells]
                            if any(cells):
                                text_parts.append(" | ".join(cells))
            
            return "\n".join(text_parts)
            
        except Exception as e:
            logger.error(f"PPTX extraction failed: {e}")
            raise
    
    @staticmethod
    def _extract_rtf(file_path: Path) -> str:
        """Extract text from Rich Text Format file"""
        try:
            from striprtf.striprtf import rtf_to_text
            
            content = FileLoader._read_text_file(file_path)
            return rtf_to_text(content)
            
        except Exception as e:
            logger.error(f"RTF extraction failed: {e}")
            raise
    
    @staticmethod
    def extract_text_from_bytes(data: bytes, filename: str) -> Tuple[str, dict]:
        """Extract text from in-memory file bytes (no disk storage)."""
        filename = str(filename)
        suffix = Path(filename).suffix.lower()

        file_info = {
            "filename": Path(filename).name,
            "file_size": len(data),
            "file_type": suffix,
            "last_modified": None,
        }

        text = FileLoader._extract_bytes(data, filename, depth=0)

        return text, file_info

    @staticmethod
    def _extract_bytes(data: bytes, filename: str, depth: int) -> str:
        """Dispatch in-memory extraction by suffix (used by zip recursion too)."""
        from io import BytesIO

        suffix = Path(filename).suffix.lower()
        stream = BytesIO(data)

        if suffix == '.pdf':
            return FileLoader._extract_pdf_stream(stream)
        elif suffix == '.docx':
            return FileLoader._extract_docx_stream(stream)
        elif suffix in ['.md', '.markdown']:
            return FileLoader._decode_bytes(data)
        elif suffix in ['.txt', '.text']:
            return FileLoader._decode_bytes(data)
        elif suffix == '.csv':
            return FileLoader._extract_csv_bytes(data)
        elif suffix == '.xlsx':
            return FileLoader._extract_xlsx_stream(stream)
        elif suffix == '.pptx':
            return FileLoader._extract_pptx_stream(stream)
        elif suffix == '.rtf':
            from striprtf.striprtf import rtf_to_text
            return rtf_to_text(FileLoader._decode_bytes(data))
        elif suffix in ['.html', '.htm']:
            return FileLoader._extract_html_bytes(data)
        elif suffix == '.zip':
            return FileLoader._extract_zip(data, filename, depth)
        else:
            supported = ', '.join(sorted([
                '.pdf', '.docx', '.md', '.markdown',
                '.txt', '.text', '.csv', '.xlsx', '.pptx', '.rtf',
                '.html', '.htm', '.zip'
            ]))
            raise ValueError(f"Unsupported file type: {suffix}. Supported types: {supported}")

    @staticmethod
    def _decode_bytes(data: bytes) -> str:
        for encoding in ('utf-8-sig', 'utf-8', 'latin-1'):
            try:
                return data.decode(encoding)
            except (UnicodeDecodeError, UnicodeError):
                continue
        return data.decode('latin-1', errors='replace')

    @staticmethod
    def _extract_pdf_stream(stream) -> str:
        from pypdf import PdfReader

        reader = PdfReader(stream)
        text_parts = []
        for page_num, page in enumerate(reader.pages, 1):
            page_text = page.extract_text()
            if page_text:
                text_parts.append(f"[Page {page_num}]\n{page_text}")
        return "\n\n".join(text_parts)

    @staticmethod
    def _extract_docx_stream(stream) -> str:
        from docx import Document

        doc = Document(stream)
        text_parts = []
        for para in doc.paragraphs:
            if para.text.strip():
                text_parts.append(para.text)
        for table in doc.tables:
            for row in table.rows:
                row_text = " | ".join(cell.text for cell in row.cells)
                if row_text.strip():
                    text_parts.append(row_text)
        return "\n\n".join(text_parts)

    @staticmethod
    def _extract_csv_bytes(data: bytes) -> str:
        """Extract a CSV. Each physical row is a separate paragraph so the
        chunker breaks at row boundaries (fixes the old collapse-into-one-paragraph
        behavior that mangled tabular data)."""
        import csv
        from io import StringIO

        reader = csv.reader(StringIO(FileLoader._decode_bytes(data)))
        text_parts = [" | ".join(row) for row in reader]
        return "\n\n".join(text_parts)

    @staticmethod
    def _extract_xlsx_stream(stream) -> str:
        """Extract an Excel workbook. Rows within a sheet are blank-line-separated
        so paragraph grouping chunks by rows, and sheet markers stay intact."""
        from openpyxl import load_workbook

        wb = load_workbook(stream, read_only=True, data_only=True)
        text_parts = []
        for sheet in wb.worksheets:
            text_parts.append(f"[Sheet: {sheet.title}]")
            for row in sheet.iter_rows(values_only=True):
                cells = [str(c).strip() if c is not None else "" for c in row]
                if any(cells):
                    text_parts.append(" | ".join(cells))
        wb.close()
        return "\n\n".join(text_parts)

    @staticmethod
    def _extract_pptx_stream(stream) -> str:
        from pptx import Presentation

        prs = Presentation(stream)
        text_parts = []
        for slide_num, slide in enumerate(prs.slides, 1):
            text_parts.append(f"[Slide {slide_num}]")
            for shape in slide.shapes:
                if shape.has_text_frame:
                    for para in shape.text_frame.paragraphs:
                        text = "".join(run.text for run in para.runs)
                        if text.strip():
                            text_parts.append(text)
                if shape.has_table:
                    for row in shape.table.rows:
                        cells = [cell.text.strip() for cell in row.cells]
                        if any(cells):
                            text_parts.append(" | ".join(cells))
        return "\n\n".join(text_parts)

    @staticmethod
    def _extract_html_bytes(data: bytes) -> str:
        """Extract text from HTML with BeautifulSoup (stdlib fallback if absent).

        Strips scripts/styles, keeps table cell text as its own paragraph so
        tabular HTML also chunks cleanly with the existing TextChunker.
        """
        try:
            from bs4 import BeautifulSoup
        except ImportError:
            logger.warning("beautifulsoup4 not installed - using stdlib HTML parser")
            return FileLoader._extract_html_fallback(data)

        soup = BeautifulSoup(FileLoader._decode_bytes(data), "html.parser")
        for tag in soup(["script", "style", "noscript", "template", "svg"]):
            tag.decompose()

        text_parts = []
        title = soup.title.get_text(strip=True) if soup.title else None
        if title:
            text_parts.append(f"[Title: {title}]")

        for el in soup.find_all(['p', 'tr', 'li', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'pre', 'blockquote']):
            if el.find_parent('tr'):
                continue
            block_text = el.get_text(" ", strip=True)
            if block_text:
                text_parts.append(block_text)

        return "\n\n".join(text_parts)

    @staticmethod
    def _extract_html_fallback(data: bytes) -> str:
        """Extract text from HTML using only the Python stdlib."""
        parser = _HTMLTextParser()
        parser.feed(FileLoader._decode_bytes(data))
        text_parts = []
        if parser.title:
            text_parts.append(f"[Title: {parser.title}]")
        text_parts.extend(part for part in parser.parts if part)
        return "\n\n".join(text_parts)

    @staticmethod
    def _extract_zip(data: bytes, filename: str, depth: int) -> str:
        """Extract every supported member of a zip archive in-memory.

        Members that parse fine are wrapped in [member/path] markers and joined
        with blank lines, so one zip indexes as a single coherent document.
        """
        import zipfile
        from io import BytesIO

        if depth > 3:
            logger.warning(f"ZIP nesting too deep, skipping {filename}")
            return ""

        try:
            zf = zipfile.ZipFile(BytesIO(data))
        except zipfile.BadZipFile as e:
            logger.warning(f"Invalid ZIP {filename}: {e}")
            return ""

        parts = []
        try:
            infos = zf.infolist()
            if len(infos) > 200:
                logger.warning(f"ZIP {filename} has many entries, truncating to 200")
                infos = infos[:200]

            total_extracted = 0
            for member in infos:
                if member.is_dir():
                    continue
                name = member.filename
                try:
                    member_data = zf.read(member)
                    total_extracted += len(member_data)
                    if total_extracted > 200 * 1024 * 1024:
                        logger.warning(f"ZIP {filename} exceeds 200MB extracted, stopping")
                        break
                except Exception as e:
                    logger.warning(f"Skipping zip member {name} ({e})")
                    continue

                try:
                    member_text = FileLoader._extract_bytes(
                        member_data, name, depth=depth + 1
                    )
                except Exception as e:
                    logger.warning(f"Skipping unreadable zip member {name}: {e}")
                    continue
                if not member_text or not member_text.strip():
                    continue
                parts.append(f"[{name}]\n{member_text.strip()}")
        finally:
            zf.close()

        return "\n\n".join(parts)

    @staticmethod
    def content_hash_from_bytes(data: bytes) -> str:
        """Generate SHA-256 hash of in-memory file bytes."""
        sha256 = hashlib.sha256()
        sha256.update(data)
        return sha256.hexdigest()

    @staticmethod
    def get_content_hash(file_path: str) -> str:
        """Generate SHA-256 hash of file content"""
        sha256 = hashlib.sha256()
        
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256.update(chunk)
        
        return sha256.hexdigest()
    
    @staticmethod
    def get_file_department(file_path: str) -> str:
        """Extract department from file path"""
        # Assumes structure: documents/{department}/filename
        path = Path(file_path)
        parts = path.parts
        
        # Find 'documents' in path and get next folder as department
        try:
            doc_idx = parts.index('documents')
            if doc_idx + 1 < len(parts):
                return parts[doc_idx + 1]
        except ValueError:
            pass
        
        return "general"