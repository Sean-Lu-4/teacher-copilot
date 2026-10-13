from . import q

q('2.1','B','选择还是重复', 'Task A: choose a discount based on age.\nTask B: print all integers from 1 through n.',
  'Which task primarily needs selection and which needs repetition? Explain the difference.', 'A 需要条件选择；B 需要重复执行。选择决定执行哪条路径，循环多次执行一组步骤。',
  ['正确对应两个任务','区分选择和重复'], '把重复次数当成分支数量', kind='concept')
q('2.1','A','循环中的选择', 'int count=0;\nfor(int n=1;n<=6;n++){\n    if(n%2==0) count++;\n}\nSystem.out.print(count);',
  'State the output. Describe the algorithm in one sentence without restating each line.', '输出 3；算法统计 1 到 6 内的偶数个数。', ['区分循环范围和筛选条件','总结计数目标'], '每次循环都增加 count', expected='3')
q('2.1','E','给算法选择测试', 'Algorithm: start count at 0; inspect every input value; increase count only when value > 0; return count.',
  'Design tests for no inputs, all nonpositive inputs, and mixed inputs. Explain why replacing > 0 with >= 0 changes the requirement.',
  '空输入应为 0；[-2,0,-1] 应为 0；[-1,3,0,2] 应为 2。>=0 会把零错误地计入正数。',
  ['覆盖空输入','覆盖零与负数','混合输入的期望值正确'], '没有测试恰好等于零的输入', kind='concept')

q('2.2','B','比较表达式的真值', 'int a=5,b=5;\nSystem.out.print((a<b)+","+(a==b)+","+(a!=b));',
  'State the output and explain each comparison.', '输出 false,true,false。a 与 b 相等。', ['三个真值正确','区分相等与不等'], '把 == 当作赋值', expected='false,true,false')
q('2.2','A','浮点计算后的比较', 'double x=0.1+0.2;\nSystem.out.print(x==0.3);',
  'State the output. Explain why a small tolerance can be useful when comparing calculated double values.', '输出 false。二进制浮点表示存在舍入，计算值不一定与十进制写出的值完全相同；可按题目精度用 Math.abs(x-0.3)<1e-9。',
  ['认识浮点舍入','解释容差用途'], '所有数学上相等的 double 都能用 == 判真', expected='false', checks='if(!(Math.abs(x-0.3)<1e-9))throw new AssertionError();')
q('2.2','E','null 安全的内容比较', 'String s=null;\n// Candidate I: s.equals("yes")\n// Candidate II: "yes".equals(s)',
  'Which candidate can be evaluated safely for null s? State its result. Give a safe condition that also works for "yes" and "no".',
  'II 安全且为 false；I 的接收者为 null，会异常。可直接用 "yes".equals(s)，或 s != null && s.equals("yes")。',
  ['区分调用接收者','给出 null 时结果','给出安全且正确的条件'], '只考虑参数是否为空而忽略接收者', expected='false', body='String s=null;System.out.print("yes".equals(s));', checks='if(!"yes".equals("yes")||"yes".equals("no"))throw new AssertionError();boolean thrown=false;try{s.equals("yes");}catch(NullPointerException e){thrown=true;}if(!thrown)throw new AssertionError();')

q('2.3','B','二选一分支', 'int score=72;\nif(score>=60) System.out.print("pass");\nelse System.out.print("retry");', 'State the output and whether the else branch executes.', '输出 pass，else 不执行。', ['判断条件为真','只执行一个分支'], '两个分支都执行', expected='pass')
q('2.3','A','分支顺序的重要性', 'int n=12;\nif(n>5) System.out.print("small");\nelse if(n>10) System.out.print("large");',
  'State the output. Reorder the tests so values above 10 print large and values from 6 through 10 print small.', '原输出 small；应先测 n>10，再 else if(n>5)。',
  ['指出首个真条件决定路径','用较严格条件优先修正'], '后续分支会覆盖早先输出', expected='small')
