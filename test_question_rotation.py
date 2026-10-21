from test_pdf_fixtures import pdf_ids
import tempfile
import unittest
import base64
from io import BytesIO
from docx import Document
from pathlib import Path
from teacher_copilot.review_app import ReviewStore, Conflict
from teacher_copilot.worksheets import TOPIC_CONTENTS, selection_objectives, CONTENT


class RotationTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.store = ReviewStore(self.tmp.name)

    def generate(self, topic='csa-selection', minutes=20, current=None):
        return self.store.mutate(dict(action='generate', run=current, settings=dict(topic=topic,
            contents=TOPIC_CONTENTS[topic], difficulty='any', minutes=minutes, purpose='homework')))

    def action(self, state, action, **args):
        return self.store.mutate(dict(action=action, run=state['run'], version=state['version'], **args))

    def test_rotation_preserves_quality_and_original(self):
        first = self.generate('csa-calls')
        original = (self.store.directory(first['run']) / 'questions.json').read_bytes()
        second = self.generate('csa-calls', current=first['run'])
        ids = lambda s: {r['content']['id'] for r in s['records']}
        self.assertNotEqual(ids(first), ids(second))
        self.assertEqual(first['summary']['minutes'], second['summary']['minutes'])
        self.assertEqual(first['summary']['homework']['missing_contents'], second['summary']['homework']['missing_contents'])
        self.assertEqual(original, (self.store.directory(first['run']) / 'questions.json').read_bytes())
        self.assertEqual(ReviewStore(self.tmp.name).recent_usage(), self.store.recent_usage())

    def test_replace_history_coverage_export_and_conflict(self):
        state = self.generate()
        original = state
        index = 0
        old = state['records'][index]
        state = self.action(state, 'replace', id=old['content']['id'])
        replacement = next(r for r in state['records'] if r['history'] and r['history'][-1]['action']=='replace')
        self.assertNotEqual(old['content']['id'], replacement['content']['id'])
        originals = {r['content']['id']:r for r in original['records']}
        for r in state['records']:
            if r['content']['id'] in originals:self.assertEqual(r, originals[r['content']['id']])
        self.assertEqual([r['content']['level'] for r in state['records']], sorted(r['content']['level'] for r in state['records']))
        before = set().union(*(selection_objectives(r['content'],'csa-selection') for r in original['records']))
        after = set().union(*(selection_objectives(r['content'],'csa-selection') for r in state['records']))
        self.assertLessEqual(before, after)
        self.assertLessEqual(state['summary']['minutes'], 20)
        self.assertEqual(replacement['history'][-1]['detail']['previous_content'], old['content'])
        self.assertTrue(all(v=='pending' for v in replacement['validation'].values()))
        export = self.action(state, 'export', audience='teacher')
        self.assertIn(replacement['content']['task'], export['report'])
        exported_word = self.action(state, 'export', audience='student', format='docx')
        document = Document(BytesIO(base64.b64decode(exported_word['download'])))
        text = '\n'.join(p.text for p in document.paragraphs)
        self.assertIn(replacement['content']['task'], text)
        self.assertNotIn(old['content']['task'], text)
        with self.assertRaises(Conflict):self.action(original, 'replace', id=old['content']['id'])
        state = self.action(state, 'lock', id=replacement['content']['id'], locked=True, actor='Teacher')
        with self.assertRaises(ValueError):self.action(state, 'replace', id=replacement['content']['id'])

    def test_exhaustion_does_not_modify_and_reuse_is_disclosed(self):
        from unittest.mock import patch
        from teacher_copilot.worksheets import BANKS
        source=next(q for q in BANKS['csa-arrays'] if q.get('source_item_id') and q.get('options'))
        with patch.dict(BANKS,{'csa-arrays':[source]}):
            state = self.generate('csa-arrays',10)
            second = self.generate('csa-arrays',10,current=state['run'])
            self.assertIn('使用过', second['generation_notice'])
            with self.assertRaisesRegex(ValueError, '保持不变'):
                self.action(state,'replace',id=state['records'][0]['content']['id'])
            self.assertEqual(state, self.store.state(state['run']))

    def test_replacements_do_not_cycle(self):
        state = self.generate()
        index = 0
        seen = set()
        for _ in range(200):
            question_id = state['records'][index]['content']['id']
            self.assertNotIn(question_id, seen)
            seen.add(question_id)
            try:
                state=self.action(state,'replace',id=question_id)
                index=next(i for i,r in enumerate(state['records']) if r['history'] and r['history'][-1]['action']=='replace')
            except ValueError:break
        else:self.fail('Replacement pool should exhaust')


if __name__=='__main__':unittest.main()
