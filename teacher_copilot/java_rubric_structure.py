"""Small AST predicates used only alongside successful behavioral tests."""


def accumulation_lines(nodes, conditional=False, value_call=None, counter=False):
    """Recognize zero-initialized local accumulators without fixed names.

    Accept +=, ++ and x = x + value, in for/enhanced-for/while/do loops.
    Unknown forms stay unverified rather than being marked incorrect.
    """
    nodes = list(nodes)
    initialized = {}
    for node in nodes:
        if node.type == 'variable_declarator':
            value = node.child_by_field_name('value')
            if value and value.text.decode() in {'0', '0.0', '0.0d', '0.0D'}:
                initialized[node.child_by_field_name('name').text.decode()] = node.start_byte
    found = []
    loops = {'for_statement', 'enhanced_for_statement', 'while_statement', 'do_statement'}
    for node in nodes:
        target, value = None, None
        if node.type == 'update_expression' and b'++' in node.text:
            target = next((n.text.decode() for n in node.named_children if n.type == 'identifier'), None)
        elif node.type == 'assignment_expression':
            left = node.child_by_field_name('left')
            if left.type != 'identifier':
                continue
            target = left.text.decode()
            op = node.child_by_field_name('operator').text
            value = node.child_by_field_name('right')
            if op == b'=':
                if value.type != 'binary_expression' or value.child_by_field_name('operator').text != b'+':
                    continue
                a, b = value.child_by_field_name('left'), value.child_by_field_name('right')
                if a.text == left.text: value = b
                elif b.text == left.text: value = a
                else: continue
            elif op != b'+=':
                continue
        if target not in initialized:
            continue
        parent, guarded = node.parent, False
        while parent and parent.type not in loops:
            guarded |= parent.type == 'if_statement'
            parent = parent.parent
        if not parent or initialized[target] >= parent.start_byte or (conditional and not guarded):
            continue
        if counter and value is not None and value.text != b'1':
            continue
        if value_call:
            if value is None:
                continue
            pending, matched = [value], False
            while pending:
                child = pending.pop()
                matched |= child.type == 'method_invocation' and child.child_by_field_name('name').text.decode() == value_call
                pending.extend(child.named_children)
            if not matched:
                continue
        found.append(node.start_point.row)
    return found


def null_comparison_lines(nodes):
    return [node.start_point.row for node in nodes
            if node.type == 'binary_expression'
            and node.child_by_field_name('operator').text in {b'==', b'!='}
            and any(child.type == 'null_literal' for child in node.named_children)]
