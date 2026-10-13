"""Local teaching checklists and conservative evidence retrieval (no API calls)."""
import re

METHODS_CALLING = {
    'id': 'methods-calling',
    'title': '方法调用、参数与返回值',
    'subject': 'AP Computer Science A',
    'level': 'Grade 10',
    'duration': 45,
    'topic': 'Calling existing methods with parameters and using return values',
    'objectives': ('Call existing methods with compatible arguments, use return values, '
                   'and trace short method calls. Students know variables and primitive '
                   'data types. Do not require students to write their own methods.'),
    'prerequisites': '已学变量和基本数据类型；不假定已学数组、循环或类设计。',
    'scope': '调用已有方法、传入正确实参、使用返回值、追踪简单调用。',
    'excluded': '独立编写方法、类设计、对象引用传递、数组算法、递归。',
    'items': [
        dict(id='parameters', title='参数与实参',
             check='能指出声明中的参数与调用中的实参，并说明两者关系。',
             query='formal actual parameters arguments method declaration calling',
             groups=[r'\bparameters?\b|形参|参数', r'\barguments?\b|actual parameters?|实参']),
        dict(id='argument_count', title='实参数量匹配',
             check='能根据方法声明确定调用所需的实参数量，识别多传或少传。',
             query='method arguments parameters number how many',
             groups=[r'\bparameters?\b|\barguments?\b|参数|实参',
                     r'\bnumber\b|how many|数量|个数']),
        dict(id='argument_order', title='实参顺序匹配',
             check='能按声明顺序传入实参，并解释调换顺序可能产生的不同结果。',
             query='method arguments parameters order corresponding position',
             groups=[r'\bparameters?\b|\barguments?\b|参数|实参',
                     r'\b(order|positions?)\b|顺序|位置']),
        dict(id='argument_types', title='实参类型兼容',
             check='能判断实参类型是否与对应参数兼容，识别不兼容的调用。',
             query='method arguments parameters types match compatible',
             groups=[r'\bparameters?\b|\barguments?\b|参数|实参',
                     r'\btypes?\b|类型', r'\b(match|compatible|corresponding)\b|匹配|兼容|对应']),
        dict(id='void', title='void 与非 void 方法',
             check='区分没有返回值与有返回值；知道 void 调用不能作为取值表达式。',
             query='void non void method return value',
             groups=[r'\bvoid\b', r'\breturn\b|返回']),
        dict(id='return_use', title='返回值的使用',
             check='能保存返回值或把它用于表达式，区分 return 与打印输出。',
             query='return value stored variable expression print method',
             groups=[r'\breturn(?:ed)?\s+values?\b|返回值',
                     r'\b(stored?|variables?|expressions?)\b|存储|表达式|变量']),
        dict(id='trace', title='方法调用过程跟踪',
             check='从实参赋值到执行、返回和后续语句，逐步解释变量或输出。',
             query='method call execution control returns trace output',
             groups=[r'\bmethods?\b|方法',
                     r'\b(execut\w*|control|trac\w*|output)\b|执行|跟踪|输出']),
        dict(id='errors', title='常见错误',
             check='有与调用有关的错误示例及解释；不把方法编写错误直接当成本课练习。',
             query='method call arguments parameters void return compile error invalid uses',
             groups=[r'\b(methods?|parameters?|arguments?|void)\b|方法|参数',
                     r'\b(errors?|incorrect|invalid|compile|compilation)\b|valid uses|错误|编译',
                     r'\bcall(?:s|ing)?\b|uses of the method|调用']),
        dict(id='practice', title='练习与达标检查',
             check='学生只需调用或追踪已有方法；检查题目完整、难度适当并有可核对的答案。',
             query='method call parameters return exercise question output result',
             groups=[r'\b(methods?|parameters?|arguments?)\b|方法|参数',
                     r'\b(exercises?|questions?|output|result)\b|练习|题目|输出']),
    ],
}


def find_candidates(profile, chunks, search):
    """Every checklist item has its own lexical search and evidence gates.

    A candidate is NOT a judgement of coverage, correctness, or difficulty.
    At most two different pages are retained per item for a readable review.
    """
    coverage = []
    for item in profile['items']:
        eligible = [c for c in chunks if all(re.search(pattern, c['text'], re.I)
                                             for pattern in item['groups'])]
        ranked = search(item['query'], eligible)
        candidates, seen = [], set()
        for score, chunk in ranked:
            key = (chunk['file'], chunk['page'])
            if key in seen:
                continue
            seen.add(key)
            candidates.append(dict(score=score, chunk=chunk))
            if len(candidates) == 2:
                break
        coverage.append(dict(id=item['id'], title=item['title'], check=item['check'],
                             query=item['query'], candidates=candidates))
    return coverage


