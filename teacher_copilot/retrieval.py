from collections import Counter
import math
import re
from .storage import fingerprint
STOP_WORDS = set('a an the and or of to in on for with is are be students student learn learning'.split())

def tokens(text):
    words = re.findall(r'[a-z0-9_]+|[\u4e00-\u9fff]', text.lower())
    return [w for w in words if w not in STOP_WORDS]


def keyword_search(query, chunks):
    """Local BM25 ranking. Scores are relevance hints, not probabilities."""
    terms = set(tokens(query))
    docs = [Counter(tokens(c['text'])) for c in chunks]
    lengths = [sum(d.values()) for d in docs]
    avg = sum(lengths) / max(len(docs), 1) or 1
    frequency = Counter(t for d in docs for t in d)
    results = []
    for chunk, doc, length in zip(chunks, docs, lengths):
        score = 0.0
        for term in terms:
            count = doc[term]
            if count:
                idf = math.log(1 + (len(docs) - frequency[term] + .5) / (frequency[term] + .5))
                score += idf * count * 2.5 / (count + 1.5 * (.25 + .75 * length / avg))
        if score > 0:
            results.append((score, chunk))
    return sorted(results, key=lambda item: item[0], reverse=True)


def select_material(results, top_k, budget, all_chunks=None):
    """Expand to one neighbor on each side, then merge overlapping page ranges.

    No selected text is shortened to fit the budget. Missing context is reported.
    """
    selected, seen, used = [], set(), 0
    all_chunks = all_chunks or [c for _, c in results]
    for score, chunk in results:
        chunk = dict(chunk)
        if 'page_text' in chunk:
            neighbors = [c for c in all_chunks if c['file'] == chunk['file']
                         and c['page'] == chunk['page'] and abs(c['chunk'] - chunk['chunk']) <= 1]
            left = min(c['start'] for c in neighbors)
            right = max(c['end'] for c in neighbors)
            chunk.update(start=left, end=right, text=chunk['page_text'][left:right])
            overlaps = [(i, s, c) for i, (s, c) in enumerate(selected)
                        if c['file'] == chunk['file'] and c['page'] == chunk['page']
                        and c.get('start', float('inf')) <= right and c.get('end', -1) >= left]
            for _, _, old in overlaps:
                left, right = min(left, old['start']), max(right, old['end'])
            chunk.update(start=left, end=right, text=chunk['page_text'][left:right])
            removed = sum(len(c['text']) for _, _, c in overlaps)
            if used - removed + len(chunk['text']) > budget:
                continue
            if overlaps:
                old_indices = {i for i, _, _ in overlaps}
                score = max([score] + [s for _, s, _ in overlaps])
                selected = [(s, c) for i, (s, c) in enumerate(selected) if i not in old_indices]
                used -= removed
            elif len(selected) >= top_k:
                continue
        key = fingerprint(' '.join(chunk['text'].split()))
        seen = {fingerprint(' '.join(c['text'].split())) for _, c in selected}
        if key in seen:
            continue
        if len(selected) >= top_k:
            continue
        if used + len(chunk['text']) > budget:
            continue  # Keep whole snippets, rather than cut a Java example again.
        selected.append((score, chunk))
        seen.add(key)
        used += len(chunk['text'])
    return sorted(selected, key=lambda item: item[0], reverse=True)
