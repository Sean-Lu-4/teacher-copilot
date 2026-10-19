"""Reviewed behavioral checks. These are practice checks, not official AP scores."""
import hashlib
import base64
import json
import re
import secrets
import threading
import time
from pathlib import Path
from . import java_runner
from . import bead_grading

PROFILES = json.loads(Path(__file__).with_name('java_profiles.json').read_text(encoding='utf8'))
PROFILES.update(json.loads(Path(__file__).with_name('java_profiles_extended.json').read_text(encoding='utf8')))
PROFILES[bead_grading.QUESTION_ID] = bead_grading.PROFILE
PROFILES['AP-FRQ764c3eaaeb638f9fS13']['note'] = '运行检查覆盖编程小问；(c) 的文字设计说明请对照参考评分建议复核。'
_lock = threading.Lock()
_slots = threading.BoundedSemaphore(2)
_cache = {}
_daily = {'day': '', 'count': 0}

SUPPORT = '''
record ItemInfo(double cost,boolean available){public double getCost(){return cost;}public boolean isAvailable(){return available;}}
record Player(String id,int score){public String getID(){return id;}public int getScore(){return score;}}
record ElectricVehicle(String model,int range){public String getModelName(){return model;}public int getRange(){return range;}}
record Candy(String flavor){public String getFlavor(){return flavor;}}
record TriviaQuestion(int difficulty){public int getDifficultyLevel(){return difficulty;}}
record Location(int row,int col){public int getRow(){return row;}public int getCol(){return col;}}
record Plot(String crop,int yield){public String getCropType(){return crop;}public int getCropYield(){return yield;}}
'''


def build_source(profile, code, marker):
    if profile.get('kind') in {'snippet', 'email'}:
        from .java_snippets import build
        return build(profile, code, marker)
    if profile.get('kind') == 'fragment':
        return bead_grading.build(code, marker)
    # The editor accepts method/constructor implementations, not a replacement test harness.
    from tree_sitter import Language, Parser
    import tree_sitter_java
    whole_class = profile.get('kind') == 'class'
    tree = Parser(Language(tree_sitter_java.language())).parse((code if whole_class else 'class Submission {\n' + code + '\n}').encode())
    if tree.root_node.has_error:
        raise ValueError('请填写完整的类声明，并修正提示的语法问题。' if whole_class else '请只填写题目要求的方法或构造器，无需填写外层 class、字段或 main。')
    declarations = [n for n in tree.root_node.named_children if n.type not in {'line_comment','block_comment'}]
    if len(declarations) != 1 or declarations[0].type != 'class_declaration':
        raise ValueError('请只填写题目要求的方法或构造器。')
    body = declarations[0].child_by_field_name('body')
    if whole_class:
        name = declarations[0].child_by_field_name('name').text.decode()
        if name != profile['class_name']:
            raise ValueError('请填写完整的 ' + profile['class_name'] + ' 类。')
        # Nest the student's complete class without adding/removing any lines.
        # Do not permit sibling classes/imports to replace the trusted harness.
        start = declarations[0].start_byte
        encoded = code.encode()
        code = (encoded[:start] + b'static ' + encoded[start:]).decode()
    allowed = {'method_declaration', 'constructor_declaration', 'line_comment', 'block_comment'}
    if whole_class:
        allowed.add('field_declaration')
    if not body or not body.named_children or any(n.type not in allowed for n in body.named_children):
        raise ValueError('这里只需填写方法或构造器；题目给定的字段和辅助类由系统提供。')
    prefix = 'import java.util.*;\npublic class Main {\n' + SUPPORT + '\n' + profile.get('support','') + '\n'
    if not whole_class:
        prefix += 'static class ' + profile['class_name'] + ' {\n' + profile['fields'] + '\n'
    source = prefix + code + ('\n' if whole_class else '\n}\n') + 'public static void main(String[] args) {\n'
    for index, case in enumerate(profile['cases']):
        source += ('try { ' + case['setup'] + '\nboolean passed = (' + case['condition'] + ');'
                   + 'System.out.println("' + marker + ':' + str(index) + ':" + (passed ? "PASS" : "FAIL"));'
                   + '} catch (Throwable e) { System.out.println("' + marker + ':' + str(index) + ':ERROR:" + e.getClass().getSimpleName()); }\n')
    return source + '}}\n', prefix.count('\n')


