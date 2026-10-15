import base64
import json
import tempfile
import unittest
import uuid
from copy import deepcopy
from io import BytesIO
from types import SimpleNamespace as NS
from unittest.mock import patch
from docx import Document
from teacher_copilot import ai_questions as ai
from teacher_copilot.gap_bank import QUESTIONS
from teacher_copilot.review_app import ReviewStore

SETTINGS=dict(topic='csa-math',contents=['ced_1_11'],difficulty='any',minutes=10,purpose='homework')
ENV=dict(TEACHER_COPILOT_ENABLE_AI='1',OPENAI_MODEL='test-model',OPENAI_API_KEY='test-placeholder')


def payload():
    rows=[]
    for qid in ['GM_B2','GM_B3']:
        q=next(q for q in QUESTIONS if q['id']==qid)
        row={key:deepcopy(q.get(key,'')) for key in ai.PROPERTIES}
        n=17+len(rows)
        row.update(question_kind='concept',code=f'int result = Math.abs(-{n});',task='Which value is stored in result?',
                   answer=str(n),options=[str(-n),str(n),'0',str(n*2)],answer_key='B',distractors=['Wrong sign.','Not zero.','Not doubled.'],
                   marks=1,scoring_points=[dict(criterion='Select B',points=1)],minutes=5)
        rows.append(row)
    return dict(questions=rows)


class FakeClient:
    response=None
    calls=[]
    def __init__(self,**kwargs):self.options=kwargs;self.responses=self
    def __enter__(self):return self
    def __exit__(self,*args):pass
    def create(self,**kwargs):
        self.calls.append((self.options,kwargs))
        return self.response


