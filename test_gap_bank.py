import unittest
from teacher_copilot.gap_bank import QUESTIONS, FIXTURES, VERSION
from teacher_copilot.questions import create_record
from teacher_copilot.worksheets import assemble, summary, TOPIC_CONTENTS, replace_question, QUESTIONS as ALL
from build_gap_review import audit


class GapBankTests(unittest.TestCase):
    def test_records_unique_with_executable_checks(self):
        self.assertEqual(len(QUESTIONS),60)
        self.assertEqual(len({q['id'] for q in ALL}),len(ALL))
        self.assertEqual({q['id'] for q in QUESTIONS},{f['id'] for f in FIXTURES})
        for q in QUESTIONS:
            record=create_record(q,VERSION,dict(kind='original',sources=[]))
            self.assertEqual(record['validation']['teacher_review'],'pending')
            if q['question_kind']=='write':
                self.assertTrue(q['reference_solution'])
                self.assertTrue(next(f for f in FIXTURES if f['id']==q['id'])['checks'])

    def test_all_twenty_four_scenarios_complete_and_rotatable(self):
        for topic in ['csa-math','csa-strings','csa-string-algorithms','csa-files']:
            for difficulty in ['basic','advanced','exam']:
                for minutes in [10,20]:
                    with self.subTest(topic=topic,difficulty=difficulty,minutes=minutes):
                        s,r=assemble(dict(topic=topic,contents=TOPIC_CONTENTS[topic],difficulty=difficulty,minutes=minutes,purpose='homework'))
                        self.assertEqual(summary(s,r)['homework']['status'],'complete')
                        _,next_rows=assemble(s,{q['content']['id']:1000 for q in r})
                        self.assertNotEqual({q['content']['id'] for q in r},{q['content']['id'] for q in next_rows})
                        self.assertTrue(any(self.can_replace(s,r,i) for i in range(len(r))))

    @staticmethod
    def can_replace(settings,records,index):
        try:replace_question(settings,records,index);return True
        except ValueError:return False

    def test_audit_covers_all_combinations(self):
        rows=audit()
        self.assertEqual(len(rows),126)
        self.assertEqual(len({(r['topic'],r['difficulty'],r['target']) for r in rows}),126)
        self.assertTrue(all(r['actual']<=r['target'] for r in rows))


if __name__=='__main__':unittest.main()
