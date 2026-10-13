"""Targeted Math/String expansion. Estimated timings require classroom trials."""
VERSION = 'gap-bank-20261008-v2'
QUESTIONS = []
FIXTURES = []


def add(id, topic, level, minutes, title, code, task, answer, points, error,
        expected, *, solution='', body=None, checks='', files=None):
    QUESTIONS.append(dict(id=id, ced_topics=[topic], objectives=['ced_'+topic.replace('.','_')],
        level=level, minutes=minutes, title=title, code=code, task=task, answer=answer,
        origin='原创补充题；考试风格非真题', reasoning=points, errors=[error],
        rubric='；'.join(p+'（1 分）' for p in points)+f'。共 {len(points)} 分；等价正确答案同样给分。',
        intervention='让学生先解释“'+error+'”为什么不成立，再用题目中的边界输入核对。',
        prerequisites={'1.11':'已学习 Math 常用方法与数值转换。','1.15':'已学习 String 方法、索引与不可变性。',
                       '2.10':'已学习循环、条件判断和 String 方法。','4.6':'已学习 Scanner 与 File；假设文件存在，所需异常由调用方声明或处理。'}[topic],
        question_kind='write' if solution else 'trace', verification_mode='java_fixture',
        **({'reference_solution':solution} if solution else {})))
    FIXTURES.append(dict(id=id, members=solution, body=code if body is None else body,
                         solution='', checks=checks, expected=expected, files=files or {}))


add('GM_B1','1.11',2,5,'数轴距离与方向',
    'int start=-4, end=7;\nSystem.out.print((end-start)+","+Math.abs(start-end));',
    'State both outputs. Explain why distance is nonnegative. Give both results when start and end are exchanged.',
    '输出 11,11；交换后为 -11,11。位移带方向，距离取差的绝对值。',
    ['计算原结果','计算交换后结果','区分位移与距离'],'把有向差和距离混为一谈','11,11')
add('GM_B2','1.11',2,5,'平方与平方根的返回类型',
    'double a=Math.pow(3,2);\ndouble b=Math.sqrt(49);\nSystem.out.print(a+","+b+","+(a+b));',
    'State the output, identify the return types, and give a Java expression for the side length of a square of area 81.',
    '输出 9.0,7.0,16.0；两个方法都返回 double；边长表达式 Math.sqrt(81)，结果 9.0。',
    ['正确输出','两个返回类型都是 double','面积开平方得到边长'],'把整数参数误认为整数返回类型','9.0,7.0,16.0')
add('GM_B3','1.11',2,5,'先开方再转换',
    'double root=Math.sqrt(20);\nint whole=(int)root;\nSystem.out.print(whole+","+(whole*whole<=20));',
    'State the output. Between which two consecutive integers is root? Explain whether the cast rounds to the nearest integer.',
    '输出 4,true；root 在 4 和 5 之间。转换为 int 截去小数，不是四舍五入。',
    ['输出正确','平方比较定位区间','解释截断'],'把强制转换当作四舍五入','4,true')
add('GM_B4','1.11',2,5,'随机整数公式的边界',
    'double r=0.0;\nint first=(int)(r*6)+1;\nr=0.999;\nint second=(int)(r*6)+1;\nSystem.out.print(first+","+second);',
    'State the output. If r is replaced by Math.random(), list all possible integer results and explain why 7 is impossible.',
    '输出 1,6；可能为 1 至 6。r 小于 1，r*6 小于 6，截断后最大为 5，再加 1 最大为 6。',
    ['两次输出正确','列出闭区间 1 至 6','解释上界排除'],'把 Math.random 的上界 1 当成可取值','1,6')
add('GM_B5','1.11',2,2,'幂与乘法不是同一运算',
    'System.out.print(Math.pow(2,3)+","+(2*3));',
    'State the output and explain the difference between the two operations.',
    '输出 8.0,6；前者计算 2 的三次方，后者是乘积。',
    ['幂结果正确','区分幂与乘积'],'把第二个参数当成乘数','8.0,6')

