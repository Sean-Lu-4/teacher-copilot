import json,unittest
from copy import deepcopy
from types import SimpleNamespace as NS
from unittest.mock import patch
from test_ai_questions import payload,SETTINGS,ENV
from teacher_copilot import ai_questions as ai

def response(data):
 return NS(status='completed',output=[],output_text=json.dumps(data),usage=NS(input_tokens=5,output_tokens=7))
def review(approved=True):
 return {'reviews':[dict(index=i,approved=approved,solution_check='17 or 18, respectively; only B matches absolute value.',issues=[] if approved else ['Incorrect answer or unsupported scoring criterion.']) for i in range(2)]}
class QualityTests(unittest.TestCase):
 def test_rejected_review_repairs_once_and_accounts_all_calls(self):
  usage=[]
  with patch.dict('os.environ',ENV,clear=True),patch.object(ai,'model_response',side_effect=[response(payload()),response(review(False)),response(payload()),response(review())]) as call:
   rows,meta=ai.generate(SETTINGS,'ai',usage_callback=usage.append)
  self.assertEqual(call.call_count,4);self.assertEqual(meta['attempts'],2)
  self.assertEqual(meta['output_tokens'],28);self.assertEqual(usage[-1]['output_tokens'],28)
  self.assertIn('previous_attempt_issues',json.loads(call.call_args_list[2].kwargs['prompt']))
  self.assertTrue(all(r['validation']['teacher_review']=='pending' for r in rows))
 def test_second_rejection_never_returns_questions(self):
  with patch.dict('os.environ',ENV,clear=True),patch.object(ai,'model_response',side_effect=[response(payload()),response(review(False))]*2) as call:
   with self.assertRaisesRegex(ValueError,'仍未通过'):ai.generate(SETTINGS,'ai')
  self.assertEqual(call.call_count,4)
 def test_english_only_teacher_text_rejected(self):
  d=payload();d['questions'][0]['answer']='The result is 17.'
  with self.assertRaisesRegex(ValueError,'中文'):ai.check_language_and_rubric(d)
 def test_review_must_cover_every_question(self):
  for d in [{'reviews':[]},{'reviews':[review()['reviews'][0]]},{'reviews':[review()['reviews'][0]]*2}]:
   with self.assertRaises(ValueError):ai.check_review(d,2)
 def test_review_cannot_approve_with_issues(self):
  d=review();d['reviews'][0]['issues']=['Missing bounds']
  with self.assertRaises(ValueError):ai.check_review(d,2)
 def test_unknown_provider_usage_retains_reservation_and_stops(self):
  usage=[]
  with patch.dict('os.environ',ENV,clear=True),patch.object(ai,'model_response',side_effect=[response(payload()),RuntimeError('secret-key')]) as call:
   with self.assertRaises(ValueError) as e:ai.generate(SETTINGS,'ai',usage_callback=usage.append)
  self.assertNotIn('secret-key',str(e.exception));self.assertEqual(call.call_count,2)
  self.assertIsNone(usage[-1]['output_tokens'])
 def test_structural_failure_repair_gets_exact_gap(self):
  bad=payload();bad['questions'][0]['scoring_points'][0]['points']=9
  with patch.dict('os.environ',ENV,clear=True),patch.object(ai,'model_response',side_effect=[response(bad),response(payload()),response(review())]) as call:
   ai.generate(SETTINGS,'ai',supplement_minutes=10)
  self.assertEqual(call.call_count,3)
  req=json.loads(call.call_args_list[1].kwargs['prompt'])
  self.assertEqual(req['total_minutes'],10);self.assertIn('分值',req['previous_attempt_issues'])
 def test_reservation_includes_generation_review_and_one_repair(self):
  self.assertEqual(ai.request_output_limit(SETTINGS),2*(12000+6000))
 def test_english_student_text_and_real_answer_required(self):
  for change in [dict(task='请写方法'),dict(answer='参考实现：')]:
   d=payload();d['questions'][0].update(change)
   with self.assertRaises(ValueError):ai.check_language_and_rubric(d)
 def test_matching_option_prefixes_are_removed(self):
  d=payload();q=d['questions'][0];q['options']=[k+') '+v for k,v in zip('ABCD',q['options'])]
  rows=ai.validate_result(d,SETTINGS,[])
  self.assertEqual(rows[0]['content']['options']['B'],'17')
 def test_schema_constrains_new_question_time_and_type(self):
  request=dict(question_count=1,total_minutes=4,allowed_objectives=['ced_1_11'])
  schema=ai.generation_schema(dict(SETTINGS,question_types=['concept']),request)
  q=schema['properties']['questions'];p=q['items']['properties']
  self.assertEqual(q['maxItems'],1);self.assertEqual(p['minutes']['maximum'],4)
  self.assertEqual(p['options']['minItems'],4);self.assertEqual(p['question_kind']['enum'],['concept'])
 def test_free_router_configuration_is_preserved(self):
  with patch.dict('os.environ',dict(TEACHER_COPILOT_ENABLE_AI='1',OPENROUTER_API_KEY='test',OPENROUTER_MODEL='openrouter/free'),clear=True):
   state=ai.availability()
   self.assertEqual(state['model'],'openrouter/free');self.assertTrue(state['free_ready'])
 def test_java_syntax_rejects_missing_bodies_and_corrupted_newlines(self):
  from teacher_copilot.java_syntax import check_java_syntax
  for code in ['public class MathUtil {','public class M {n public int f(){n return 1;n }n}']:
   with self.assertRaises(ValueError):check_java_syntax(code,method_required=True)
  check_java_syntax('public int f(int x) { return x*x; }',method_required=True)
  check_java_syntax('public class M { public int f(int x) { return x*x; } }',method_required=True)
 def test_newline_repair_preserves_java_string_literals(self):
  from teacher_copilot.java_syntax import normalize_code_newlines, check_java_syntax
  code=r'class X {\n public String f() { return "\n"; }\n}'
  repaired=normalize_code_newlines(code)
  self.assertIn('\n public',repaired);self.assertIn(r'"\n"',repaired)
  check_java_syntax(repaired,method_required=True)
 def test_rate_limit_is_not_retried_or_reflected(self):
  with patch.dict('os.environ',ENV,clear=True),patch.object(ai,'model_response',side_effect=ai.ProviderFailure(429)) as call:
   with self.assertRaisesRegex(ValueError,'限流'):ai.generate(SETTINGS,'ai')
  self.assertEqual(call.call_count,1)
 def test_wrong_math_topic_and_missing_english_scoring_rejected(self):
  d=payload();d['questions'][0]['code']='int result=17;'
  with self.assertRaisesRegex(ValueError,'Math'):ai.check_language_and_rubric(d)
  d=payload();d['questions'][0]['explanation_en']='The absolute value is positive.'
  with self.assertRaises(ValueError):ai.check_language_and_rubric(d)
