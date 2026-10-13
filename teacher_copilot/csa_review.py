"""Batch review data and local teacher feedback, separate from generated papers."""
import json
from pathlib import Path
from .csa_bank import QUESTIONS
from .csa_curriculum import LABELS, UNITS, SOURCE, VERSION
from .questions import content_hash
from .storage import atomic_json, fingerprint

DECISIONS = {'unreviewed','suitable','too_easy','too_hard','unclear','incorrect'}


def feedback_state(root):
    path = Path(root)/'csa_full_review/teacher_feedback.json'
    data = json.loads(path.read_text(encoding='utf-8')) if path.exists() else dict(version=VERSION, overall='', items={})
    return dict(data=data, revision=fingerprint(json.dumps(data, ensure_ascii=False, sort_keys=True)))


def save_feedback(root, payload):
    current = feedback_state(root)
    if payload.get('revision') != current['revision']:
        raise ValueError('反馈已在其他页面更新，请重新载入后再保存。')
    if payload.get('bank_version') != VERSION:
        raise ValueError('题库版本已变化，请重新载入。')
    overall, items = payload.get('overall'), payload.get('items')
    if not isinstance(overall,str) or len(overall)>20000 or not isinstance(items,dict):
        raise ValueError('反馈格式无效或内容过长。')
    bank={q['id']:q for q in QUESTIONS}
    for id, item in items.items():
        if id not in bank or not isinstance(item,dict):
            raise ValueError('未知题号。')
        if item.get('decision') not in DECISIONS or not isinstance(item.get('comment'),str) or len(item['comment'])>4000:
            raise ValueError('题目反馈格式无效。')
        if item.get('content_hash') != content_hash(bank[id]):
            raise ValueError('题目内容已更新，请重载后反馈。')
        if set(item) != {'decision','comment','content_hash'}:
            raise ValueError('题目反馈包含不支持的字段。')
    atomic_json(Path(root)/'csa_full_review/teacher_feedback.json', dict(version=VERSION, overall=overall, items=items))
    return feedback_state(root)


def review_data(root):
    verification = Path(root)/'csa_full_review/java_checks/verification.json'
    checks = {}
    if verification.exists():
        report=json.loads(verification.read_text(encoding='utf-8'))
        if report.get('version')==VERSION:
            checks={r['id']:r for r in report['results']}
    questions=[]
    for q in QUESTIONS:
        hash=content_hash(q)
        check=checks.get(q['id'],{})
        status=('java_passed' if check.get('passed') and check.get('content_hash')==hash else
                'conceptual' if q['question_kind']=='concept' else 'unverified')
        questions.append(dict(content=q, content_hash=hash, technical_status=status))
    return dict(version=VERSION, source=SOURCE, labels=LABELS, units=UNITS, questions=questions,
                feedback=feedback_state(root),
                scope='53 个 Topic 每个 3 道代表题；Topic 有题不等于每条知识要求全部覆盖。难度、预计用时和教学适用性待教师反馈。')
