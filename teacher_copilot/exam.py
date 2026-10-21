"""Server-timed, source-backed practice exam; not an official AP assessment."""
import json,re,secrets,threading,time
from pathlib import Path
from .worksheets import bank_data
from .student_check import check_submission,scoring_points
LOCK=threading.RLock()
DURATION=90*60
SET=[('AP-FRQ69fc5af861bea528S2','方法与控制结构'),('AP-FRQ414a8797b527e415S1','类设计'),('AP-FRQe12b4823e927b30fS1','ArrayList'),('AP-FRQ8b32f5bc1d3ab57aS1','二维数组')]

def questions():
    pool={q['id']:q for q in bank_data()['questions']}
    return [pool[key] for key,_ in SET]

def path_for(root,key):
    if not isinstance(key,str) or not re.fullmatch('[a-f0-9]{48}',key):raise ValueError('考试记录无效。')
    return Path(root)/'exams'/(key+'.json')

def write(root,s):
    path=path_for(root,s['id']);path.parent.mkdir(parents=True,exist_ok=True)
    temp=path.with_suffix('.tmp');temp.write_text(json.dumps(s,ensure_ascii=False),encoding='utf8');temp.replace(path)

def read(root,key,now):
    path=path_for(root,key)
    if not path.exists():raise ValueError('考试记录不存在或试用服务器已清理记录。')
    s=json.loads(path.read_text(encoding='utf8'))
    if s['status']=='active' and now>=s['deadline']:
        s.update(status='submitted',submitted_at=s['deadline'],reason='timeout',revision=s['revision']+1);write(root,s)
    return s

def view(s,now):
    fields=['id','title','task','code','question_images','java_input_kind']
    qs=[]
    for q,(_,label) in zip(questions(),SET):
        row={k:q.get(k) for k in fields};row['section']=label
        if s['status']=='submitted':
            row.update({k:q.get(k) for k in ['answer','reference_solution','rubric','explanation_en','scoring_pages']})
            row['scoring_points']=scoring_points(q)
        qs.append(row)
    return dict(**s,server_now=now,questions=qs)

def drafts(payload):
    source=payload.get('drafts',{})
    if not isinstance(source,dict):raise ValueError('作答格式无效。')
    if set(source)-{key for key,_ in SET}:raise ValueError('题目不属于本次考试。')
    for value in source.values():
        if not isinstance(value,str) or len(value)>20000:raise ValueError('每题最多输入 20000 个字符。')
    return source

def action(root,payload,now=None):
    now=time.time() if now is None else now
    if not isinstance(payload,dict):raise ValueError('请求格式无效。')
    kind=payload.get('action')
    with LOCK:
        if kind=='latest':
            folder=Path(root)/'exams'
            candidates=[]
            if folder.exists():
                for file in folder.glob('*.json'):
                    try:
                        item=json.loads(file.read_text(encoding='utf8'))
                        candidates.append((item['started_at'],item['id']))
                    except (ValueError,KeyError,OSError):
                        continue
            if not candidates:return {'session':None}
            return {'session':view(read(root,max(candidates)[1],now),now)}
        if kind=='start':
            questions() # Fail before creating a session if the curated set is missing.
            s=dict(id=secrets.token_hex(24),started_at=now,deadline=now+DURATION,status='active',revision=0,drafts={},results={})
            write(root,s);return view(s,now)
        s=read(root,payload.get('id'),now)
        if kind=='get':return view(s,now)
        if kind in {'save','submit'}:
            if s['status']=='submitted':return view(s,now) # Idempotent; never change submitted code.
            if payload.get('revision')!=s['revision']:raise ValueError('另一页面已更新本次考试，请重新载入后继续。')
            s['drafts'].update(drafts(payload));s['revision']+=1
            if kind=='submit':s.update(status='submitted',submitted_at=now,reason='manual')
            write(root,s);return view(s,now)
        if kind!='grade':raise ValueError('不支持的考试操作。')
        if s['status']!='submitted':raise ValueError('交卷后才能查看评分。')
        qid=payload.get('question_id')
        if qid not in {key for key,_ in SET}:raise ValueError('题目不属于本次考试。')
        if qid in s['results'] and not s['results'][qid].get('retryable'):return view(s,now)
        code=s['drafts'].get(qid,'')
    if not code.strip():result={'empty':True,'retryable':False}
    else:
        result=check_submission(dict(question_id=qid,code=code),questions())
        status=result.get('automatic',{}).get('status')
        result['retryable']=status not in {'passed','failed','compile_error','runtime_error','timeout','rejected'}
    with LOCK:
        s=read(root,payload['id'],time.time() if now is None else now);s['results'][qid]=result;write(root,s)
        return view(s,now)
