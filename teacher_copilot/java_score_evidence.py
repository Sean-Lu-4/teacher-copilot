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
    whole = profile.get('kind') == 'class'
    source = code if whole else 'class X {\n' + code + '\n}'
    tree = Parser(Language(tree_sitter_java.language())).parse(source.encode())
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
    for rule in RULES.get(question_id, []):
        method = methods.get(rule['method'])
        if method and all(i < len(cases) and cases[i]['status'] == 'passed' for i in rule['cases']):
            line = method.start_point.row + (1 if whole else 0)
            award(rule['index'], [max(1,line)], '该方法通过对应边界和功能测试；这是参考得分依据，不是官方评分。', rule['label'])
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
    # Printed statement problems are checked one part at a time. Only observable
    # final-output criteria are awarded; internal loop/substring points remain
    # pending. No points from a different part can leak into this result.
    if profile.get('kind') == 'parts' and isinstance(part, int) and all(c['status']=='passed' for c in cases) and cases:
        mapping = {
            'AP-FRQ69fc5af861bea528S3': {0:2,1:5},
            'AP-FRQ69fc5af861bea528S4': {0:2,1:5},
            'AP-FRQabac91d826c61ac9': {0:2,1:5,2:8,3:11},
        }
        index = mapping.get(question_id, {}).get(part)
        if index is not None:
            award(index, [], '所选小问通过全部输出样例和边界测试。', '所选小问输出正确')
    return rows
