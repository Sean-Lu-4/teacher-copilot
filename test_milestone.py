import builtins
from copy import deepcopy
import importlib
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from teacher_copilot import embeddings as emb
from teacher_copilot import questions as q
from teacher_copilot.exercises import QUESTIONS, BANK_VERSION


class QuestionTests(unittest.TestCase):
    def record(self, index=0):
        return q.create_record(QUESTIONS[index], BANK_VERSION, dict(kind='original', sources=[]))

    def test_bank_roundtrip_preserves_every_content_field(self):
        records = [self.record(i) for i in range(len(QUESTIONS))]
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'questions.json'
            q.save_questions(path, records)
            restored = q.load_questions(path)
        self.assertEqual([r['content'] for r in restored], QUESTIONS)
        self.assertTrue(all(r['validation'] == q.pending_validation() for r in restored))

    def test_revision_invalidates_review_retains_old_content(self):
        original = self.record()
        checked = q.review(original, 'teacher_review', 'passed', 'teacher', 'Reviewed wording and prerequisites.')
        edited = q.revise(checked, {'title': 'Revised title'}, 'teacher', 'Clearer wording')
        self.assertEqual(edited['revision'], 2)
        self.assertEqual(edited['validation'], q.pending_validation())
        self.assertEqual(edited['history'][-1]['detail']['previous_content'], original['content'])
        self.assertEqual(checked['validation']['teacher_review'], 'passed')
        self.assertEqual(original['validation']['teacher_review'], 'pending')

    def test_locked_question_rejects_edit_until_explicit_unlock(self):
        locked = q.set_locked(self.record(), True, 'teacher')
        with self.assertRaises(ValueError):
            q.revise(locked, {'minutes': 4}, 'teacher', 'Adjust time')
        unlocked = q.set_locked(locked, False, 'teacher')
        edited = q.revise(unlocked, {'minutes': 4}, 'teacher', 'Adjust time')
        self.assertEqual(edited['content']['minutes'], 4)
        self.assertTrue(locked['locked'])

    def test_direct_edits_and_duplicate_ids_rejected(self):
        tampered = self.record()
        tampered['content']['answer'] = 'Changed without revision'
        with self.assertRaises(ValueError):
            q.validate_record(tampered)
        with tempfile.TemporaryDirectory() as folder:
            with self.assertRaises(ValueError):
                q.save_questions(Path(folder) / 'questions.json', [self.record(), self.record()])

    def test_mcq_answer_and_all_distractors_required(self):
        for changes in ({'answer_key': 'Z'}, {'distractors': {}}, {'minutes': 0}, {'level': 5}):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                q.revise(self.record(3), changes, 'teacher', 'Validation test')

    def test_provenance_requires_real_reference_and_adaptation_note(self):
        for provenance in [dict(kind='textbook', sources=[]),
                           dict(kind='adapted', sources=[dict(file='book.pdf', page=2)]),
                           dict(kind='textbook', sources=[dict(file='book.pdf', page=0)])]:
            with self.subTest(provenance=provenance), self.assertRaises(ValueError):
                q.create_record(QUESTIONS[0], BANK_VERSION, provenance)
        valid = q.create_record(QUESTIONS[0], BANK_VERSION,
                                dict(kind='adapted', sources=[dict(file='book.pdf', page=2)], changes='Changed numbers'))
        self.assertEqual(valid['provenance']['kind'], 'adapted')

    def test_unknown_schema_and_empty_review_evidence_rejected(self):
        record = self.record()
        record['schema_version'] = 99
        with self.assertRaises(ValueError):
            q.validate_record(record)
        with self.assertRaises(ValueError):
            q.review(self.record(), 'technical_review', 'passed', 'teacher', '')


class BatchTests(unittest.TestCase):
    @staticmethod
    def response(texts):
        # Deliberately return responses in reverse order to test index alignment.
        return SimpleNamespace(data=[SimpleNamespace(index=i, embedding=[float(ord(t[0])), 1.])
                                     for i, t in reversed(list(enumerate(texts)))])

    def test_batch_checkpoint_resume_dedup_and_changed_text(self):
        calls = []
        def create(**kwargs):
            texts = kwargs['input']
            calls.append(texts)
            if texts == ['c']:
                raise RuntimeError('simulated interruption')
            return self.response(texts)
        client = SimpleNamespace(embeddings=SimpleNamespace(create=create))
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'cache.json'
            cache = emb.load_cache(path)
            with self.assertRaises(RuntimeError):
                emb.cache_batch(client, ['a', 'b', 'a', 'c'], cache, path, 2)
            self.assertEqual(len(emb.load_cache(path)['vectors']), 2)
            client.embeddings.create = lambda **kw: (calls.append(kw['input']) or self.response(kw['input']))
            vectors = emb.cache_batch(client, ['b', 'a', 'c', 'a changed'], emb.load_cache(path), path, 2)
            self.assertEqual(calls, [['a', 'b'], ['c'], ['c', 'a changed']])
            self.assertEqual(vectors[:3], [[98., 1.], [97., 1.], [99., 1.]])

    def test_malformed_batches_never_checkpoint_partial_data(self):
        cases = [[], [SimpleNamespace(index=0, embedding=[1., 2.])],
                 [SimpleNamespace(index=0, embedding=[1., 2.]), SimpleNamespace(index=0, embedding=[3., 4.])],
                 [SimpleNamespace(index=0, embedding=[1., 2.]), SimpleNamespace(index=1, embedding=[float('nan'), 1.])],
                 [SimpleNamespace(index=0, embedding=[1., 2.]), SimpleNamespace(index=1, embedding=[3.])]]
        for data in cases:
            with self.subTest(data=data), tempfile.TemporaryDirectory() as folder:
                path = Path(folder) / 'cache.json'
                cache = emb.load_cache(path)
                client = SimpleNamespace(embeddings=SimpleNamespace(create=lambda **kw: SimpleNamespace(data=data)))
                with self.assertRaises(ValueError):
                    emb.cache_batch(client, ['a', 'b'], cache, path)
                self.assertEqual(cache['vectors'], {})
                self.assertFalse(path.exists())

    def test_checkpoint_write_failure_does_not_mark_batch_complete(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'cache.json'
            cache = emb.load_cache(path)
            client = SimpleNamespace(embeddings=SimpleNamespace(create=lambda **kw: self.response(kw['input'])))
            with patch.object(emb, 'atomic_json', side_effect=OSError('disk full')), self.assertRaises(OSError):
                emb.cache_batch(client, ['a'], cache, path)
            self.assertEqual(cache['vectors'], {})

    def test_importing_entrypoint_is_safe_without_api_or_input(self):
        with patch.dict('sys.modules', {'openai': None}), patch.object(builtins, 'input', side_effect=AssertionError('No prompts on import')):
            import lesson_generator
            importlib.reload(lesson_generator)


if __name__ == '__main__':
    unittest.main()