q('2.3','E','编写有边界的分段函数', 'static int delivery(int units) { /* complete */ }\n// Precondition: units >= 0.\n// Zero units cost 0; 1..5 units cost 4; each unit beyond 5 adds 2.',
  'Complete delivery. Give the results for 0, 1, 5, and 6.', '四个结果为 0、4、4、6。先处理零，再区分不超过 5 和超出部分。',
  ['零值单独处理','1..5 的费用正确','超出部分按 units-5 计算'], '对零也收取起步费或多算一件', kind='write',
  solution='static int delivery(int units){\n    if(units==0) return 0;\n    if(units<=5) return 4;\n    return 4+(units-5)*2;\n}', members='{{solution}}', body='System.out.print(delivery(0)+","+delivery(1)+","+delivery(5)+","+delivery(6));', expected='0,4,4,6', checks='for(int n=0;n<=100;n++){int expected=n==0?0:4;for(int i=6;i<=n;i++)expected+=2;if(delivery(n)!=expected)throw new AssertionError();}')

q('2.4','B','内层条件只在进入后判断', 'int a=-1,b=8;\nif(a>0){\n    if(b>5)System.out.print("X");\n    else System.out.print("Y");\n}else System.out.print("Z");', 'State the output and whether b>5 is evaluated.', '输出 Z；外层为 false，内层条件不求值。', ['外层条件正确','说明跳过内层'], '所有 if 的条件都会求值', expected='Z')
q('2.4','A','else 的最近匹配', 'int x=1,y=0;\nif(x>0)\n    if(y>0) System.out.print("A");\n    else System.out.print("B");',
  'State the output and add braces to show the same structure.', '输出 B；等价于 if(x>0){if(y>0){打印 A;}else{打印 B;}}。else 属于内层 if。',
  ['正确匹配 else','用括号说明嵌套关系'], '根据缩进猜 else 属于谁', expected='B')
q('2.4','E','嵌套规则变成互斥分支', 'static int charge(boolean member, int age){\n if(member){if(age<18)return 3;else return 5;}\n else{if(age<18)return 6;else return 8;}\n}',
  'Rewrite charge as one if/else-if/else chain without nested if statements. Preserve behavior at age 18.',
  '先判断 member && age<18；再判断 member；再判断 age<18；最后返回 8。18 岁进入对应的成年分支。',
  ['四种组合均覆盖','条件顺序保持互斥','18 岁边界正确'], '把 age<18 改成 <=18', kind='write',
  solution='static int charge(boolean member,int age){\n if(member && age<18)return 3;\n else if(member)return 5;\n else if(age<18)return 6;\n else return 8;\n}', members='{{solution}}', body='System.out.print(charge(true,17)+","+charge(true,18)+","+charge(false,17)+","+charge(false,18));', expected='3,5,6,8', checks='for(int age=0;age<=100;age++){if(charge(true,age)!=(age<18?3:5)||charge(false,age)!=(age<18?6:8))throw new AssertionError();}')

q('2.5','B','与、或、非', 'boolean a=true,b=false;\nSystem.out.print((a&&b)+","+(a||b)+","+(!a));', 'State the output.', '输出 false,true,false。&& 需要两者真，|| 只需至少一者真，! 取反。', ['与或运算正确','非运算正确'], '混淆至少一个和同时两个', expected='false,true,false')
q('2.5','A','保护字符串访问', 'String s="";\nboolean ok=s.length()>0 && s.substring(0,1).equals("A");\nSystem.out.print(ok);',
  'State the output and explain why no invalid substring access occurs.', '输出 false；左侧 false 导致 && 短路，右侧不会执行。', ['识别空串的长度','说明保护条件与短路顺序'], '认为右侧一定执行', expected='false')
