"""Local teacher workspace; optional explicitly enabled AI generation."""
import argparse
import base64
from copy import deepcopy
from datetime import datetime
import hashlib
import hmac
from http.cookies import SimpleCookie
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import secrets
import tempfile
import threading
import webbrowser
from urllib.parse import urlparse

from .config import OUTPUT_FOLDER
from .questions import load_questions, save_questions, revise, review, set_locked
from .storage import atomic_json
from .worksheets import assemble, assemble_exam, summary, paper_report, catalog, bank_data, TOPICS, navigation_settings, replace_question, validate_settings, availability_preview, selection_objectives, partial_exam
from . import ai_questions

ASSETS = Path(__file__).parent / 'review_static'
LABELS = {'pending': '待审核', 'passed': '通过', 'failed': '需修改'}


class Conflict(ValueError):
    pass


def fence(text, language='text'):
    import re
    mark = '`' * max(3, 1 + max((len(m[0]) for m in re.finditer(r'`+', text)), default=0))
    return f'{mark}{language}\n{text}\n{mark}'


def reviewed_report(plan, records):
    """Render saved records, never substitute the fixed bank or stale validations."""
    lines = ['# Methods 教师审阅版', '', '本报告来自已保存的题目档案；未调用 AI。', '',
             f"课程：{plan.get('course', {}).get('topic', 'Methods')}", '',
             '## 课堂时间参考', '',
             '以下为原方案。修改单题时间后，需要教师重新核对活动及反馈时间。', '']
    for stage, minutes, detail in plan.get('schedule', []):
        lines += [f'- {stage}：{minutes} 分钟；{detail}']
    lines += ['', f"当前题目作答时间合计：{sum(r['content']['minutes'] for r in records)} 分钟（不含讲解与反馈）。", '',
              '## 学生题目', '']
    for record in records:
        c = record['content']
        lines += [f"### {c['id']} · {c['title']}", '',
                  f"层级 {c['level']} · {c['minutes']} 分钟 · {c['origin']}", '',
                  '目标：' + '、'.join(c['objectives']), '', fence(c['code'], 'java'), '', fence(c['task']), '']
        for key, value in c.get('options', {}).items():
            lines += [f'{key}.', '', fence(value), '']
    lines += ['## 教师答案与处理', '']
    for record in records:
        c = record['content']
        lines += [f"### {c['id']} · {c['title']}", '', c['answer'], '']
        if c.get('answer_key'):
            lines += [f"正确选项：{c['answer_key']}", '']
        lines += ['**推理步骤**', ''] + [f'{i}. {v}' for i, v in enumerate(c['reasoning'], 1)]
        if c.get('distractors'):
            lines += ['', '**干扰项解释**', ''] + [f'- {k}：{v}' for k, v in c['distractors'].items()]
        lines += ['', '**常见错误**', ''] + [f'- {v}' for v in c['errors']]
        lines += ['', '评分：' + c['rubric'], '', '教师处理：' + c['intervention'], '',
                  f"修订 {record['revision']} · {'已锁定' if record['locked'] else '可修改'}", '',
                  '审核：' + '；'.join(f'{name}：{LABELS[record["validation"][key]]}' for key, name in
                                   [('teacher_review', '教师审核'), ('technical_review', '技术审核'), ('difficulty_trial', '难度试测')]), '',
                  '来源类型：' + record['provenance']['kind'], '']
        for source in record['provenance']['sources']:
            lines += [f"- {source['file']} · PDF 第 {source['page']} 页"]
        if record['provenance'].get('changes'):
            lines += ['改编说明：' + record['provenance']['changes']]
    lines += ['', '## 教材候选与范围', '', '候选页码不等于已确认覆盖；本报告不自动确认 Java 正确性或考试难度。', '']
    for item in plan.get('textbook_evidence', []):
        sources = '；'.join(f"{s['file']} PDF 第{s['page']}页" for s in item['sources']) or '无候选'
        lines += [f"- {item['title']}：{item['status']}；{sources}"]
    return '\n'.join(lines) + '\n'


