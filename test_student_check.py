import unittest
from teacher_copilot.student_check import check_submission, scoring_points, syntax_report


class StudentCheckTests(unittest.TestCase):
    def setUp(self):
        self.q = dict(id='test', source_item_id='pdf', question_kind='write', answer='''Part A Point 1
To earn this point, responses must demonstrate the following:
Traverses all elements.
Canonical Solution:
for (int i = 0; i < a.length; i++) {}
0
1
The response earns the point.
Responses can still earn the point even if they
make an error in the return value.
Part A Point 2
To earn this point, responses must demonstrate the following:
Returns the computed total.
Canonical Solution:
return total;
''')

    def test_preserves_criteria_and_partial_credit_exception(self):
        points = scoring_points(self.q)
        self.assertEqual(len(points), 2)
        self.assertIn('return value', points[0]['exceptions'])
        self.assertEqual(points[0]['status'], 'unverified')

    def test_no_guessed_rubric(self):
        self.assertEqual(scoring_points(dict(answer='Worth 9 points.')), [])

    def test_valid_different_implementations(self):
        for code in ['int f(int[] a) { int s=0; for(int x:a)s+=x; return s; }',
                     'int f(int[] a) { int s=0,i=0; while(i<a.length){s+=a[i++];} return s; }',
                     'int x = 2; System.out.println(x);']:
            self.assertEqual(syntax_report(code)['status'], 'passed')

    def test_syntax_errors_have_student_line_numbers(self):
        report = syntax_report('int f() {\n return ; @\n}')
        self.assertEqual(report['status'], 'failed')
        self.assertTrue(all(1 <= e['line'] <= 3 for e in report['diagnostics']))

    def test_syntax_is_never_compilation_or_score(self):
        report = check_submission(dict(question_id='test', code='int x = "wrong type";'), [self.q])
        self.assertEqual(report['syntax']['status'], 'passed')
        self.assertEqual(report['compilation']['status'], 'unavailable')
        self.assertIsNone(report['score'])
        self.assertTrue(all(p['status'] == 'unverified' for p in report['scoring_points']))

    def test_untrusted_code_is_only_parsed(self):
        report = check_submission(dict(question_id='test', code='while(true){}'), [self.q])
        self.assertEqual(report['tests']['status'], 'unavailable')

    def test_input_bounds_and_question_validation(self):
        for payload in [[], dict(question_id='test', code=''), dict(question_id='test', code='x'*20001),
                        dict(question_id='missing', code='int x;')]:
            with self.assertRaises(ValueError):
                check_submission(payload, [self.q])


if __name__ == '__main__':
    unittest.main()
