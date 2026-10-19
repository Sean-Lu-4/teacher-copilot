import json
import unittest
from pathlib import Path
from tree_sitter import Language, Parser
import tree_sitter_java
from teacher_copilot.java_initialization import initialization_lines
from teacher_copilot.java_score_evidence import evidence
from teacher_copilot.java_grading import PROFILES


class InitializationTests(unittest.TestCase):
    def trace(self, code):
        tree=Parser(Language(tree_sitter_java.language())).parse(code.encode())
        self.assertFalse(tree.root_node.has_error)
        return initialization_lines(tree.root_node.named_children[0])

    def test_all_reviewed_class_fixtures(self):
        refs=json.loads(Path('tools/java_reference_fixtures.json').read_text(encoding='utf8'))
        for id,code in refs.items():
            if PROFILES[id].get('kind')=='class':
                with self.subTest(id=id):self.assertTrue(self.trace(code))

    def test_this_and_aliases_are_accepted(self):
        self.assertTrue(self.trace('public class Car {double fuel,mpg;public Car(double fuel,double mpg){double saved=fuel;this.fuel=saved;this.mpg=mpg;}}'))

    def test_local_shadowing_does_not_initialize_fields(self):
        self.assertFalse(self.trace('public class Car {double fuel,mpg;public Car(double fuel,double mpg){fuel=fuel;mpg=mpg;}}'))

    def test_overwritten_parameter_is_not_evidence(self):
        self.assertFalse(self.trace('public class Car {double f,m;public Car(double a,double b){f=a;m=b;f=0;}}'))

    def test_unused_alias_is_not_evidence(self):
        self.assertFalse(self.trace('public class Car {double f,m;public Car(double a,double b){double unused=a;f=0;m=b;}}'))

    def test_conditional_or_unknown_helper_stays_pending(self):
        self.assertFalse(self.trace('public class Car {double f,m;public Car(double a,double b){if(a>0)f=a;m=b;}}'))
        self.assertFalse(self.trace('public class Car {double f,m;public Car(double a,double b){f=Math.abs(a);m=b;}}'))

    def test_wrong_runtime_result_does_not_award_initialization(self):
        id='AP-FRQ414a8797b527e415S1'
        code=json.loads(Path('tools/java_reference_fixtures.json').read_text(encoding='utf8'))[id]
        points=[dict(id=str(i),description='criterion',points=1) for i in range(7)]
        result=dict(status='passed',cases=[dict(status='passed')]*3)
        scored=evidence(id,code,result,points)
        self.assertEqual(scored[3]['status'],'earned')
        self.assertEqual(sum(p['status']=='earned' for p in scored),7)
        result['status']='failed';result['cases'][1]['status']='failed'
        self.assertEqual(evidence(id,code,result,points)[3]['status'],'unverified')

    def test_empty_results_cannot_award_initialization(self):
        code='public class Car {double f,m;public Car(double a,double b){f=a;m=b;}}'
        points=[dict(id=str(i),description='criterion',points=1) for i in range(7)]
        self.assertEqual(evidence('AP-FRQ414a8797b527e415S1',code,dict(status='passed',cases=[]),points)[3]['status'],'unverified')


if __name__=='__main__':unittest.main()
