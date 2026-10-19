"""Conservative scoring evidence for the source-bank bead-sequence FRQ."""
import json
import re

QUESTION_ID = 'AP-FRQ00a62e501cd4dea8'
PROFILE = dict(class_name='BeadSequence', kind='fragment', cases=[
    dict(label='长度：5 和 10 都应包含在范围内'),
    dict(label='颜色：必须同时含 B 和 W'),
    dict(label='首尾：比较第一个和最后一个字符'),
    dict(label='输出：Acceptable / Not acceptable')])


def build(code, marker):
    from tree_sitter import Language, Parser
    import tree_sitter_java
    root = Parser(Language(tree_sitter_java.language())).parse(('class Student { void answer() {\n' + code + '\n}}').encode()).root_node
    if root.has_error or len(root.named_children) != 1:
        raise ValueError('请按题目顺序填写 A–D 四段代码，不需要外层 class 或方法。')
    inputs = ['OBWO','BWBGOGWBB','ROYGBIVW','BOBOBOBO','WBWRWBWRWBWR','BWWWBBWWWB',
              'BWWWB','BWBB','BWWWWWWWWWB','BWBWBWBWBW','RRRRR','WWWWW','BBBBB',
              'WBBBW','WBWWW','RWBWR','B','W','BW','RBBBBBBBBR','RWWWWWWWWR']
    prefix = 'import java.io.*;\npublic class Main {\nstatic boolean[] answer(String beadSequence) {\n'
    source = prefix + code + '\nreturn new boolean[]{lengthGood,correctColors,startEndGood};\n}\n'
    source += 'public static void main(String[] args) throws Exception {\nString[] inputs=' + json.dumps(inputs).replace('[','{').replace(']','}') + ';\n'
    source += '''boolean[] pass={true,true,true,true};
String[] information={"","","",""};
PrintStream saved=System.out;
for(String input:inputs){
 ByteArrayOutputStream capture=new ByteArrayOutputStream();
 try {
  System.setOut(new PrintStream(capture,true,"UTF-8"));
  boolean[] actual=answer(new String(input));
  boolean a=input.length()>=5 && input.length()<=10;
  boolean b=input.contains("B") && input.contains("W");
  boolean c=input.charAt(0)==input.charAt(input.length()-1);
  String[] expected={""+a,""+b,""+c,a&&b&&c ? "Acceptable":"Not acceptable"};
  String[] received={""+actual[0],""+actual[1],""+actual[2],capture.toString("UTF-8").trim()};
  for(int i=0;i<4;i++){
   boolean matches=received[i].equals(expected[i]);pass[i]&=matches;
   if(!matches && information[i].isEmpty()) information[i]="Input: "+input+"\\nExpected: "+expected[i]+"\\nYour result: "+received[i];
  }
 } catch(Throwable e){for(int i=0;i<4;i++)pass[i]=false;}
 finally{System.setOut(saved);}
}
'''
    source += 'for(int i=0;i<4;i++) {saved.println("' + marker + ':"+i+":"+(pass[i]?"PASS":"FAIL")); if(!information[i].isEmpty()) saved.println("' + marker + ':"+i+":INFO:"+java.util.Base64.getEncoder().encodeToString(information[i].getBytes("UTF-8")));}\n}}'
    return source, prefix.count('\n')