class ReviewStore:
    def __init__(self, root):
        self.root = Path(root).resolve()
        self.lock = threading.Lock()

    def runs(self):
        if not self.root.exists():
            return []
        return sorted([p.name for p in self.root.iterdir() if p.is_dir()
                       and (p / 'questions.json').is_file() and (p / 'exercise_plan.json').is_file()], reverse=True)

    def directory(self, run):
        if not isinstance(run, str) or run not in self.runs():
            raise ValueError('请选择已有的练习报告。')
        path = (self.root / run).resolve()
        if path.parent != self.root:
            raise ValueError('报告目录无效。')
        return path

    def state(self, run):
        directory = self.directory(run)
        path = directory / 'questions_review.json'
        if not path.exists():
            path = directory / 'questions.json'
        records = load_questions(path)
        version = hashlib.sha256(path.read_bytes()).hexdigest()
        plan = json.loads((directory / 'exercise_plan.json').read_text(encoding='utf-8'))
        settings = plan.get('worksheet_settings')
        source=plan.get('generation',{}).get('source','local')
        info=summary(settings,records)
        if source not in {'local','mock'}:
            info['warnings'].append('AI 模拟体验：使用本地题库，未调用 AI。' if source=='mock' else 'AI 生成题目待教师审核；已检查结构、标签、重复和时长，未自动验证答案正确性或运行 Java。')
            if 'homework' in info:
                info['homework'].update(source=source,api_enabled=source in {'ai','hybrid'})
        return dict(run=run, records=records, version=version, settings=settings,
                    source=source,generation=plan.get('generation',{}),
                    navigation_settings=navigation_settings(settings), summary=info,
                    generation_notice=plan.get('generation_notice', ''))

    def recent_usage(self, current=None):
        """Five newest worksheets, including removed questions; exports do not count."""
        runs = sorted(self.runs(), key=lambda run: (self.directory(run) / 'questions.json').stat().st_mtime_ns, reverse=True)[:5]
        weights = {}
        for age, run in enumerate(runs):
            state = self.state(run)
            ids = {r['content']['id'] for r in state['records']}
            for record in state['records']:
                ids.update(e['detail']['previous_content']['id'] for e in record['history'] if e.get('action') == 'replace')
            for question_id in ids:
                weights[question_id] = weights.get(question_id, 0) + (5 - age)
        if current:
            for record in self.state(current)['records']:
                question_id = record['content']['id']
                weights[question_id] = weights.get(question_id, 0) + 1000
        return weights

    def ai_records(self, settings, mode, current=None, **kwargs):
        settings=validate_settings(settings)
        runs=self.runs()
        runs=sorted(runs,key=lambda r:(self.directory(r)/'questions.json').stat().st_mtime_ns,reverse=True)[:5]
        if current and current not in runs:runs.insert(0,current)
        excluded=[]
        for run in runs:
            for record in self.state(run)['records']:
                excluded.append(record['content'])
                excluded.extend(e['detail']['previous_content'] for e in record['history'] if e.get('action')=='replace')
        excluded=kwargs.pop('extra_excluded', [])+excluded
        request_id=kwargs.pop('request_id',None)
        from . import ai_usage
        def generate(record_usage):
            return ai_questions.generate(settings,mode,excluded=excluded[:100],
                recent=self.recent_usage(current),usage_callback=record_usage,**kwargs)
        if mode!='ai':return generate(None)
        if not ai_questions.availability()['ready']:
            raise ValueError('实时生成未启用，请使用本地题库。')
        return ai_usage.call(self.root,request_id,'replace' if kwargs.get('replacement') else 'generate',
            ai_questions.availability()['model'],ai_questions.request_output_limit(settings,kwargs.get('replacement')),
            generate,dict(settings=settings,run=current))

    def ai_usage(self):
        from .ai_usage import summary
        return summary(self.root)

    def mutate(self, payload):
        with self.lock:
            if payload.get('action')=='availability':
                return availability_preview(payload.get('settings') or {})
            if payload.get('action')=='ai-limits':
                from .ai_usage import set_limits
                set_limits(self.root,payload.get('limits'))
                return self.ai_usage()
            if payload.get('action')=='recover':
                from .ai_usage import request_path
                path=request_path(self.root,payload.get('recover_id'))
                if not path.exists():raise ValueError('找不到该请求。')
                entry=json.loads(path.read_text(encoding='utf-8'))
                if entry.get('operation')!='generate' or entry.get('status')!='completed':
                    raise ValueError('该请求没有完整生成结果。可恢复设置后手动重试。')
                if entry.get('run') in self.runs():return self.state(entry['run'])
                records,generation=entry['result']
                settings=entry['details']['settings']
                directory=Path(tempfile.mkdtemp(prefix=datetime.now().strftime('%Y%m%d_%H%M%S_worksheet_'),dir=self.root))
                atomic_json(directory/'exercise_plan.json',dict(worksheet_settings=settings,course=dict(topic=TOPICS.get(settings['topic'],'跨课题综合练习')),
                    generation=generation,questions=[r['content'] for r in records]))
                save_questions(directory/'questions.json',records)
                entry['run']=directory.name;atomic_json(path,entry)
                return self.state(directory.name)
            if payload.get('action') == 'bank-feedback':
                from .csa_review import save_feedback
                return save_feedback(self.root, payload)
            if payload.get('action') == 'teacher-feedback':
                from .feedback import save_feedback
                base_root = self.root.parent.parent if self.root.parent.name == 'sessions' else self.root
                return save_feedback(base_root, payload)
            if payload.get('action') == 'submit-question':
                from .feedback import save_submission
                base_root = self.root.parent.parent if self.root.parent.name == 'sessions' else self.root
                return save_submission(base_root, payload)
            if payload.get('action') == 'generate':
                mode=payload.get('source','local')
                if mode not in {'local','mock','ai','hybrid'}:raise ValueError('请选择有效的题目来源。')
                recent = self.recent_usage(payload.get('run'))
                requested=payload.get('settings') or {}
                settings=validate_settings(requested)
                builder=assemble_exam if settings.get('purpose')=='exam' else assemble
                if mode=='local':
                    settings,records=builder(settings,recent)
                    generation=dict(source='local')
                elif mode=='hybrid':
                    if settings.get('selected_ids'):
                        raise ValueError('自选清单请使用题库组卷；补题请先取消自选限制。')
                    try:
                        _,records=builder(settings,recent)
                    except ValueError:
                        records=[]
                        if settings.get('purpose')=='exam':
                            records=partial_exam(settings,recent)
                    used=sum(r['content']['minutes'] for r in records)
                    exam=settings.get('purpose')=='exam'
                    # A fixed-size paper with all requested questions needs no extra question.
                    needs_more=(len(records)<settings['question_count']) if exam else used<settings['minutes']
                    if needs_more:
                        if exam:
                            # Reserve at least one minute for each missing question.
                            while records and settings['minutes']-used < settings['question_count']-len(records):
                                used-=records.pop()['content']['minutes']
                        covered=set().union(*(selection_objectives(r['content'],settings['topic']) for r in records))
                        kwargs={}
                        if exam:
                            allocated=0
                            for r in records:
                                marks=max(1,round(settings['total_marks']*r['content']['minutes']/settings['minutes']))
                                marks=min(marks,settings['total_marks']-allocated-(settings['question_count']-len(records))-(len(records)-records.index(r)-1))
                                allocated+=marks
                                r['content']['marks']=marks
                                from .questions import content_hash
                                r['content']['rubric']+=f'\n本卷本题按 {marks} 分计：按原评分标准得分比例折算。'
                                r['content_hash']=content_hash(r['content'])
                            kwargs=dict(supplement_count=settings['question_count']-len(records),
                                        supplement_marks=settings['total_marks']-allocated)
                        try:
                            if not ai_questions.availability()['free_ready']:
                                raise ValueError('免费补题尚未启用，请先配置 OpenRouter 免费模型。')
                            extra,generation=self.ai_records(settings,'ai',payload.get('run'),
                                supplement_minutes=settings['minutes']-used,covered_objectives=covered,
                                extra_excluded=[r['content'] for r in records],request_id=payload.get('request_id'),**kwargs)
                            records+=extra
                            generation['source']='hybrid'
                            generation['notice']=f'保留题库题目，补充 {len(extra)} 道题。'
                            if generation.get('remaining_minutes'):
                                generation['notice']+=f"仍缺约 {generation['remaining_minutes']} 分钟，已保留通过检查的题目，可稍后继续补充。"
                        except ValueError as exc:
                            if not records: raise
                            generation=dict(source='local',notice='补题未完成，已保留题库练习。'+str(exc))
                    else:
                        generation=dict(source='local',notice='题库已满足题量要求，未调用 AI。')
                else:
                    records,generation=self.ai_records(settings,mode,payload.get('run'),request_id=payload.get('request_id'))
                reused = sum(r['content']['id'] in recent for r in records)
                notice = (f'本次有 {reused} 道题在近期作业中使用过；满足当前内容、难度和时长的题量有限，已优先选择较少使用的题目。'
                          if reused else '本次题目未出现在最近 5 份作业和当前预览中。')
                if mode=='ai':notice='AI 已生成并保存；结构检查通过，内容与难度待教师确认。'
                elif mode=='mock':notice='模拟流程使用本地题库，未调用 AI；'+notice
                elif mode=='hybrid':notice=generation.get('notice','题库已满足设定时长，未调用 AI。')
                self.root.mkdir(parents=True, exist_ok=True)
                directory = Path(tempfile.mkdtemp(prefix=datetime.now().strftime('%Y%m%d_%H%M%S_worksheet_'), dir=self.root))
                atomic_json(directory / 'exercise_plan.json', dict(course=dict(topic=TOPICS.get(settings['topic'],'跨课题综合练习'), duration=settings['minutes']),
                            worksheet_settings=settings, schedule=[], textbook_evidence=[], mode='local_worksheet',
                            questions=[r['content'] for r in records], generation_notice=notice,generation=generation))
                save_questions(directory / 'questions.json', records)
                if mode in {'ai','hybrid'} and generation.get('source') in {'ai','hybrid'}:
                    from .ai_usage import request_path
                    path=request_path(self.root,payload.get('request_id'))
                    entry=json.loads(path.read_text(encoding='utf-8'));entry['run']=directory.name;entry['result']=[records,generation]
                    atomic_json(path,entry)
                return self.state(directory.name)
            state = self.state(payload.get('run'))
            if payload.get('version') != state['version']:
                raise Conflict('内容已在其他页面更新。请重新载入后再操作。')
            action = payload.get('action')
            directory = self.directory(state['run'])
            if action in {'rename','archive','duplicate'}:
                from .library import manage
                return manage(self,state,payload)
            if action == 'quality-check':
                from .library import check
                return check(state)
            if action == 'export':
                plan = json.loads((directory / 'exercise_plan.json').read_text(encoding='utf-8'))
                audience = payload.get('audience')
                if audience is not None and audience not in {'student', 'teacher'}:
                    raise ValueError('请选择学生版或教师版。')
                export_format = payload.get('format', 'md')
                if export_format not in {'md', 'docx'}:
                    raise ValueError('不支持的导出格式。')
                extra = {}
                if export_format == 'docx':
                    from .docx_export import build_docx, MIME
                    binary = build_docx(plan, state['records'], audience, language=payload.get('language','bilingual'))
                    extra = dict(download=base64.b64encode(binary).decode('ascii'), mime=MIME,
                                 filename=f'AP-CSA-{audience}.docx')
                folder = Path(tempfile.mkdtemp(prefix='reviewed_' + datetime.now().strftime('%Y%m%d_%H%M%S_'), dir=directory))
                text = paper_report(plan, state['records'], audience) if audience else reviewed_report(plan, state['records'])
                (folder / 'report.md').write_text(text, encoding='utf-8')
                if export_format == 'docx':
                    (folder / extra['filename']).write_bytes(binary)
                save_questions(folder / 'questions.json', state['records'])
                snapshot = deepcopy(plan)
                snapshot['questions'] = [r['content'] for r in state['records']]
                snapshot['mode'] = 'teacher_reviewed_snapshot'
                snapshot['validation'] = '参见 questions.json 中逐题审核状态；修改后的题目未自动复核。'
                snapshot['note'] = '教师保存的题目快照；课堂安排仍为原参考方案。'
                atomic_json(folder / 'exercise_plan.json', snapshot)
                return dict(**state, report=text, export_path=str(folder), **extra)
            records = state['records']
            index = next((i for i, r in enumerate(records) if r['content']['id'] == payload.get('id')), None)
            if index is None:
                raise ValueError('找不到该题目。')
            record = records[index]
            actor = payload.get('actor', '')
            if action == 'replace':
                if record['locked']:raise ValueError('这道题已锁定，请先解锁再换题。')
                if state['source'] in {'local','hybrid'}:
                    replacement = replace_question(state['settings'], records, index, self.recent_usage())
                else:
                    replacement_rows,usage=self.ai_records(state['settings'],state['source'],state['run'],
                        replacement=record['content'],records=records,index=index,request_id=payload.get('request_id'))
                    replacement=replacement_rows[0]
                    replacement['generation_usage']=usage
                replacement['history'] = deepcopy(record['history']) + [dict(action='replace',
                    actor='本地教师', at=datetime.now().isoformat(), revision=1,
                    detail=dict(previous_content=deepcopy(record['content']),
                                previous_validation=deepcopy(record['validation'])))]
                if state['settings'].get('purpose')=='exam' and record['content'].get('marks'):
                    replacement['content']['marks']=record['content']['marks']
                    raw_marks=replacement['content'].get('reference_marks')
                    if raw_marks and raw_marks!=record['content']['marks']:
                        replacement['content']['rubric']+=f"\n本卷分值换算 / Paper scaling: 得分 = 原始评分点得分 × {record['content']['marks']}/{raw_marks}。"
                    from .questions import content_hash
                    replacement['content_hash']=content_hash(replacement['content'])
                records[index] = replacement
                records.sort(key=lambda r: r['content']['level'])
            elif action == 'revise':
                changes = payload.get('changes')
                if not isinstance(changes, dict) or set(changes) - ((set(record['content']) | {'explanation_en'}) - {'id', 'origin'}):
                    raise ValueError('修改包含不支持的字段。')
                actual = {k: v for k, v in changes.items() if record['content'].get(k) != v}
                if not actual:
                    return state
                records[index] = revise(record, actual, actor, payload.get('reason', ''))
            elif action == 'translate':
                if record['locked']:
                    raise ValueError('这道题已锁定，请先解锁再生成英文解析。')
                from .ai_questions import translate_explanation
                from . import ai_usage
                if not ai_questions.availability()['ready']:raise ValueError('实时生成未启用。')
                english = ai_usage.call(self.root,payload.get('request_id'),'translate',ai_questions.availability()['model'],1800,
                    lambda usage: translate_explanation(record['content'],usage_callback=usage),dict(run=state['run'],id=record['content']['id']))
                records[index] = revise(record, {'explanation_en': english}, actor or '本地教师', '生成英文双语解析')
            elif action == 'review':
                records[index] = review(record, payload.get('check'), payload.get('status'), actor, payload.get('evidence', ''))
            elif action == 'lock':
                records[index] = set_locked(record, payload.get('locked'), actor)
            else:
                raise ValueError('不支持的操作。')
            save_questions(directory / 'questions_review.json', records)
            return self.state(state['run'])


