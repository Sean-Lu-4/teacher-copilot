import unittest
from collections import Counter
from teacher_copilot.conditionals_bank import QUESTIONS, BANK_VERSION
from teacher_copilot.questions import create_record
from teacher_copilot.worksheets import assemble, paper_report, summary, TOPIC_CONTENTS, catalog


class ConditionalsTests(unittest.TestCase):
    def test_bank_complete(self):
        self.assertEqual(len({q['id'] for q in QUESTIONS}), 12)
        self.assertEqual(Counter('basic' if q['level'] < 3 else str(q['level']) for q in QUESTIONS), {'basic': 4, '3': 4, '4': 4})
        for q in QUESTIONS:
            create_record(q, BANK_VERSION, dict(kind='original', sources=[]))
        self.assertGreater(catalog()['bank_count'], 0)

    def test_live_pdf_exports(self):
        settings, records = assemble(dict(topic='csa-selection',contents=TOPIC_CONTENTS['csa-selection'],difficulty='any',minutes=20))
        self.assertLessEqual(summary(settings,records)['minutes'],20)
        self.assertTrue(all(r['content'].get('source_item_id') for r in records))
        for r in records:
            r['content'].update(answer='PRIVATE_ANSWER_SENTINEL',rubric='PRIVATE_RUBRIC_SENTINEL')
        plan=dict(worksheet_settings=settings)
        student=paper_report(plan,records,'student');teacher=paper_report(plan,records,'teacher')
        for marker in ['PRIVATE_ANSWER_SENTINEL','PRIVATE_RUBRIC_SENTINEL']:
            self.assertIn(marker,teacher);self.assertNotIn(marker,student)

    def test_cross_topic_rejected(self):
        for topic, contents in [('methods',['logic']), ('conditionals',['returns'])]:
            with self.assertRaises(ValueError):
                assemble(dict(topic=topic, contents=contents, difficulty='basic', minutes=20))


if __name__ == '__main__': unittest.main()
