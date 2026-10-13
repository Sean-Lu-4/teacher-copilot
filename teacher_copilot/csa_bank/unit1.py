from . import q

q('1.1','B','算法与一次执行', 'Plan: read a price; multiply by 2; display the result.',
  'Identify the input, processing, and output. Is the plan the same thing as the output for price 7?',
  '输入是 price，处理是乘 2，输出为计算结果。输入 7 得到 14；算法是可重复执行的规则，不是单次结果。',
  ['识别输入和输出','区分处理规则与一次执行结果'], '把某次结果当作算法', kind='concept')
q('1.1','A','编译错误与逻辑错误', 'Program P: int n = "4";\nProgram Q: int n = 4; System.out.print(n + 2);\nRequirement: print twice n.',
  'Classify the problem in each program. Explain whether successful compilation proves the requirement was met.',
  'P 有类型不兼容的编译错误。Q 可编译但输出 6 而非 8，是逻辑错误。编译成功不证明满足需求。',
  ['区分编译错误和逻辑错误','用输入 4 的结果说明需求不满足'], '把编译通过等同于程序正确', kind='concept')
q('1.1','E','用测试识别错误算法', 'A proposed average algorithm computes a + b / 2 for two integer inputs.\nThe required result is the real-number mean.',
  'Give two different defects, a counterexample for each, and an unambiguous corrected algorithm.',
  '缺少括号且可能整数除法。a=2,b=4 得 4 而非 3；修正括号后 a=1,b=2 仍因整除得 1 而非 1.5。先转为实数再相加除以 2，例如 ((double)a+b)/2。',
  ['用反例揭示优先级错误','用奇数和揭示整数除法','给出明确的正确步骤'], '只加括号而忽略数据类型', kind='concept')

q('1.2','B','保存整数、实数和逻辑值', 'int seats = 12;\ndouble price = 2.5;\nboolean open = true;\nSystem.out.print(seats + "," + price + "," + open);',
  'State the output and name the type of each variable.', '输出 12,2.5,true；类型依次为 int、double、boolean。',
  ['正确识别三个变量类型','写出准确输出'], '把 boolean 当作 0 或 1', expected='12,2.5,true')
q('1.2','A','变量复制不建立联动', 'int a = 4;\nint b = a;\na = 9;\nSystem.out.print(a + "," + b);',
  'State the output. Explain why assigning a new value to a does not update b.', '输出 9,4。b 保存赋值当时的整数 4，之后给 a 赋值不会修改 b。',
  ['跟踪赋值时复制的值','说明两个基本类型变量独立'], '以为 b 会一直跟随 a', expected='9,4')
q('1.2','E','选择合适的数据表示', 'A booking record stores a room number such as "007", a number of guests, a measured temperature, and whether breakfast is included.',
  'Choose a Java type for each field and justify it. Explain what information is lost if the room identifier is stored as int.',
  '房间编号用 String；人数用 int；温度用 double；是否含早餐用 boolean。int 会把 007 存为 7，不能保留编号前导零。',
  ['四个字段选择合理类型','区分标识符与需要计算的数量','指出前导零信息损失'], '所有看起来是数字的字段都用 int', kind='concept')

q('1.3','B','运算优先级', 'System.out.print(3 + 4 * 2);', 'State the output and the order of operations.', '输出 11。先算 4*2=8，再加 3。', ['先乘后加','输出 11'], '完全从左到右计算', expected='11')
q('1.3','A','拼接从左向右发生', 'System.out.print("v=" + 2 + 3);\nSystem.out.print(";" + (2 + 3));',
  'State the exact output. Explain the role of the parentheses.', '输出 v=23;5。前半从字符串开始拼接，后半括号内先作数值加法。',
  ['区分拼接和算术','解释括号先求值'], '认为两个表达式都打印 5', expected='v=23;5')