add('GM_A1','1.11',3,5,'绝对值与截断顺序',
    'double x=-3.8;\nSystem.out.print(Math.abs((int)x)+","+(int)Math.abs(x)+","+(int)(x+0.5));',
    'State the output. Explain each conversion and why adding 0.5 then casting is unsuitable for rounding all negative values.',
    '输出 3,3,-3；int 转换朝零截断。-3.8+0.5=-3.3，截断为 -3，而最近整数是 -4。',
    ['跟踪三项结果','说明朝零截断','用 -3.8 反驳通用舍入说法'],'把朝零截断当作向下取整','3,3,-3')
add('GM_A2','1.11',3,5,'勾股公式中的括号',
    'int x=3,y=4;\nSystem.out.print(Math.sqrt(x*x+y*y)+","+(Math.sqrt(x*x)+y*y));',
    'State the output. Which expression gives the distance from the origin? Explain what the other expression computes.',
    '输出 5.0,19.0；第一项是两平方和的平方根；第二项只对 x*x 开方，再加 y*y。',
    ['两个数值正确','选择正确距离公式','解释开方范围'],'认为括号位置不影响开方范围','5.0,19.0')
add('GM_A3','1.11',3,5,'随机区间的宽度和偏移',
    'double r=0.75;\nint a=(int)(r*8)-3;\nint b=(int)(r*7)-3;\nSystem.out.print(a+","+b);',
    'State the output. For 0 <= r < 1, give each integer range. Which formula can generate every integer from -3 through 4?',
    '输出 3,2；a 范围 -3 至 4，b 范围 -3 至 3。应使用宽度为 8 的 a 公式。',
    ['计算给定输入','确定两个范围','包含两端时宽度为 8'],'把端点差当作整数个数','3,2')
add('GM_A4','1.11',3,5,'平方前转换防止整数溢出',
    'int n=50000;\nSystem.out.print(n*n+","+((double)n*n));',
    'State the output. Explain why converting after n*n cannot repair the result. Give a safe expression for this input.',
    '输出 -1794967296,2.5E9。int 乘法已溢出后再转换不能恢复结果；先转一个操作数，如 (double)n*n。',
    ['识别 int 溢出与输出','说明转换过晚无效','给出先转换的表达式'],'以为给 double 变量赋值能避免右侧 int 溢出','-1794967296,2.5E9')
add('GM_A5','1.11',3,2,'随机公式中过早的强制转换',
    'double r=0.84;\nSystem.out.print((int)r*10+","+(int)(r*10));',
    'State the output. Which expression can vary from 0 through 9 when r comes from Math.random()?',
    '输出 0,8；第二项可为 0 至 9，第一项先将 r 转为 0。',
    ['输出正确','指出转换必须在乘法之后'],'忽略转换运算的结合范围','0,8')

add('GM_E1','1.11',4,5,'编写闭区间映射方法',
    'static int map(double r, int low, int high) { /* complete */ }\n// 0 <= r < 1; -100 <= low <= high <= 100.',
    'Return the integer obtained by mapping r into the inclusive range low..high. Use scaling and a cast. Explain the low==high case.',
    '宽度为 high-low+1，先乘再截断再加 low；low==high 时宽度为 1，总是返回 low。',
    ['包含两个端点的宽度','先乘再截断','正确偏移及单值区间'],'漏掉闭区间宽度中的加一','-2,3,7',
    solution='static int map(double r,int low,int high){return (int)(r*(high-low+1))+low;}',
    body='System.out.print(map(0,-2,3)+","+map(0.999,-2,3)+","+map(0.5,7,7));',
    checks='for(int k=0;k<1000;k++){int v=map(k/1000.0,-2,3);if(v< -2||v>3)throw new AssertionError();}')
add('GM_E2','1.11',4,5,'完成点间距离方法',
    'static double distance(int x1,int y1,int x2,int y2){ /* complete */ }\n// Each coordinate is between -100000 and 100000.',
    'Return the Euclidean distance. Avoid int overflow when squaring differences. Use Math.sqrt; explain when conversion must occur.',
    '差值先保存为 double，再平方相加开方。仅在整个整数平方表达式之后转换仍可能溢出。',
    ['两个坐标差正确','平方前使用 double','平方和开方'],'在溢出的平方之后才转换','5.0,200000.0',
    solution='static double distance(int x1,int y1,int x2,int y2){double dx=(double)x2-x1,dy=(double)y2-y1;return Math.sqrt(dx*dx+dy*dy);}',
    body='System.out.print(distance(0,0,3,4)+","+distance(-100000,0,100000,0));',
    checks='if(distance(2,-3,2,-3)!=0||distance(3,4,0,0)!=5)throw new AssertionError();')