class SupplementRegressionTests(unittest.TestCase):
 def single(self,index=0,minutes=2):
  q=payload()['questions'][index];q['minutes']=minutes
  return {'questions':[q]}
 def approval(self):
  return {'reviews':[review()['reviews'][0]]}
 def test_mcq_broken_code_cannot_pass(self):
  d=self.single();d['questions'][0]['code']='class X { void f(){ // comment swallows closing braces }} Math.abs(-3);'
  with self.assertRaises(ValueError):ai.check_language_and_rubric(d)
 def test_intentional_compile_error_requires_explicit_task_and_key(self):
  d=self.single();q=d['questions'][0];q.update(code='int n = Math.abs( ;',task='Which statement about compilation is correct?')
  with self.assertRaises(ValueError):ai.check_language_and_rubric(d)
  q['options'][1]='The code compiles.'
  with self.assertRaises(ValueError):ai.check_language_and_rubric(d)
  q['options'][1]='The code does not compile.'
  ai.check_language_and_rubric(d)
 def test_frq_supplied_signature_not_scored(self):
  d=self.single();q=d['questions'][0];q.update(question_kind='write',scoring_points=[dict(criterion='方法签名正确',points=1)])
  with self.assertRaisesRegex(ValueError,'签名'):ai.check_language_and_rubric(d)
 def test_short_valid_batch_kept_then_remaining_gap_requested(self):
  seq=[response(self.single()),response(self.approval()),response(self.single(1)),response(self.approval())]
  with patch.dict('os.environ',ENV,clear=True),patch.object(ai,'model_response',side_effect=seq) as call:
   rows,meta=ai.generate(SETTINGS,'ai',supplement_minutes=4)
  self.assertEqual(len(rows),2);self.assertEqual(meta['remaining_minutes'],0)
  req=json.loads(call.call_args_list[2].kwargs['prompt'])
  self.assertEqual(req['total_minutes'],2);self.assertEqual(req['settings']['minutes'],2)
  self.assertTrue(any('17' in x['code'] for x in req['avoid']))
 def test_later_service_failure_preserves_accepted_question(self):
  with patch.dict('os.environ',ENV,clear=True),patch.object(ai,'model_response',side_effect=[response(self.single()),response(self.approval()),RuntimeError('private')]) as call:
   rows,meta=ai.generate(SETTINGS,'ai',supplement_minutes=4)
  self.assertEqual(len(rows),1);self.assertEqual(meta['remaining_minutes'],2)
  self.assertEqual(call.call_count,3);self.assertNotIn('private',meta['partial_reason'])
 def test_duplicate_second_batch_preserves_first_only(self):
  seq=[response(self.single()),response(self.approval()),response(self.single())]
  with patch.dict('os.environ',ENV,clear=True),patch.object(ai,'model_response',side_effect=seq):
   rows,meta=ai.generate(SETTINGS,'ai',supplement_minutes=4)
  self.assertEqual(len(rows),1);self.assertEqual(meta['remaining_minutes'],2)
 def test_non_supplement_duration_stays_exact(self):
  with self.assertRaises(ValueError):ai.validate_result(self.single(),SETTINGS,[])

if __name__=='__main__':unittest.main()

