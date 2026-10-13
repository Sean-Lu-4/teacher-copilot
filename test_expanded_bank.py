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
        # Every nonempty content subset: no unrelated objectives, duplicates,
        # difficulty leakage or budget overruns; unsupported cases explicitly fail.
        for topic,contents in TOPIC_CONTENTS.items():
            for n in range(1,len(contents)+1):
                for selected in combinations(contents,n):
                    allowed=set().union(*(CONTENT[c][1] for c in selected))
                    for difficulty,(_,levels) in DIFFICULTIES.items():
                        for minutes in [10,20,30]:
                            settings=dict(topic=topic,contents=list(selected),difficulty=difficulty,minutes=minutes)
                            eligible=[q for q in BANKS[topic] if q['level'] in levels and selection_objectives(q,topic)<=allowed and q['minutes']<=minutes]
                            with self.subTest(settings=settings):
                                if not eligible:
                                    with self.assertRaises(ValueError):assemble(settings)
                                    continue
                                s,records=assemble(settings)
                                self.assertLessEqual(summary(s,records)['minutes'],minutes)
                                ids=[r['content']['id'] for r in records]
                                self.assertEqual(len(ids),len(set(ids)))
                                for r in records:
                                    self.assertIn(r['content']['level'],levels)
                                    self.assertLessEqual(selection_objectives(r['content'],topic),allowed)

    def test_dp_matches_exhaustive_optimum(self):
        for difficulty,(_,levels) in DIFFICULTIES.items():
            eligible=[q for q in QUESTIONS if q['level'] in levels]
            def score(group):
                return (len(set().union(*(set(q['objectives']) for q in group))),len({q['level'] for q in group}),sum(q['minutes'] for q in group))
            groups=[g for n in range(1,len(eligible)+1) for g in combinations(eligible,n) if sum(q['minutes'] for q in g)<=20]
            _,records=assemble(dict(topic='methods',contents=TOPIC_CONTENTS['methods'],difficulty=difficulty,minutes=20))
            self.assertEqual(score([r['content'] for r in records]),max(map(score,groups)))


if __name__=='__main__':unittest.main()
