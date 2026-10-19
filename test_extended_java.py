import json
import unittest
from pathlib import Path
from unittest.mock import patch

from teacher_copilot import java_grading as grading
from teacher_copilot.student_check import scoring_points, check_submission
from teacher_copilot.java_score_evidence import evidence


class ExtendedJavaTests(unittest.TestCase):
    def test_whole_class_cannot_replace_harness(self):
        profile = grading.PROFILES['AP-FRQ414a8797b527e415S1']
        for code in ['class Car {} class Main {}', 'class Wrong {}',
                     'class Car { static { while(true){} } }']:
            with self.assertRaises(ValueError):
                grading.build_source(profile, code, 'test')

    def test_class_line_numbers_preserved(self):
        code = '// comment\npublic class Car {\nprivate double fuel;\n}'
        source, offset = grading.build_source(grading.PROFILES['AP-FRQ414a8797b527e415S1'], code, 'test')
        self.assertEqual(source.splitlines()[offset+2], 'private double fuel;')

    def test_no_combined_parts_without_selection(self):
        for part in [None, -1, 8, True, '0']:
            with self.assertRaises(ValueError):
                grading.grade('AP-FRQ69fc5af861bea528S3', 'System.out.println(1);', part)

    def test_snippet_escape_rejected(self):
        profile = grading.PROFILES['AP-FRQ69fc5af861bea528S3']['parts'][0]
        with self.assertRaises(ValueError):
            grading.build_source(profile, '} void evil(){', 'test')

    def test_distinct_criteria_with_same_label_are_retained(self):
        text = '\n'.join('Part A Point 1\nTo earn this point, responses must demonstrate the following:\n'+s+'\nCanonical Solution:\ncode' for s in ['Prints text', 'Prints song'])
        points = scoring_points(dict(answer=text))
        self.assertEqual(len(points), 2)
        self.assertNotEqual(points[0]['id'], points[1]['id'])

    def test_skill_points_after_canonical_solution_are_retained(self):
        points=scoring_points(dict(answer='+1 [Skill 3.A] First criterion\nCanonical Solution:\ncode\nPart B\n+1 [Skill 3.B] Second criterion\nCanonical Solution:\ncode'))
        self.assertEqual([p['description'] for p in points], ['First criterion','Second criterion'])

    def test_failed_function_does_not_earn_algorithm_points(self):
        points=[dict(id=str(i),description='criterion',points=1) for i in range(7)]
        code='public class Car {public boolean canMakeTrip(double d){return true;}}'
        r=evidence('AP-FRQ414a8797b527e415S1',code,dict(status='failed',cases=[dict(status='failed')]*3),points)
        self.assertEqual(r[0]['status'],'earned')
        self.assertEqual(r[5]['status'],'unverified')
        self.assertEqual(r[6]['status'],'unverified')

    def test_service_failure_never_awards_points(self):
        points=[dict(id='1',description='class declaration',points=1)]
        r=evidence('AP-FRQ414a8797b527e415S1','public class Car {}',dict(status='unavailable'),points)
        self.assertEqual(r[0]['status'],'unverified')

    def test_other_part_does_not_receive_output_score(self):
        points=[dict(id=str(i),description='criterion',points=1) for i in range(6)]
        r=evidence('AP-FRQ69fc5af861bea528S3','System.out.println("x");',dict(status='passed',cases=[dict(status='passed')]*2),points,1)
        self.assertEqual(r[2]['status'],'unverified')
        self.assertEqual(r[5]['status'],'earned')


if __name__ == '__main__':
    unittest.main()
