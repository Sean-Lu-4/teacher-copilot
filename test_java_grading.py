import base64
import json
import unittest
from unittest.mock import patch
from pathlib import Path
from teacher_copilot import java_grading as grading, java_runner, bead_grading

GOOD = '''int len = beadSequence.length();
boolean lengthGood = len >= 5 && len <= 10;
boolean correctColors = beadSequence.contains("B") && beadSequence.contains("W");
boolean startEndGood = beadSequence.charAt(0) == beadSequence.charAt(len-1);
if (lengthGood && correctColors && startEndGood) System.out.println("Acceptable");
else System.out.println("Not acceptable");'''


class GradingTests(unittest.TestCase):
    def test_all_reference_methods_wrap(self):
        refs=json.loads(Path('teacher_copilot/imported_bank/reference_solutions_20261015.json').read_text(encoding='utf8'))
        for profile in [p for p in grading.PROFILES.values() if p.get("reference_key") or p is bead_grading.PROFILE]:
            code=GOOD if profile.get('kind')=='fragment' else refs[profile['reference_key']]['code']
            source,offset=grading.build_source(profile,code,'marker')
            self.assertIn(code,source)
            self.assertEqual(source.splitlines()[offset],code.splitlines()[0])

    def test_no_class_escape_or_static_initializer(self):
        p=grading.PROFILES['AP-FRQ764c3eaaeb638f9fS7']
        for code in ['} class Escape {} class X {','static { while(true){} }','int x;']:
            with self.assertRaises(ValueError):grading.build_source(p,code,'marker')

    def test_compile_error_is_not_zero(self):
        r=grading._interpret({},'int x;',dict(status=dict(id=6),compile_output='Main.java:11: error: bad'),'',10)
        self.assertEqual(r['diagnostics'][0]['line'],1)
        self.assertIsNone(r['practice_score'])

    def test_timeout_is_not_zero(self):
        r=grading._interpret({},GOOD,dict(status=dict(id=5)),'',0)
        self.assertEqual(r['status'],'timeout')
        self.assertIsNone(r['practice_score'])

    def test_missing_results_fail_closed(self):
        with self.assertRaises(java_runner.RunnerUnavailable):
            grading._interpret(dict(cases=[dict(label='case')]),GOOD,dict(status=dict(id=3),stdout=''), 'marker',0)

    def test_mixed_cases_and_score_evidence(self):
        raw=dict(status=dict(id=3),stdout='m:0:FAIL\nm:1:PASS\nm:2:PASS\nm:3:FAIL\n')
        r=grading._interpret(bead_grading.PROFILE,GOOD,raw,'m',0)
        self.assertEqual(r['practice_score']['earned'],2)
        self.assertEqual(sum(x['status']=='earned' for x in r['score_evidence']),7)
        self.assertEqual(r['score_evidence'][1]['status'],'unverified')

    def test_unused_api_call_not_scoring_evidence(self):
        code=GOOD.replace('int len = beadSequence.length();','int unused=beadSequence.length(); int len=7;')
        cases=[dict(status='passed')]*4
        points=bead_grading.evidence(code,cases)
        self.assertEqual(points[0]['status'],'unverified')

    def test_comment_mentions_not_scoring_evidence(self):
        points=bead_grading.evidence('// beadSequence.length();\nint len=7;', [dict(status='passed')]*4)
        self.assertTrue(all(x['status']=='unverified' for x in points))

    def test_runner_network_disabled_and_bounded(self):
        value=base64.b64encode(b'OK').decode()
        with patch.dict('os.environ',{'CSA_JAVA_RUNNER_URL':'https://runner.example'}), patch.object(java_runner,'_request',side_effect=[{'token':'a'*36},{'status':{'id':3},'stdout':value}]) as request:
            self.assertEqual(java_runner.run_java('code')['stdout'],'OK')
            payload=request.call_args_list[0].args[2]
            self.assertFalse(payload['enable_network'])
            self.assertEqual(payload['cpu_time_limit'],2)

    def test_no_local_fallback(self):
        with patch.dict('os.environ',{'CSA_JAVA_RUNNER_URL':''}):
            self.assertEqual(grading.grade(bead_grading.QUESTION_ID,GOOD)['status'],'unavailable')


if __name__=='__main__':unittest.main()