q('2.5','E','组合业务条件', 'Entry is allowed when age is at least 16 and a ticket is valid, or when a staff pass is valid regardless of age.\nVariables: int age; boolean ticket, staff;',
  'Write one boolean expression. Evaluate it for (15,true,false), (16,true,false), and (12,false,true). Explain your parentheses.',
  '表达式 (age>=16 && ticket) || staff。三个结果为 false、true、true；职员通行证是独立允许条件。',
  ['年龄与票据使用 &&','职员通行证用外层 ||','三组情况判断正确'], '让职员也必须满足年龄条件', kind='write',
  solution='static boolean allowed(int age,boolean ticket,boolean staff){return (age>=16 && ticket)||staff;}', members='{{solution}}', body='System.out.print(allowed(15,true,false)+","+allowed(16,true,false)+","+allowed(12,false,true));', expected='false,true,true', checks='for(int age=0;age<=30;age++)for(int t=0;t<2;t++)for(int s=0;s<2;s++){boolean expected=false;if(s==1)expected=true;else if(age>=16&&t==1)expected=true;if(allowed(age,t==1,s==1)!=expected)throw new AssertionError();}')

q('2.6','B','德摩根律', 'boolean a=true,b=false;\nSystem.out.print(!(a&&b)+","+(!a||!b));', 'State the output and name the equivalence illustrated.', '输出 true,true；!(a&&b) 等价于 !a||!b。', ['两个结果正确','取反时交换与或'], '只翻转变量不交换运算符', expected='true,true')
q('2.6','A','用反例推翻等价', 'I: x>=2 && x<=7\nII: x>=2 || x<=7', 'Are these equivalent for every int x? Give a counterexample and both results.', '不等价，例如 x=0，I=false、II=true。II 对每个整数都为 true，因为两区间并集覆盖所有整数。', ['给出有效反例','说明两个表达式的差异'], '用区间内相同的结果证明等价', kind='concept')
q('2.6','E','逻辑等价与求值安全', 'A: s!=null && s.length()>0\nB: !(s==null || s.length()==0)\nC: s.length()>0 && s!=null',
  'For a String reference s, which expressions are safe and equivalent for all possible values, including null? Explain the distinction between truth values and evaluation order.',
  'A 和 B 都安全且等价，均表示非 null 的非空字符串。C 在 s=null 时先调用 length 而异常；交换 && 两侧不能忽略求值安全。',
  ['A 与 B 的等价关系','null 时短路保证安全','指出 C 的求值顺序问题'], '只按布尔代数交换危险表达式', kind='concept')

q('2.7','B','while 更新与终止', 'int n=1;\nwhile(n<8){n*=2;}\nSystem.out.print(n);', 'State the output and list values assigned to n.', '依次为 1、2、4、8；输出 8，最后条件 8<8 为 false。', ['列出状态变化','解释终止条件'], '循环停止时仍满足条件', expected='8')
q('2.7','A','循环条件检查次数', 'int n=10,count=0;\nwhile(n>0){n-=3;count++;}\nSystem.out.print(n+","+count);',
  'State the output and how many times n>0 is evaluated.', '输出 -2,4；条件求值 5 次，最后一次为 false。', ['四次执行后的 n 正确','条件比成功循环多一次'], '把条件检查次数等同于执行次数', expected='-2,4')
q('2.7','E','统计十进制位数', 'static int digits(int n){ /* complete */ }\n// Precondition: n >= 0; digits(0) must return 1.',
  'Complete digits using a while loop. Give results for 0, 7, 1000, and 2147483647.', '结果为 1、1、4、10。零要单独处理，其余每除以 10 去掉一位并计数。',
  ['处理零的特殊情况','循环每次缩小 n','正确返回位数'], '对零直接返回 0 位', kind='write', solution='static int digits(int n){\n if(n==0)return 1;\n int count=0;\n while(n>0){count++;n/=10;}\n return count;\n}', members='{{solution}}', body='System.out.print(digits(0)+","+digits(7)+","+digits(1000)+","+digits(2147483647));', expected='1,1,4,10', checks='for(int n=0;n<=10000;n++)if(digits(n)!=String.valueOf(n).length())throw new AssertionError();')