q('1.3','E','表达式的类型与舍入损失', 'int total = 17, count = 4;\nSystem.out.print(total / count + "," + total % count + "," + (total / count * 1.0));',
  'State the output. Give an expression that computes the real average without losing the fractional part first.',
  '输出 4,1,4.0。可用 (double)total / count；先整数除法再乘 1.0 无法找回小数。',
  ['正确计算商和余数','识别转换发生过晚','给出除法前的类型转换'], '以为结果赋给 double 就会恢复小数', expected='4,1,4.0', checks='if ((double)17/4 != 4.25) throw new AssertionError();')

q('1.4','B','赋值右侧先求值', 'int n = 5;\nn = n + 2;\nSystem.out.print(n);', 'State the output and explain how n can appear on both sides of the assignment.', '输出 7。先读取旧 n=5 计算右侧，再把 7 存入 n。', ['先求右侧表达式','赋值后 n 为 7'], '把赋值当成数学恒等式', expected='7')
q('1.4','A','读取数字后读取一整行', 'java.util.Scanner in = new java.util.Scanner("12\\nAda\\n");\nint n = in.nextInt();\nString a = in.nextLine();\nString b = in.nextLine();\nSystem.out.print(n + "|" + a + "|" + b);',
  'State the output. Why is the first line read after nextInt empty?', '输出 12||Ada。nextInt 只读数字，紧接的 nextLine 消耗剩余换行前的空内容。',
  ['跟踪输入位置','说明空字符串的来源'], '以为 nextInt 同时读取下一整行', expected='12||Ada')
q('1.4','E','输入与正确更新', 'java.util.Scanner in = new java.util.Scanner("5 8");\nint a = in.nextInt();\nint b = in.nextInt();\n// Insert statements that swap a and b.\nSystem.out.print(a + "," + b);',
  'Write statements to swap the values using one temporary int. Explain why a=b; b=a; fails.',
  '先保存旧 a，再复制 b 到 a，最后把保存值赋给 b；直接两次赋值会丢失旧 a。输入 5 8 应输出 8,5。',
  ['保存旧值','正确完成交换','解释覆盖导致的数据丢失'], '第二次赋值仍能取到旧 a', kind='write',
  solution='int temp = a;\na = b;\nb = temp;', body='int a=5,b=8; {{solution}} System.out.print(a+","+b);', expected='8,5')

q('1.5','B','浮点转整数', 'System.out.print((int)3.9 + "," + (int)(-3.9));', 'State the output. Does the cast always round down?',
  '输出 3,-3。强制转 int 向零截断，不是始终向下取整。', ['两个结果正确','说明向零截断'], '把负数截断当作向负无穷取整', expected='3,-3')
q('1.5','A','转换放在除法前后', 'int a = 7, b = 2;\nSystem.out.print((double)(a / b) + "," + (double)a / b);',
  'State the output and explain why the values differ.', '输出 3.0,3.5。前者先整数除法，后者先把一个操作数变成 double。',
  ['识别两种求值顺序','指出第一次小数已被截断'], '以为转换位置无关紧要', expected='3.0,3.5')
q('1.5','E','避免整数加法溢出', 'int a = 2000000000, b = 2000000000;\ndouble average = (a + b) / 2.0;\nSystem.out.print(average);',
  'Explain why the expression may produce an incorrect average. Repair it so it computes the average of any two int values without overflowing their sum. You do not need to calculate the exact overflowed value.',
  'a+b 在 int 范围内先溢出，之后除以 2.0 无法修复。可改为 ((double)a+b)/2.0，两个给定输入的正确结果为 2.0E9；不要求手算溢出后的数值。',
  ['识别加法先在 int 中发生','转换须在加法前','修正后得到正确平均值'], '只把除数写成 2.0 就能避免加法溢出', expected='-1.47483648E8', checks='if (((double)2000000000+2000000000)/2.0 != 2000000000.0) throw new AssertionError();')

