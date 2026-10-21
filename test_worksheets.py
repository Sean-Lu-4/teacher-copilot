import unittest
from teacher_copilot.worksheets import assemble, summary, paper_report, CONTENT, TOPIC_CONTENTS, catalog
import test_review_app


class WorksheetTests(unittest.TestCase):
    def test_topic_catalog_and_scope(self):
        data = catalog()
        self.assertEqual([d['title'] for d in data['difficulties']], ['全部难度（含未标定）', '基础', '巩固', '考试'])
        topics = {t['id']: {c['id'] for c in t['contents']} for t in data['topics']}
        self.assertNotIn('method-calls', topics)
        self.assertIn('returns', topics['csa-calls'])
        with self.assertRaises(ValueError):
            assemble(self.settings(topic='method-calls', contents=['returns']))
        settings, records = assemble(self.settings())
        self.assertTrue(records)
        self.assertIn('（教师版）', paper_report(dict(worksheet_settings=settings),records,'teacher'))

    def test_removed_mixed_difficulty_and_guidance_export(self):
        with self.assertRaises(ValueError):
            assemble(self.settings(difficulty='mixed'))
        settings, records = assemble(self.settings())
        teacher = paper_report(dict(worksheet_settings=settings), records, 'teacher')
        student = paper_report(dict(worksheet_settings=settings), records, 'student')
        self.assertNotIn('学生答错时的讲解建议', teacher)
        self.assertNotIn('教师处理', teacher)
        self.assertNotIn('AI 模拟体验', student)

    def settings(self, **changes):
        return dict(dict(topic='csa-calls', contents=TOPIC_CONTENTS['csa-calls'], difficulty='any', minutes=20), **changes)

    def test_budget_difficulty_and_determinism(self):
        s, records = assemble(self.settings())
        self.assertLessEqual(summary(s, records)['minutes'], 20)
        self.assertEqual(len({r['content']['id'] for r in records}), len(records))
        self.assertEqual([r['content']['level'] for r in records], sorted(r['content']['level'] for r in records))
        self.assertEqual(assemble(self.settings())[1], records)
        self.assertTrue(all(r['content'].get('source_item_id') for r in records))

    def test_strict_scope_and_no_match(self):
        from teacher_copilot.worksheets import selection_objectives
        selected=TOPIC_CONTENTS['csa-calls']
        _,records=assemble(self.settings(contents=selected))
        allowed=set().union(*(CONTENT[c][1] for c in selected))
        self.assertTrue(all(selection_objectives(r['content'],'csa-calls') & allowed for r in records))
        with self.assertRaises(ValueError):
            assemble(self.settings(contents=['ced_4_3']))

    def test_short_bank_and_invalid_inputs(self):
        s, records = assemble(self.settings(minutes=90))
        self.assertLessEqual(summary(s, records)['minutes'],90)
        for changes in [dict(minutes=0), dict(minutes=True), dict(contents=[]), dict(topic='arrays'), dict(difficulty='invalid')]:
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                assemble(self.settings(**changes))

    def test_student_export_has_no_answer_or_rubric(self):
        s, records = assemble(self.settings())
        plan = dict(worksheet_settings=s)
        student = paper_report(plan, records, 'student')
        teacher = paper_report(plan, records, 'teacher')
        for r in records:
            q = r['content']
            q.update(answer='PRIVATE_ANSWER_SENTINEL',rubric='PRIVATE_RUBRIC_SENTINEL')
            student=paper_report(plan,records,'student')
            teacher=paper_report(plan,records,'teacher')
            if q.get('question_images'):
                for image in q['question_images']:self.assertIn(image,student)
            else:self.assertIn(q['task'], student)
            self.assertNotIn(q['answer'], student)
            self.assertNotIn(q['rubric'], student)
            self.assertIn(q['answer'], teacher)
            self.assertIn(q['rubric'], teacher)


class AssemblyStoreTests(unittest.TestCase):
    setUp = test_review_app.ReviewTests.setUp
    def test_generate_save_and_export_modified_student_paper(self):
        state = self.store.mutate(dict(action='generate',settings=dict(topic='csa-calls',contents=TOPIC_CONTENTS['csa-calls'], difficulty='any',minutes=20)))
        self.assertEqual(state['settings']['minutes'],20)
        first=state['records'][0]['content']['id']
        state=self.store.mutate(dict(action='revise',run=state['run'],version=state['version'],id=first,actor='teacher',reason='edit',changes={'title':'New paper title'}))
        output=self.store.mutate(dict(action='export',audience='student',run=state['run'],version=state['version']))
        self.assertIn('New paper title',output['report'])
        self.assertNotIn('教师处理',output['report'])


if __name__ == '__main__':
    unittest.main()
