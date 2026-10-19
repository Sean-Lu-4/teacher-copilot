"""Conservative, explicit mappings from reviewed tests to rubric evidence.

Unmapped criteria and untested parts remain pending, including randomness,
design prose, and equivalent implementations requiring human interpretation.
"""
import json
from pathlib import Path

RULES = json.loads(Path(__file__).with_name('java_score_rules.json').read_text(encoding='utf8'))


def evidence(question_id, code, result, points, part=None):
    rows = [dict(id=p['id'], label=p['description'], points=p['points'], status='unverified',
                 lines=[], reason='当前测试不足以确认此评分点，保留部分分复核。',
                 provenance=p.get('provenance', 'source')) for p in points]
    if result.get('status') not in {'passed', 'failed'}:
        return rows
    from tree_sitter import Language, Parser
    import tree_sitter_java
    from .java_grading import PROFILES
    profile = PROFILES[question_id]
    if profile.get('kind') == 'parts' and type(part) is int and 0 <= part < len(profile['parts']):
        # Each imported statement part has three distinct rubric points. Other
        # parts were not submitted; they are not pending points in this answer.
        for index, row in enumerate(rows):
            row['applicable'] = index // 3 == part
    whole = profile.get('kind') == 'class'
    snippet = profile.get('kind') in {'parts', 'email'}
    source = code if whole else ('class X { void answer() {\n' if snippet else 'class X {\n') + code + ('\n}}' if snippet else '\n}')
    tree = Parser(Language(tree_sitter_java.language())).parse(source.encode())
    if tree.root_node.has_error:
        return rows
    methods = {}
    stack = [tree.root_node]
    while stack:
        n = stack.pop()
        if n.type in {'method_declaration', 'constructor_declaration'}:
            name = n.child_by_field_name('name').text.decode()
            methods[name] = n
        stack.extend(n.named_children)
    def award(index, lines, reason, label=None):
        if 0 <= index < len(rows):
            rows[index].update(status='earned', lines=lines, reason=reason)
            if label:
                rows[index]['label'] = label
    cases = result.get('cases', [])
    def reachable_nodes(method):
        # Follow student helper methods, so extracting a helper does not lose a
        # point. Never inspect comments or unrelated, uncalled methods.
        visited = set()
        pending = [method]
        while pending:
            current = pending.pop()
            if current.start_byte in visited:
                continue
            visited.add(current.start_byte)
            nodes = [current]
            while nodes:
                node = nodes.pop()
                yield node
                if node.type == 'method_invocation':
                    name = node.child_by_field_name('name').text.decode()
                    obj = node.child_by_field_name('object')
                    if name in methods and (obj is None or obj.text == b'this'):
                        pending.append(methods[name])
                # Local/anonymous classes have their own execution context.
                if node.type not in {'class_declaration', 'class_body', 'lambda_expression'}:
                    nodes.extend(node.named_children)
    def call_evidence(method, required):
        found, lines = set(), set()
        for node in reachable_nodes(method):
            if node.type == 'method_invocation' and node.child_by_field_name('name').text.decode() in required:
                found.add(node.child_by_field_name('name').text.decode())
                lines.add(max(1, node.start_point.row + (1 if whole else 0)))
        return sorted(lines) if set(required) <= found else []
    for rule in RULES.get(question_id, []):
        method = methods.get(rule['method'])
        if method and rule['cases'] and all(0 <= i < len(cases) and cases[i]['status'] == 'passed' for i in rule['cases']):
            line = method.start_point.row + (1 if whole else 0)
            lines = call_evidence(method, rule['calls']) if rule.get('calls') else [max(1,line)]
            if not lines:
                continue
            if rule.get('any_calls'):
                lines = sorted({line for name in rule['any_calls'] for line in call_evidence(method, [name])})
            if rule.get('creates'):
                lines = [max(1,n.start_point.row+(1 if whole else 0)) for n in reachable_nodes(method)
                         if n.type=='object_creation_expression' and n.child_by_field_name('type').text.decode().split('<')[0].split('.')[-1] == rule['creates']]
            if rule.get('operator'):
                lines = [max(1,n.start_point.row+(1 if whole else 0)) for n in reachable_nodes(method)
                         if n.type=='binary_expression' and n.child_by_field_name('operator').text.decode()==rule['operator']]
            if rule.get('accumulator'):
                from .java_rubric_structure import accumulation_lines
                lines = [max(1,line+(1 if whole else 0)) for line in accumulation_lines(reachable_nodes(method), **rule['accumulator'])]
            if rule.get('null_check'):
                from .java_rubric_structure import null_comparison_lines
                lines = [max(1,line+(1 if whole else 0)) for line in null_comparison_lines(reachable_nodes(method))] or call_evidence(method, ['isNull']) or call_evidence(method, ['nonNull'])
            if lines:
                award(rule['index'], lines, rule.get('reason', '该方法通过对应边界和功能测试；这是参考得分依据，不是官方评分。'), rule.get('label'))
    if whole and not tree.root_node.has_error:
        declarations = [n for n in tree.root_node.named_children if n.type == 'class_declaration']
        if len(declarations) == 1:
            cls = declarations[0]
            modifiers = next((n.text.decode().split() for n in cls.named_children if n.type == 'modifiers'), [])
            if 'public' in modifiers and cls.child_by_field_name('name').text.decode() == profile['class_name']:
                award(0, [cls.start_point.row+1], '已核对完整类名与 public 可见性。', '类声明正确')
            members = cls.child_by_field_name('body').named_children
            def matches(node, spec):
                mods = next((n.text.decode().split() for n in node.named_children if n.type=='modifiers'), [])
                if 'public' not in mods or 'static' in mods:
                    return False
                if node.child_by_field_name('name').text.decode() != spec['name']:
                    return False
                args = [a.child_by_field_name('type').text.decode() for a in node.child_by_field_name('parameters').named_children if a.type=='formal_parameter']
                return args == spec['args'] and ('returns' not in spec or node.child_by_field_name('type').text.decode()==spec['returns'])
            for header in profile.get('headers', []):
                found = []
                for spec in header['signatures']:
                    kind = 'method_declaration' if 'returns' in spec else 'constructor_declaration'
                    found.extend(n for n in members if n.type == kind and matches(n, spec))
                if len(found) == len(header['signatures']):
                    award(header['index'], sorted({n.start_point.row+1 for n in found}), '已核对名称、参数类型、返回类型和可见性。', '方法 / 构造器声明正确')
            fields = [n for n in members if n.type=='field_declaration']
            counts = {}
            private_only = bool(fields)
            for f in fields:
                mods = next((n.text.decode().split() for n in f.named_children if n.type=='modifiers'), [])
                private_only &= 'private' in mods and 'static' not in mods
                typ = f.child_by_field_name('type').text.decode()
                counts[typ] = counts.get(typ,0) + sum(n.type=='variable_declarator' for n in f.named_children)
            needed = profile.get('private_fields')
            if needed and private_only and all(counts.get(t,0)>=n for t,n in needed.items()) and all(c['status']=='passed' for c in cases):
                award(1, [f.start_point.row+1 for f in fields], '已核对私有非静态字段及对象独立性测试。', '实例字段与对象独立性')
            if cases and len(cases)==len(profile['cases']) and all(c['status']=='passed' for c in cases):
                from .java_initialization import initialization_lines
                lines=initialization_lines(cls)
                name=profile['class_name']
                index={'Car':3,'TrashCan':3,'CubePair':3,'CupcakeMachine':3,
                       'LapTracker':3,'AdditionPattern':3,'Sign':1,'Scoreboard':2}.get(name)
                ctor_public=all('public' in next((n.text.decode().split() for n in c.named_children if n.type=='modifiers'), []) for c in members if c.type=='constructor_declaration')
                if lines and index is not None and ctor_public and (name!='Sign' or private_only):
                    award(index,lines,'构造参数已存入实例字段，且初始状态、连续操作与对象独立性测试通过。','构造器正确初始化实例变量')
    # Each statement subproblem has its own inputs, output and rubric indices.
    # Equivalent arithmetic/string implementations are accepted by behavior.
    if profile.get('kind') == 'parts' and type(part) is int and 0 <= part < len(profile['parts']) and len(cases) == len(profile['parts'][part]['examples']) and all(c['status']=='passed' for c in cases) and cases:
        mapping = {
            'AP-FRQ69fc5af861bea528S3': {0:[0,1,2],1:[3,4,5]},
            'AP-FRQ69fc5af861bea528S4': {0:[0,1,2],1:[3,5]},
            'AP-FRQabac91d826c61ac9': {0:[0,1,2],1:[3,5],2:[6,7,8],3:[9,10,11]},
        }
        for index in mapping.get(question_id, {}).get(part, []):
            award(index, [], '所选小问在不同长度、边界及格式样例中表现正确，不要求固定变量名或同一种算法。')
        prefix_index = {'AP-FRQ69fc5af861bea528S4': (1,4), 'AP-FRQabac91d826c61ac9': (1,4)}.get(question_id)
        if prefix_index and part == prefix_index[0]:
            lines = []
            for name in ('contains', 'indexOf', 'startsWith', 'regionMatches', 'equals'):
                lines.extend(call_evidence(methods['answer'], [name]))
            if lines:
                award(prefix_index[1], sorted(set(lines)), '字符串匹配调用与前缀边界测试均通过。')
    if profile.get('kind') == 'email' and len(cases) == 3:
        # These tests inspect actual String values, not student variable names.
        # Randomness/uniformity points cannot be inferred from valid output.
        for case, indices in ((0,[1,2]),(1,[3,4])):
            if cases[case]['status'] == 'passed':
                for index in indices:
                    # This source question explicitly requires substring for
                    # extracting names/initials. Correct output alone is not
                    # enough to satisfy a mandated API requirement.
                    if index in {1,3} and not call_evidence(methods['answer'], ['substring']):
                        continue
                    award(index, [], '不同姓名长度与边界样例均生成了题目要求的用户名。')
    return rows
