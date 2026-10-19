"""Harnesses for source questions requesting statements, not methods."""
import json


def _literal(value):
    return json.dumps(value, ensure_ascii=True) if isinstance(value, str) else str(value)


def build(profile, code, marker):
    from tree_sitter import Language, Parser
    import tree_sitter_java
    wrapped = 'class X { void answer() {\n' + code + '\n}}'
    tree = Parser(Language(tree_sitter_java.language())).parse(wrapped.encode())
    if tree.root_node.has_error:
        raise ValueError('请只填写所选小问的 Java 语句，不需要外层类或方法。')
    classes = tree.root_node.named_children
    if len(classes) != 1 or classes[0].type != 'class_declaration':
        raise ValueError('请只填写所选小问的代码片段。')
    members = classes[0].child_by_field_name('body').named_children
    if len(members) != 1 or members[0].type != 'method_declaration':
        raise ValueError('请只填写所选小问的代码片段。')
    if profile['kind'] == 'email':
        body = members[0].child_by_field_name('body')
        names = []
        for statement in body.named_children:
            if statement.type == 'local_variable_declaration' and statement.child_by_field_name('type').text == b'String':
                names.extend(n.child_by_field_name('name').text.decode() for n in statement.named_children if n.type == 'variable_declarator')
        if not names:
            raise ValueError('请按题意将用户名保存在 String 变量中。变量名可自行命名。')
        prefix = 'import java.util.*;\npublic class Main {\nstatic String[] answer(String email){\n'
        source = prefix + code + '\nreturn new String[]{' + ','.join(names) + '};}\n'
        source += 'public static void main(String[] args){boolean[] ok={true,true,true};\n'
        source += '''for(String email:new String[]{"joseph.martin@school.org","virginia.farmingham@school.net","a.abc@x.org","Z.longname@x.io"}){
            String first=email.substring(0,email.indexOf('.')),last=email.substring(email.indexOf('.')+1,email.indexOf('@'));
            for(int attempt=0;attempt<12;attempt++){
                String[] results=answer(email);List<String> values=Arrays.asList(results);
                ok[0]&=values.contains(first+"_"+last);ok[1]&=values.contains(first.substring(0,1)+"_"+last);
                boolean valid=false;
                for(String s:results)if(s!=null&&s.length()==5&&s.charAt(1)=='_'&&first.contains(s.substring(0,1))&&last.contains(s.substring(2)))valid=true;
                ok[2]&=valid;
            }
        }
        '''
        for i in range(3):
            source += f'System.out.println("{marker}:{i}:"+(ok[{i}]?"PASS":"FAIL"));\n'
        return source + '}}', prefix.count('\n')
    prefix = 'import java.util.*;\npublic class Main {\nstatic void answer(' + profile['args'] + ') {\n'
    source = prefix + code + '\n}\npublic static void main(String[] args){\n'
    for i, example in enumerate(profile['examples']):
        values = example['input'] if isinstance(example['input'], list) else [example['input']]
        args = ','.join(_literal(v) for v in values)
        expected = _literal(example['expected'])
        source += '{java.io.PrintStream saved=System.out;java.io.ByteArrayOutputStream bytes=new java.io.ByteArrayOutputStream();String result="ERROR";String actual="";try{System.setOut(new java.io.PrintStream(bytes,true,"UTF-8"));answer(' + args + ');actual=bytes.toString("UTF-8").replaceAll("[\\r\\n]+$", "");result=actual.equals(' + expected + ')?"PASS":"FAIL";}catch(Throwable e){result="ERROR:"+e.getClass().getSimpleName();}finally{System.setOut(saved);}System.out.println("' + marker + ':' + str(i) + ':"+result);'
        detail = _literal('Input: ' + str(values) + '\nExpected: ' + example['expected'] + '\nYour result: ')
        source += 'if(!result.equals("PASS"))System.out.println("' + marker + ':' + str(i) + ':INFO:"+Base64.getEncoder().encodeToString((' + detail + '+actual).getBytes(java.nio.charset.StandardCharsets.UTF_8)));}\n'
    return source + '}}', prefix.count('\n')
