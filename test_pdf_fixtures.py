"""Live PDF examples for workflow tests; no retired classroom short-answer IDs."""
from teacher_copilot.worksheets import BANKS

def pdf_ids():
    return [q['id'] for q in BANKS['csa-calls'] if q.get('source_item_id') and q.get('question_kind')=='concept'][:3]
