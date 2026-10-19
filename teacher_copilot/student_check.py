"""Non-executing Java diagnostics and source-backed FRQ scoring checklist.

No student code is compiled or executed in the web process. Syntax results
never award points: AP criteria can require human interpretation.
"""
import re


def scoring_points(question):
    text = question.get('answer', '')
    pattern = re.compile(r'(?m)^\s*((?:Part\s+[A-Z]\s+)?Point\s+\d+)\s*$')
    matches = list(pattern.finditer(text))
    points = []
    seen = set()
    for index, match in enumerate(matches):
        label = ' '.join(match.group(1).split())
        section = text[match.end():matches[index + 1].start() if index + 1 < len(matches) else len(text)]
        criterion = re.search(r'To earn this point, responses must demonstrate the following:\s*(.*?)(?=Canonical Solution\s*:|Canonical Solution\s*\n|\n\s*0\s*\n|\Z)', section, re.S)
        if not criterion:
            continue
        description = ' '.join(criterion.group(1).split())
        if not description or len(description) > 1600:
            continue
        if (label, description) in seen:
            continue
        duplicate = sum(previous == label for previous, _ in seen)
        seen.add((label, description))
        # Keep exception rules with the criterion; these affect partial credit.
        exception = re.search(r'(Responses (?:can still|will not) earn the point.*?)(?=\n\s*\d+\.\s*\n|\Z)', section, re.S)
        point_id = label if not duplicate else f'{label} (section {duplicate + 1})'
        points.append(dict(id=point_id, label=point_id, points=1, description=description,
                           exceptions=exception.group(1).strip()[:3000] if exception else '',
                           status='unverified'))
    if not points:
        # Newer guides use +1 [Skill ...] instead of numbered Point headings.
        # Stop before sample scored responses, whose repeated bullets are not
        # additional criteria.
        guide = text
        bullets = list(re.finditer(r'(?m)^\s*\+1\s+\[Skill[^\]]+\]\s*', guide))
        for i, match in enumerate(bullets):
            section = guide[match.end():bullets[i+1].start() if i+1 < len(bullets) else len(guide)].split('Canonical Solution')[0]
            description = re.split(r'Responses (?:can still|will not)', section)[0]
            description = ' '.join(description.split())
            if description and len(description) < 1600:
                points.append(dict(id=f'Point {i+1}', label=f'Point {i+1}', points=1,
                                   description=description, exceptions=section[len(re.split(r'Responses (?:can still|will not)', section)[0]):].strip(), status='unverified'))
    if not points and question.get('reference_marks'):
        # These are labelled reference criteria, never represented as an
        # extracted official scoring guide.
        import json
        from pathlib import Path
        from .java_grading import PROFILES
        key = PROFILES.get(question['id'], {}).get('reference_key')
        references = json.loads(Path(__file__).with_name('imported_bank').joinpath('reference_solutions_20261015.json').read_text(encoding='utf8'))
        for part, descriptions in references.get(key, {}).get('parts', []):
            for description in descriptions:
                index = len(points) + 1
                points.append(dict(id=f'Reference {index}', label=f'参考评分点 {index}', points=1,
                                   description=part + ': ' + description, exceptions='', status='unverified',
                                   provenance='reference'))
    return points


def syntax_report(code):
    from tree_sitter import Language, Parser
    import tree_sitter_java
    parser = Parser(Language(tree_sitter_java.language()))
    attempts = [(code, 0), ('class Student {\n' + code + '\n}', 1),
                ('class Student { void answer() {\n' + code + '\n}}', 1)]
    best = None
    for source, offset in attempts:
        tree = parser.parse(source.encode('utf-8'))
        errors = []
        stack = [tree.root_node]
        while stack:
            item = stack.pop()
            if item.is_error or item.is_missing:
                line = min(len(code.splitlines()) or 1, max(1, item.start_point.row + 1 - offset))
                symbols = {';': '分号 ;', ')': '右括号 )', '}': '右花括号 }', ']': '右方括号 ]'}
                message = ('这里缺少' + symbols[item.type] + '。') if item.is_missing and item.type in symbols else '这里可能缺少符号或存在不完整的 Java 语句。'
                errors.append(dict(line=line, message=message))
            stack.extend(reversed(item.children))
        if not tree.root_node.has_error:
            return dict(status='passed', diagnostics=[], message='未发现语法结构错误；尚未检查类型、变量和运行结果。')
        if best is None or len(errors) < len(best):
            best = errors
    unique = {item['line']: item for item in best or []}
    return dict(status='failed', diagnostics=list(unique.values())[:10],
                message='发现语法结构问题。请检查提示行附近的代码。')


def check_submission(payload, questions):
    if not isinstance(payload, dict):
        raise ValueError('提交格式无效。')
    code = payload.get('code')
    if not isinstance(code, str) or not code.strip() or len(code) > 20000:
        raise ValueError('请提交 1–20000 个字符的 Java 代码。')
    question = next((q for q in questions if q['id'] == payload.get('question_id')
                     and q.get('source_item_id') and q.get('question_kind') == 'write'), None)
    if question is None:
        raise ValueError('请选择题库中的 FRQ。')
    try:
        syntax = syntax_report(code)
    except ImportError:
        syntax = dict(status='unavailable', diagnostics=[], message='语法检查暂不可用。')
    from .java_grading import grade
    from .java_runner import RunnerUnavailable
    try:
        automatic = grade(question['id'], code, payload.get('part'))
    except (RunnerUnavailable, ValueError) as exc:
        automatic = dict(status='unavailable', message=str(exc), cases=[], practice_score=None)
    points = scoring_points(question)
    if not automatic.get('score_evidence'):
        from .java_score_evidence import evidence
        automatic['score_evidence'] = evidence(question['id'], code, automatic, points, payload.get('part'))
    return dict(question_id=question['id'], syntax=syntax, automatic=automatic,
                compilation=dict(status='passed' if automatic['status'] in {'passed','failed','runtime_error','timeout'} else 'compile_error' if automatic['status']=='compile_error' else 'unavailable', message=automatic['message']),
                tests=dict(status='unavailable' if automatic['status']=='unsupported' else automatic['status'], cases=automatic.get('cases', [])),
                scoring_points=points, score=None,
                message='以下得分点来自题目评分指南，请逐项对照。语法检查不会自动判分。')
