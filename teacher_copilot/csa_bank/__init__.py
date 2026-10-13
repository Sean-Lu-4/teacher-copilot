"""Original first-batch questions: three distinct tasks for every CED topic.

Fixtures check authored reference solutions, never execute edited teacher input.
"""
from ..csa_curriculum import LABELS, VERSION, objective

QUESTIONS = []
FIXTURES = []


def q(topic, tier, title, code, task, answer, points, error, *, expected=None,
      body=None, members='', solution='', checks='', files=None, kind='trace'):
    id = 'CSA' + topic.replace('.', '_') + '_' + tier
    level = {'B': 2, 'A': 3, 'E': 4}[tier]
    # Static nesting belongs only to the isolated test harness. Learners see
    # ordinary helper classes, assumed to be declared separately.
    display_code = code.replace('static class ', 'class ').replace('// In main: ', '// In main:\n')
    content = dict(id=id, title=title, code=display_code, task=task, answer=answer,
        objectives=[objective(topic)], ced_topics=[topic], level=level,
        minutes={'B':3,'A':5,'E':8}[tier],
        origin='原创' + {'B':'基础题','A':'巩固题','E':'考试风格练习（非真题）'}[tier],
        reasoning=points, errors=[error],
        rubric='；'.join(f'{p}（1 分）' for p in points) + f'。共 {len(points)} 分；等价正确答案同样给分。',
        intervention='围绕“' + error + '”让学生给出一个反例或逐步跟踪，再解释本题的关键规则。',
        prerequisites='本题对应 ' + topic + ' ' + LABELS[topic] + '；题目中已给出的辅助代码可直接使用。',
        question_kind=kind,
        verification_mode='conceptual_review' if kind=='concept' else 'java_fixture')
    if solution:
        content['reference_solution'] = solution.replace('static class ', 'class ')
    QUESTIONS.append(content)
    if kind != 'concept':
        if expected is None:
            raise ValueError('Executable questions require an explicit expected result: ' + id)
        FIXTURES.append(dict(id=id, members=members, body=code if body is None else body,
                             solution=solution, checks=checks, expected=expected, files=files or {}))


from . import unit1, unit2, unit3, unit4  # noqa: E402,F401
