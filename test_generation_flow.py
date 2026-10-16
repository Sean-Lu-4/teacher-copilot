import base64,json,tempfile,unittest,uuid
from copy import deepcopy
from io import BytesIO
from unittest.mock import patch
from docx import Document
from teacher_copilot import ai_questions as ai
from teacher_copilot.worksheets import availability_preview,assemble,validate_settings
from teacher_copilot.review_app import ReviewStore
from teacher_copilot.questions import create_record
S=dict(topic='csa-math',contents=['ced_1_11'],difficulty='any',minutes=20,purpose='homework',question_types=['concept'])
def generated(minutes=7):
    return dict(title='Math result',code='int result = Math.abs(-17);',task='Which value is stored in result?',
        answer='绝对值为 17。',rubric='正确选择 B 得 1 分；其他答案得 0 分。',intervention='复习绝对值。',reference_solution='',prerequisites='Math.abs',
        explanation_en='B. The absolute value of -17 is 17. Award 1 point for B.',objectives=['ced_1_11'],reasoning=['绝对值非负。'],errors=['混淆正负号。'],
        scoring_points=[dict(criterion='选择 B 得分，其他选项不得分',points=1)],level=2,minutes=minutes,question_kind='concept',marks=1,options=['-17','17','0','34'],answer_key='B',distractors=['Sign is incorrect.','Not zero.','Not doubled.'])
