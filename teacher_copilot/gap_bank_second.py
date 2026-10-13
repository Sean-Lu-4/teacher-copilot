"""Round two: string algorithms and reading actual text-file fixtures."""
from .gap_bank import add


def string(id, level, minutes, title, code, task, answer, points, error, expected, **kwargs):
    add('GA_'+id,'2.10',level,minutes,title,code,task,answer,points,error,expected,**kwargs)


string('B1',2,5,'逐字符计数',
    'String s="banana"; int count=0;\nfor(int i=0;i<s.length();i++)\n if(s.substring(i,i+1).equals("a"))count++;\nSystem.out.print(count);',
    'List the matching indices, state the output, and explain why the loop uses i<s.length().',
    '匹配索引 1、3、5，输出 3；末次 i=5，子串右边界为 6，仍合法。',
    ['三个索引正确','计数正确','解释最后合法索引'],'把 length 当成可访问字符索引','3')
string('B2',2,5,'在前端拼接形成逆序',
    'String s="code", result="";\nfor(int i=0;i<s.length();i++)result=s.substring(i,i+1)+result;\nSystem.out.print(result);',
    'Show result after each iteration. State what changes if the new character is appended instead of prepended.',
    '依次 c、oc、doc、edoc，输出 edoc；改为末尾追加会保留 code 的顺序。',
    ['四个中间状态正确','逆序结果正确','解释拼接方向'],'忽略新字符放在结果的哪一端','edoc')
string('B3',2,5,'按条件过滤字符',
    'String s="a b  c", result="";\nfor(int i=0;i<s.length();i++){String ch=s.substring(i,i+1);if(!ch.equals(" "))result+=ch;}\nSystem.out.print(result);',
    'State the output, count the skipped spaces, and give the result for a string containing only spaces.',
    '输出 abc，跳过 3 个空格；全空格输入返回空字符串。',
    ['保留字符顺序','三个空格被跳过','全空格边界正确'],'将连续空格视为一个字符','abc')
string('B4',2,5,'按固定步长选取字符',
    'String s="abcdefg", result="";\nfor(int i=0;i<s.length();i+=2)result+=s.substring(i,i+1);\nSystem.out.print(result);',
    'List visited indices and state the output. What would starting i at 1 produce?',
    '访问 0、2、4、6，输出 aceg；从 1 开始得到 bdf。',
    ['索引序列正确','原输出正确','改变起点的结果正确'],'把步长二当作每次取两个字符','aceg')
string('B5',2,2,'空串循环执行次数',
    'String s="";int count=0;\nfor(int i=0;i<s.length();i++)count++;\nSystem.out.print(count);',
    'State the output and explain whether the loop body executes.',
    '输出 0，初始条件 0<0 为假，循环体不执行。',
    ['输出为零','解释初始条件'],'认为循环体至少执行一次','0')
string('A1',3,5,'允许重叠的子串计数',
    'String s="aaaa", key="aa";int count=0;\nfor(int i=0;i<=s.length()-key.length();i++)\n if(s.substring(i,i+key.length()).equals(key))count++;\nSystem.out.print(count);',
    'State the output and all matching start indices. Why is <= required? What happens if key is longer than s?',
    '输出 3，起点 0、1、2；<= 包含最后一个合法起点；key 更长时条件初始为假，得到 0。',
    ['三个重叠匹配','包含末合法起点','长目标边界正确'],'重叠匹配只计一次','3')
string('A2',3,5,'相邻相同关系与字符个数',
    'String s="aaabb";int pairs=0;\nfor(int i=1;i<s.length();i++)\n if(s.substring(i-1,i).equals(s.substring(i,i+1)))pairs++;\nSystem.out.print(pairs);',
    'List each matching adjacent pair of indices and state the output. Is this the number of repeated characters or of matching neighbor pairs?',
    '匹配 (0,1)、(1,2)、(3,4)，输出 3；统计的是相邻相等关系数。',
    ['列出三对索引','计数正确','准确解释统计对象'],'将长度三的重复段计成三对相邻关系','3')