q('1.6','B','复合赋值更新', 'int n = 8;\nn += 3;\nn *= 2;\nSystem.out.print(n);', 'State the output and the value after each update.', '依次为 11、22；输出 22。', ['按顺序更新','最后输出 22'], '每次都从初始值 8 计算', expected='22')
q('1.6','A','整除与取余连续执行', 'int n = 29;\nn /= 4;\nn %= 3;\nn++;\nSystem.out.print(n);', 'State the output and all intermediate values.', '29/4 得 7，7%3 得 1，递增后得 2。', ['正确执行整除','按新值取余并递增'], '保留整数除法的小数部分', expected='2')
q('1.6','E','百分比更新中的类型陷阱', 'double price = 80.0;\nprice *= 1 + 15 / 100;\nSystem.out.print(price);',
  'State the output. Repair the update to increase price by 15 percent. Explain the original error.',
  '原输出 80.0；可改为 price *= 1 + 15 / 100.0;，得到 92.0。15/100 是整数除法，值为 0。',
  ['识别整数除法为零','给出正确复合赋值','说明应在除法前使用浮点操作数'], 'price 是 double 所以所有子表达式也都是 double', expected='80.0', checks='double fixed=80.0; fixed*=1+15/100.0; if(Math.abs(fixed-92.0)>1e-9)throw new AssertionError();')

q('1.7','B','阅读 API 合约', 'Library documentation:\npublic static int clamp(int value, int low, int high)\nRequires low <= high. Returns low if value < low, high if value > high, otherwise value.',
  'Using only the contract, determine clamp(12,0,10) and name the precondition.', '返回 10；前置条件是 low <= high。无需知道内部实现。',
  ['依据合约得到 10','正确说明前置条件'], '必须先读方法内部才能调用', kind='concept')
q('1.7','A','API 改版后的兼容性', 'Old API: public static int cost(int count)\nNew API: public static double cost(int count)\nClient: int bill = Shop.cost(3);',
  'Explain why the client no longer compiles and propose a repair that preserves fractional currency values.', '新的返回值是 double，不能隐式赋给 int；将 bill 声明为 double 可保留小数，直接转 int 可能丢失信息。',
  ['识别返回类型不兼容','修正客户端类型','解释不能盲目截断'], '调用语句没变化就一定兼容', kind='concept')
q('1.7','E','为黑盒库设计验证', 'API: public static int first(String text, String key)\nRequires key to be nonempty. Returns the first index of key, or -1 when absent.',
  'Design four tests with expected results: a match at the start, repeated matches, absence, and a match at the end. Explain why an empty key is not a valid conformance test under this contract.',
  '例如 first("abc","a")=0；first("ababa","ba")=1；first("abc","z")=-1；first("abc","bc")=1。空 key 违反前置条件，不能据其结果判断是否遵守该合约。',
  ['覆盖起点与终点','检查多次匹配时返回第一次','测试不存在情况并尊重前置条件'], '只用正常中间位置的一组测试', kind='concept')

q('1.8','B','注释不会执行', 'int n = 2;\n// n = 9;\nSystem.out.print(n);', 'State the output. Explain the purpose of the commented line.', '输出 2。注释不会作为 Java 语句执行，可供人阅读说明。', ['识别被注释的赋值','区分程序执行和说明文字'], '把注释中的赋值也执行', expected='2')
q('1.8','A','注释与代码不一致', '// Prints the real average of two ints.\nint a = 5, b = 2;\nSystem.out.print((a + b) / 2);',
  'State the output. Does the comment make the behavior correct? Repair the expression to match the comment.', '输出 3，注释不能改变整除行为。可改为 ((double)a+b)/2，输出 3.5。',
  ['以实际代码为准','修正为实数平均值'], '相信注释而忽略实际类型', expected='3', checks='if(((double)5+2)/2!=3.5)throw new AssertionError();')
q('1.8','E','写可检验的方法文档', 'public static String middle(String s) {\n    return s.substring(1, s.length() - 1);\n}',
  'Write a concise contract: valid input, returned value, and behavior when length is exactly 2. Do not merely restate each code line.',
  '前置条件：s 非 null，长度至少为 2。返回删除首尾字符后的字符串；不修改 s。长度为 2 时返回空字符串。',
  ['写出非 null 与长度限制','准确描述返回结果','覆盖长度恰为 2 的边界'], '文档只描述语法不描述使用条件', expected='[]', members='static String middle(String s){return s.substring(1,s.length()-1);}', body='System.out.print("["+middle("ab")+"]");')