def create_server(root=OUTPUT_FOLDER, port=8765, host=None, allowed_hosts=None, allowed_origins=None):
    store = ReviewStore(root)
    # Rehydrate approved teacher submissions after a restart so they remain in the bank.
    try:
        from .feedback import list_items
        from .worksheets import register_approved_question
        for submission in list_items(root).get('submissions', []):
            if submission.get('status') == 'approved':
                register_approved_question(submission)
    except (OSError, ValueError, TypeError):
        pass
    token = secrets.token_urlsafe(32)
    host = host or os.getenv('TEACHER_COPILOT_HOST', '127.0.0.1')
    if allowed_hosts is None:
        raw_hosts = os.getenv('TEACHER_COPILOT_ALLOWED_HOSTS', '')
        allowed_hosts = {item.strip() for item in raw_hosts.split(',') if item.strip()}
    if allowed_origins is None:
        raw_origins = os.getenv('TEACHER_COPILOT_ALLOWED_ORIGINS', '')
        allowed_origins = {item.strip().rstrip('/') for item in raw_origins.split(',') if item.strip()}
    # Keep the default localhost-only behavior. Public deployments must state
    # their host and browser origin explicitly instead of accepting arbitrary
    # Host/Origin headers.
    if host not in {'127.0.0.1', 'localhost', '::1'} and (not allowed_hosts or not allowed_origins):
        raise ValueError('公网部署必须设置允许的域名和来源：TEACHER_COPILOT_ALLOWED_HOSTS、TEACHER_COPILOT_ALLOWED_ORIGINS。')
    demo = os.getenv('TEACHER_COPILOT_PUBLIC_DEMO') == '1'
    if demo and ai_questions.availability()['ready'] and not ai_questions.availability()['free_ready']:
        raise ValueError('Public demo only supports configured free AI models.')
    session_secret = secrets.token_bytes(32)
    stores = {}
    stores_lock = threading.Lock()
    explicit_hosts = bool(allowed_hosts)
    explicit_origins = bool(allowed_origins)

    class Handler(BaseHTTPRequestHandler):
        def workspace(self):
            if not demo:
                return store
            if hasattr(self, '_workspace'):
                return self._workspace
            cookies = SimpleCookie()
            try:
                cookies.load(self.headers.get('Cookie', ''))
                value = cookies['tc_session'].value if 'tc_session' in cookies else ''
            except Exception:
                value = ''
            sid, _, signature = value.partition('.')
            valid = len(sid) == 64 and all(c in '0123456789abcdef' for c in sid)
            expected = hmac.new(session_secret, sid.encode(), hashlib.sha256).hexdigest()
            if not valid or not hmac.compare_digest(signature, expected):
                sid = secrets.token_hex(32)
                signature = hmac.new(session_secret, sid.encode(), hashlib.sha256).hexdigest()
                self._new_cookie = f'tc_session={sid}.{signature}; Path=/; HttpOnly; Secure; SameSite=Lax'
            with stores_lock:
                if sid not in stores:
                    stores[sid] = ReviewStore(Path(root) / 'sessions' / sid)
                self._workspace = stores[sid]
            return self._workspace

        def log_message(self, *_):
            pass

        def send(self, data, status=200, mime='application/json; charset=utf-8'):
            if not isinstance(data, bytes):
                data = json.dumps(data, ensure_ascii=False).encode('utf-8')
            self.send_response(status)
            self.send_header('Content-Type', mime)
            if getattr(self, '_new_cookie', None):
                self.send_header('Set-Cookie', self._new_cookie)
            self.send_header('Content-Length', str(len(data)))
            self.send_header('Cache-Control', 'no-store')
            self.send_header('X-Content-Type-Options', 'nosniff')
            self.send_header('Content-Security-Policy', "default-src 'self'; script-src 'self'; style-src 'self'; connect-src 'self'; frame-ancestors 'none'; base-uri 'none'")
            self.end_headers()
            self.wfile.write(data)

        def local_request(self):
            host_header = self.headers.get('Host', '').rstrip('/')
            origin = self.headers.get('Origin')
            host_ok = (host_header in allowed_hosts if explicit_hosts else
                       host_header in {f'127.0.0.1:{self.server.server_port}',
                                       f'localhost:{self.server.server_port}',
                                       f'[::1]:{self.server.server_port}'})
            if explicit_origins:
                origin_ok = not origin or origin.rstrip('/') in allowed_origins
            else:
                origin_ok = not origin or origin.rstrip('/') in {
                    f'http://127.0.0.1:{self.server.server_port}',
                    f'http://localhost:{self.server.server_port}'}
            return host_ok and origin_ok

        def admin_key_ok(self):
            configured = os.getenv('TEACHER_COPILOT_ADMIN_KEY', '').strip()
            supplied = self.headers.get('X-Admin-Key', '').strip()
            return bool(configured) and hmac.compare_digest(supplied, configured)

        def admin_root(self):
            return self.workspace().root.parent.parent if self.workspace().root.parent.name == 'sessions' else self.workspace().root

        def do_GET(self):
            if self.path == '/healthz':
                return self.send({'ok': True})
            if not self.local_request():
                return self.send({'error': '仅支持本机页面访问。'}, 403)
            from urllib.parse import parse_qs
            parsed = urlparse(self.path)
            try:
                if parsed.path == '/api/state':
                    run = parse_qs(parsed.query).get('run', [None])[0]
                    runs = self.workspace().runs()
                    with self.workspace().lock:
                        state = self.workspace().state(run or runs[0]) if runs else None
                    return self.send(dict(runs=runs, state=state, token=token, catalog=catalog(include_mixed=True),ai=ai_questions.availability(),usage=self.workspace().ai_usage()))
                if parsed.path == '/api/curriculum':
                    from .csa_review import review_data
                    with self.workspace().lock:
                        data=review_data(self.workspace().root)
                    return self.send(dict(**data, token=token))
                if parsed.path == '/api/source-bank':
                    path = ASSETS.parent / 'imported_bank' / 'bank.json'
                    if not path.exists(): return self.send({'error':'资料题库尚未导入。'},404)
                    return self.send(path.read_bytes())
                if parsed.path.startswith('/source-image/'):
                    import re
                    filename=parsed.path.removeprefix('/source-image/')
                    if not re.fullmatch(r'FRQ-[a-f0-9]{16}-S[0-9]+-p[0-9]+\.png',filename): return self.send({'error':'无效的文件。'},404)
                    path=ASSETS.parent / 'imported_bank' / 'images' / filename
                    if not path.is_file(): return self.send({'error':'文件不存在。'},404)
                    return self.send(path.read_bytes(),mime='image/png')
                if parsed.path.startswith('/source-pdf/'):
                    import re
                    filename=parsed.path.removeprefix('/source-pdf/')
                    if not re.fullmatch(r'[a-f0-9]{64}\.pdf',filename): return self.send({'error':'无效的文件。'},404)
                    path=ASSETS.parent / 'imported_bank' / 'pdfs' / filename
                    if not path.is_file(): return self.send({'error':'文件不存在。'},404)
                    return self.send(path.read_bytes(),mime='application/pdf')
                if parsed.path == '/api/bank':
                    return self.send(bank_data())
                if parsed.path == '/api/admin/intake':
                    if not self.admin_key_ok(): return self.send({'error':'需要管理员密钥。'}, 401)
                    from .feedback import list_items
                    return self.send(list_items(self.admin_root()))
                if parsed.path == '/api/library':
                    from .library import items
                    with self.workspace().lock:
                        return self.send(dict(items=items(self.workspace()),token=token))
                if parsed.path in {'/gap-review', '/gap-review.css'}:
                    filename, mime = ('report.html', 'text/html') if parsed.path == '/gap-review' else ('report.css', 'text/css')
                    report_path = self.workspace().root / 'gap_review' / filename
                    if not report_path.is_file():
                        return self.send({'error': '尚未生成题库缺口报告。'}, 404)
                    return self.send(report_path.read_bytes(), mime=mime+'; charset=utf-8')
                names = {'/': ('index.html' if parse_qs(parsed.query).get('run') or parse_qs(parsed.query).get('picked') else 'home.html', 'text/html'), '/teacher': ('index.html','text/html'), '/practice': ('practice.html','text/html'), '/practice.js': ('practice.js','text/javascript'), '/learn.css': ('learn.css','text/css'), '/app.js': ('app.js', 'text/javascript'), '/style.css': ('style.css', 'text/css'),
                         '/bank-audit': ('bank-audit.html', 'text/html'),
                         '/bank-audit.css': ('bank-audit.css', 'text/css'),
                         '/bank': ('bank.html', 'text/html'), '/bank.js': ('bank.js', 'text/javascript')}
                names.update({'/curriculum': ('curriculum.html','text/html'),
                              '/curriculum.js': ('curriculum.js','text/javascript')})
                names.update({'/library':('library.html','text/html'), '/library.js':('library.js','text/javascript'),
                              '/source-bank':('source-bank.html','text/html'), '/source-bank.js':('source-bank.js','text/javascript'),
                              '/admin':('admin.html','text/html'), '/admin.js':('admin.js','text/javascript')})
                if parsed.path not in names:
                    return self.send({'error': '页面不存在。'}, 404)
                name, mime = names[parsed.path]
                content = (ASSETS / name).read_bytes()
                if demo and name in {'index.html','library.html'}:
                    notice = '<p class="public-notice" role="status">完成组卷后请下载保存，试用期间在线练习记录可能被清理。</p>'
                    content = content.replace(b'<main>', ('<main>' + notice).encode())
                    content = content.replace('本地题库 / AI 按需生成'.encode(), '公开试用版 · 教师工作台'.encode())
                    content = content.replace('本地题库 · 可筛选组卷'.encode(), '公开试用版 · 可筛选组卷'.encode())
                    content = content.replace('查看全课程题目审核页 →'.encode(), '查看课程范围与题库说明 →'.encode())
                    content = content.replace('有额度时可为旧题生成英文解析。'.encode(), '教师答案支持中英双语导出。'.encode())
                self.send(content, mime=mime + '; charset=utf-8')
            except (ValueError, OSError) as exc:
                self.send({'error': str(exc)}, 400)

        def do_POST(self):
            if not self.local_request():
                return self.send({'error': '请从允许的页面提交。'}, 403)
            if self.path == '/api/admin/action':
                if not self.admin_key_ok(): return self.send({'error':'需要管理员密钥。'}, 401)
                try:
                    size=int(self.headers.get('Content-Length','0'))
                    payload=json.loads(self.rfile.read(size))
                    from .feedback import update_feedback, update_submission, list_items
                    root=self.admin_root(); action=payload.get('action'); item_id=payload.get('id')
                    if action=='update-feedback': result=update_feedback(root,item_id,payload.get('status','reviewed'),payload.get('note',''),payload.get('actor','管理员'))
                    elif action=='update-submission':
                        result=update_submission(root,item_id,payload.get('status','rejected'),payload.get('note',''),payload.get('actor','管理员'))
                        if result['item']['status']=='approved':
                            from .worksheets import register_approved_question
                            result['question_id']=register_approved_question(result['item'])
                    else: raise ValueError('不支持的管理操作。')
                    result['items']=list_items(root); self.send(result)
                except (ValueError,TypeError,KeyError,OSError) as exc: self.send({'error':str(exc)},400)
                return
            if self.headers.get('X-Review-Token') != token:
                return self.send({'error': '请从练习页面提交。'}, 403)
            if self.path != '/api/action':
                return self.send({'error': '页面不存在。'}, 404)
            try:
                size = int(self.headers.get('Content-Length', '0'))
                if not 0 < size <= 1_000_000:
                    raise ValueError('提交内容过大或为空。')
                payload = json.loads(self.rfile.read(size))
                if not isinstance(payload, dict):
                    raise ValueError('提交格式无效。')
                self.send(self.workspace().mutate(payload))
            except Conflict as exc:
                self.send({'error': str(exc)}, 409)
            except (ValueError, TypeError, KeyError, OSError) as exc:
                self.send({'error': str(exc)}, 400)

    return ThreadingHTTPServer((host, port), Handler)


def main():
    parser = argparse.ArgumentParser(description='Teacher Copilot teacher workspace')
    parser.add_argument('--port', type=int, default=8765)
    parser.add_argument('--host', default=None, help='监听地址；公网部署使用 0.0.0.0')
    parser.add_argument('--allowed-hosts', default=None, help='允许的 Host，多个值用逗号分隔')
    parser.add_argument('--allowed-origins', default=None, help='允许的浏览器来源，多个值用逗号分隔')
    parser.add_argument('--outputs', type=Path, default=OUTPUT_FOLDER)
    parser.add_argument('--no-browser', action='store_true')
    args = parser.parse_args()
    split = lambda value: {item.strip() for item in value.split(',') if item.strip()} if value else None
    server = create_server(args.outputs, args.port, args.host, split(args.allowed_hosts), split(args.allowed_origins))
    display_host = args.host or os.getenv('TEACHER_COPILOT_HOST', '127.0.0.1')
    url = f'http://{display_host}:{server.server_port}'
    print(f'Teacher Copilot review: {url}\nPress Ctrl+C to stop.', flush=True)
    if not args.no_browser:
        webbrowser.open(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == '__main__':
    main()
