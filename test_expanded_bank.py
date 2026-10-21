import unittest
from collections import Counter
from itertools import combinations
from teacher_copilot.expanded_bank import QUESTIONS, BANK_VERSION
from teacher_copilot.questions import create_record
from teacher_copilot.worksheets import assemble, summary, CONTENT, TOPIC_CONTENTS, DIFFICULTIES, QUESTIONS as ALL_QUESTIONS, BANKS, selection_objectives


class ExpandedBankTests(unittest.TestCase):
    def test_thirty_distinct_complete_questions(self):
        self.assertEqual(len(QUESTIONS),30)
        self.assertEqual(len({q['id'] for q in QUESTIONS}),30)
        self.assertEqual(len({q['task'] for q in QUESTIONS}),30)
        buckets=Counter('basic' if q['level']<3 else 'advanced' if q['level']==3 else 'exam' for q in QUESTIONS)
        self.assertEqual(dict(buckets),dict(basic=10,advanced=10,exam=10))
        for q in QUESTIONS:
            create_record(q,BANK_VERSION,dict(kind='original',sources=[]))
            self.assertTrue(q['prerequisites'])

    def test_all_topic_difficulty_time_combinations(self):
        from teacher_copilot.worksheets import VISIBLE_TOPICS, eligible_questions, validate_settings
        # Single labels, adjacent pairs and complete topic: bounded even as the bank grows.
        for topic in VISIBLE_TOPICS:
            if topic == 'all-csa': continue
            contents = TOPIC_CONTENTS[topic]
            subsets = [[c] for c in contents] + [contents[i:i+2] for i in range(len(contents)-1)] + [contents]
            for selected in subsets:
                for difficulty in DIFFICULTIES:
                    for minutes in [10,20,30]:
                        settings=dict(topic=topic,contents=list(selected),difficulty=difficulty,minutes=minutes)
                        eligible=[q for q in eligible_questions(validate_settings(settings)) if q['minutes'] <= minutes]
                        with self.subTest(settings=settings):
                            if not eligible:
                                with self.assertRaises(ValueError): assemble(settings)
                                continue
                            s, records=assemble(settings)
                            self.assertLessEqual(summary(s, records)['minutes'], minutes)
                            ids=[r['content']['id'] for r in records]
                            self.assertEqual(len(ids),len(set(ids)))
                            self.assertLessEqual(set(ids), {q['id'] for q in eligible})
                            self.assertTrue(all(r['content'].get('source_item_id') for r in records))

    def test_dp_matches_exhaustive_optimum(self):
        from unittest.mock import patch
        from teacher_copilot.worksheets import eligible_questions, validate_settings
        settings=dict(topic='csa-calls',contents=TOPIC_CONTENTS['csa-calls'],difficulty='any',minutes=20)
        eligible=eligible_questions(validate_settings(settings))[:10]
        wanted=set().union(*(CONTENT[c][1] for c in settings['contents']))
        def score(group):
            return (len(set().union(*(selection_objectives(q,'csa-calls') & wanted for q in group))),len({q['level'] for q in group}),sum(q['minutes'] for q in group))
        groups=[g for n in range(1,len(eligible)+1) for g in combinations(eligible,n) if sum(q['minutes'] for q in g)<=20]
        with patch.dict(BANKS, {'csa-calls':eligible}):
            _, records=assemble(settings)
        self.assertEqual(score([r['content'] for r in records]), max(map(score,groups)))

if __name__=='__main__':unittest.main()