q('1.9','B','识别方法签名', 'public static double scale(int count, double rate) { return count * rate; }',
  'Name the method, list its parameter types in order, and state its return type. Which of these form its Java signature?',
  '方法名 scale；参数依次 int、double；返回类型 double。签名由方法名和有序参数类型组成，不包括返回类型与参数名。',
  ['给出方法名与有序参数类型','区分返回类型和签名'], '把返回类型也算进签名', kind='concept')
q('1.9','A','重载选择', 'static int f(int x) { return x + 1; }\nstatic double f(double x) { return x + 0.5; }\n// Calls: f(3), f(3.0)',
  'Give both returned values and identify the selected overload for each call.', 'f(3) 选 int 版本，返回 4；f(3.0) 选 double 版本，返回 3.5。',
  ['按实参类型选择重载','计算两个返回值'], '仅按数值相同选择同一方法', expected='4,3.5', members='static int f(int x){return x+1;} static double f(double x){return x+0.5;}', body='System.out.print(f(3)+","+f(3.0));')
q('1.9','E','返回类型不能区分重载', 'I. int pick(int n)\nII. double pick(int value)\nIII. int pick(double n)\nIV. int pick(int n, int m)',
  'Which pair cannot be declared together in the same class? Explain, then give one legal call selecting III.',
  'I 与 II 的签名相同，不能只靠返回类型或参数名重载。III、IV 的参数类型或数量不同。pick(2.5) 可选择 III。',
  ['找出 I 和 II 冲突','用有序参数列表解释','给出匹配 III 的调用'], '改返回类型就构成重载', kind='concept')

q('1.10','B','类名调用 static 方法', 'static class Meter { static int twice(int n) { return 2*n; } }\n// In main: System.out.print(Meter.twice(6));',
  'State the output. Is a Meter instance needed for this call?', '输出 12；static 方法可通过类名调用，不需要创建实例。',
  ['返回值为 12','识别类方法调用'], '所有方法都必须先创建对象', expected='12', members='static class Meter{static int twice(int n){return 2*n;}}', body='System.out.print(Meter.twice(6));')
q('1.10','A','嵌套类方法调用', 'static int next(int x) { return x+1; }\nstatic int twice(int x) { return 2*x; }\n// Expression: next(twice(next(2)))',
  'Evaluate the expression and explain the argument value received by every call.', 'next(2)=3，twice(3)=6，next(6)=7；结果 7。',
  ['从最内层计算','把返回值作为下一次实参','最后结果为 7'], '按方法名从左向右直接执行', expected='7', members='static int next(int x){return x+1;} static int twice(int x){return 2*x;}', body='System.out.print(next(twice(next(2))));')
q('1.10','E','调用不会自动更新实参', 'static int step(int n) { return n+2; }\n// In main:\nint x=3;\nstep(x);\nint y=step(step(x));\nSystem.out.print(x+","+y);',
  'State the output. Rewrite only the standalone call so x receives its returned value; then give the new final output.',
  '原输出 3,7。把 step(x); 改为 x=step(x); 后，x=5，y=9，输出 5,9。',
  ['说明忽略返回值不会更新 x','跟踪嵌套调用','修改调用并给出新结果'], '把参数的变化当成调用者变量变化', expected='3,7', members='static int step(int n){return n+2;}', body='int x=3; step(x); int y=step(step(x)); System.out.print(x+","+y);', checks='int z=3; z=step(z); if(z!=5||step(step(z))!=9)throw new AssertionError();')

q('1.11','B','Math 的返回值', 'System.out.print(Math.abs(-7) + "," + Math.sqrt(25));', 'State the output and explain what each method computes.', '输出 7,5.0；分别求绝对值和非负平方根。', ['正确解释方法','注意 sqrt 返回 double'], 'sqrt 返回 int', expected='7,5.0')
q('1.11','A','离散随机区间', 'int roll = (int)(Math.random() * 6) + 1;', 'List all possible values of roll. Explain the lower and upper limits without assuming a specific random draw.',
  '可能为 1、2、3、4、5、6。Math.random() 位于 [0,1)，乘 6 后截断得到 0..5，再加 1。',
  ['说明随机值上界不含 1','逐步推导 1..6'], '认为结果可以是 7', kind='concept')