add('GM_E3','1.11',4,5,'从平方根构造向上整数界',
    'static int ceilingRoot(int n){ /* complete */ }\n// 0 <= n <= 1000000.',
    'Return the smallest nonnegative integer k with k*k >= n. Use Math.sqrt and a conditional adjustment, without a loop. Test a square and a nonsquare.',
    '先令 k=(int)Math.sqrt(n)；若 k*k<n 则加 1。平方数保持不变，非平方数向上补一。',
    ['得到截断平方根','仅在平方不足时加一','处理零与完全平方数'],'无条件加一导致平方数错误','0,4,5',
    solution='static int ceilingRoot(int n){int k=(int)Math.sqrt(n);if(k*k<n)k++;return k;}',
    body='System.out.print(ceilingRoot(0)+","+ceilingRoot(16)+","+ceilingRoot(17));',
    checks='for(int n=0;n<=1000000;n++){int k=ceilingRoot(n);if(k*k<n||(k>0&&(k-1)*(k-1)>=n))throw new AssertionError();}')
add('GM_E4','1.11',4,5,'按距离判定允许误差',
    'static boolean close(double actual,double target,double tolerance){ /* complete */ }\n// Finite inputs between -1000 and 1000; 0 <= tolerance <= 1000.',
    'Return true exactly when actual is within tolerance of target, including the boundary. Explain why testing only actual-target<=tolerance fails.',
    '应比较 Math.abs(actual-target)<=tolerance。单向比较会把远小于目标的数也误判为接近。',
    ['使用绝对差','包含误差边界','解释单向条件反例'],'只检查一侧误差','true,false,true',
    solution='static boolean close(double actual,double target,double tolerance){return Math.abs(actual-target)<=tolerance;}',
    body='System.out.print(close(8,10,2)+","+close(0,10,2)+","+close(12,10,2));',
    checks='if(!close(3,3,0)||close(3,4,0))throw new AssertionError();')
add('GM_E5','1.11',4,2,'辨别平方根恒等式的符号',
    'int x=-6;\nSystem.out.print(Math.sqrt(x*x));',
    'State the output. For integer x from -100 through 100, is sqrt(x*x) always x? State a correct identity.',
    '输出 6.0；负数时不是 x，而是 Math.abs(x) 对应的非负数值。',
    ['正确输出','用绝对值修正恒等式'],'忽略平方根返回非负主值','6.0')

add('GS_B1','1.15',2,5,'子串的包含和排除边界',
    'String s="planet";\nSystem.out.print(s.substring(1,4)+","+s.substring(4));',
    'State the output. List the indices included in the first substring and give an expression for the final character as a String.',
    '输出 lan,et；首个子串取索引 1、2、3；末字符可用 s.substring(s.length()-1)。',
    ['两个子串正确','解释右端索引排除','构造末字符表达式'],'将子串的结束索引也包括在内','lan,et')
add('GS_B2','1.15',2,5,'查找成功与查找失败',
    'String s="banana";\nSystem.out.print(s.indexOf("na")+","+s.indexOf("x")+","+s.indexOf("ba"));',
    'State the output. Explain each value and why index 0 must not be treated as failure.',
    '输出 2,-1,0；分别为首次匹配位置、不存在、开头匹配。失败标志是 -1。',
    ['首次匹配索引正确','失败为 -1','零代表有效匹配'],'用大于零判断是否找到','2,-1,0')
add('GS_B3','1.15',2,5,'字符串内容与大小写',
    'String a="Java",b="java";\nSystem.out.print(a.equals(b)+","+a.equals("Ja"+"va"));',
    'State the output. Explain case sensitivity and give an equals call that checks whether b has content "java".',
    '输出 false,true；equals 区分大小写，比较内容；可用 b.equals("java")。',
    ['两次比较正确','说明区分大小写','给出内容比较表达式'],'以为 equals 忽略大小写','false,true')