class FlowTests(unittest.TestCase):
    def test_availability_matches_actual_and_empty_type(self):
        d=availability_preview(S);_,r=assemble(S)
        self.assertEqual(d['planned_minutes'],sum(x['content']['minutes'] for x in r))
        self.assertEqual(d['planned_count'],len(r));self.assertTrue(all(x['content'].get('options') for x in r))
        z=availability_preview(dict(S,topic='csa-foundations',contents=['ced_1_1'],question_types=['write']))
        self.assertEqual(z['count'],0);self.assertTrue(z['error'])
    def test_default_pool_excludes_original_questions(self):
        from teacher_copilot.worksheets import selected_bank, BANKS, assemble_exam
        from teacher_copilot.questions import content_hash
        settings=validate_settings(S)
        clone=deepcopy(selected_bank(settings)[0]);clone['id']='ORIGINAL_PRIORITY_TEST';clone.pop('source_item_id',None)
        with patch.dict(BANKS,{'csa-math':[clone]+BANKS['csa-math']}):
            self.assertTrue(all(q.get('source_item_id') for q in selected_bank(settings)))
            _,records=assemble(settings)
            self.assertTrue(all(r['content'].get('source_item_id') for r in records))
            _,exam=assemble_exam(dict(settings,purpose='exam',minutes=45,question_count=3,total_marks=10))
            self.assertTrue(all(r['content'].get('source_item_id') for r in exam))

    def test_mcq_validation_and_short_answer_rejected(self):
        r=ai.validate_result({'questions':[generated()]},validate_settings(dict(S,minutes=7)),[])
        self.assertEqual(r[0]['content']['answer_key'],'B')
        for change in [dict(options=[]),dict(options=['17']*4),dict(answer_key='E'),dict(question_kind='write')]:
            q=generated();q.update(change)
            with self.assertRaises(ValueError):ai.validate_result({'questions':[q]},validate_settings(dict(S,minutes=7)),[])
    def test_hybrid_no_call_when_sufficient(self):
        with tempfile.TemporaryDirectory() as root,patch.object(ReviewStore,'ai_records',side_effect=AssertionError('Unexpected paid call')):
            state=ReviewStore(root).mutate(dict(action='generate',source='hybrid',settings=S))
            self.assertEqual(state['summary']['minutes'],20)
    def test_hybrid_failure_preserves_local(self):
        with tempfile.TemporaryDirectory() as root,patch.dict('os.environ',{'TEACHER_COPILOT_ENABLE_AI':'1','OPENROUTER_API_KEY':'test'}),patch.object(ReviewStore,'ai_records',side_effect=ValueError('provider unavailable')):
            state=ReviewStore(root).mutate(dict(action='generate',source='hybrid',settings=dict(S,minutes=45)))
            self.assertTrue(state['records']);self.assertLess(state['summary']['minutes'],45)
            self.assertIn('provider unavailable',state['generation_notice'])
    def test_only_gap_sent_and_export_edit_roundtrip(self):
        with tempfile.TemporaryDirectory() as root:
            store=ReviewStore(root); original=store.ai_records
            def generate(settings,mode,current=None,**kw):
                self.assertEqual(kw['supplement_minutes'],13)
                self.assertEqual(len(kw['extra_excluded']),16)
                raise ValueError('test fallback')
            with patch.dict('os.environ',{'TEACHER_COPILOT_ENABLE_AI':'1','OPENROUTER_API_KEY':'test'}),patch.object(store,'ai_records',side_effect=generate):
                state=store.mutate(dict(action='generate',source='hybrid',settings=dict(S,minutes=45)))
            q=state['records'][0]['content']
            state=store.mutate(dict(action='revise',run=state['run'],version=state['version'],id=q['id'],actor='test',reason='edit test',changes={'title':'Updated classroom question'}))
            for audience in ['student','teacher']:
                exported=store.mutate(dict(action='export',run=state['run'],version=state['version'],format='docx',audience=audience))
                doc=Document(BytesIO(base64.b64decode(exported['download'])))
                text='\n'.join(p.text for p in doc.paragraphs)
                self.assertIn('Updated classroom question',text)
                self.assertNotIn('AI 模拟',text);self.assertNotIn('provider unavailable',text)
                self.assertIn('A.',text)
                self.assertEqual('参考答案' in text,audience=='teacher')
    def test_exam_hybrid_keeps_bank_and_fills_exact_count_marks(self):
        from types import SimpleNamespace
        def response(factory,**kw):
            req=json.loads(kw['prompt'])
            if kw['name']=='question_review':
                return SimpleNamespace(status='completed',output=[],output_text=json.dumps(dict(reviews=[dict(index=i,approved=True,solution_check='Test-only review fixture.',issues=[]) for i in range(len(req['questions']))])),usage=SimpleNamespace(input_tokens=1,output_tokens=1))
            count=req['question_count'];minutes=req['total_minutes'];marks=req['total_marks'];rows=[]
            self.assertEqual(count,4)
            for i in range(count):
                q=generated(minutes//count+(i<minutes%count));q['code']=f'int result = Math.abs(-{31+i});'
                q['task']=f'Which value is stored in result in case {i+1}?'
                q['marks']=marks//count+(i<marks%count);q['scoring_points'][0]['points']=q['marks'];rows.append(q)
            return SimpleNamespace(status='completed',output=[],output_text=json.dumps(dict(questions=rows)),usage=SimpleNamespace(input_tokens=1,output_tokens=1))
        with tempfile.TemporaryDirectory() as root,patch.dict('os.environ',{'TEACHER_COPILOT_ENABLE_AI':'1','OPENROUTER_API_KEY':'test'},clear=True),patch.object(ai,'model_response',side_effect=response):
            state=ReviewStore(root).mutate(dict(action='generate',source='hybrid',settings=dict(S,purpose='exam',minutes=45,question_count=20,total_marks=40),request_id=str(uuid.uuid4())))
            rows=state['records'];self.assertEqual(len(rows),20)
            self.assertEqual(sum(r['content']['marks'] for r in rows),40)
            self.assertEqual(sum(r['content']['minutes'] for r in rows),45)
            self.assertEqual(sum(r['content']['id'].startswith('AI_') for r in rows),4)

    def test_public_demo_allows_free_model_only(self):
        from teacher_copilot.review_app import create_server
        with tempfile.TemporaryDirectory() as root,patch.dict('os.environ',{'TEACHER_COPILOT_PUBLIC_DEMO':'1','TEACHER_COPILOT_ENABLE_AI':'1','OPENROUTER_API_KEY':'test'},clear=True):
            server=create_server(root,port=0);server.server_close()
            with patch.dict('os.environ',{'OPENROUTER_MODEL':'paid/model'}):
                with self.assertRaises(ValueError):create_server(root,port=0)
    def test_openrouter_uses_strict_schema_without_openai_fallback(self):
        from types import SimpleNamespace as NS
        class Client:
            def __init__(self,**kw):self.kw=kw;self.chat=NS(completions=self)
            def __enter__(self):return self
            def __exit__(self,*a):pass
            def create(self,**kw):
                selftest.assertEqual(self.kw['base_url'],'https://openrouter.ai/api/v1')
                selftest.assertEqual(kw['model'],'openrouter/free')
                selftest.assertEqual(kw['response_format']['type'],'json_schema')
                return NS(choices=[NS(finish_reason='stop',message=NS(content='{}'))],usage=None)
        selftest=self
        with patch.dict('os.environ',{'TEACHER_COPILOT_ENABLE_AI':'1','OPENROUTER_API_KEY':'test'},clear=True):
            result=ai.model_response(Client,instructions='test',prompt='test',schema=ai.SCHEMA,name='worksheet',limit=100,timeout=1)
            self.assertEqual(result.status,'completed')

    def test_exam_supplement_contract(self):
        s=validate_settings(dict(S,purpose='exam',minutes=45,question_count=3,total_marks=20))
        q=generated(9);q['marks']=6;q['scoring_points'][0]['points']=6
        r=ai.validate_result({'questions':[q]},s,[],supplement_minutes=9,supplement_count=1,supplement_marks=6,covered_objectives=['ced_1_11'])
        self.assertEqual(len(r),1)
if __name__=='__main__':unittest.main()