q('1.11','E','随机表达式边界设计', 'A game needs an integer from -3 through 4, inclusive.',
  'Write a Math.random expression for the eight possible results. Explain why casting before multiplication would fail, and test your mapping at random values 0 and 0.999.',
  '可用 (int)(Math.random()*8)-3。先把 random 转 int 会总得到 0。代入 0 得 -3；代入 0.999 得 4。',
  ['正确计算八种结果','偏移到 -3 起点','解释转换位置与两个端点'], '先转换随机小数再乘范围', kind='concept')

BOX='static class Box { private int size; Box(int s){size=s;} int get(){return size;} void grow(){size++;} }'
q('1.12','B','两个实例各有状态', BOX+'\n// In main: Box a=new Box(2); Box b=new Box(5); a.grow(); System.out.print(a.get()+","+b.get());',
  'State the output and explain why b does not change.', '输出 3,5。两个 new 创建不同对象，各有自己的 size。', ['区分两个实例','跟踪仅 a 的状态变化'], '认为同一类的所有对象共享实例字段', expected='3,5', members=BOX, body='Box a=new Box(2),b=new Box(5); a.grow();System.out.print(a.get()+","+b.get());')
q('1.12','A','引用相等与内容相等', 'String a=new String("sun");\nString b=new String("sun");\nSystem.out.print((a==b)+","+a.equals(b));',
  'State the output and distinguish the two comparisons.', '输出 false,true。两个 new 创建不同对象，== 比引用；equals 比字符串内容。', ['区分身份与内容','两个比较结果正确'], '字符串内容相同就一定引用相同', expected='false,true')
q('1.12','E','状态与行为的建模', 'A library loan tracks one book identifier, whether the book is on loan, and supports borrow and return operations.',
  'Propose instance fields and two method contracts. State an invariant and explain why a public onLoan field would weaken enforcement.',
  '可用 private String bookId、private boolean onLoan；borrow 仅未借出时成功并设 true；returnBook 在归还时设 false。约束是不能重复成功借出同一本书；公开字段可绕过方法直接改状态。',
  ['选择实例状态','明确两种行为的前后条件','解释封装如何保护约束'], '只列变量而不约束行为', kind='concept')

q('1.13','B','引用赋值不复制对象', BOX+'\n// In main: Box a=new Box(4); Box b=a; b.grow(); System.out.print(a.get());',
  'State the output and the number of Box objects created.', '输出 5；只有一个 Box 对象，a 和 b 引用它。', ['识别只调用一次 new','通过别名更新同一对象'], '每声明一个引用变量就创建一个对象', expected='5', members=BOX, body='Box a=new Box(4),b=a;b.grow();System.out.print(a.get());')
q('1.13','A','重新绑定不改变旧对象', BOX+'\n// In main: Box a=new Box(2); Box b=a; a=new Box(9); b.grow(); System.out.print(a.get()+","+b.get());',
  'State the output and draw the final reference relationships.', '输出 9,3。a 指向第二个对象，b 仍指向第一个对象。', ['追踪两次 new','区分重新绑定和修改对象'], 'a 重新赋值会让 b 跟随', expected='9,3', members=BOX, body='Box a=new Box(2),b=a;a=new Box(9);b.grow();System.out.print(a.get()+","+b.get());')
q('1.13','E','null 与对象生命周期', BOX+'\n// In main: Box a=new Box(6); Box b=a; a=null; b.grow(); System.out.print(b.get());',
  'State the output. Is the Box unreachable after a=null? What happens if a.get() is then executed?',
  '输出 7。b 仍引用对象，所以对象仍可达；a.get() 会抛出 NullPointerException，null 不是一个空 Box。',
  ['跟踪 b 保留的引用','区分 null 和有效对象','指出空引用调用错误'], '某个引用设 null 就销毁对象', expected='7', members=BOX, body='Box a=new Box(6),b=a;a=null;b.grow();System.out.print(b.get());', checks='boolean thrown=false;try{a.get();}catch(NullPointerException e){thrown=true;}if(!thrown)throw new AssertionError();')

