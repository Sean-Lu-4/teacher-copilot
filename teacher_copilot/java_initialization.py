"""Trace constructor parameter storage without executing student code locally.

This is evidence alongside behavioral tests, not an equivalence proof. Unknown
control flow or helper calls remain unverified rather than guessed correct.
"""

def initialization_lines(cls):
    members = cls.child_by_field_name('body').named_children
    fields = set()
    constructors = []
    for node in members:
        if node.type == 'field_declaration':
            mods = next((n.text.decode().split() for n in node.named_children if n.type=='modifiers'), [])
            if 'static' in mods:
                return []
            fields.update(n.child_by_field_name('name').text.decode() for n in node.named_children if n.type=='variable_declarator')
        elif node.type == 'constructor_declaration':
            constructors.append(node)
    if not constructors or not fields:
        return []

    def run(ctor, arguments, active):
        if ctor.start_byte in active:
            raise ValueError('recursive delegation')
        active = active | {ctor.start_byte}
        params = [n for n in ctor.child_by_field_name('parameters').named_children if n.type=='formal_parameter']
        env = {p.child_by_field_name('name').text.decode(): value for p,value in zip(params,arguments)}
        stored = {f:set() for f in fields}
        lines = []
        def value(n):
            if n is None:
                return set()
            if n.type == 'identifier':
                name=n.text.decode()
                if name in env:return env[name]
                if name in stored:return stored[name]
                raise ValueError('unknown identifier')
            if n.type == 'field_access':
                if n.child_by_field_name('object').text != b'this':raise ValueError('foreign field')
                return stored[n.child_by_field_name('field').text.decode()]
            if n.type in {'decimal_integer_literal','decimal_floating_point_literal','true','false','string_literal','null_literal','character_literal'}:
                return set()
            if n.type == 'parenthesized_expression':return value(n.named_children[0])
            if n.type == 'cast_expression':return value(n.child_by_field_name('value'))
            if n.type == 'object_creation_expression':
                # Constructor allocation stores its arguments, e.g. new Cube(type).
                return set().union(*(value(a) for a in n.child_by_field_name('arguments').named_children))
            raise ValueError('unreviewed expression')
        for statement in ctor.child_by_field_name('body').named_children:
            if statement.type in {'line_comment','block_comment'}:continue
            if statement.type == 'explicit_constructor_invocation':
                if not statement.text.lstrip().startswith(b'this(') and not statement.text.lstrip().startswith(b'this ('):
                    raise ValueError('unsupported delegation')
                args=[value(a) for a in statement.child_by_field_name('arguments').named_children]
                candidates=[c for c in constructors if len([p for p in c.child_by_field_name('parameters').named_children if p.type=='formal_parameter'])==len(args)]
                if len(candidates)!=1:raise ValueError('ambiguous overload')
                stored, delegated=run(candidates[0],args,active)
                lines.extend(delegated);lines.append(statement.start_point.row+1)
                continue
            if statement.type == 'local_variable_declaration':
                for d in statement.named_children:
                    if d.type=='variable_declarator':env[d.child_by_field_name('name').text.decode()]=value(d.child_by_field_name('value'))
                continue
            if statement.type != 'expression_statement' or len(statement.named_children)!=1:
                raise ValueError('unsupported statement')
            assignment=statement.named_children[0]
            if assignment.type!='assignment_expression' or assignment.child_by_field_name('operator').text!=b'=':
                raise ValueError('unsupported assignment')
            left=assignment.child_by_field_name('left');right=value(assignment.child_by_field_name('right'))
            if left.type=='identifier':
                name=left.text.decode()
                if name in env:env[name]=right;continue
            elif left.type=='field_access' and left.child_by_field_name('object').text==b'this':
                name=left.child_by_field_name('field').text.decode()
            else:raise ValueError('unsupported target')
            if name not in stored:raise ValueError('not an instance field')
            stored[name]=right;lines.append(statement.start_point.row+1)
        return stored,lines

    all_lines=[]
    try:
        for ctor in constructors:
            params=[p for p in ctor.child_by_field_name('parameters').named_children if p.type=='formal_parameter']
            expected=set(range(len(params)))
            stored,lines=run(ctor,[{i} for i in expected],set())
            if not expected or set().union(*stored.values()) != expected:return []
            all_lines.extend(lines)
    except (ValueError,KeyError,AttributeError):
        return []
    return sorted(set(all_lines))
