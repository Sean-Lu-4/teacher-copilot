"""Verify trusted authored fixtures, including suggested repairs and boundaries."""
import json
import subprocess
from pathlib import Path
from teacher_copilot.conditionals_bank import QUESTIONS, JAVA_CASES, BANK_VERSION
from teacher_copilot.questions import content_hash


def verify(jdk, output):
    output.mkdir(parents=True, exist_ok=True)
    snippets = [f'static void {q["id"]}() {{ {q["code"]} }}' for q in QUESTIONS]
    snippets.append('''static void boundaries() {
        for (int age = -5; age <= 100; age++) {
            boolean allowed = age >= 12 && age <= 17;
            if (allowed != (age == 12 || age == 13 || age == 14 || age == 15 || age == 16 || age == 17)) throw new AssertionError("IB03");
        }
        for (int score = 0; score <= 100; score++) {
            String grade;
            if (score >= 90) grade = "A"; else if (score >= 80) grade = "B"; else grade = "C";
            String expected = score < 80 ? "C" : score < 90 ? "B" : "A";
            if (!grade.equals(expected)) throw new AssertionError("IA01");
        }
        int x = 4;
        if (x < 5) x += 3; else if (x > 6) x -= 2;
        if (x != 7) throw new AssertionError("IA02");
        boolean rejected = false;
        int count = 0, total = 12;
        try { boolean ok = total / count > 2 && count != 0; }
        catch (ArithmeticException e) { rejected = true; }
        if (!rejected) throw new AssertionError("IA03");
        String output = "";
        x = -2; int y = -1;
        if (x > 0) { if (y > 0) { output = "A"; } else { output = "B"; } }
        if (!output.equals("")) throw new AssertionError("IA04");
        for (int hours = 1; hours <= 100; hours++) {
            int fee;
            if (hours <= 3) fee = 6; else fee = 6 + (hours - 3) * 4;
            int expected = 6;
            for (int h = 4; h <= hours; h++) expected += 4;
            if (fee != expected) throw new AssertionError("IE01");
        }
        int a = 5, b = 2;
        if (a > b) a = a - b; else if (a > b) b = a + b; else b = a - b;
        if (a != 3 || b != 2) throw new AssertionError("IE02");
        for (x = -100; x <= 100; x++) {
            if (!(x < 10 || x > 20) != (x >= 10 && x <= 20)) throw new AssertionError("IE03");
        }
        for (x = -10; x <= 10; x++) for (y = -10; y <= 10; y++) {
            String original, rewritten;
            if (x >= 0) { if (y >= 0) original = "I"; else original = "IV"; }
            else { if (y >= 0) original = "II"; else original = "III"; }
            if (x >= 0 && y >= 0) rewritten = "I"; else if (x >= 0) rewritten = "IV";
            else if (y >= 0) rewritten = "II"; else rewritten = "III";
            if (!original.equals(rewritten)) throw new AssertionError("IE04");
        }
    }''')
    calls = ''.join(f'System.out.print("{q["id"]}|");{q["id"]}();System.out.println();' for q in QUESTIONS)
    source = output / 'ConditionalsCheck.java'
    source.write_text('public class ConditionalsCheck {\n' + '\n'.join(snippets) + '\npublic static void main(String[] args){' + calls + 'boundaries();}}', encoding='utf-8')
    def run(args):
        result = subprocess.run(args, capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=60)
        if result.returncode: raise AssertionError(result.stderr)
        return result
    run([str(jdk/'bin/javac.exe'), '--release', '17', '-encoding', 'UTF-8', '-d', str(output), str(source)])
    result = run([str(jdk/'bin/java.exe'), '-cp', str(output), 'ConditionalsCheck'])
    actual = dict(line.split('|', 1) for line in result.stdout.splitlines())
    for case in JAVA_CASES:
        assert actual[case['id']] == case['expected'], case
    report = dict(bank_version=BANK_VERSION, questions=[dict(id=q['id'], content_hash=content_hash(q), actual=actual[q['id']], passed=True) for q in QUESTIONS],
                  additional_checks='IB03 age -5..100; IA01 score 0..100; IA02 else-if; IA03 reversed short-circuit exception; IA04 negative outer condition; IE01 hours 1..100; IE02 else-if; IE03 x -100..100; IE04 441 coordinate pairs including zero.',
                  limitations='Executable outputs and authored repairs verified. Difficulty and timing need classroom trials; not a claim of complete AP syllabus coverage.')
    (output/'verification.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    return report


if __name__ == '__main__':
    root = Path(__file__).resolve().parent
    report = verify(root/'.cache/java/jdk-21.0.12.1+1', root/'outputs/conditionals_acceptance/java_checks')
    print('Passed:', len(report['questions']), 'questions plus repairs and boundaries')