q('1.14','B','在正确的接收者上调用方法', BOX+'\n// In main: Box a=new Box(1); a.grow(); a.grow(); System.out.print(a.get());',
  'State the output and identify the receiver of each instance method call.', '输出 3，三次调用的接收者都是 a 所指向的 Box。', ['两次更新状态','识别接收者对象'], 'get 会恢复初始值', expected='3', members=BOX, body='Box a=new Box(1);a.grow();a.grow();System.out.print(a.get());')
q('1.14','A','访问方法与修改方法', BOX+'\n// In main: Box a=new Box(3); int old=a.get(); a.grow(); System.out.print(old+","+a.get());',
  'State the output. Explain the different roles of get and grow.', '输出 3,4。get 返回当前 size 而不修改；grow 修改 size；old 保存的是之前返回的基本类型值。', ['区分访问与修改','旧的返回值不会自动更新'], '保存的 old 跟着对象变化', expected='3,4', members=BOX, body='Box a=new Box(3);int old=a.get();a.grow();System.out.print(old+","+a.get());')
q('1.14','E','有副作用的调用顺序', 'static class Counter { private int n=1; int take(){int old=n; n++; return old;} }\n// In main: Counter c=new Counter(); int result=c.take()*10+c.take(); System.out.print(result);',
  'State the output and final counter value. Would calling take once and multiplying that value by 11 preserve behavior? Explain.',
  '输出 12，最终 n=3。第一次返回 1、第二次返回 2。仅调用一次再乘 11 得 11，n=2，结果与状态都不同。',
  ['按左到右顺序跟踪返回值','跟踪对象状态','说明不能合并有副作用的调用'], '把两次调用看作同一个固定值', expected='12', members='static class Counter {int n=1;int take(){int old=n;n++;return old;}}', body='Counter c=new Counter();int result=c.take()*10+c.take();System.out.print(result);', checks='if(c.n!=3)throw new AssertionError();')

q('1.15','B','substring 的结束位置', 'String s="planet";\nSystem.out.print(s.substring(1,4)+","+s.length());', 'State the output and the included indices.', '输出 lan,6。substring 包含索引 1、2、3，不含 4。', ['下标从零开始','结束位置不包含'], '把结束下标也算进去', expected='lan,6')
q('1.15','A','字符串不可变', 'String s="banana";\ns.substring(1);\nString t=s.substring(2,5);\nSystem.out.print(s+","+t+","+s.indexOf("na"));',
  'State the output and explain why the standalone call does not shorten s.', '输出 banana,nan,2。substring 返回新值，不原地改变 s；indexOf 返回首次匹配位置。',
  ['说明不可变及忽略返回值','正确确定子串','找出首次出现位置'], 'substring 会原地修改字符串', expected='banana,nan,2')
q('1.15','E','按分隔符提取字段', 'static String suffix(String text) {\n    // Return text after its first colon; return text unchanged if absent.\n    // Empty suffix is permitted.\n}',
  'Complete suffix without a loop. Give the results for "ab:cd:ef", "plain", and "x:".',
  '先找第一个冒号；不存在则返回原文本，否则取冒号后一位开始的子串。三个结果为 cd:ef、plain、空字符串。假设 text 非 null。',
  ['找到首次分隔符','处理不存在情况','允许末尾分隔符得到空串'], '把 -1 当成正常位置继续切片', kind='write',
  solution='static String suffix(String text) {\n    int p=text.indexOf(":");\n    if(p<0) return text;\n    return text.substring(p+1);\n}', members='{{solution}}', body='System.out.print(suffix("ab:cd:ef")+"|"+suffix("plain")+"|"+suffix("x:"));', expected='cd:ef|plain|', checks='if(!suffix("").equals("")||!suffix(":a").equals("a"))throw new AssertionError();')
