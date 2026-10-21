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
                   answer=f'绝对值为 {n}。',options=[str(-n),str(n),'0',str(n*2)],answer_key='B',distractors=['Wrong sign.','Not zero.','Not doubled.'],
                   marks=1,scoring_points=[dict(criterion='选择 B 得分，其他选项不得分',points=1)],minutes=5,
                   reasoning=['绝对值非负。'],errors=['误保留负号。'],intervention='复习绝对值。',explanation_en='B. Absolute value is nonnegative. Award 1 point only for B.')
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
        if kwargs.get('text',{}).get('format',{}).get('name')=='question_review':
            data=json.loads(kwargs['input'])
            return NS(status='completed',output=[],output_text=json.dumps(dict(reviews=[dict(index=i,approved=True,solution_check='Absolute value matches B.',issues=[]) for i in range(len(data['questions']))])),usage=NS(input_tokens=10,output_tokens=20))
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
        self.assertEqual(meta['output_tokens'],220)
        self.assertTrue(all(r['validation']['technical_review']=='pending' for r in records))
        options,request=FakeClient.calls[0]
        self.assertEqual(options['max_retries'],0)
        self.assertEqual(options['timeout'],90)
        self.assertFalse(request['store'])
        self.assertEqual(request['max_output_tokens'],12000)
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



    def test_replacement_preserves_required_objectives_and_time(self):
        data=payload();data['questions']=data['questions'][:1]
        old=deepcopy(data['questions'][0]);old.update(id='old',task='different')
        result=ai.validate_result(data,SETTINGS,[old],replacement=old)
        self.assertEqual(len(result),1)
        data['questions'][0]['minutes']=4
        with self.assertRaises(ValueError):ai.validate_result(data,SETTINGS,[],replacement=old)



if __name__=='__main__':unittest.main()
