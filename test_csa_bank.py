import json
import tempfile
import threading
import unittest
from collections import Counter
from pathlib import Path
from urllib.request import urlopen, Request
from urllib.error import HTTPError
from teacher_copilot.csa_bank import QUESTIONS, FIXTURES
from teacher_copilot.csa_curriculum import LABELS, GROUPS, VERSION, objective
from teacher_copilot.csa_review import feedback_state, review_data, save_feedback
from teacher_copilot.questions import create_record, content_hash
from teacher_copilot.review_app import ReviewStore, create_server
from teacher_copilot.worksheets import assemble, paper_report, TOPIC_CONTENTS, CONTENT, catalog, selection_objectives


class CSABankTests(unittest.TestCase):
    def test_all_topics_and_tiers(self):
        expected={f'{unit}.{i}' for unit,n in [(1,15),(2,12),(3,9),(4,17)] for i in range(1,n+1)}
        self.assertEqual(set(LABELS),expected)
        self.assertEqual(len(QUESTIONS),159)
        self.assertEqual(len({q['id'] for q in QUESTIONS}),159)
        self.assertEqual(len({q['task'] for q in QUESTIONS}),159)
        self.assertEqual(Counter(q['ced_topics'][0] for q in QUESTIONS),{t:3 for t in expected})
        for t in expected:
            self.assertEqual({q['level'] for q in QUESTIONS if q['ced_topics']==[t]}, {2,3,4})
        self.assertEqual(Counter(t for _,ts in GROUPS.values() for t in ts),{t:1 for t in expected})
        for q in QUESTIONS:
            create_record(q,VERSION,dict(kind='original',sources=[]))
            self.assertEqual(q['objectives'],[objective(q['ced_topics'][0])])
            self.assertTrue(q['reasoning'])

    def test_fixture_coverage_and_no_placeholder_solutions(self):
        self.assertEqual({f['id'] for f in FIXTURES}, {q['id'] for q in QUESTIONS if q['question_kind']!='concept'})
        for q in QUESTIONS:
            if q['question_kind']=='write':
                self.assertTrue(q['reference_solution'])
                self.assertNotIn('/* complete */',q['reference_solution'])

    def test_every_topic_reports_actual_pdf_availability(self):
        from teacher_copilot.worksheets import eligible_questions,validate_settings,DIFFICULTIES
        for group,(_,topics) in GROUPS.items():
            for t in topics:
                for difficulty in DIFFICULTIES:
                    contents=['calls','returns','tracing'] if t=='1.10' else [objective(t)]
                    settings=dict(topic=group,contents=contents,difficulty=difficulty,minutes=30)
                    eligible=[q for q in eligible_questions(validate_settings(settings)) if q['minutes']<=30]
                    with self.subTest(topic=t,difficulty=difficulty):
                        if not eligible:
                            with self.assertRaises(ValueError):assemble(settings)
                        else:
                            _,records=assemble(settings)
                            self.assertLessEqual({r['content']['id'] for r in records},{q['id'] for q in eligible})
                            self.assertTrue(all(r['content'].get('source_item_id') for r in records))

    def test_student_export_and_saved_reference_edit(self):
        with tempfile.TemporaryDirectory() as temp:
            store=ReviewStore(temp)
            state=store.mutate(dict(action='generate',settings=dict(topic='csa-arrays',contents=[objective('4.5')],difficulty='any',minutes=20,question_types=['write'])))
            q=state['records'][0]['content']
            payload=dict(run=state['run'],version=state['version'])
            teacher=store.mutate(dict(payload,action='export',audience='teacher'))['report']
            student=store.mutate(dict(payload,action='export',audience='student'))['report']
            self.assertIn(q['reference_solution'],teacher)
            for field in ['answer','reference_solution','rubric','intervention']:
                if len(q.get(field,''))>5:self.assertNotIn(q[field],student)
            self.assertIn('一维数组',student)
            state=store.mutate(dict(payload,action='revise',id=q['id'],actor='test',reason='test update',changes={'reference_solution':q['reference_solution']+'\n// reviewed'}))
            report=store.mutate(dict(action='export',run=state['run'],version=state['version'],audience='teacher'))['report']
            self.assertIn('// reviewed',report)
            self.assertEqual(state['records'][0]['validation']['technical_review'],'pending')

    def test_feedback_persistence_conflict_and_hash(self):
        with tempfile.TemporaryDirectory() as temp:
            q=QUESTIONS[0]
            payload=dict(revision=feedback_state(temp)['revision'],bank_version=VERSION,overall='多一些选择题',items={q['id']:dict(decision='too_easy',comment='增加反例',content_hash=content_hash(q))})
            saved=save_feedback(temp,payload)
            self.assertEqual(feedback_state(temp),saved)
            with self.assertRaises(ValueError):save_feedback(temp,payload)
            payload['revision']=saved['revision']
            payload['items'][q['id']]['content_hash']='stale'
            with self.assertRaises(ValueError):save_feedback(temp,payload)
            self.assertEqual(feedback_state(temp),saved)

    def test_no_stale_java_pass_badge(self):
        with tempfile.TemporaryDirectory() as temp:
            q=next(q for q in QUESTIONS if q['question_kind']=='trace')
            path=Path(temp)/'csa_full_review/java_checks'
            path.mkdir(parents=True)
            report=dict(version=VERSION,results=[dict(id=q['id'],passed=True,content_hash='old')])
            (path/'verification.json').write_text(json.dumps(report),encoding='utf-8')
            row=next(r for r in review_data(temp)['questions'] if r['content']['id']==q['id'])
            self.assertEqual(row['technical_status'],'unverified')

    def test_http_review_and_feedback_security(self):
        with tempfile.TemporaryDirectory() as temp:
            server=create_server(temp,port=0)
            thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
            base=f'http://127.0.0.1:{server.server_port}'
            try:
                with urlopen(base+'/api/curriculum') as response: data=json.load(response)
                self.assertEqual(len(data['questions']),159)
                with urlopen(base+'/curriculum') as response: self.assertIn('保存全部反馈',response.read().decode())
                payload=dict(action='bank-feedback',bank_version=VERSION,revision=data['feedback']['revision'],overall='测试反馈',items={})
                body=json.dumps(payload).encode()
                with self.assertRaises(HTTPError) as err: urlopen(Request(base+'/api/action',data=body,headers={'Content-Type':'application/json'}))
                self.assertEqual(err.exception.code,403)
                with urlopen(Request(base+'/api/action',data=body,headers={'Content-Type':'application/json','X-Review-Token':data['token']})) as response:
                    self.assertEqual(json.load(response)['data']['overall'],'测试反馈')
            finally:
                server.shutdown();server.server_close();thread.join()


if __name__=='__main__':unittest.main()