add('GS_B4','1.15',2,5,'字符串操作不改变原变量',
    'String s="hello";\ns.substring(1);\nString t=s.substring(1);\nSystem.out.print(s+","+t);',
    'State the output. Explain why the standalone call does not shorten s. Write one assignment that would update s.',
    '输出 hello,ello；String 不可变，substring 返回新结果；需要 s=s.substring(1)。',
    ['保留原字符串','跟踪返回的新字符串','显式赋值更新变量'],'以为调用 substring 会原地删除字符','hello,ello')
add('GS_B5','1.15',2,2,'空字符串与一个空格',
    'System.out.print("".length()+","+" ".length());',
    'State the output and explain why the lengths differ.',
    '输出 0,1；空字符串无字符，一个空格仍是一个字符。',
    ['空字符串长度为零','空格也占一个字符'],'把不可见空格当作没有字符','0,1')

add('GS_A1','1.15',3,5,'在后缀中查找的相对索引',
    'String s="bananas";\nString tail=s.substring(3);\nint p=tail.indexOf("na");\nSystem.out.print(tail+","+p+","+(p+3));',
    'State the output. Explain how to convert the found suffix index into an index in s, and why the conversion must not be applied to -1.',
    '输出 anas,1,4；后缀从原索引 3 开始，所以成功索引加 3；失败 -1 不是字符位置，必须先检查。',
    ['后缀与查找结果正确','成功索引加偏移','失败不作偏移换算'],'混淆子串坐标与原串坐标','anas,1,4')
add('GS_A2','1.15',3,5,'拼接表达式的左结合',
    'String a=2+3+"x";\nString b="x"+2+3;\nSystem.out.print(a+","+b);',
    'State the output. Explain the change from numeric addition to concatenation. Rewrite b\'s expression to produce "x5".',
    '输出 5x,x23；从左到右，遇到字符串后为拼接；改成 "x"+(2+3)。',
    ['两结果正确','解释求值与类型变化','使用括号先加数字'],'把包含字符串的所有加号都当数字加法','5x,x23')
add('GS_A3','1.15',3,5,'按字典顺序比较前缀',
    'String a="car",b="cart",c="cat";\nSystem.out.print((a.compareTo(b)<0)+","+(b.compareTo(c)<0));',
    'State the output. Explain the prefix rule and the first differing character. Does compareTo always return only -1, 0, or 1?',
    '输出 true,true；相同前缀下短串在前；cart 与 cat 首个不同字符是 r 和 t。compareTo 可返回其他负数或正数，只应依赖符号。',
    ['前缀比较正确','定位首个差异','只依赖返回值符号'],'认为 compareTo 只能返回 -1 或 1','true,true')
add('GS_A4','1.15',3,5,'交换两个子串',
    'String s="abcdefg";\nint mid=s.length()/2;\nString result=s.substring(mid)+s.substring(0,mid);\nSystem.out.print(mid+","+result);',
    'State the output. For odd length, which piece contains the extra character? Give the result for s="ab".',
    '输出 3,defgabc；长度整除得到左侧 3、右侧 4，额外字符在右侧；ab 得 ba。',
    ['分割位置正确','拼接顺序正确','奇数与短串边界正确'],'认为两个子串总是等长','3,defgabc')
add('GS_A5','1.15',3,2,'允许位于末尾的空子串',
    'String s="abc";\nSystem.out.print("["+s.substring(s.length())+"]");',
    'State the output. Is the index s.length() valid for this substring call?',
    '输出 []；substring(length) 返回空字符串，这个开始索引合法。',
    ['空串输出正确','区分取字符索引与子串边界'],'认为任何等于 length 的索引都非法','[]')