string('A3',3,5,'压缩连续重复字符',
    'String s="aaabbcca", result="";\nfor(int i=0;i<s.length();i++)\n if(i==0||!s.substring(i,i+1).equals(s.substring(i-1,i)))result+=s.substring(i,i+1);\nSystem.out.print(result);',
    'State the output. Explain why the final a remains and why the i==0 test prevents an invalid substring call.',
    '输出 abca；只压缩相邻重复，末尾 a 开始新段；短路避免 i=0 时访问 -1。',
    ['输出正确','区分连续与全局去重','短路边界解释正确'],'误将算法理解为删除所有重复字符','abca')
string('A4',3,5,'对称位置比较',
    'String s="level";boolean same=true;\nfor(int i=0;i<s.length()/2;i++)\n if(!s.substring(i,i+1).equals(s.substring(s.length()-1-i,s.length()-i)))same=false;\nSystem.out.print(same);',
    'List compared index pairs, state the output, and explain why the middle character need not be compared.',
    '比较 (0,4)、(1,3)，输出 true；中间字符与自身相同，无需额外比较。',
    ['对称索引正确','结果正确','解释只检查前半'],'将对称位置写成 length-i','true')
string('A5',3,2,'遗漏最后一个字符的循环',
    'String s="cat",result="";\nfor(int i=0;i<s.length()-1;i++)result+=s.substring(i,i+1);\nSystem.out.print(result);',
    'State the output and repair the loop condition to copy the entire string.',
    '输出 ca；条件应为 i<s.length()。',
    ['识别遗漏末字符','修复上界'],'把最大索引直接用于严格小于条件','ca')


def algorithm(id,title,signature,task,answer,points,error,solution,body,expected,checks):
    string(id,4,5,title,signature+'\n// Inputs are non-null strings of ordinary ASCII characters.',
           task,answer,points,error,expected,solution=solution,body=body,checks=checks)


algorithm('E1','完成最长连续相同字符段','static int longestRun(String s){ /* complete */ }',
    'Return the length of the longest run of equal adjacent characters. Return 0 for an empty string. Use a loop.',
    '维护当前段长度和最大值；与前一个字符不同则重置为 1；空串循环不执行，返回 0。',
    ['相同字符延长当前段','不同字符重置','更新最大值并处理空串'],'只在段结束时更新而漏掉末段',
    'static int longestRun(String s){int run=0,best=0;for(int i=0;i<s.length();i++){if(i>0&&s.substring(i,i+1).equals(s.substring(i-1,i)))run++;else run=1;if(run>best)best=run;}return best;}',
    'System.out.print(longestRun("abbccc")+","+longestRun(""));','3,0',
    'if(longestRun("x")!=1||longestRun("aaaa")!=4||longestRun("aabbc")!=2)throw new AssertionError();')
algorithm('E2','循环删除指定字符','static String remove(String s,String key){ /* complete */ }',
    'key has length 1. Return s with every occurrence of key removed, preserving all other characters. Do not use replace methods.',
    '逐字符比较，不等于 key 时追加到结果。空串或全部匹配时结果为空。',
    ['逐字符访问','正确筛除指定字符','保留顺序与空串边界'],'删除时跳过相邻匹配字符',
    'static String remove(String s,String key){String result="";for(int i=0;i<s.length();i++){String ch=s.substring(i,i+1);if(!ch.equals(key))result+=ch;}return result;}',
    'System.out.print("["+remove("banana","a")+"]["+remove("aaa","a")+"]");','[bnn][]',
    'if(!remove("","x").equals("")||!remove("abc","z").equals("abc"))throw new AssertionError();')
algorithm('E3','统计不重叠出现次数','static int occurrences(String s,String key){ /* complete */ }',
    'key is nonempty. Count nonoverlapping matches from left to right. Advance past the entire key on a match, otherwise advance one position.',
    '成功则计数并前进 key.length()；失败仅前进 1。循环限定起点不超过 length-key.length()。',
    ['合法子串范围','匹配后跳过整个目标','失败前进一步'],'成功后只前进一步导致重叠计数',
    'static int occurrences(String s,String key){int i=0,count=0;while(i<=s.length()-key.length()){if(s.substring(i,i+key.length()).equals(key)){count++;i+=key.length();}else i++;}return count;}',
    'System.out.print(occurrences("aaaaa","aa")+","+occurrences("bananana","na"));','2,3',
    'if(occurrences("","a")!=0||occurrences("abc","abcd")!=0||occurrences("abc","z")!=0||occurrences("abc","abc")!=1)throw new AssertionError();')