q('2.8','B','for 的起点与步长', 'for(int i=2;i<8;i+=2)System.out.print(i+" ");', 'State the exact output and number of iterations.', '输出 2 4 6 （末尾有空格），循环 3 次。', ['正确列出 2、4、6','上界 8 不包含'], '把 8 也输出', expected='2 4 6 ')
q('2.8','A','循环变量与累积变量', 'int sum=0;\nfor(int i=1;i<=5;i+=2){sum+=i;}\nSystem.out.print(sum);', 'State the output and explain which values are added.', '加入 1、3、5，输出 9。sum 不决定循环次数，i 才是控制变量。', ['正确列出步长序列','累积得到 9'], '把所有 1..5 都加进去', expected='9')
q('2.8','E','倒序构造字符串', 'static String reverse(String s){ /* complete */ }\n// Precondition: s is non-null.',
  'Complete reverse using a for loop and substring. It must work for empty and one-character strings.', '从 length-1 到 0 依次提取一个字符拼接。空串循环零次返回空串。',
  ['正确初始化最后一个索引','倒序包含索引零','空串不产生越界'], '起始索引用 length 而不是 length-1', kind='write', solution='static String reverse(String s){\n String result="";\n for(int i=s.length()-1;i>=0;i--)result+=s.substring(i,i+1);\n return result;\n}', members='{{solution}}', body='System.out.print(reverse("code")+"|"+reverse("")+"|"+reverse("x"));', expected='edoc||x', checks='if(!reverse(reverse("abca")).equals("abca"))throw new AssertionError();')

q('2.9','B','累加满足条件的值', 'int sum=0;\nfor(int i=1;i<=6;i++){if(i%3==0)sum+=i;}\nSystem.out.print(sum);', 'State the output and describe the selected values.', '输出 9，选中 3 和 6。', ['筛选 3 的倍数','求和为 9'], '把个数 2 当成总和', expected='9')
q('2.9','A','分解整数并筛选数位', 'int n=5024,sum=0;\nwhile(n>0){int d=n%10;if(d%2==0)sum+=d;n/=10;}\nSystem.out.print(sum);',
  'State the output. Explain the separate roles of %10 and /10.', '输出 6。提取 4、2、0、5，只累加偶数；%10 取个位，/10 去掉个位。', ['正确筛选并求和','解释取位与移位'], '把 n%10 误认为去掉个位', expected='6')
q('2.9','E','最小达标循环', 'static int months(int start,int target,int add){ /* complete */ }\n// 0<=start<=target<=1000000; 1<=add<=1000.\n// Add a fixed amount each month; return the first month when balance >= target.',
  'Complete months. Return 0 if already at target, and avoid an off-by-one error.', '先判断当前余额是否不足，只有不足时才增加余额和月数。达到或超过即停止。',
  ['已达标返回零','余额和月数同步更新','首次达到目标时停止'], '无条件先加一个月', kind='write', solution='static int months(int start,int target,int add){\n int count=0;\n while(start<target){start+=add;count++;}\n return count;\n}', members='{{solution}}', body='System.out.print(months(5,5,2)+","+months(5,10,2)+","+months(0,10,5));', expected='0,3,2', checks='for(int a=0;a<=20;a++)for(int t=a;t<=30;t++)for(int d=1;d<=7;d++)if(months(a,t,d)!=(t-a+d-1)/d)throw new AssertionError();')

q('2.10','B','逐字符筛选', 'String s="level";\nint count=0;\nfor(int i=0;i<s.length();i++)if(s.substring(i,i+1).equals("l"))count++;\nSystem.out.print(count);',
  'State the output and the indices that cause an increment.', '输出 2，在索引 0 和 4 增加计数。', ['遍历合法索引','正确比较字符子串'], '漏掉最后一个字符', expected='2')
q('2.10','A','相邻字符比较', 'String s="aabbaa";\nint pairs=0;\nfor(int i=0;i<s.length()-1;i++)if(s.substring(i,i+1).equals(s.substring(i+1,i+2)))pairs++;\nSystem.out.print(pairs);',
  'State the output. Why must the loop stop before the last index?', '输出 3，对应 aa、bb、aa；需要访问下一字符，所以 i 最大只能是 length-2。', ['找出三对相邻相同字符','解释循环上界'], '把相同字符总数当成相邻对数', expected='3')
