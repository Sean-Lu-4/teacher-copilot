from pathlib import Path
import json
import math
from .config import CACHE_FILE, EMBEDDING_MODEL, CHUNK_SIZE, CHUNK_OVERLAP, BATCH_SIZE
from .storage import atomic_json, fingerprint

def valid_vector(value):
    return (isinstance(value, list) and bool(value)
            and all(isinstance(v, (int, float)) and not isinstance(v, bool)
                    and math.isfinite(v) for v in value)
            and any(v != 0 for v in value))


def load_cache(path=CACHE_FILE):
    config = dict(version=3, model=EMBEDDING_MODEL, chunk_size=CHUNK_SIZE,
                  overlap=CHUNK_OVERLAP)
    empty = dict(config=config, vectors={})
    if not Path(path).exists():
        return empty
    try:
        data = json.loads(Path(path).read_text(encoding='utf-8'))
        if not isinstance(data, dict) or data.get('config') != config:
            raise ValueError('incompatible cache configuration')
        vectors = data['vectors']
        if not isinstance(vectors, dict) or any(not valid_vector(v) for v in vectors.values()):
            raise ValueError('invalid vectors')
        if len({len(v) for v in vectors.values()}) > 1:
            raise ValueError('inconsistent vector dimensions')
        return data
    except (ValueError, KeyError, TypeError) as exc:
        # Never silently discard a cache and trigger paid rebuilding.
        raise ValueError(f'Cache is damaged or incompatible: {path}. '
                         'Use offline mode, or back it up and choose a new --cache path.') from exc


def cached_embedding(client, text, cache, path):
    key = fingerprint(text)
    if key not in cache['vectors']:
        response = client.embeddings.create(model=EMBEDDING_MODEL, input=text)
        vector = response.data[0].embedding
        if not valid_vector(vector):
            raise ValueError('API returned an invalid embedding.')
        existing = next(iter(cache['vectors'].values()), vector)
        if len(vector) != len(existing):
            raise ValueError('Embedding dimensions changed; use a new cache path.')
        cache['vectors'][key] = vector
        # Checkpoint every completed request, including query embeddings.
        atomic_json(path, cache)
    return cache['vectors'][key]


def cosine_similarity(a, b):
    if len(a) != len(b):
        raise ValueError('Embedding dimensions do not match.')
    denominator = math.sqrt(sum(v*v for v in a) * sum(v*v for v in b))
    return sum(x*y for x, y in zip(a, b)) / denominator if denominator else 0


def cache_batch(client, texts, cache, path, batch_size=BATCH_SIZE):
    """Content-addressed batches; commit only a complete, validated response.

    Response order is not assumed. Failed batches leave prior checkpoints intact.
    Text edits and source reordering cannot reuse a different text's embedding.
    """
    if type(batch_size) is not int or batch_size <= 0:
        raise ValueError('Batch size must be a positive integer.')
    unique = {fingerprint(text): text for text in texts}
    missing = [(key, text) for key, text in unique.items() if key not in cache['vectors']]
    for start in range(0, len(missing), batch_size):
        batch = missing[start:start + batch_size]
        response = client.embeddings.create(model=EMBEDDING_MODEL, input=[text for _, text in batch])
        data = list(response.data)
        indices = [getattr(item, 'index', None) for item in data]
        if (len(data) != len(batch) or any(type(i) is not int for i in indices)
                or set(indices) != set(range(len(batch)))):
            raise ValueError('Embedding batch is incomplete or has invalid indices; nothing from this batch saved.')
        pending = {batch[item.index][0]: item.embedding for item in data}
        if any(not valid_vector(v) for v in pending.values()):
            raise ValueError('API returned an invalid embedding batch.')
        dimensions = {len(v) for v in pending.values()} | {len(v) for v in cache['vectors'].values()}
        if len(dimensions) != 1:
            raise ValueError('Embedding dimensions changed; use a new cache path.')
        updated = dict(cache, vectors={**cache['vectors'], **pending})
        atomic_json(path, updated)
        cache['vectors'] = updated['vectors']
        print(f'Embedding checkpoint: {min(start + batch_size, len(missing))}/{len(missing)} new texts saved.')
    return [cache['vectors'][fingerprint(text)] for text in texts]


def semantic_search(client, query, chunks, path, threshold, batch_size=BATCH_SIZE):
    cache = load_cache(path)
    missing = len({fingerprint(c['text']) for c in chunks} - cache['vectors'].keys())
    print(f'Embedding cache: {missing} new unique material chunks to process.')
    vectors = cache_batch(client, [c['text'] for c in chunks], cache, path, batch_size)
    query_vector = cached_embedding(client, query, cache, path)
    scores = [(cosine_similarity(query_vector, v), c) for c, v in zip(chunks, vectors)]
    return sorted((item for item in scores if item[0] >= threshold),
                  key=lambda item: item[0], reverse=True)
