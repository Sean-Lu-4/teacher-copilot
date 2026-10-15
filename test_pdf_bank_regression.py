import unittest,json,subprocess
from pathlib import Path
from teacher_copilot import worksheets as w
class PdfBankRegression(unittest.TestCase):
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