def interleave_candidates(coverage):
    """First candidate of every objective before any objective's second candidate."""
    ranked, seen = [], set()
    for rank in range(2):
        for item in coverage:
            if len(item['candidates']) <= rank:
                continue
            candidate = item['candidates'][rank]
            chunk = candidate['chunk']
            key = (chunk['file'], chunk['page'], chunk['chunk'])
            if key not in seen:
                seen.add(key)
                ranked.append((candidate['score'], chunk))
    return ranked


def included(candidate, selected):
    chunk = candidate['chunk']
    for _, passage in selected:
        if (passage['file'], passage['page']) != (chunk['file'], chunk['page']):
            continue
        if 'start' in chunk and 'start' in passage:
            if passage['start'] <= chunk['start'] and passage['end'] >= chunk['end']:
                return True
        elif chunk['text'] in passage['text']:
            return True
    return False


def summarize(coverage, selected):
    output = []
    for item in coverage:
        candidates = [dict(score=c['score'], included_in_prompt=included(c, selected),
                           **{k: v for k, v in c['chunk'].items() if k != 'page_text'})
                      for c in item['candidates']]
        status = ('not_found' if not candidates else
                  'candidate_in_prompt' if any(c['included_in_prompt'] for c in candidates)
                  else 'candidate_not_selected')
        output.append(dict(id=item['id'], title=item['title'], check=item['check'],
                           query=item['query'], status=status, teacher_confirmed=False,
                           candidates=candidates))
    return output


STATUS_LABELS = {
    'not_found': '未找到候选，需补充或调整检索',
    'candidate_in_prompt': '找到候选并已纳入提示词，待教师确认',
    'candidate_not_selected': '找到候选，但未纳入提示词（片段数或长度限制）',
}


def scope_instructions(profile, summary):
    lines = ['LESSON SCOPE AND COVERAGE REVIEW',
             'Prerequisites: variables and primitive data types only.',
             'Teach calling existing methods with arguments, using return values, and tracing calls.',
             'Do not require students to implement methods. Do not require arrays, loops,',
             'class design, object-reference mutation, or recursion.',
             'The checklist below is lexical retrieval evidence only, not verified coverage.',
             'A candidate outside the prompt is unavailable evidence. Clearly flag unsupported',
             'objectives; do not claim the materials cover them. Adapt questions to this scope.']
    for item in summary:
        lines.append(f"- {item['title']}: {STATUS_LABELS[item['status']]}。检查：{item['check']}")
    return '\n'.join(lines)


def coverage_report(profile, course, summary, args):
    lines = [f"# 本课知识点覆盖检查：{profile['title']}", '',
             f"年级：{course['level']}；课时：{course['duration']} 分钟。", '',
             f"前置知识：{profile['prerequisites']}", '', f"本课范围：{profile['scope']}", '',
             f"暂不教学：{profile['excluded']}", '',
             f'检索范围：Unit {args.unit or "全部"}；材料类型：{args.material_type}。', '',
             '本报告逐项进行本地关键词检索。候选命中不等于已覆盖，也不等于教材正确或难度合适。',
             '未找到候选不代表整套教材没有该知识点。候选可能因检索词、PDF 提取或单元筛选遗漏。',
             '“纳入提示词”只表示文字已发送到待用提示词中；是否足够仍需教师确认。',
             '页码按 PDF 第一页开始计数。分数仅用于单项内排序，不在知识点之间比较。', '',
             '| 知识点 | 检索状态 | 教师确认 |', '|---|---|---|']
    for item in summary:
        lines.append(f"| {item['title']} | {STATUS_LABELS[item['status']]} | 待确认 |")
    for item in summary:
        lines += ['', f"## {item['title']}", '', item['check'], '',
                  f"状态：{STATUS_LABELS[item['status']]}", '', f"检索词：{item['query']}", '']
        if not item['candidates']:
            lines += ['建议：在限定教材中补查相关页，或补充针对本课的示例／练习。', '']
        for number, c in enumerate(item['candidates'], 1):
            lines += [f"### 候选 {number}：{c['file']}，PDF 第 {c['page']} 页", '',
                      f"单项分数：{c['score']:.3f}；纳入提示词：{'是' if c['included_in_prompt'] else '否'}。", '']
            for warning in c.get('warnings', []):
                lines += [f'提取提醒：{warning}', '']
            fence = '`' * max(3, 1 + max((len(m[0]) for m in re.finditer(r'`+', c['text'])), default=0))
            lines += [fence + 'text', c['text'], fence, '']
        lines += ['- [ ] 教师确认：内容足以支持本项教学目标',
                  '- [ ] 示例完整，且只依赖本课允许的前置知识',
                  '教师备注／待补充材料：________________', '']
    return '\n'.join(lines)
