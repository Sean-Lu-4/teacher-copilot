from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
MATERIALS_FOLDER = BASE_DIR / 'materials' / 'ap csa'
CACHE_FILE = BASE_DIR / 'embeddings_cache_v3.json'
OUTPUT_FOLDER = BASE_DIR / 'outputs'
TEXT_CACHE_FOLDER = BASE_DIR / '.cache' / 'pdf_text'
EMBEDDING_MODEL = 'text-embedding-3-small'
CHUNK_SIZE, CHUNK_OVERLAP = 1200, 200
TOP_K = 4
BATCH_SIZE = 50
