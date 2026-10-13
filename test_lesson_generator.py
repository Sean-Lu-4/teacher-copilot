import importlib.util
from pathlib import Path
import tempfile
import sys
import unittest
from types import SimpleNamespace
from unittest.mock import patch

import teacher_copilot.cli as app
import lesson_profiles as profiles
import json
import exercise_plan as exercises


class CopilotTests(unittest.TestCase):
    def test_exercise_bank_structure_time_and_provenance(self):
        plan = exercises.make_plan({'duration': 45}, [])
        self.assertEqual(sum(row[1] for row in plan['schedule']), 45)
        self.assertEqual([q['level'] for q in plan['questions'][:5]], [1, 2, 3, 4, 4])
        self.assertTrue(all(q['origin'].startswith('原创') for q in plan['questions']))
        for q in plan['questions']:
            self.assertTrue(q['objectives'] and q['reasoning'] and q['rubric'])
            if 'options' in q:
                self.assertEqual(len(q['options']), 4)
                self.assertEqual(set(q['distractors']), set(q['options']) - {q['answer_key']})
        self.assertTrue(exercises.make_plan({'duration': 30}, [])['needs_rescheduling'])
        self.assertIn('需要重新分配时间', exercises.render_report(exercises.make_plan({'duration': 30}, [])))

    def test_exercise_answers_and_distractor_arithmetic(self):
        # Independent arithmetic checks for the fixed examples; not Java compilation.
        bank = {q['id']: q for q in exercises.QUESTIONS}
        combine = lambda a, b: 2*a-b
        half = lambda n: n//2  # All half inputs in this bank are positive.
        result = combine(half(5+3), combine(3, half(5)))
        self.assertEqual(result, int(bank['Q4']['options'][bank['Q4']['answer_key']]))
        self.assertEqual(combine((5+3)/2, combine(3, 5/2)), float(bank['Q4']['options']['A']))
        reversed_combine = lambda a, b: 2*b-a
        self.assertEqual(reversed_combine(4, reversed_combine(3, 2)), int(bank['Q4']['options']['C']))
        self.assertEqual(combine(4, 3), int(bank['Q4']['options']['D']))
        price = lambda quantity, unit_price, discount: quantity*unit_price-discount
        fee = lambda amount: amount+2
        results = [fee(price(3, 8, 5)), price(3, fee(8), 5), fee(price(3, 5, 8)), price(3, 8, fee(5))]
        self.assertEqual(results, [21, 25, 9, 17])
        self.assertEqual(results.count(21), 1)
        self.assertEqual(bank['Q5']['answer_key'], 'A')
        difference = lambda first, second: first-second
        a, b = difference(9, 4), difference(4, 9)
        self.assertEqual((a, b, difference(a, b)), (5, -5, 10))
        increase = lambda value: value+3
        x = 4
        y = increase(x)
        increase(x)
        x = increase(y)
        self.assertEqual((x, y), (10, 7))

    def test_profile_search_requires_multiple_evidence_signals(self):
        chunks = [dict(file='a.pdf', page=1, chunk=1, text='Methods are useful.'),
                  dict(file='a.pdf', page=2, chunk=1, text='Formal parameters receive actual arguments.'),
                  dict(file='a.pdf', page=3, chunk=1, text='A return value is stored in a variable.')]
        coverage = profiles.find_candidates(profiles.METHODS_CALLING, chunks, app.keyword_search)
        items = {c['id']: c for c in coverage}
        self.assertEqual(items['parameters']['candidates'][0]['chunk']['page'], 2)
        self.assertEqual(items['return_use']['candidates'][0]['chunk']['page'], 3)
        self.assertEqual(items['errors']['candidates'], [])
        self.assertEqual(items['argument_order']['candidates'], [])
        self.assertEqual(items['argument_types']['candidates'], [])
        summary = profiles.summarize(coverage, [])
        self.assertTrue(all(not c['teacher_confirmed'] for c in summary))
        self.assertEqual(summary[0]['status'], 'candidate_not_selected')

    def test_profile_round_robin_and_budget_status(self):
        def candidate(page):
            return dict(score=100-page, chunk=dict(file='a.pdf', page=page, chunk=1, text=f'page {page}'))
        coverage = [dict(id='a', title='A', check='check', query='a', candidates=[candidate(1), candidate(3)]),
                    dict(id='b', title='B', check='check', query='b', candidates=[candidate(2)]),
                    dict(id='c', title='C', check='check', query='c', candidates=[])]
        ordered = profiles.interleave_candidates(coverage)
        self.assertEqual([c['page'] for _, c in ordered], [1, 2, 3])
        selected = app.select_material(ordered, 1, 100)
        summary = profiles.summarize(coverage, selected)
        self.assertEqual([c['status'] for c in summary],
                         ['candidate_in_prompt', 'candidate_not_selected', 'not_found'])

    def test_profile_command_is_noninteractive_and_offline(self):
        chunks = [dict(file='a.pdf', page=1, chunk=1, text='Formal parameters receive actual arguments.')]
        with tempfile.TemporaryDirectory() as folder, patch.object(app, 'load_pdf_chunks', return_value=chunks), \
                patch('builtins.input', side_effect=AssertionError('Profile should supply inputs')), \
                patch.dict(sys.modules, {'openai': None}):
            status = app.main(['--profile', 'methods-calling', '--output-dir', folder])
            self.assertEqual(status, 0)
            run = next(Path(folder).iterdir())
            coverage = json.loads((run / 'coverage.json').read_text(encoding='utf-8'))
            self.assertEqual(len(coverage['items']), 9)
            report = (run / 'coverage_report.md').read_text(encoding='utf-8')
            self.assertIn('未找到候选', report)
            prompt = (run / 'prompt.md').read_text(encoding='utf-8')
            self.assertIn('Do not require students to implement methods', prompt)
            self.assertIn('DIFFERENTIATED PRACTICE REQUIREMENTS', prompt)
            exercise_report = (run / 'exercise_report.md').read_text(encoding='utf-8')
            self.assertIn('Q5', exercise_report)
            self.assertIn('不是教材原题', exercise_report)
            self.assertTrue((run / 'exercise_plan.json').exists())
            metadata = json.loads((run / 'metadata.json').read_text(encoding='utf-8'))
            self.assertEqual(metadata['unit'], 1)
            self.assertEqual(metadata['course']['duration'], 45)
            self.assertEqual(metadata['course']['level'], 'Grade 10')

    def test_validation(self):
        for value in ['0', '-2', 'abc', '1.5']:
            with self.assertRaises(Exception):
                app.positive_int(value)
        with self.assertRaises(ValueError):
            app.chunk_text('abc', 2, 2)
        self.assertEqual(app.chunk_text('abcdef', 4, 2), ['abcdef'])

    def test_checkpoint_survives_failure_and_resume(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'cache.json'
            calls = []
            def create(**kwargs):
                calls.append(kwargs['input'])
                if kwargs['input'] == 'second':
                    raise RuntimeError('simulated quota failure')
                return SimpleNamespace(data=[SimpleNamespace(embedding=[1., 2.])])
            client = SimpleNamespace(embeddings=SimpleNamespace(create=create))
            cache = app.load_cache(path)
            app.cached_embedding(client, 'first', cache, path)
            with self.assertRaises(RuntimeError):
                app.cached_embedding(client, 'second', cache, path)
            restored = app.load_cache(path)
            app.cached_embedding(client, 'first', restored, path)
            self.assertEqual(calls, ['first', 'second'])
            self.assertEqual(len(restored['vectors']), 1)
            path.write_text('{broken', encoding='utf-8')
            with self.assertRaises(ValueError):
                app.load_cache(path)

    def test_ranking_dedup_budget_and_no_match(self):
        chunks = [dict(file='a.pdf', page=1, chunk=1, text='method parameter return'),
                  dict(file='a.pdf', page=1, chunk=2, text='method parameter value'),
                  dict(file='b.pdf', page=1, chunk=1, text='method parameter return'),
                  dict(file='a.pdf', page=2, chunk=1, text='array loop')]
        results = app.keyword_search('method parameter', chunks)
        selected = app.select_material(results, 4, 100)
        self.assertEqual(len(selected), 2)
        self.assertEqual(app.keyword_search('zzzz', chunks), [])
        self.assertEqual(app.select_material(results, 4, 2), [])

    def test_offline_never_imports_openai(self):
        import builtins
        original = builtins.__import__
        def guarded(name, *args, **kwargs):
            if name == 'openai':
                raise AssertionError('Offline must not import OpenAI')
            return original(name, *args, **kwargs)
        chunks = [dict(file='test.pdf', page=1, chunk=1, text='Methods accept parameters.')]
        with tempfile.TemporaryDirectory() as folder, patch('builtins.__import__', guarded), \
                patch.object(app, 'load_pdf_chunks', return_value=chunks):
            result = app.main(['--subject', 'AP CSA', '--level', '10', '--topic', 'Methods',
                               '--duration', '45', '--objectives', '', '--output-dir', folder])
            self.assertEqual(result, 0)
            self.assertEqual(len(list(Path(folder).glob('*/prompt.md'))), 1)
            self.assertEqual(len(list(Path(folder).glob('*/lesson.md'))), 0)
            self.assertEqual(len(list(Path(folder).glob('*/retrieval_report.md'))), 1)

    def test_code_boundaries_and_neighbor_merge(self):
        separate_brace = 'public int example()\n{\n return 1;\n}\n'
        self.assertEqual(len(app.split_page(separate_brace, 10)), 1)
        text = 'Intro\nint f() {\n    return 42;\n}\nExplanation\nEnd\n'
        parts = app.split_page(text, 10)
        self.assertTrue(any('int f() {\n    return 42;\n}' in p['text'] for p in parts))
        self.assertEqual(''.join(p['text'] for p in parts), text)
        chunks = [dict(p, file='a.pdf', page=1, chunk=i, page_text=text)
                  for i, p in enumerate(parts, 1)]
        result = app.select_material([(10-i, c) for i, c in enumerate(chunks)], 1, 1000, chunks)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0][1]['text'], text)
        self.assertEqual(app.select_material([(1, chunks[0])], 1, 2, chunks), [])

    def test_cleaning_preserves_java_and_flags_glyphs(self):
        raw = 'TESTDAILY\nA P\n    x++; // keep indentation\nՀ\n'
        cleaned, warnings = app.clean_page(raw)
        self.assertEqual(cleaned, '    x++; // keep indentation\nՀ\n')
        self.assertTrue(warnings)
        self.assertEqual(app.material_info('AP CSA Unit1 讲义.pdf'), (1, 'lecture'))
        self.assertEqual(app.material_info('AP CSA 练习册 Unit4.pdf'), (4, 'workbook'))

    def test_pdf_filter_and_cache_invalidation(self):
        import pypdf
        from unittest.mock import Mock
        reader = Mock(return_value=SimpleNamespace(pages=[SimpleNamespace(extract_text=lambda: 'Methods\n')]))
        with tempfile.TemporaryDirectory() as folder, patch.object(pypdf, 'PdfReader', reader):
            root = Path(folder)
            first = root / 'AP CSA Unit1 讲义.pdf'
            first.write_bytes(b'first')
            (root / 'AP CSA Unit4 练习册.pdf').write_bytes(b'second')
            cache = root / 'cache'
            chunks = app.load_pdf_chunks(root, 1, 'lecture', cache)
            self.assertEqual({c['file'] for c in chunks}, {first.name})
            app.load_pdf_chunks(root, 1, 'lecture', cache)
            self.assertEqual(reader.call_count, 1)
            first.write_bytes(b'changed')
            app.load_pdf_chunks(root, 1, 'lecture', cache)
            self.assertEqual(reader.call_count, 2)

    def test_no_matches_still_saves_report(self):
        chunks = [dict(file='test.pdf', page=1, chunk=1, text='Methods parameters')]
        with tempfile.TemporaryDirectory() as folder, patch.object(app, 'load_pdf_chunks', return_value=chunks):
            status = app.main(['--subject', 'AP CSA', '--level', '10', '--topic', 'zzzz',
                               '--duration', '45', '--objectives', '', '--output-dir', folder])
            self.assertEqual(status, 1)
            self.assertEqual(len(list(Path(folder).glob('*/retrieval_report.md'))), 1)
            self.assertEqual(len(list(Path(folder).glob('*/prompt.md'))), 0)

    def test_online_incomplete_is_saved_without_retry(self):
        class Dump:
            def model_dump(self):
                return {'reason': 'max_output_tokens'}
        from unittest.mock import Mock
        create = Mock(return_value=SimpleNamespace(output_text='partial lesson',
                      status='incomplete', id='fake', usage=None, incomplete_details=Dump()))
        fake = SimpleNamespace(OpenAI=Mock(return_value=SimpleNamespace(
                               responses=SimpleNamespace(create=create))))
        chunks = [dict(file='test.pdf', page=1, chunk=1, text='Methods parameters')]
        with tempfile.TemporaryDirectory() as folder, patch.dict(sys.modules, {'openai': fake}), \
                patch.dict(app.os.environ, {'OPENAI_API_KEY': 'fake-test-key'}), \
                patch.object(app, 'load_pdf_chunks', return_value=chunks):
            status = app.main(['--online', '--subject', 'AP CSA', '--level', '10',
                               '--topic', 'Methods', '--duration', '45', '--objectives', '',
                               '--output-dir', folder])
            self.assertEqual(status, 1)
            create.assert_called_once()
            self.assertEqual(len(list(Path(folder).glob('*/lesson_partial.md'))), 1)
            self.assertEqual(len(list(Path(folder).glob('*/lesson.md'))), 0)


if __name__ == '__main__':
    unittest.main()