def evidence(code, cases):
    """A passed behavior test is evidence, not a guarantee or official grade.

    Only grant reference points when the associated behavior and required API
    evidence are present. Failed checks leave partial credit for human review.
    """
    from tree_sitter import Language, Parser
    import tree_sitter_java
    prefix = 'class Student { void answer() {\n'
    source = (prefix + code + '\n}}').encode()
    root = Parser(Language(tree_sitter_java.language())).parse(source).root_node
    calls = {}; conditions = []; definitions = {}; direct_output = []
    def printed_literal(branch):
        if branch is None:return None
        if branch.type=='block':
            children=[n for n in branch.named_children if n.type not in ('line_comment','block_comment')]
            if len(children)!=1:return None
            branch=children[0]
        if branch.type!='expression_statement' or len(branch.named_children)!=1:return None
        invocation=branch.named_children[0]
        if invocation.type!='method_invocation':return None
        name=invocation.child_by_field_name('name');obj=invocation.child_by_field_name('object');args=invocation.child_by_field_name('arguments')
        if not name or not obj or not args or len(args.named_children)!=1:return None
        if source[name.start_byte:name.end_byte].decode() not in ('print','println') or source[obj.start_byte:obj.end_byte].decode()!='System.out':return None
        try:return json.loads(source[args.named_children[0].start_byte:args.named_children[0].end_byte].decode())
        except ValueError:return None
    stack = [root]
    while stack:
        item = stack.pop()
        if item.type == 'variable_declarator':
            name=item.child_by_field_name('name'); value=item.child_by_field_name('value')
            if name and value: definitions.setdefault(source[name.start_byte:name.end_byte].decode(),[]).append(value)
        if item.type == 'assignment_expression':
            name=item.child_by_field_name('left'); value=item.child_by_field_name('right')
            if name and name.type=='identifier' and value: definitions.setdefault(source[name.start_byte:name.end_byte].decode(),[]).append(value)
        if item.type == 'method_invocation':
            name = item.child_by_field_name('name')
            if name:
                calls.setdefault(source[name.start_byte:name.end_byte].decode(), []).append(max(1,item.start_point.row))
        if item.type in ('if_statement','ternary_expression'):
            condition = item.child_by_field_name('condition')
            if condition:
                identifiers = []; todo=[condition]
                while todo:
                    child=todo.pop()
                    if child.type=='identifier': identifiers.append(source[child.start_byte:child.end_byte].decode())
                    todo.extend(child.named_children)
                expression=re.sub(r'[\s()]','',source[condition.start_byte:condition.end_byte].decode())
                if sorted(expression.split('&&'))==sorted(('lengthGood','correctColors','startEndGood')):
                    conditions.append(max(1,item.start_point.row))
                    if item.type=='if_statement' and printed_literal(item.child_by_field_name('consequence'))=='Acceptable' and printed_literal(item.child_by_field_name('alternative'))=='Not acceptable':
                        direct_output.append(max(1,item.start_point.row))
        stack.extend(item.named_children)
    def dependencies(variable, wanted):
        found=[]; seen=set(); todo=list(definitions.get(variable,[]))
        while todo:
            item=todo.pop()
            if item.type=='method_invocation':
                name=item.child_by_field_name('name')
                obj=item.child_by_field_name('object')
                if name and obj and source[obj.start_byte:obj.end_byte].decode()=='beadSequence' and source[name.start_byte:name.end_byte].decode() in wanted:
                    found.append(max(1,item.start_point.row))
            if item.type=='identifier':
                name=source[item.start_byte:item.end_byte].decode()
                if name not in seen:
                    seen.add(name);todo.extend(definitions.get(name,[]))
            todo.extend(item.named_children)
        return found
    ok = [c['status']=='passed' for c in cases]
    rules = [('A',0,'长度取值与判断',dependencies('lengthGood',{'length'})),
             ('B',1,'检查 B 和 W',dependencies('correctColors',{'indexOf','contains'})),
             ('C',2,'首尾字符判断',dependencies('startEndGood',{'substring','charAt'})),
             ('D',3,'使用三个条件并输出',conditions)]
    labels = {'A': ('正确读取字符串长度','判断长度是否在 5–10 之间'),
              'B': ('检查 B 和 W 是否出现','正确设置 correctColors'),
              'C': ('取得首尾字符','正确设置 startEndGood'),
              'D': ('组合三个布尔条件','输出正确消息')}
    variables={'A':'lengthGood','B':'correctColors','C':'startEndGood'}
    rows=[]
    for part,index,label,lines in rules:
        for point in (1,2):
            # Conservative: alternative valid approaches stay pending, never zeroed.
            earned = ok[index] and bool(lines)
            if part=='A' and point==1 and lines:
                # Retrieving length can earn credit even when the later comparison is wrong.
                earned = True
            if part=='D' and point==1 and conditions:
                earned = True
            if part=='D' and point==2 and direct_output and len(calls.get('println',[])+calls.get('print',[]))==2:
                earned = True
            evidence_lines=lines if point==1 or part=='D' else [max(1,n.start_point.row) for n in definitions.get(variables[part],[])]
            rows.append(dict(id=f'Part {part} Point {point}',label=f'{part}{point} · {labels[part][point-1]}',points=1,
                             status='earned' if earned else 'unverified',lines=sorted(set(evidence_lines)),
                             reason='测试与代码结构提供了得分依据。' if earned else '测试或结构证据不足，部分分需要复核。'))
    return rows
