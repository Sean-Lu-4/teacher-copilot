import json,subprocess,pathlib,sys
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]))
from teacher_copilot.java_grading import PROFILES,build_source
from test_java_grading import GOOD
refs=json.load(open('tools/java_reference_fixtures.json',encoding='utf8'))
old=json.load(open('teacher_copilot/imported_bank/reference_solutions_20261015.json',encoding='utf8'))
for id,p in PROFILES.items():
 if id not in refs:refs[id]=GOOD if p.get('kind')=='fragment' else old[p['reference_key']]['code']
import argparse
parser=argparse.ArgumentParser(description='Run only the reviewed repository fixtures; never accepts student code')
parser.add_argument('--jdk',required=True,type=pathlib.Path)
args=parser.parse_args()
jdk=args.jdk/'bin';work=pathlib.Path('tmp/extended-check');work.mkdir(exist_ok=True)
report=[]
def run(id,p,code,should_pass=True):
 source,_=build_source(p,code,'VERIFY');(work/'Main.java').write_text(source,encoding='utf8')
 c=subprocess.run([str(jdk/'javac.exe'),'-encoding','UTF-8',str(work/'Main.java')],capture_output=True,text=True,timeout=20)
 if c.returncode:report.append(dict(id=id,ok=False,compile_error=c.stderr));return
 r=subprocess.run([str(jdk/'java.exe'),'-cp',str(work),'Main'],capture_output=True,text=True,timeout=5)
 failed=r.returncode!=0 or ':FAIL' in r.stdout or ':ERROR' in r.stdout
 expected=len(p.get('cases',p.get('examples',[])))
 count=len([x for x in r.stdout.splitlines() if x.startswith('VERIFY:') and (x.endswith(':PASS') or x.endswith(':FAIL') or ':ERROR:' in x)])
 report.append(dict(id=id,ok=(not failed if should_pass else failed) and count==expected,expected_cases=expected,stdout=r.stdout,stderr=r.stderr,variant='correct' if should_pass else 'intentional_error'))
for id,code in refs.items():
 p=PROFILES[id]
 if p.get('kind')=='parts':
  for i,c in enumerate(code):run(id+':'+str(i),p['parts'][i],c)
 else:run(id,p,code)
mutants=[('AP-FRQ414a8797b527e415S1','if(need>fuel)','if(need>=fuel)'),('AP-FRQ414a8797b527e415S1','fuel-=need;',''),('AP-FRQ906422c04f2fa6d6S9','if(n==0)first=!first;','if(n==0)first=true;'),('AP-FRQe12b4823e927b30fS1','a.getAge()>=13','a.getAge()>13'),('AP-FRQ69fc5af861bea528S5','i+s.length()<=moveSequence.length();i++','i+s.length()<=moveSequence.length();i+=s.length()'),('AP-FRQ906422c04f2fa6d6S10','if(current>start)','if(current>=start)'),('AP-FRQ69fc5af861bea528S2','getNextWord(next)','getNextWord(s)'),('AP-FRQ906422c04f2fa6d6S7','if(r>0&&apples[r-1][c].isRotten())continue;','')]
# A top-edge rotten apple is already covered by the row-below sample.
for id,a,b in mutants:
 code=refs[id]
 if a not in code:raise AssertionError(a)
 run(id+' mutation '+a,PROFILES[id],code.replace(a,b),False)
pathlib.Path('tmp/frq-expanded-acceptance.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
sys.stdout.reconfigure(encoding='utf8');print('Runs',len(report),'passed',sum(r['ok'] for r in report));print(json.dumps([r for r in report if not r['ok']],ensure_ascii=False,indent=2))