algorithm('E4','返回首个相邻重复字符的位置','static int firstDouble(String s){ /* complete */ }',
    'Return the first index i where characters i and i+1 are equal, or -1. Handle strings of length 0 and 1.',
    '检查 i<length-1 的相邻字符，第一次相等立即返回 i；循环结束仍无匹配返回 -1。',
    ['访问两个合法相邻字符','首次匹配立即返回','缺失及短串返回 -1'],'返回后一个字符的索引',
    'static int firstDouble(String s){for(int i=0;i<s.length()-1;i++)if(s.substring(i,i+1).equals(s.substring(i+1,i+2)))return i;return -1;}',
    'System.out.print(firstDouble("abccdd")+","+firstDouble("abc"));','2,-1',
    'if(firstDouble("")!=-1||firstDouble("x")!=-1||firstDouble("aa")!=0||firstDouble("abb")!=1)throw new AssertionError();')
string('E5',4,2,'用反例区分包含和前缀',
    'String s="ababa",key="ba";\nSystem.out.print(s.indexOf(key)==0);',
    'A method uses this expression to test whether s contains key. State the output and give the corrected condition.',
    '输出 false，但 ba 在索引 1 存在。包含应判断 indexOf(key)>=0，==0 只检查前缀。',
    ['用当前输入反驳','给出包含条件'],'把位于开头等同于存在于任何位置','false')


def file_task(id,level,minutes,title,data,body,task,answer,points,error,expected,**kwargs):
    code='// input.txt contents: '+repr(data)+'\n// File exists; main declares throws Exception.\n'
    code+='java.util.Scanner in=new java.util.Scanner(new java.io.File("input.txt"));\n'+body+'\nin.close();'
    add('GF_'+id,'4.6',level,minutes,title,code,task,answer,points,error,expected,
        files={'input.txt':data},**kwargs)


file_task('B1',2,5,'从文件逐个读取整数','4 7 -2\n','int total=0;while(in.hasNextInt())total+=in.nextInt();System.out.print(total);',
    'List the consumed integers and running sums. State the output and explain what hasNextInt checks.',
    '读取 4、7、-2；累计 4、11、9；输出 9。hasNextInt 检查下一 token 是否能作为 int 读取。',
    ['读取次序正确','累计与输出正确','区分检查与消费'],'以为 hasNextInt 已经消费整数','9')
file_task('B2',2,5,'空行也属于文件中的一行','red\n\nblue\n','int count=0;while(in.hasNextLine()){in.nextLine();count++;}System.out.print(count);',
    'List the strings returned by nextLine and state the count. Does the blank line count? Does the final newline create a fourth line?',
    '返回 red、空字符串、blue，共 3 行；空行计入，最后换行后没有第四个可读取行。',
    ['三个返回值正确','空行计入','不虚构末尾额外行'],'将空行直接跳过','3')
file_task('B3',2,5,'按空白分隔词元','red  blue\ngreen\n','int count=0;String first=in.next();while(in.hasNext()){in.next();count++;}System.out.print(first+","+count);',
    'State the output. How many tokens are consumed in total? Explain why two spaces do not produce an empty token.',
    '输出 red,2；总共消费 3 个 token，默认分隔符会跨过连续空白。',
    ['首词正确','剩余与总数区分','解释空白分隔'],'以为每个空格都会产生空 token','red,2')
file_task('B4',2,5,'空文件不会执行读取循环','', 'int sum=0,count=0;while(in.hasNextInt()){sum+=in.nextInt();count++;}System.out.print(sum+","+count);',
    'State the output. Explain why nextInt is never called and why computing sum/count afterward would fail.',
    '输出 0,0；初始检查失败，不读取。整数 sum/count 会除以零。',
    ['初始化结果正确','空文件不读取','识别除零风险'],'认为空文件包含一个零','0,0')
