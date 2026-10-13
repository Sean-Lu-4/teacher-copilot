import tempfile
import unittest
from pathlib import Path
from teacher_copilot.worksheets import catalog, assemble, summary, TOPIC_CONTENTS, BANKS, navigation_settings, selection_objectives, CONTENT
from teacher_copilot.review_app import ReviewStore


class HomeworkTests(unittest.TestCase):
    def test_single_hierarchy_and_legacy_preservation(self):
        data=catalog();topics={t['id']:t for t in data['topics']}
        self.assertEqual(len(data['units']),4)
        self.assertEqual(len(topics),21)
        self.assertFalse({'methods','method-calls','method-returns','conditionals','csa-logic'} & topics.keys())
        self.assertTrue(all(t['unit'] in {'1','2','3','4'} and not t['title'].startswith('U') for t in topics.values()))
        self.assertEqual(len({q['id'] for q in BANKS['csa-calls']}),len(BANKS['csa-calls']))
        self.assertIn('Q1',{q['id'] for q in BANKS['csa-calls']})
        self.assertIn('IE03',{q['id'] for q in BANKS['csa-selection']})

    def test_pilot_twenty_minutes_all_tiers_and_ten_basic(self):
        for topic in ['csa-loops','csa-arrays']:
            for difficulty in ['basic','advanced','exam']:
                settings,rows=assemble(dict(topic=topic,contents=TOPIC_CONTENTS[topic],difficulty=difficulty,minutes=20,purpose='homework'))
                info=summary(settings,rows)
                self.assertEqual(info['minutes'],20)
                self.assertEqual(info['homework']['status'],'complete')
                self.assertIsNone(info['homework']['supplement_request'])
                self.assertEqual(len(rows),len({r['content']['id'] for r in rows}))
            settings,rows=assemble(dict(topic=topic,contents=TOPIC_CONTENTS[topic],difficulty='basic',minutes=10,purpose='homework'))
            self.assertEqual(summary(settings,rows)['homework']['status'],'complete')

    def test_strict_shortfall_and_coverage_gap(self):
        settings,rows=assemble(dict(topic='csa-api',contents=['ced_1_7'],difficulty='basic',minutes=20,purpose='homework'))
        info=summary(settings,rows)['homework']
        self.assertEqual(info['shortfall_minutes'],17)
        self.assertFalse(info['api_enabled'])
        self.assertEqual(info['supplement_request']['strategy'],'add')
        settings,rows=assemble(dict(topic='csa-arrays',contents=TOPIC_CONTENTS['csa-arrays'],difficulty='exam',minutes=10,purpose='homework'))
        info=summary(settings,rows)['homework']
        self.assertEqual(info['actual_minutes'],10)
        self.assertEqual(info['status'],'partial')
        self.assertTrue(info['missing_contents'])
        self.assertEqual(info['supplement_request']['strategy'],'rebalance')

    def test_history_not_rewritten_and_selection_restored(self):
        with tempfile.TemporaryDirectory() as temp:
            store=ReviewStore(temp)
            state=store.mutate(dict(action='generate',settings=dict(topic='conditionals',contents=['logic'],difficulty='basic',minutes=10)))
            path=Path(temp)/state['run']/'questions.json';before=path.read_bytes()
            loaded=store.state(state['run'])
            self.assertEqual(loaded['settings']['topic'],'conditionals')
            self.assertEqual(loaded['navigation_settings']['topic'],'csa-selection')
            self.assertEqual(loaded['navigation_settings']['contents'],['ced_2_5'])
            self.assertEqual(path.read_bytes(),before)
        nav=navigation_settings(dict(topic='csa-calls',contents=['ced_1_10'],difficulty='exam',minutes=20))
        self.assertEqual(nav['contents'],['calls','returns','tracing'])

    def test_edit_recomputes_budget_and_rejects_custom_homework(self):
        settings,rows=assemble(dict(topic='csa-arrays',contents=TOPIC_CONTENTS['csa-arrays'],difficulty='basic',minutes=10,purpose='homework'))
        rows[0]['content']['minutes']+=5
        self.assertEqual(summary(settings,rows)['homework']['status'],'partial')
        self.assertTrue(any('超过' in w for w in summary(settings,rows)['warnings']))
        with self.assertRaises(ValueError):
            assemble(dict(topic='csa-arrays',contents=['ced_4_3'],difficulty='basic',minutes=15,purpose='homework'))


if __name__=='__main__':unittest.main()
