"""Compile trusted authored cases; run in isolated fixture directories.

Does not execute teacher-edited code, call APIs, or infer pedagogical approval.
"""
import hashlib
import json
import subprocess
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from teacher_copilot.csa_bank import QUESTIONS, FIXTURES
from teacher_copilot.csa_curriculum import VERSION
from teacher_copilot.questions import content_hash


def verify(jdk, output, questions=None, fixtures=None, version=VERSION):
    questions=QUESTIONS if questions is None else questions
    fixtures=FIXTURES if fixtures is None else fixtures
    jdk, output = Path(jdk).resolve(), Path(output).resolve()
    output.mkdir(parents=True, exist_ok=True)
    by_id = {q['id']: q for q in questions}
    sources = []
    source_hashes = {}
    for f in fixtures:
        name = 'Check_' + f['id']
        members = f['members'].replace('{{solution}}', f['solution'])
        body = f['body'].replace('{{solution}}', f['solution'])
        source = f'class {name} {{\n{members}\npublic static void main(String[] args) throws Exception {{\n{body}\n{f["checks"]}\n}}\n}}'
        path = output / (name + '.java')
        path.write_text(source, encoding='utf-8')
        sources.append(path)
        source_hashes[f['id']] = hashlib.sha256(source.encode('utf-8')).hexdigest()
        work = output / f['id']
        work.mkdir(exist_ok=True)
        for filename, text in f['files'].items():
            assert Path(filename).name == filename
            (work / filename).write_text(text, encoding='utf-8')
    def run(args, cwd=None):
        return subprocess.run(args, cwd=cwd, capture_output=True, text=True,
                              encoding='utf-8', errors='replace', timeout=30)
    # Argument file avoids Windows command length limits as the bank grows.
    argfile = output/'sources.txt'
    argfile.write_text('\n'.join('"'+str(p).replace('\\','/')+'"' for p in sources), encoding='utf-8')
    compiled = run([str(jdk/'bin/javac.exe'), '--release','17','-encoding','UTF-8', '-d',str(output), '@'+str(argfile)])
    (output/'compiler.txt').write_text(compiled.stderr, encoding='utf-8')
    if compiled.returncode:
        raise AssertionError(compiled.stderr)
    def execute(f):
        result = run([str(jdk/'bin/java.exe'), '-cp',str(output),'Check_'+f['id']], output/f['id'])
        passed = result.returncode == 0 and result.stdout == f['expected']
        return dict(id=f['id'], passed=passed, expected=f['expected'], actual=result.stdout,
                    stderr=result.stderr, source_hash=source_hashes[f['id']],
                    content_hash=content_hash(by_id[f['id']]),
                    additional_assertions=bool(f['checks']), files=list(f['files']))
    with ThreadPoolExecutor(max_workers=4) as pool:
        results = list(pool.map(execute, fixtures))
    concept = [dict(id=q['id'], content_hash=content_hash(q), status='requires_teacher_judgment')
               for q in questions if q['question_kind']=='concept']
    report = dict(version=version, question_count=len(questions), java_cases=len(results),
                  passed=sum(r['passed'] for r in results), results=results, conceptual=concept,
                  limitations='Checks authored code outputs/reference solutions and explicit assertions only. Does not prove prose explanations, full EK coverage, exam difficulty, timing, or teacher approval.')
    (output/'verification.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    failed = [r for r in results if not r['passed']]
    if failed:
        raise AssertionError(json.dumps(failed, ensure_ascii=False, indent=2))
    print(f'{len(results)} Java cases passed; {len(concept)} conceptual cases require judgment.')
    return report


if __name__=='__main__':
    root=Path(__file__).resolve().parent
    verify(root/'.cache/java/jdk-21.0.12.1+1', root/'outputs/csa_full_review/java_checks')