def _interpret(profile, code, raw, marker, offset):
    status = raw['status']['id']
    if status == 6:
        diagnostics = []
        for match in re.finditer(r'Main\.java:(\d+):\s*(?:error:\s*)?([^\n]+)', raw['compile_output']):
            line = int(match.group(1)) - offset
            if 1 <= line <= len(code.splitlines()):
                diagnostics.append(dict(line=line, message=match.group(2)))
        return dict(status='compile_error', diagnostics=diagnostics[:10],
                    detail=raw['compile_output'][:4000], cases=[], practice_score=None,
                    message='编译没有通过。先修改标出的代码；本次不判零分。')
    if status != 3:
        return dict(status='timeout' if status == 5 else 'runtime_error', diagnostics=[],
                    detail=raw.get('stderr', '')[:2000], cases=[], practice_score=None,
                    message='运行超时，请检查循环是否能结束。' if status == 5 else '程序运行中断，暂时不能完成判分。')
    # Require one and only one well-formed result per case. Truncation is not success.
    cases = []
    for index, case in enumerate(profile['cases']):
        matches = re.findall(r'^' + re.escape(marker) + ':' + str(index) + r':(PASS|FAIL|ERROR:[A-Za-z0-9_$]+)$', raw['stdout'], re.M)
        if len(matches) != 1:
            raise java_runner.RunnerUnavailable('测试结果不完整，暂时不能判分。')
        result = matches[0]
        details = re.findall(r'^' + re.escape(marker) + ':' + str(index) + r':INFO:([A-Za-z0-9+/=]+)$', raw['stdout'], re.M)
        detail = ''
        if len(details) == 1:
            try: detail = base64.b64decode(details[0],validate=True).decode('utf-8')[:1000]
            except (ValueError,UnicodeError): pass
        cases.append(dict(label=case['label'], status='passed' if result == 'PASS' else 'failed',
                          detail=detail,reason='符合此项测试要求。' if result == 'PASS' else ('运行异常：' + result[6:] if result.startswith('ERROR:') else '运行结果与此项要求不符。')))
    earned = sum(case['status'] == 'passed' for case in cases)
    result = dict(status='passed' if earned == len(cases) else 'failed', diagnostics=[], cases=cases,
                practice_score=dict(earned=earned, possible=len(cases)),
                message='已通过当前功能测试。' if earned == len(cases) else '下面这些功能还需要修改。')
    if profile.get('kind') == 'fragment':
        result['score_evidence'] = bead_grading.evidence(code, cases)
    return result


def grade(question_id, code, part=None):
    profile = PROFILES.get(question_id)
    if profile is None:
        return dict(status='unsupported', message='这道题尚未配置运行测试，请对照评分指南检查。', cases=[], practice_score=None)
    if profile.get('kind') == 'parts':
        if not isinstance(part, int) or isinstance(part, bool) or not 0 <= part < len(profile['parts']):
            raise ValueError('请先选择要检查的小问。')
        profile = dict(profile['parts'][part])
        profile['cases'] = [dict(label=e['label']) for e in profile['examples']]
    if not java_runner.configured():
        return dict(status='unavailable', message='Java 运行服务尚未启用。', cases=[], practice_score=None)
    fingerprint = hashlib.sha256((question_id + '\0' + str(part) + '\0' + code).encode()).hexdigest()
    with _lock:
        cached = _cache.get(fingerprint)
        if cached and time.monotonic() - cached[0] < 300:
            return cached[1]
    if not _slots.acquire(blocking=False):
        raise java_runner.RunnerUnavailable('当前检查人数较多，请稍后重试。')
    try:
        marker = secrets.token_hex(16)
        source, offset = build_source(profile, code, marker)
        with _lock:
            day = time.strftime('%Y-%m-%d', time.gmtime())
            if _daily['day'] != day:
                _daily.update(day=day, count=0)
            if _daily['count'] >= 100:
                raise java_runner.RunnerUnavailable('今天的代码检查试用次数已用完，请明天再试。')
            _daily['count'] += 1
        result = _interpret(profile, code, java_runner.run_java(source), marker, offset)
        with _lock:
            if len(_cache) >= 100:
                _cache.pop(next(iter(_cache)))
            _cache[fingerprint] = (time.monotonic(), result)
        return result
    finally:
        _slots.release()