q('2.10','E','统计重叠匹配', 'static int occurrences(String text,String key){ /* complete */ }\n// Both non-null; key is nonempty. Count overlapping occurrences.',
  'Complete occurrences using substring and a loop. For "aaaa" and "aa", return 3, not 2. Handle key longer than text.', '逐个起点比较长度为 key.length 的子串，每次起点加 1。循环到 text.length-key.length，保留重叠。',
  ['合法起点包含最后可能位置','每次只移动一位','较长 key 返回零'], '匹配后跳过 key 的整个长度', kind='write', solution='static int occurrences(String text,String key){\n int count=0;\n for(int i=0;i<=text.length()-key.length();i++)\n  if(text.substring(i,i+key.length()).equals(key))count++;\n return count;\n}', members='{{solution}}', body='System.out.print(occurrences("aaaa","aa")+","+occurrences("a","ab")+","+occurrences("","x"));', expected='3,0,0', checks='if(occurrences("banana","ana")!=2||occurrences("abc","abc")!=1)throw new AssertionError();')

q('2.11','B','矩形嵌套循环', 'int count=0;\nfor(int r=0;r<3;r++)for(int c=0;c<2;c++)count++;\nSystem.out.print(count);', 'State the output and explain why the counts multiply.', '输出 6。每个外层值执行 2 次内层，共 3*2。', ['识别内层每轮重启','正确相乘'], '把两个循环次数相加', expected='6')
q('2.11','A','三角形循环', 'int count=0;\nfor(int r=1;r<=4;r++)for(int c=0;c<r;c++)count++;\nSystem.out.print(count);',
  'State the output and give the number of inner iterations for each outer iteration.', '内层次数分别为 1、2、3、4，总数 10。', ['发现内层上界随 r 变化','用逐轮求和得到 10'], '直接计算 4*4', expected='10')
q('2.11','E','生成阶梯字符串', 'static String stairs(int n){ /* complete */ }\n// 0<=n<=20. Row r (starting at 1) contains r stars followed by a newline.',
  'Complete stairs using nested loops. For n=3 return "*\\n**\\n***\\n". Return an empty string for n=0.', '外层控制行，内层追加当前行数量的星号，内层结束后追加一个换行。',
  ['外层生成 n 行','内层生成正确星号数','换行在内层之外且零行返回空串'], '每输出一个星号就换行', kind='write', solution='static String stairs(int n){\n String out="";\n for(int r=1;r<=n;r++){\n  for(int c=0;c<r;c++)out+="*";\n  out+="\n";\n }\n return out;\n}'.replace('out+="\n";', 'out+="\\n";'), members='{{solution}}', body='System.out.print(stairs(3).replace("\n","/"));'.replace('replace("\n",','replace("\\n",'), expected='*/**/***/', checks='if(!stairs(0).equals("")||!stairs(1).equals("*\\n"))throw new AssertionError();')

q('2.12','B','单循环的执行次数', 'int count=0;\nfor(int i=0;i<7;i++)count++;\nSystem.out.print(count);', 'How many times does count++ execute? How many times is i<7 tested?', '语句执行 7 次，条件检查 8 次，输出 7。', ['区分执行次数和条件次数','包含最后失败的判断'], '忘记终止时的条件检查', expected='7')
q('2.12','A','每次减半的循环', 'int n=32,count=0;\nwhile(n>1){n/=2;count++;}\nSystem.out.print(count);',
  'State the output. If the starting value doubles to 64, how many additional iterations occur?', '32→16→8→4→2→1，输出 5。起始 64 时为 6 次，只多一次。', ['列出减半序列','解释翻倍只增加一次'], '输入翻倍就认为循环次数也翻倍', expected='5')
q('2.12','E','比较两种增长趋势', 'A: for(int i=0;i<n;i++) visit();\nB: for(int i=0;i<n;i++) for(int j=0;j<n;j++) visit();\nAssume n is positive and each visit takes the same time.',
  'Give exact visit counts for A and B. When n triples, by what factor does each count grow? Explain without relying only on Big-O notation.',
  'A 为 n 次，B 为 n*n 次。n 变成 3n 时分别增为 3 倍和 9 倍；B 每个外层步骤都有 n 次内层。',
  ['两个精确次数正确','两个增长倍数正确','解释嵌套导致乘法'], '两种算法输入翻倍都会同倍增长', kind='concept')