add('GS_E1','1.15',4,5,'安全取得分隔符之前的内容',
    'static String before(String s,String marker){ /* complete */ }\n// s is non-null; marker is non-null and nonempty.',
    'Return the part of s before its first marker. If absent, return s unchanged. Handle a marker at index 0.',
    '查找首次索引；小于 0 返回 s，否则返回 substring(0,p)。开头匹配时返回空串。',
    ['首次查找','无匹配时保留原串','正确处理索引零'],'未经检查将 -1 传给 substring','[ab][abc][]',
    solution='static String before(String s,String marker){int p=s.indexOf(marker);if(p<0)return s;return s.substring(0,p);}',
    body='System.out.print("["+before("ab:cd:ef",":")+"]["+before("abc",":")+"]["+before(":x",":")+"]");',
    checks='if(!before("","x").equals("")||!before("a--b","--").equals("a"))throw new AssertionError();')
add('GS_E2','1.15',4,5,'替换第一次出现的目标',
    'static String replaceFirst(String s,String key,String value){ /* complete */ }\n// All arguments are non-null; key is nonempty.',
    'Use indexOf, substring and concatenation to replace only the first occurrence of key by value. If key is absent, return s. Do not call replace methods.',
    '首次位置 p；找不到返回原串，否则拼接 s.substring(0,p)+value+s.substring(p+key.length())。',
    ['找到首次匹配且处理缺失','保留正确前缀','跳过完整 key 并保留后缀'],'只跳过 key 的首个字符','bXna,abc',
    solution='static String replaceFirst(String s,String key,String value){int p=s.indexOf(key);if(p<0)return s;return s.substring(0,p)+value+s.substring(p+key.length());}',
    body='System.out.print(replaceFirst("banana","ana","X")+","+replaceFirst("abc","z","X"));',
    checks='if(!replaceFirst("abc","abc","").equals("")||!replaceFirst("abc","bc","!").equals("a!")||!replaceFirst("","a","!").equals(""))throw new AssertionError();')
add('GS_E3','1.15',4,5,'比较首尾指定长度的内容',
    'static boolean matchingEnds(String s,int k){ /* complete */ }\n// s is non-null; 0 <= k <= s.length().',
    'Return whether the first k characters equal the last k characters. Overlap is allowed. Explain the result when k is 0 or s.length().',
    '比较 substring(0,k) 与 substring(length-k) 的 equals；k=0 比较两个空串，k=length 比较整个串与自身，都为 true。',
    ['正确构造两个子串','使用 equals 比较内容','两个边界均正确'],'用 == 代替字符串内容比较','true,false,true',
    solution='static boolean matchingEnds(String s,int k){return s.substring(0,k).equals(s.substring(s.length()-k));}',
    body='System.out.print(matchingEnds("ababa",3)+","+matchingEnds("abcd",2)+","+matchingEnds("abc",0));',
    checks='if(!matchingEnds("abc",3)||!matchingEnds("",0))throw new AssertionError();')
add('GS_E4','1.15',4,5,'返回第二次不重叠匹配的位置',
    'static int second(String s,String key){ /* complete */ }\n// s is non-null; key is non-null and nonempty.',
    'Return the original-string index of the second nonoverlapping occurrence of key, or -1. Use a suffix search after the entire first match.',
    '找首个 p；不存在返回 -1。令 start=p+key.length()，在 substring(start) 中找 q；q 不存在返回 -1，否则返回 start+q。',
    ['跳过完整第一次匹配','两次缺失判断','换算为原字符串索引'],'把相对后缀索引直接作为答案','2,-1,4',
    solution='static int second(String s,String key){int p=s.indexOf(key);if(p<0)return -1;int start=p+key.length();int q=s.substring(start).indexOf(key);return q<0?-1:start+q;}',
    body='System.out.print(second("aaaa","aa")+","+second("aaa","aa")+","+second("abXabX","bX"));',
    checks='if(second("","x")!=-1||second("ab","ab")!=-1||second("abc","z")!=-1)throw new AssertionError();')
add('GS_E5','1.15',4,2,'字符串边界合约的反例',
    'String s="a";\nSystem.out.print("["+s.substring(1,s.length())+"]");',
    'State the output. A claim says this expression removes both the first and last characters for every nonempty s. Give a counterexample.',
    '输出 []；s="abc" 时表达式得到 bc，仍保留末字符 c，因此并未删除两端。',
    ['单字符结果正确','给出反例并解释保留末字符'],'从单一短串测试推断一般结论','[]')

from . import gap_bank_second  # noqa: E402,F401
