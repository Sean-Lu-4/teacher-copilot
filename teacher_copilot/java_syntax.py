"""Parse generated Java without executing it; this is syntax checking, not proof of behavior."""
def check_java_syntax(code, *, method_required=False):
    try:
        from tree_sitter import Language, Parser
        import tree_sitter_java
    except ImportError:
        raise ValueError('Java 语法检查组件不可用，未放行补题。') from None
    parser=Parser(Language(tree_sitter_java.language()))
    candidates=[code, 'class SyntaxCheck {\n'+code+'\n}']
    if not method_required:candidates.append('class SyntaxCheck { void run() {\n'+code+'\n}}')
    for source in candidates:
        root=parser.parse(source.encode('utf-8')).root_node
        if root.has_error:continue
        stack=[root];found=False
        while stack:
            node=stack.pop()
            if node.type in {'method_declaration','constructor_declaration'}:found=True
            stack.extend(node.named_children)
        if not method_required or found:return
    raise ValueError('Java 代码不完整或有语法错误；请提供完整方法/类，使用真实换行或合法 JSON 转义，不能用字母 n 代替换行。')


def normalize_code_newlines(code):
    """Repair over-escaped separators outside literals, including in comments."""
    out=[];quote=None;i=0;line_comment=False;block_comment=False
    while i<len(code):
        c=code[i]
        if quote:
            out.append(c)
            if c=='\\' and i+1<len(code):
                i+=1;out.append(code[i])
            elif c==quote:quote=None
        elif code.startswith('\\r\\n',i):
            out.append('\n');i+=3;line_comment=False
        elif code.startswith('\\n',i):
            out.append('\n');i+=1;line_comment=False
        elif code.startswith('\\t',i):
            out.append('\t');i+=1
        elif line_comment:
            out.append(c)
            if c=='\n':line_comment=False
        elif block_comment:
            out.append(c)
            if code.startswith('*/',i):out.append('/');i+=1;block_comment=False
        elif code.startswith('//',i):
            out.append('//');i+=1;line_comment=True
        elif code.startswith('/*',i):
            out.append('/*');i+=1;block_comment=True
        elif c in ('"', "'"):
            quote=c;out.append(c)
        else:out.append(c)
        i+=1
    return ''.join(out)
