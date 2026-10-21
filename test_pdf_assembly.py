import tempfile,time,unittest
from unittest.mock import patch
from teacher_copilot.worksheets import assemble_exam,availability_preview,TOPIC_CONTENTS,VISIBLE_TOPICS,bank_data
from teacher_copilot.review_app import ReviewStore
class PdfAssemblyTests(unittest.TestCase):
    def settings(self,all_topics=False):
        topics=[t for t in VISIBLE_TOPICS if t!='all-csa']
        if not all_topics:topics=topics[:11]
        return dict(topics=topics,topic='all-csa',contents=list(dict.fromkeys(c for t in topics for c in TOPIC_CONTENTS[t])),purpose='exam',difficulty='any',minutes=90,question_count=30,total_marks=100,question_types=['concept','write'])
    def test_large_papers_bounded_and_valid(self):
        for all_topics in [False,True]:
            s=self.settings(all_topics);start=time.perf_counter();_,rows=assemble_exam(s)
            self.assertLess(time.perf_counter()-start,10,'Large assembly regressed to combinatorial search')
            self.assertEqual(len(rows),30);self.assertEqual(len({r['content']['id'] for r in rows}),30)
            self.assertLessEqual(sum(r['content']['minutes'] for r in rows),90)
            self.assertEqual(sum(r['content']['marks'] for r in rows),100)
            self.assertTrue(all(r['content'].get('source_item_id') for r in rows))
            preview=availability_preview(s);self.assertEqual(preview['planned_count'],30);self.assertFalse(preview['error'])
    def test_retired_sources_never_call_model_or_create_runs(self):
        with tempfile.TemporaryDirectory() as root,patch.object(ReviewStore,'ai_records',side_effect=AssertionError('Model must not run')):
            store=ReviewStore(root)
            for mode in ['ai','hybrid','mock']:
                with self.assertRaisesRegex(ValueError,'PDF'):store.mutate(dict(action='generate',source=mode,settings=self.settings()))
            self.assertEqual(store.runs(),[])
            state=store.mutate(dict(action='generate',source='local',settings=self.settings()))
            self.assertEqual(len(state['records']),30)
    def test_visible_bank_is_pdf_only(self):
        data=bank_data()
        self.assertTrue(data['questions'])
        self.assertTrue(all(q.get('source_item_id') for q in data['questions']))
if __name__=='__main__':unittest.main()
