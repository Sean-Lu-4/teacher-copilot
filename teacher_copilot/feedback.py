"""Small, file-backed feedback and teacher question intake queue."""
from datetime import datetime, timezone
import re
import secrets
from pathlib import Path

from .storage import atomic_json


def _root(root):
    path = Path(root).resolve() / 'teacher_feedback'
    (path / 'feedback').mkdir(parents=True, exist_ok=True)
    (path / 'submissions').mkdir(parents=True, exist_ok=True)
    return path


def _text(value, name, limit=2000, required=False):
    value = str(value or '').strip()
    if required and not value:
        raise ValueError(f'{name}不能为空。')
    if len(value) > limit:
        raise ValueError(f'{name}不能超过 {limit} 个字符。')
    return value


def save_feedback(root, payload):
    kind = payload.get('kind', 'experience')
    if kind not in {'experience', 'question', 'bug'}:
        raise ValueError('反馈类型无效。')
    rating = payload.get('rating')
    if rating not in (None, ''):
        rating = int(rating)
        if rating < 1 or rating > 5:
            raise ValueError('评分请选择 1 到 5。')
    item = {'id': 'FB-' + secrets.token_hex(5).upper(), 'kind': kind,
            'rating': rating, 'comment': _text(payload.get('comment'), '反馈内容', 2000, True),
            'email': _text(payload.get('email'), '联系邮箱', 254),
            'run': _text(payload.get('run'), '练习编号', 120),
            'question_id': _text(payload.get('question_id'), '题目编号', 120),
            'created_at': datetime.now(timezone.utc).isoformat()}
    atomic_json(_root(root) / 'feedback' / f"{item['id']}.json", item)
    return {'saved': True, 'id': item['id']}


def save_submission(root, payload):
    title = _text(payload.get('title'), '题目标题', 200, True)
    task = _text(payload.get('task'), '题干', 6000, True)
    answer = _text(payload.get('answer'), '参考答案', 6000, True)
    code = _text(payload.get('code'), 'Java 代码', 10000)
    topic = _text(payload.get('topic'), '课题', 200, True)
    item = {'id': 'SUB-' + secrets.token_hex(5).upper(), 'status': 'pending',
            'title': title, 'task': task, 'answer': answer, 'code': code,
            'topic': topic, 'difficulty': _text(payload.get('difficulty'), '难度', 40),
            'minutes': int(payload.get('minutes') or 5),
            'teacher': _text(payload.get('teacher'), '教师姓名', 100),
            'email': _text(payload.get('email'), '联系邮箱', 254),
            'created_at': datetime.now(timezone.utc).isoformat()}
    if item['minutes'] < 1 or item['minutes'] > 60:
        raise ValueError('预计用时应在 1 到 60 分钟之间。')
    atomic_json(_root(root) / 'submissions' / f"{item['id']}.json", item)
    return {'saved': True, 'id': item['id'], 'status': 'pending'}

