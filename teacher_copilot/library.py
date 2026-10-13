"""Local worksheet library and transparent structural checks."""
import json
import tempfile
from pathlib import Path
from datetime import datetime
from .storage import atomic_json
from .questions import save_questions


def metadata(directory):
    path = directory / 'library.json'
    return json.loads(path.read_text(encoding='utf-8')) if path.exists() else {}


def items(store):
    result = []
    for run in store.runs():
        state = store.state(run)
        meta = metadata(store.directory(run))
        default_title = state['settings'].get('topic', '练习') if state['settings'] else '练习'
        result.append(dict(run=run, title=meta.get('title') or default_title,
                           archived=meta.get('archived',False), count=len(state['records']),
                           minutes=state['summary']['minutes'], source=state['source'], version=state['version']))
    return result


def manage(store, state, payload):
    directory = store.directory(state['run'])
    meta = metadata(directory)
    action = payload['action']
    if action == 'rename':
        title = payload.get('title')
        if not isinstance(title,str) or not 1 <= len(title.strip()) <= 100:
            raise ValueError('练习名称应为 1 至 100 个字符。')
        meta['title'] = title.strip()
    elif action == 'archive':
        if type(payload.get('archived')) is not bool:
            raise ValueError('归档状态无效。')
        meta['archived'] = payload['archived']
    elif action == 'duplicate':
        plan = json.loads((directory/'exercise_plan.json').read_text(encoding='utf-8'))
        target = Path(tempfile.mkdtemp(prefix=datetime.now().strftime('%Y%m%d_%H%M%S_worksheet_'),dir=store.root))
        atomic_json(target/'exercise_plan.json',plan)
        save_questions(target/'questions.json',state['records'])
        atomic_json(target/'library.json',dict(title=meta.get('title','练习')+' · 副本',archived=False))
        return store.state(target.name)
    atomic_json(directory/'library.json',meta)
    return store.state(state['run'])


def check(state):
    warnings = list(state['summary']['warnings'])
    signatures = set()
    for index,record in enumerate(state['records'],1):
        q = record['content']
        signature = ''.join((q['code']+q['task']).split()).casefold()
        if signature in signatures:
            warnings.append(f'第 {index} 题与前面的题目重复。')
        signatures.add(signature)
        if not q.get('answer','').strip() or not q.get('rubric','').strip():
            warnings.append(f'第 {index} 题缺少答案或评分标准。')
        if q.get('question_kind') == 'write' and not q.get('reference_solution','').strip():
            warnings.append(f'第 {index} 题缺少参考实现。')
    return dict(warnings=list(dict.fromkeys(warnings)),
                scope='检查重复、答案字段、参考实现、时长、考查覆盖与总分。未验证 Java 执行结果、答案语义或是否超纲。')