file_task('B5',2,2,'先检查再读取','8', 'System.out.print(in.hasNextInt()+","+in.nextInt()+","+in.hasNextInt());',
    'State the output. Does the first hasNextInt call consume 8?',
    '输出 true,8,false；检查不消费，nextInt 才读取 8。',
    ['三项结果正确','检查不消费'],'把查询当成读取','true,8,false')
file_task('A1',3,5,'读取数字后的行尾内容','12\nAda Lovelace\n',
    'int n=in.nextInt();String a=in.nextLine();String b=in.nextLine();System.out.print(n+"|"+a+"|"+b);',
    'State the output and explain both nextLine results. How would you read the number and then the name into a single name variable?',
    '输出 12||Ada Lovelace；第一行剩余内容为空。读完数字后先 nextLine 消耗该行余部，再 nextLine 读姓名。',
    ['输出正确','解释残留行尾','给出读取姓名顺序'],'以为 nextInt 同时读完整行','12||Ada Lovelace')
file_task('A2',3,5,'非整数使整数循环停止','3 x 5',
    'int total=0;while(in.hasNextInt())total+=in.nextInt();System.out.print(total+","+in.next());',
    'State the output. Is 5 processed? Explain why hasNextInt does not skip x automatically.',
    '输出 3,x；遇到 x 停止，5 未处理。检查只针对下一个 token，不会自动跳过无效项。',
    ['总和正确','指出未消费 x','解释未处理后续数字'],'认为 hasNextInt 会寻找下一个整数','3,x')
file_task('A3',3,5,'过滤后计数求平均','-2 4 0 8',
    'int sum=0,count=0;while(in.hasNextInt()){int n=in.nextInt();if(n>0){sum+=n;count++;}}System.out.print(sum+","+count+","+((double)sum/count));',
    'State the output, list included values, and explain why dividing by the total number of file tokens would be wrong.',
    '输出 12,2,6.0；只包含 4、8，分母应是符合筛选条件的 2 个值。',
    ['正确过滤','总和与数量正确','使用筛选后的分母'],'用全部记录数作筛选平均值分母','12,2,6.0')
file_task('A4',3,5,'哨兵读取后的文件位置','5 7 -1 9',
    'int sum=0;boolean stop=false;while(in.hasNextInt()&&!stop){int n=in.nextInt();if(n==-1)stop=true;else sum+=n;}System.out.print(sum+","+in.nextInt());',
    'State the output. Is the sentinel added? Which token remains after the loop?',
    '输出 12,9；-1 已读取但不累加，9 留在输入中。',
    ['总和正确','哨兵不计入','准确跟踪剩余 token'],'将哨兵或哨兵后的数也累加','12,9')
file_task('A5',3,2,'不可忽略的空白行内容','  \n',
    'String line=in.nextLine();System.out.print(line.length()+","+in.hasNextLine());',
    'State the output. Is a line containing two spaces an empty string?',
    '输出 2,false；两个空格是两个字符，不能视为空字符串。',
    ['行长度正确','文件结束检查正确'],'将空白内容当作零长度','2,false')


def file_method(id,title,data,signature,task,answer,points,error,solution,body,expected,checks):
    opening='java.util.Scanner in=new java.util.Scanner(new java.io.File("input.txt"));\n'
    add('GF_'+id,'4.6',4,5,title,
        signature+'\n// in scans an existing text file; the caller owns and closes it.\n// Test file input.txt: '+repr(data),
        task,answer,points,error,expected,solution=solution,body=opening+body+'\nin.close();',
        checks=checks,files={'input.txt':data})


