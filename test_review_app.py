import json
from pathlib import Path
import tempfile
import threading
import unittest
from urllib.request import Request, urlopen
from urllib.error import HTTPError

from teacher_copilot.exercises import make_plan
from teacher_copilot.questions import create_record, save_questions, load_questions
from teacher_copilot.review_app import ReviewStore, Conflict, create_server
from teacher_copilot.storage import atomic_json
from teacher_copilot.library import check as quality_check, items as library_items, manage as manage_library


class ReviewTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.run = self.root / 'sample'
        self.run.mkdir()
        plan = make_plan(dict(duration=45, topic='Methods'), [])
        atomic_json(self.run / 'exercise_plan.json', plan)
        records = [create_record(q, plan['version'], dict(kind='original', sources=[])) for q in plan['questions']]
        save_questions(self.run / 'questions.json', records)
        self.original = (self.run / 'questions.json').read_bytes()
        self.store = ReviewStore(self.root)

    def action(self, action, **extra):
        state = self.store.state('sample')
        return self.store.mutate(dict(run='sample', version=state['version'], id='Q1', actor='Teacher', action=action, **extra))

    def test_save_reload_and_export_use_edited_records_preserve_original(self):
        self.action('review', check='teacher_review', status='passed', evidence='Checked content')
        self.action('revise', changes=dict(title='Edited question', minutes=7), reason='Class needs time')
        state = ReviewStore(self.root).state('sample')
        self.assertEqual(state['records'][0]['content']['title'], 'Edited question')
        self.assertEqual(state['records'][0]['validation']['teacher_review'], 'pending')
        output = self.action('export')
        self.assertIn('Edited question', output['report'])
        self.assertIn('7 分钟', output['report'])
        self.assertNotIn('算术答案与选项已做离线检查', output['report'])
        self.assertEqual(load_questions(Path(output['export_path'])/'questions.json'), state['records'])
        self.assertEqual((self.run/'questions.json').read_bytes(), self.original)
        second = self.action('export')
        self.assertNotEqual(output['export_path'], second['export_path'])

    def test_stale_revision_cannot_overwrite_new_review(self):
        stale = self.store.state('sample')
        self.action('review', check='teacher_review', status='passed', evidence='Checked')
        with self.assertRaises(Conflict):
            self.store.mutate(dict(run='sample', version=stale['version'], id='Q1', actor='Teacher', action='lock', locked=True))

    def test_lock_and_invalid_edits_leave_disk_unchanged(self):
        self.action('lock', locked=True)
        before = (self.run/'questions_review.json').read_bytes()
        with self.assertRaises(ValueError):
            self.action('revise', changes=dict(title='Blocked'), reason='test')
        self.assertEqual((self.run/'questions_review.json').read_bytes(), before)
        self.action('lock', locked=False)
        with self.assertRaises(ValueError):
            self.action('revise', changes=dict(minutes=-1), reason='test')
        self.assertEqual(self.store.state('sample')['records'][0]['content']['title'], '识别合法调用')

    def test_paths_and_provenance_not_editable(self):
        with self.assertRaises(ValueError):
            self.store.state('../sample')
        with self.assertRaises(ValueError):
            self.action('revise', changes=dict(origin='AP 真题'), reason='test')

    def test_http_rejects_foreign_origin_and_requires_session_token(self):
        server = create_server(self.root, 0)
        worker = threading.Thread(target=server.serve_forever, daemon=True)
        worker.start()
        self.addCleanup(server.server_close)
        self.addCleanup(server.shutdown)
        url = f'http://127.0.0.1:{server.server_port}'
        with urlopen(url+'/api/state') as response:
            data = json.load(response)
        body = json.dumps(dict(run='sample', version=data['state']['version'], action='export')).encode()
        for headers in [{}, {'X-Review-Token': data['token'], 'Origin': 'https://foreign.example'}]:
            with self.assertRaises(HTTPError) as error:
                urlopen(Request(url+'/api/action', data=body, headers=headers))
            self.assertEqual(error.exception.code, 403)
        with urlopen(Request(url+'/api/action', data=body, headers={'X-Review-Token':data['token']})) as response:
            self.assertIn('report', json.load(response))
        with urlopen(url) as response:
            self.assertIn('CSA Studio', response.read().decode())

    def test_http_exposes_read_only_bank_browser(self):
        server = create_server(self.root, 0)
        worker = threading.Thread(target=server.serve_forever, daemon=True)
        worker.start()
        self.addCleanup(server.server_close)
        self.addCleanup(server.shutdown)
        url = f'http://127.0.0.1:{server.server_port}'
        with urlopen(url+'/api/bank') as response:
            data = json.load(response)
        self.assertEqual(data['total_count'], len(data['questions']))
        self.assertGreater(data['count'], 0)
        self.assertTrue(all(q.get('id') for q in data['questions']))
        with urlopen(url+'/bank') as response:
            self.assertIn('浏览题库', response.read().decode())

    def test_library_rename_archive_duplicate_and_quality_check(self):
        state = self.store.state('sample')
        renamed = manage_library(self.store, state, {'action':'rename', 'title':'期中 Methods 练习'})
        self.assertEqual(library_items(self.store)[0]['title'], '期中 Methods 练习')
        archived = manage_library(self.store, renamed, {'action':'archive', 'archived':True})
        self.assertTrue(library_items(self.store)[0]['archived'])
        duplicate = manage_library(self.store, archived, {'action':'duplicate'})
        self.assertNotEqual(duplicate['run'], 'sample')
        self.assertEqual(len(duplicate['records']), len(state['records']))
        self.assertEqual(quality_check(state)['warnings'], [])


if __name__ == '__main__':
    unittest.main()
