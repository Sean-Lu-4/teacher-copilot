from pathlib import Path
import hashlib
import json
import re
import unicodedata
from .config import CHUNK_SIZE, CHUNK_OVERLAP, TEXT_CACHE_FOLDER
from .storage import atomic_json, fingerprint

def chunk_text(text, chunk_size=CHUNK_SIZE, overlap=CHUNK_OVERLAP):
    if not 0 <= overlap < chunk_size:
        raise ValueError('Chunk size must be positive and overlap smaller than size.')
    return [part['text'] for part in split_page(text, chunk_size)]


def split_page(text, target=CHUNK_SIZE):
    """Soft size limit: never cut a line; keep brace-delimited code together.

    Braces are a heuristic, not a Java parser. Page boundaries can still split code.
    Exact character offsets allow lossless context merging later.
    """
    parts, start, end, depth = [], 0, 0, 0
    lines = text.splitlines(keepends=True)
    for index, line in enumerate(lines):
        end += len(line)
        depth = max(0, depth + line.count('{') - line.count('}'))
        next_line = lines[index + 1].lstrip() if index + 1 < len(lines) else ''
        if end - start >= target and depth == 0 and not next_line.startswith('{'):
            parts.append(dict(start=start, end=end, text=text[start:end]))
            start = end
    if start < len(text):
        parts.append(dict(start=start, end=len(text), text=text[start:]))
    return parts


def clean_page(raw):
    # Remove only exact known boilerplate lines. Preserve code whitespace/symbols.
    noise = {'TESTDAILY', 'A P', '@ 2026 TestDaily', 'From Here, Go Anywhere'}
    cleaned = ''.join(line for line in raw.splitlines(keepends=True)
                      if line.strip() not in noise)
    warnings = []
    odd = [c for c in cleaned if c == '\ufffd' or
           unicodedata.category(c) in {'Co', 'Cn'} or
           '\u0530' <= c <= '\u08ff' or '\u1b00' <= c <= '\u1b7f']
    if odd:
        warnings.append('Unusual PDF glyphs detected; check the original page. Characters preserved.')
    if cleaned.count('{') != cleaned.count('}'):
        warnings.append('Unbalanced braces on this PDF page; code may continue on another page.')
    if not cleaned.strip():
        warnings.append('No readable text; this page may be blank or require OCR.')
    return cleaned, warnings


def material_info(path):
    name = Path(path).stem
    match = re.search(r'\bunit\s*([0-9]+)\b', name, re.I)
    kind = ('lecture' if '讲义' in name or re.search(r'\blecture\b', name, re.I)
            else 'workbook' if '练习册' in name or re.search(r'\bworkbook\b', name, re.I)
            else 'unknown')
    return int(match[1]) if match else None, kind


def pdf_pages(pdf, cache_folder):
    """Cache raw extraction by file contents and extractor version, not timestamp."""
    import pypdf
    digest = hashlib.sha256(pdf.read_bytes()).hexdigest()
    version = getattr(pypdf, '__version__', 'unknown')
    key = fingerprint(digest + ':' + version)
    cache_path = Path(cache_folder) / (key + '.json')
    if cache_path.exists():
        try:
            cached = json.loads(cache_path.read_text(encoding='utf-8'))
            pages = cached['pages']
            if cached['digest'] == digest and cached['extractor'] == version and isinstance(pages, list) \
                    and all(isinstance(p, str) for p in pages):
                return pages
        except (ValueError, KeyError, TypeError):
            print(f'Warning: rebuilding invalid text cache for {pdf.name}.')
    reader = pypdf.PdfReader(pdf)
    # Failed extraction is not cached as a successful blank page.
    pages = [page.extract_text() or '' for page in reader.pages]
    atomic_json(cache_path, dict(digest=digest, extractor=version, pages=pages))
    return pages


def load_pdf_chunks(folder, unit=None, material_type='all', cache_folder=TEXT_CACHE_FOLDER):
    folder = Path(folder)
    if not folder.is_dir():
        raise ValueError(f'Materials folder does not exist: {folder}')
    files = sorted(p for p in folder.iterdir() if p.suffix.lower() == '.pdf')
    files = [p for p in files if (unit is None or material_info(p)[0] == unit)
             and (material_type == 'all' or material_info(p)[1] == material_type)]
    if not files:
        raise ValueError(f'No PDFs match folder={folder}, unit={unit}, type={material_type}.')
    chunks = []
    for pdf in files:
        try:
            pages = pdf_pages(pdf, cache_folder)
            for number, raw in enumerate(pages, 1):
                try:
                    text, warnings = clean_page(raw)
                    if not text.strip():
                        print(f'Warning: no text in {pdf.name}, page {number}; OCR may be needed.')
                    for index, part in enumerate(split_page(text), 1):
                        chunks.append(dict(file=pdf.name, page=number, chunk=index,
                                           **part, page_text=text, warnings=warnings,
                                           unit=material_info(pdf)[0], material_type=material_info(pdf)[1]))
                except Exception as exc:
                    print(f'Warning: skipped {pdf.name} page {number} ({type(exc).__name__}).')
        except Exception as exc:
            print(f'Warning: cannot read {pdf.name} ({type(exc).__name__}).')
    if not chunks:
        raise ValueError('No readable PDF text. Check the PDFs or run OCR first.')
    print(f'Loaded {len(chunks)} chunks from {len(files)} PDFs.')
    return chunks
