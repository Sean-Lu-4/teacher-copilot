import tempfile,unittest
from unittest.mock import patch
from teacher_copilot import exam
class ExamTests(unittest.TestCase):
 def setUp(self):self.tmp=tempfile.TemporaryDirectory();self.root=self.tmp.name
 def tearDown(self):self.tmp.cleanup()
 def start(self):return exam.action(self.root,{'action':'start'},now=1000)
 def test_four_categories_no_answers_before_submit(self):
  s=self.start();self.assertEqual(s['deadline'],6400);self.assertEqual(len(s['questions']),4)
  for q in s['questions']:
   for key in ['answer','reference_solution','rubric','scoring_points','scoring_pages']:self.assertNotIn(key,q)
  self.assertEqual(len({q['section'] for q in s['questions']}),4)
 def test_resume_deadline_and_expiration_lock(self):
  s=self.start();q=s['questions'][0]['id'];s=exam.action(self.root,dict(action='save',id=s['id'],revision=0,drafts={q:'before'}),now=1100)
  resumed=exam.action(self.root,dict(action='get',id=s['id']),now=1200);self.assertEqual(resumed['deadline'],6400)
  ended=exam.action(self.root,dict(action='save',id=s['id'],revision=1,drafts={q:'after'}),now=6400)
  self.assertEqual(ended['status'],'submitted');self.assertEqual(ended['drafts'][q],'before');self.assertIn('answer',ended['questions'][0])
 def test_manual_submit_is_immutable_and_idempotent(self):
  s=self.start();q=s['questions'][0]['id'];payload=dict(action='submit',id=s['id'],revision=0,drafts={q:'original'})
  a=exam.action(self.root,payload,now=1200);payload['drafts'][q]='changed';b=exam.action(self.root,payload,now=1300)
  self.assertEqual(b['drafts'][q],'original');self.assertEqual(a['submitted_at'],b['submitted_at'])
 def test_grade_gate_and_stored_submission(self):
  s=self.start();q=s['questions'][0]['id'];p=dict(action='grade',id=s['id'],question_id=q,code='injected')
  with self.assertRaises(ValueError):exam.action(self.root,p,now=1100)
  exam.action(self.root,dict(action='submit',id=s['id'],revision=0,drafts={q:'stored'}),now=1200)
  with patch.object(exam,'check_submission',return_value={'automatic':{'status':'passed','score_evidence':[]}}) as check:
   exam.action(self.root,p,now=1300);self.assertEqual(check.call_args.args[0]['code'],'stored')
   exam.action(self.root,p,now=1400);self.assertEqual(check.call_count,1)
 def test_blank_is_not_sent_to_runner(self):
  s=self.start();exam.action(self.root,dict(action='submit',id=s['id'],revision=0),now=1200)
  with patch.object(exam,'check_submission') as check:
   r=exam.action(self.root,dict(action='grade',id=s['id'],question_id=s['questions'][0]['id']),now=1300);check.assert_not_called();self.assertTrue(r['results'][s['questions'][0]['id']]['empty'])
 def test_validation_and_stale_revision(self):
  s=self.start()
  for payload in [dict(action='save',id='../bad',revision=0),dict(action='save',id=s['id'],revision=99),dict(action='save',id=s['id'],revision=0,drafts={'not-in-exam':'x'})]:
   with self.assertRaises(ValueError):exam.action(self.root,payload,now=1200)
 def test_free_service_failure_can_retry(self):
  s=self.start();q=s['questions'][0]['id'];exam.action(self.root,dict(action='submit',id=s['id'],revision=0,drafts={q:'code'}),now=1100)
  with patch.object(exam,'check_submission',return_value={'automatic':{'status':'unavailable'}}):
   r=exam.action(self.root,dict(action='grade',id=s['id'],question_id=q),now=1200);self.assertTrue(r['results'][q]['retryable'])
if __name__=='__main__':unittest.main()
