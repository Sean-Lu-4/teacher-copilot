import tempfile
import unittest
from pathlib import Path
from teacher_copilot.worksheets import catalog, assemble, summary, TOPIC_CONTENTS, BANKS, navigation_settings, selection_objectives, CONTENT
from teacher_copilot.review_app import ReviewStore


class HomeworkTests(unittest.TestCase):
    def test_single_hierarchy_and_retired_short_answers_excluded(self):
        data=catalog();topics={t['id']:t for t in data['topics']}
        self.assertEqual(len(data['units']),4)
        self.assertEqual(len(topics),21)
        self.assertFalse({'methods','method-calls','method-returns','conditionals','csa-logic'} & topics.keys())
        self.assertTrue(all(t['unit'] in {'1','2','3','4'} and not t['title'].startswith('U') for t in topics.values()))
        self.assertEqual(len({q['id'] for q in BANKS['csa-calls']}),len(BANKS['csa-calls']))
        self.assertNotIn('Q1',{q['id'] for q in BANKS['csa-calls']})
        self.assertNotIn('IE03',{q['id'] for q in BANKS['csa-selection']})

    def test_pdf_budget_custom_duration_and_unique_questions(self):
        for topic in ['csa-loops','csa-arrays']:
            for minutes in [10,15,20,27]:
                settings,rows=assemble(dict(topic=topic,contents=TOPIC_CONTENTS[topic],difficulty='any',minutes=minutes,purpose='homework'))
                self.assertLessEqual(summary(settings,rows)['minutes'],minutes)
                self.assertEqual(len(rows),len({r['content']['id'] for r in rows}))
                self.assertTrue(all(r['content'].get('source_item_id') for r in rows))

    def test_strict_shortfall_and_coverage_gap(self):
        from unittest.mock import patch
        source=next(q for q in BANKS['csa-arrays'] if q.get('source_item_id') and q.get('options'))
        with patch.dict(BANKS,{'csa-arrays':[dict(source,minutes=3)]}):
            settings,rows=assemble(dict(topic='csa-arrays',contents=TOPIC_CONTENTS['csa-arrays'],difficulty='any',minutes=20,purpose='homework'))
        info=summary(settings,rows)['homework']
        self.assertEqual(info['shortfall_minutes'],17)
        self.assertEqual(info['supplement_request']['strategy'],'rebalance')
        self.assertTrue(info['missing_contents'])
        self.assertEqual(len(rows),1)

    def test_history_not_rewritten_and_selection_restored(self):
        with tempfile.TemporaryDirectory() as temp:
            store=ReviewStore(temp)
            state=store.mutate(dict(action='generate',settings=dict(topic='csa-selection',contents=TOPIC_CONTENTS['csa-selection'],difficulty='any',minutes=10)))
            path=Path(temp)/state['run']/'questions.json';before=path.read_bytes()
            loaded=store.state(state['run'])
            self.assertEqual(loaded['settings']['topic'],'csa-selection')
            self.assertEqual(loaded['navigation_settings']['topic'],'csa-selection')
            self.assertEqual(loaded['navigation_settings']['contents'],TOPIC_CONTENTS['csa-selection'])
            self.assertEqual(path.read_bytes(),before)
        nav=navigation_settings(dict(topic='csa-calls',contents=['ced_1_10'],difficulty='exam',minutes=20))
        self.assertEqual(nav['contents'],['calls','returns','tracing'])

    def test_edit_recomputes_budget_and_accepts_custom_duration(self):
        settings,rows=assemble(dict(topic='csa-arrays',contents=TOPIC_CONTENTS['csa-arrays'],difficulty='any',minutes=10,purpose='homework'))
        rows[0]['content']['minutes']+=20
        self.assertEqual(summary(settings,rows)['homework']['status'],'partial')
        self.assertTrue(any('超过' in w for w in summary(settings,rows)['warnings']))
        custom,_=assemble(dict(topic='csa-arrays',contents=['ced_4_3'],difficulty='any',minutes=15,purpose='homework'))
        self.assertEqual(custom['minutes'],15)


if __name__=='__main__':unittest.main()
