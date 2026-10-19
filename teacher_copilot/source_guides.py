"""Read-only, bounded page previews of imported scoring guides."""
import json
import re
import threading
from functools import lru_cache
from pathlib import Path

ROOT = Path(__file__).with_name('imported_bank')
_render_lock = threading.Lock()


@lru_cache(maxsize=1)
def index():
    bank = json.loads((ROOT / 'bank.json').read_text(encoding='utf8'))
    documents = {d['id']: d for d in bank['documents'] if d['role'] == 'SG'}
    starts = {}
    for question in bank['questions']:
        for ref in question.get('sources', []):
            if ref['role'] == 'SG' and ref['document'] in documents:
                starts.setdefault(ref['document'], set()).add(int(ref['page']))
    guides = {}
    for question in bank['questions']:
        # Duplicate imports often point to two copies of the same guide.
        ref = next((r for r in question.get('sources', []) if r['role'] == 'SG' and r['document'] in documents), None)
        if not ref:
            continue
        doc, start = ref['document'], int(ref['page'])
        total = int(documents[doc]['pages'])
        # Include the shared boundary page: the preceding answer may continue
        # above the next question on that page. Never silently truncate it.
        end = min((p for p in starts[doc] if p > start), default=total)
        guides[question['id']] = [dict(document=doc, page=p) for p in range(start, min(end,total)+1)]
    return documents, guides


def pages_for(question_id):
    return index()[1].get(question_id, [])


@lru_cache(maxsize=8)
def render_page(document, page):
    if not re.fullmatch(r'[a-f0-9]{64}', document) or type(page) is not int:
        raise ValueError('Invalid scoring page')
    metadata = index()[0].get(document)
    if not metadata or not 1 <= page <= int(metadata['pages']):
        raise ValueError('Unknown scoring page')
    import pymupdf
    # PyMuPDF rendering is serialized; cache at most eight bounded page images.
    with _render_lock, pymupdf.open(ROOT / 'pdfs' / (document+'.pdf')) as pdf:
        sheet = pdf[page-1]
        scale = min(1.7, 1600/max(sheet.rect.width,sheet.rect.height))
        return sheet.get_pixmap(matrix=pymupdf.Matrix(scale,scale), alpha=False).tobytes('png')
