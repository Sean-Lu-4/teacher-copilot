import unittest
from unittest.mock import patch

from teacher_copilot.worksheets import assemble_exam, summary


class ExamBuilderTests(unittest.TestCase):
    def settings(self, **changes):
        value = dict(purpose='exam', topic='csa-calls',
                     contents=['parameters', 'calls', 'returns', 'tracing'],
                     difficulty='mixed', minutes=60, question_count=10,
                     total_marks=40, question_types=['trace', 'write', 'concept'])
        value.update(changes)
        return value

    def test_exact_count_time_and_marks(self):
        settings, records = assemble_exam(self.settings())
        self.assertEqual(len(records), 10)
        self.assertLessEqual(sum(r['content']['minutes'] for r in records), 60)
        self.assertEqual(sum(r['content']['marks'] for r in records), 40)
        self.assertTrue(all((r['content'].get('question_kind') or 'concept') in settings['question_types'] for r in records))
        self.assertEqual(summary(settings, records)['exam']['actual_marks'], 40)

    def test_invalid_size_and_types_are_rejected(self):
        with self.assertRaises(ValueError):
            assemble_exam(self.settings(question_count=2))
        with self.assertRaises(ValueError):
            assemble_exam(self.settings(question_types=[]))

    def test_selected_pool_errors_are_actionable(self):
        with self.assertRaisesRegex(ValueError, '清单只有 3 道题'):
            assemble_exam(self.settings(selected_ids=['Q1', 'Q2', 'Q3']))
        with self.assertRaisesRegex(ValueError, '其他课题或已失效'):
            assemble_exam(self.settings(selected_ids=['Q1', 'IB01']))
        with self.assertRaisesRegex(ValueError, '符合所选内容、难度和题型'):
            assemble_exam(self.settings(selected_ids=['Q1', 'Q2', 'Q3'], question_count=3, difficulty='exam'))

    def test_selected_pool_is_respected(self):
        ids=['Q1', 'Q2', 'Q3']
        _, records=assemble_exam(self.settings(selected_ids=ids, question_count=3))
        self.assertEqual({r['content']['id'] for r in records}, set(ids))

    def test_total_below_question_count_is_rejected(self):
        with self.assertRaisesRegex(ValueError, '总分不能少于题目数量'):
            assemble_exam(self.settings(question_count=15, total_marks=10))

    def test_minimum_marks_and_mismatch_warning(self):
        settings, records=assemble_exam(self.settings(question_count=10, total_marks=10))
        self.assertTrue(all(r['content']['marks']==1 for r in records))
        records[0]['content']['marks']=2
        self.assertTrue(any('合计 11 分' in w for w in summary(settings, records)['warnings']))

    def test_invalid_question_marks_cannot_be_saved(self):
        from teacher_copilot.questions import revise
        _, records=assemble_exam(self.settings())
        for marks in [0, -1, True, 1.5, '5', 101]:
            with self.subTest(marks=marks), self.assertRaisesRegex(ValueError, '每题分值'):
                revise(records[0], {'marks': marks}, 'Test teacher', 'Check marks')

    def test_shortage_reports_filtered_count_and_can_be_corrected(self):
        from teacher_copilot.worksheets import BANKS
        _, records = assemble_exam(self.settings())
        pool = [r['content'] for r in records[:3]]
        with patch.dict(BANKS, {'csa-calls': pool}):
            with self.assertRaisesRegex(ValueError, '只有 3 道，无法生成 5 道'):
                assemble_exam(self.settings(question_count=5))
            _, corrected = assemble_exam(self.settings(question_count=3))
            self.assertEqual(len(corrected), 3)

    def test_time_error_gives_feasible_minimum(self):
        from teacher_copilot.worksheets import BANKS
        _, records = assemble_exam(self.settings())
        pool = [dict(r['content'], minutes=5) for r in records]
        with patch.dict(BANKS, {'csa-calls': pool}):
            with self.assertRaisesRegex(ValueError, '至少需要 50 分钟'):
                assemble_exam(self.settings(minutes=30))
            _, corrected = assemble_exam(self.settings(minutes=50))
            self.assertEqual(sum(r['content']['minutes'] for r in corrected), 50)


if __name__ == '__main__':
    unittest.main()
