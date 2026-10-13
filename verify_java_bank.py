"""Compile and run trusted, authored bank fixtures; never executes edited UI input.

Usage: py verify_java_bank.py --jdk <portable JDK directory> --output <folder>
"""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
from teacher_copilot.expanded_bank import QUESTIONS, JAVA_CASES, BANK_VERSION
from teacher_copilot.questions import content_hash

ORIGINAL_CASES = [
    dict(id='Q1',body='System.out.print(total(3,5));',expected='8',invalid=['int result=total(3);','int result=display(8);','int result=total(3.5,5);']),
    dict(id='Q2',body='int a=difference(9,4);int b=difference(4,9);int c=difference(a,b);System.out.print(a+","+b+","+c);',expected='5,-5,10',invalid=[]),
    dict(id='Q3',body='int x=4;int y=increase(x);increase(x);x=increase(y);System.out.print(x+","+y);',expected='10,7',invalid=[]),
    dict(id='Q4',body='int x=5,y=3;System.out.print(combine(half(x+y),combine(y,half(x))));',expected='4',invalid=[]),
    dict(id='Q5',body='System.out.print(withFee(price(3,8,5)));',expected='21',invalid=[]),
    dict(id='EXIT',body='int a=2;next(a);int b=next(next(a));System.out.print(a+","+b);',expected='2,4',invalid=[]),
]


def verify(jdk, output):
    output.mkdir(parents=True, exist_ok=True)
    java = str((jdk/'bin/java.exe').resolve())
    javac = str((jdk/'bin/javac.exe').resolve())
    def run(args):
        return subprocess.run(args,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=60)
    version=run([java,'-version'])
    if version.returncode: raise RuntimeError(version.stderr)
    bank={q['id']:q for q in QUESTIONS}
    fixtures=ORIGINAL_CASES+JAVA_CASES
    assert set(bank)=={f['id'] for f in fixtures}
    code=[]
    for case in fixtures:
        q=bank[case['id']]
        code.append('class Case'+q['id']+' {\n'+q['code']+'\nstatic void test() { '+case['body']+' }\n}')
    main='public class BankCheck { public static void main(String[] args) {\n'
    for case in fixtures:
        main+='System.out.print("'+case['id']+'|");Case'+case['id']+'.test();System.out.println();\n'
    code.append(main+'}}')
    source=output/'BankCheck.java';source.write_text('\n'.join(code),encoding='utf-8')
    compile_result=run([javac,'--release','17','-encoding','UTF-8','-d',str(output),str(source)])
    if compile_result.returncode: raise AssertionError(compile_result.stderr)
    execution=run([java,'-cp',str(output),'BankCheck'])
    assert execution.returncode==0,execution.stderr
    actual=dict(line.split('|',1) for line in execution.stdout.splitlines())
    results=[]
    for case in fixtures:
        assert actual[case['id']]==case['expected'],(case['id'],actual[case['id']],case['expected'])
        results.append(dict(id=case['id'],passed=True,expected=case['expected'],actual=actual[case['id']],content_hash=content_hash(bank[case['id']])))
    invalid_count=0
    for case in fixtures:
        for index,body in enumerate(case['invalid']):
            name='Invalid'+case['id']+str(index)
            path=output/(name+'.java')
            path.write_text('class '+name+' {\n'+bank[case['id']]['code']+'\nstatic void test(){'+body+'}\n}',encoding='utf-8')
            result=run([javac,'--release','17','-encoding','UTF-8','-d',str(output),str(path)])
            assert result.returncode!=0,(name,'Expected compilation failure')
            (output/(name+'.diagnostics.txt')).write_text(result.stderr,encoding='utf-8')
            invalid_count+=1
    # Evaluate all expression-choice alternatives, not just the answer key.
    expression_cases={'Q5':(['21','25','9','17'],'21'),'E01':(['4','2','3','0'],'3'),
                      'E08':(['true','false','true','true'],'false')}
    extra=[]
    for id,(expected,target) in expression_cases.items():
        q=bank[id];name='Options'+id
        body='System.out.print('+ ' + "," + '.join('('+v+')' for v in q['options'].values())+');'
        extra.append('class '+name+' { '+q['code']+' static void test(){'+body+'}}')
    extra.append('class GeneralE04 { '+bank['E04']['code']+' static void test(){ for(int n=0;n<=100;n++){if(next(twice(n))!=2*n+1)throw new AssertionError();} int n=2;System.out.print(next(twice(n))+","+twice(next(n))+","+next(next(n))+","+twice(twice(n)));}}')
    extra.append('public class OptionCheck {public static void main(String[] args){'+''.join('Options'+id+'.test();System.out.println();' for id in expression_cases)+'GeneralE04.test();}}')
    path=output/'OptionCheck.java';path.write_text('\n'.join(extra),encoding='utf-8')
    compiled=run([javac,'--release','17','-encoding','UTF-8','-d',str(output),str(path)])
    assert compiled.returncode==0,compiled.stderr
    execution=run([java,'-cp',str(output),'OptionCheck']);assert execution.returncode==0,execution.stderr
    rows=execution.stdout.splitlines()
    for (id,(expected,target)),line in zip(expression_cases.items(),rows):
        assert line.split(',')==expected,(id,line)
        assert expected.count(target)==1
        assert list(bank[id]['options'])[expected.index(target)]==bank[id]['answer_key']
    assert rows[-1]=='5,6,4,8'
    # Remaining output MCQs: the four choices must be distinct and the fixture
    # result must select exactly the recorded key. E03 uses compile diagnostics.
    for id in ['Q4','E02','E05','E06','E07']:
        q=bank[id];options=q['options']
        assert len(set(options.values()))==4
        assert [k for k,v in options.items() if v==actual[id]]==[q['answer_key']]
    report=dict(bank_version=BANK_VERSION,java=version.stderr.strip(),questions=results,
                compile_rejections=invalid_count,expression_alternatives_checked=list(expression_cases)+['E04'],
                source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
                limitations='Checks executable results and compilation, not classroom difficulty or teaching suitability.')
    (output/'java_verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(f'Java verification passed: {len(results)} questions, {invalid_count} invalid statements rejected.')
    return report


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--jdk',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    verify(args.jdk,args.output)
