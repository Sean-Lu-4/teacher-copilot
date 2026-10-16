"""Durable local API attempt accounting. Unknown usage retains its reservation."""
import json
import uuid
from datetime import datetime
from .storage import atomic_json

DEFAULTS={'daily_requests':10,'daily_output_tokens':100000}


def limits(root):
    path=root/'ai_limits.json'
    return json.loads(path.read_text(encoding='utf-8')) if path.exists() else dict(DEFAULTS)


def set_limits(root, values):
    if not isinstance(values,dict) or set(values)!=set(DEFAULTS):
        raise ValueError('请填写每日请求次数和输出额度。')
    for key,low,high in [('daily_requests',1,100),('daily_output_tokens',1800,1000000)]:
        if type(values[key]) is not int or not low<=values[key]<=high:
            raise ValueError('每日次数应为 1–100，输出额度应为 1800–1000000。')
    atomic_json(root/'ai_limits.json',values)


def rows(root):
    today=datetime.now().strftime('%Y-%m-%d')
    entries=[]
    for path in (root/'.ai_requests').glob('*.json'):
        row=json.loads(path.read_text(encoding='utf-8'))
        if row.get('date')==today:
            entries.append(dict(row,request_id=path.stem))
    return entries


def summary(root):
    entries=rows(root); config=limits(root)
    reserved=sum(r.get('output_tokens') if isinstance(r.get('output_tokens'),int) else r.get('reserved_output',6000) for r in entries)
    return dict(date=datetime.now().strftime('%Y-%m-%d'),limit=config['daily_requests'],
        limits=config,attempts=len(entries),remaining=max(0,config['daily_requests']-len(entries)),
        completed=sum(r.get('status')=='completed' for r in entries),
        failed=sum(r.get('status')=='failed' for r in entries),
        input_tokens=sum(r.get('input_tokens') or 0 for r in entries),
        output_tokens=sum(r.get('output_tokens') or 0 for r in entries),
        reserved_output=reserved,unknown=sum(r.get('output_tokens') is None for r in entries),
        requests=[{k:r.get(k) for k in ('request_id','operation','status','model','input_tokens','output_tokens','error','at','run')} for r in entries[-30:]])


def request_path(root, request_id):
    try: key=str(uuid.UUID(request_id))
    except (ValueError,TypeError,AttributeError):
        raise ValueError('生成请求编号无效，请刷新页面。') from None
    return root/'.ai_requests'/(key+'.json')


def call(root, request_id, operation, model, reserve, callback, details=None):
    path=request_path(root,request_id)
    if path.exists():
        raise ValueError('该请求已经处理或尝试过；未重复调用 AI。请恢复结果或手动发起新请求。')
    info=summary(root)
    if info['remaining']<=0:
        raise ValueError(f'今天已达到 {info["limit"]} 次 AI 请求上限，请使用本地题库。')
    if info['reserved_output']+reserve>info['limits']['daily_output_tokens']:
        raise ValueError('本次请求可能超过每日输出额度。请减少题量、切换本地题库或调整用量限制。')
    row=dict(date=info['date'],at=datetime.now().isoformat(),status='attempted',operation=operation,
        model=model,reserved_output=reserve,details=details or {})
    atomic_json(path,row)
    def record_usage(usage):
        row.update(usage);atomic_json(path,row)
    try:
        result=callback(record_usage)
        row.update(status='completed',result=result)
        atomic_json(path,row)
        return result
    except Exception:
        row.update(status='failed',error='请求未完成。请查看页面提示；生成最多修正一次，未知用量仍预留额度。')
        atomic_json(path,row)
        raise
