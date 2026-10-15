import unittest,json,subprocess
from pathlib import Path
from teacher_copilot import worksheets as w
class PdfBankRegression(unittest.TestCase):
 def test_completed_content_review(self):
  from teacher_copilot.csa_curriculum import LABELS,GROUPS
  raw=json.loads(Path('teacher_copilot/imported_bank/bank.json').read_text(encoding='utf-8'))
  audit=json.loads(Path('teacher_copilot/imported_bank/classification_review_20261015.json').read_text(encoding='utf-8'))
  self.assertEqual(len(audit),383);self.assertEqual(len({q['id'] for q in audit}),383)
  self.assertEqual(raw['audit']['unreviewed_group_count'],0)
  for q in raw['questions']:
   self.assertTrue(q['ced_topics']);self.assertNotIn('pending',q['classification_status'])
   self.assertTrue(all(c in LABELS for c in q['ced_topics']))
   self.assertEqual(q['classified_unit'],q['ced_topics'][0].split('.')[0])
   for c in q['ced_topics']:
    self.assertTrue(any(c in GROUPS[g][1] for g in q['topic_ids']))
  blocked={q['id'] for q in raw['questions'] if q.get('content_review_status','').startswith('blocked-')}
  self.assertEqual(len(blocked),24)
  self.assertFalse(blocked & {q['source_item_id'] for q in w.IMPORTED_AP})
 def test_precise_topics_reach_api(self):
  payload=w.bank_data();self.assertEqual(len(payload['ced_topics']),53)
  for q in payload['questions']:
   if q.get('source_item_id'):
    self.assertEqual(q['ap_unit'],q['ced_topics'][0].split('.')[0])
    self.assertEqual(set(q['units']),{c.split('.')[0] for c in q['ced_topics']})
 def test_complete_rows_and_unique_ids(self):
  rows=w.bank_data()['questions'];self.assertEqual(len(rows),len({q['id'] for q in rows}))
  for q in rows:
   self.assertIn(q['question_kind'],['concept','write'])
   self.assertTrue(q['answer'].strip())
   if q['question_kind']=='concept':self.assertIn(q['answer_key'],q['options']);self.assertGreaterEqual(len(q['options']),4)
 def test_every_imported_membership_reaches_generation(self):
  for q in w.IMPORTED_AP:
   for topic in q['topic_ids']:
    topic='csa-selection' if topic=='csa-logic' else topic
    self.assertIn(q['id'],{x['id'] for x in w.selected_bank({'topic':topic})})
 def test_no_false_difficulty(self):
  self.assertTrue(all(q['difficulty_status']=='unrated' for q in w.IMPORTED_AP))
 def test_custom_time_and_nested_loop_recovery(self):
  settings={'topic':'csa-nested-loops','contents':w.TOPIC_CONTENTS['csa-nested-loops'],'difficulty':'any','minutes':17,'purpose':'homework'}
  normalized,records=w.assemble(settings)
  self.assertEqual(normalized['minutes'],17);self.assertTrue(records)
  self.assertLessEqual(sum(r['content']['minutes'] for r in records),17)
 def test_missing_guides_excluded(self):
  b=json.loads(Path('teacher_copilot/imported_bank/bank.json').read_text(encoding='utf-8'))
  missing={q['id'] for q in b['questions'] if q['kind']=='FRQ' and not q['answer']}
  self.assertTrue(missing);self.assertFalse(missing & {q['source_item_id'] for q in w.IMPORTED_AP})
 def test_frq_split_and_filter_contract(self):
  self.assertGreater(sum(q['question_kind']=='write' for q in w.IMPORTED_AP),9)
  self.assertEqual(set(w.EXAM_TYPES),{'concept','write'})
  for q in w.bank_data()['questions']:self.assertTrue(q['topics']);self.assertTrue(q['units'])
if __name__=='__main__':unittest.main()