class AITests(unittest.TestCase):
    def setUp(self):
        FakeClient.calls=[]
        FakeClient.response=NS(status='completed',output=[],output_text=json.dumps(payload()),usage=NS(input_tokens=100,output_tokens=200))

    def test_default_model_is_gpt6_luna_when_not_overridden(self):
        with patch.dict('os.environ',{'TEACHER_COPILOT_ENABLE_AI':'1','OPENAI_API_KEY':'test-placeholder'},clear=True):
            status=ai.availability()
        self.assertEqual(status['model'],'gpt-6-luna')
        self.assertTrue(status['ready'])

    def test_disabled_never_calls_provider(self):
        with patch.dict('os.environ',{},clear=True):
            with self.assertRaisesRegex(ValueError,'未启用'):
                ai.generate(SETTINGS,'ai',client_factory=FakeClient)
        self.assertFalse(FakeClient.calls)

    def test_structured_request_bounded_and_pending(self):
        with patch.dict('os.environ',ENV,clear=True):
            records,meta=ai.generate(SETTINGS,'ai',client_factory=FakeClient)
        self.assertEqual(meta['output_tokens'],200)
        self.assertTrue(all(r['validation']['technical_review']=='pending' for r in records))
        options,request=FakeClient.calls[0]
        self.assertEqual(options['max_retries'],0)
        self.assertEqual(options['timeout'],45)
        self.assertFalse(request['store'])
        self.assertEqual(request['max_output_tokens'],6000)
        self.assertTrue(request['text']['format']['strict'])

    def test_reject_bad_content(self):
        mutations=[lambda p:p['questions'][0].update(answer=''),
                   lambda p:p['questions'][0].update(minutes=True),
                   lambda p:p['questions'][0].update(minutes=6),
                   lambda p:p['questions'][0].update(level=5),
                   lambda p:p['questions'][0].update(objectives=['ced_4_6']),
                   lambda p:p['questions'][0].update(question_kind='write',reference_solution=''),
                   lambda p:p['questions'].append(deepcopy(p['questions'][0]))]
        for mutate in mutations:
            data=payload();mutate(data)
            with self.subTest(data=data),self.assertRaises(ValueError):ai.validate_result(data,SETTINGS,[])
        with self.assertRaisesRegex(ValueError,'重复'):
            ai.validate_result(payload(),SETTINGS,[payload()['questions'][0]])

    def test_refusal_incomplete_malformed_and_provider_error(self):
        with patch.dict('os.environ',ENV,clear=True):
            for response in [NS(status='incomplete'),NS(status='completed',output=[NS(content=[NS(type='refusal')])]),
                             NS(status='completed',output=[],output_text='not json')]:
                FakeClient.response=response
                with self.assertRaises(ValueError):ai.generate(SETTINGS,'ai',client_factory=FakeClient)
            with patch.object(FakeClient,'create',side_effect=RuntimeError('secret-key')):
                with self.assertRaises(ValueError) as raised:ai.generate(SETTINGS,'ai',client_factory=FakeClient)
                self.assertNotIn('secret-key',str(raised.exception))

    def test_mock_saved_edit_replace_and_word(self):
        with tempfile.TemporaryDirectory() as root,patch.dict('os.environ',{},clear=True):
            store=ReviewStore(root)
            with patch('openai.OpenAI',side_effect=AssertionError('Network forbidden')):
                state=store.mutate(dict(action='generate',settings=SETTINGS,source='mock'))
                state=store.mutate(dict(action='replace',run=state['run'],version=state['version'],id=state['records'][0]['content']['id']))
                state=store.mutate(dict(action='revise',run=state['run'],version=state['version'],id=state['records'][0]['content']['id'],actor='Test',reason='Edit test',changes=dict(title='LATEST_MOCK_TITLE')))
                export=store.mutate(dict(action='export',run=state['run'],version=state['version'],format='docx',audience='student'))
            text='\n'.join(p.text for p in Document(BytesIO(base64.b64decode(export['download']))).paragraphs)
            self.assertIn('LATEST_MOCK_TITLE',text)
            self.assertNotIn('模拟',text)
            self.assertEqual(state['generation']['output_tokens'],0)
            self.assertEqual(store.state(state['run'])['source'],'mock')

    def test_same_request_once_and_daily_budget_persist(self):
        """Failed paid attempts must remain counted across process restarts."""
        with tempfile.TemporaryDirectory() as root,patch.dict('os.environ',ENV,clear=True):
            store=ReviewStore(root)
            request=dict(action='generate',source='ai',settings=SETTINGS,request_id=str(uuid.uuid4()))
            with patch.object(ai,'generate',side_effect=ValueError('failed')) as call:
                with self.assertRaises(ValueError):store.mutate(request)
                with self.assertRaisesRegex(ValueError,'已经处理'):ReviewStore(root).mutate(request)
                self.assertEqual(call.call_count,1)
                for _ in range(9):
                    with self.assertRaises(ValueError):store.mutate(dict(request,request_id=str(uuid.uuid4())))
                with self.assertRaisesRegex(ValueError,'上限'):store.mutate(dict(request,request_id=str(uuid.uuid4())))
                self.assertEqual(call.call_count,10)
                self.assertEqual(store.runs(),[])

    def test_replacement_preserves_required_objectives_and_time(self):
        data=payload();data['questions']=data['questions'][:1]
        old=deepcopy(data['questions'][0]);old.update(id='old',task='different')
        result=ai.validate_result(data,SETTINGS,[old],replacement=old)
        self.assertEqual(len(result),1)
        data['questions'][0]['minutes']=4
        with self.assertRaises(ValueError):ai.validate_result(data,SETTINGS,[],replacement=old)

    def test_ai_adapter_save_edit_reload_export_and_failed_regeneration(self):
        # Exercise the real adapter and store together, replacing only the SDK
        # client. Network access is forbidden throughout this acceptance case.
        with tempfile.TemporaryDirectory() as root,patch.dict('os.environ',ENV,clear=True), \
                patch('openai.OpenAI',FakeClient), \
                patch('socket.socket.connect',side_effect=AssertionError('Network forbidden')):
            store=ReviewStore(root)
            state=store.mutate(dict(action='generate',source='ai',settings=SETTINGS,
                                    request_id=str(uuid.uuid4())))
            self.assertEqual(state['source'],'ai')
            self.assertEqual(len(FakeClient.calls),1)
            self.assertEqual(state['summary']['minutes'],10)
            state=store.mutate(dict(action='revise',run=state['run'],version=state['version'],
                id=state['records'][0]['content']['id'],actor='Teacher',reason='Acceptance',
                changes=dict(title='SAVED_AI_QUESTION',answer='TEACHER_ONLY_ANSWER')))
            reloaded=ReviewStore(root).state(state['run'])
            self.assertEqual(reloaded['version'],state['version'])
            for audience in ('student','teacher'):
                exported=store.mutate(dict(action='export',run=state['run'],version=state['version'],
                                          format='docx',audience=audience))
                doc=Document(BytesIO(base64.b64decode(exported['download'])))
                text='\n'.join(p.text for p in doc.paragraphs)
                self.assertIn('SAVED_AI_QUESTION',text)
                self.assertEqual('TEACHER_ONLY_ANSWER' in text,audience=='teacher')
            before=store.state(state['run'])
            for output in ('not json',json.dumps({'questions':[]})):
                FakeClient.response.output_text=output
                with self.assertRaises(ValueError):
                    store.mutate(dict(action='generate',source='ai',settings=SETTINGS,
                        run=state['run'],request_id=str(uuid.uuid4())))
                self.assertEqual(store.runs(),[state['run']])
                self.assertEqual(store.state(state['run']),before)


if __name__=='__main__':unittest.main()