file_method('E1','跳过无效词元继续求和','4 x -2 y 7','static int sumInts(java.util.Scanner in){ /* complete */ }',
    'Consume all tokens. Sum tokens accepted by hasNextInt and skip each other token with next. Assume the sum fits int.',
    '用 hasNext 控制整体循环；整数用 nextInt 累加，其他 token 用 next 消费，保证每轮前进。',
    ['遍历所有 token','区分整数与其他 token','每轮消费避免死循环'],'遇到无效 token 时不消费导致无限循环',
    'static int sumInts(java.util.Scanner in){int sum=0;while(in.hasNext()){if(in.hasNextInt())sum+=in.nextInt();else in.next();}return sum;}',
    'System.out.print(sumInts(in));','9',
    'if(sumInts(new java.util.Scanner(""))!=0||sumInts(new java.util.Scanner("x y"))!=0||sumInts(new java.util.Scanner("-4 4"))!=0)throw new AssertionError();')
file_method('E2','找文件中最长的一行','cat\n\nmouse\nhorse\n','static String longestLine(java.util.Scanner in){ /* complete */ }',
    'Return the longest line, including spaces in its length. Keep the first on ties. Return "" for an empty file.',
    '初始 best 为空串；逐行读取，仅在长度严格更大时更新。相等不更新以保留首次。',
    ['逐行读取含空行','按长度严格比较','首次并列与空文件正确'],'相等时更新导致返回最后一条并列行',
    'static String longestLine(java.util.Scanner in){String best="";while(in.hasNextLine()){String line=in.nextLine();if(line.length()>best.length())best=line;}return best;}',
    'System.out.print(longestLine(in));','mouse',
    r'if(!longestLine(new java.util.Scanner("")).equals("")||!longestLine(new java.util.Scanner("a b\nxx")).equals("a b")||!longestLine(new java.util.Scanner("aa\nbb")).equals("aa"))throw new AssertionError();')
file_method('E3','统计相邻读数上升次数','2 5 5 1 4','static int rises(java.util.Scanner in){ /* complete */ }',
    'The file contains only int tokens. Count adjacent pairs where the later value is strictly greater. Return 0 for fewer than two values.',
    '先检查并读取首值；后续每次与 previous 比较，再更新 previous；相等不增加。',
    ['安全初始化首值','严格大于时计数','每轮更新前值'],'只与第一个值比较而没有更新 previous',
    'static int rises(java.util.Scanner in){if(!in.hasNextInt())return 0;int previous=in.nextInt(),count=0;while(in.hasNextInt()){int n=in.nextInt();if(n>previous)count++;previous=n;}return count;}',
    'System.out.print(rises(in));','2',
    'if(rises(new java.util.Scanner(""))!=0||rises(new java.util.Scanner("8"))!=0||rises(new java.util.Scanner("4 4 3"))!=0||rises(new java.util.Scanner("1 2 3"))!=2)throw new AssertionError();')
file_method('E4','逐行筛选并保持原顺序','Amy\nBo\nCara\n\n','static String selectLines(java.util.Scanner in,int min){ /* complete */ }',
    'min>=1. Return lines whose lengths are at least min, joined by commas with no leading or trailing comma. Return "" if none qualify.',
    '逐行筛选，非空结果追加逗号后再加新行；min>=1 保证被选行非空。',
    ['正确筛选含等号边界','保留顺序','正确处理逗号和无匹配'],'每条记录后都加逗号造成尾部逗号',
    'static String selectLines(java.util.Scanner in,int min){String result="";while(in.hasNextLine()){String line=in.nextLine();if(line.length()>=min){if(!result.equals(""))result+=",";result+=line;}}return result;}',
    'System.out.print(selectLines(in,3));','Amy,Cara',
    r'if(!selectLines(new java.util.Scanner(""),1).equals("")||!selectLines(new java.util.Scanner("a\nb"),2).equals("")||!selectLines(new java.util.Scanner("ab"),2).equals("ab"))throw new AssertionError();')
file_task('E5',4,2,'两次读取漏掉记录','2 4 6 8',
    'int sum=0;while(in.hasNextInt()){in.nextInt();sum+=in.nextInt();}System.out.print(sum);',
    'State the output. Explain why this does not sum every value, and what happens with an odd number of integers.',
    '输出 12，只累加 4 和 8，前一个读取丢掉 2 和 6；奇数个时末轮第二次 nextInt 没有值会抛出异常。',
    ['指出每轮丢弃一项','正确输出','识别奇数数量的越界读取'],'一次 hasNextInt 就能保证两次读取安全','12')
