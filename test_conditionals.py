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
        self.assertEqual(catalog()['bank_count'], 275)

    def test_tiers_and_exports(self):
        for difficulty, minutes in [('basic',12), ('advanced',16), ('exam',20)]:
            settings, records = assemble(dict(topic='conditionals', contents=TOPIC_CONTENTS['conditionals'], difficulty=difficulty, minutes=20))
            self.assertEqual(len(records), 4)
            self.assertEqual(summary(settings, records)['minutes'], minutes)
            self.assertTrue(all(r['bank_version'] == BANK_VERSION for r in records))
            plan = dict(worksheet_settings=settings)
            student = paper_report(plan, records, 'student')
            teacher = paper_report(plan, records, 'teacher')
            self.assertIn('条件判断', student)
            self.assertIn('main 方法内', student)
            for r in records:
                self.assertIn(r['content']['answer'], teacher)
                self.assertNotIn(r['content']['answer'], student)
                self.assertNotIn(r['content']['intervention'], student)

    def test_cross_topic_rejected(self):
        for topic, contents in [('methods',['logic']), ('conditionals',['returns'])]:
            with self.assertRaises(ValueError):
                assemble(dict(topic=topic, contents=contents, difficulty='basic', minutes=20))


if __name__ == '__main__': unittest.main()
