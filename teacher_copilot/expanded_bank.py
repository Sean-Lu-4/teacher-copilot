"""Thirty original Methods questions. Difficulty/time require classroom calibration.

The original six-question lesson remains in exercises.py. This bank is used by
the worksheet assembler. Fixtures are kept separately from student content.
"""
from copy import deepcopy
from .exercises import QUESTIONS as ORIGINAL

BANK_VERSION = 'methods-30-20260930-v2'
EXTRA = []
JAVA_CASES = []


def add(id, level, title, objectives, code, task, answer, reasoning, errors,
        intervention, body, expected, options=None, key=None, distractors=None,
        prerequisites='变量、基本数据类型、赋值和四则运算', invalid=()):
    minutes = 3 if level < 3 else 4 if level == 3 else 5
    q = dict(id=id, level=level, title=title, minutes=minutes,
             origin='原创基础题' if level < 3 else '原创巩固题' if level == 3 else '原创考试风格题',
             objectives=objectives.split(), code=code, task=task,
             answer=answer, reasoning=reasoning, errors=errors,
             rubric='结论正确 1 分；关键步骤与解释各 1 分，共 3 分。',
             intervention=intervention, prerequisites=prerequisites)
    if options:
        q.update(options=dict(zip('ABCD', options)), answer_key=key, distractors=distractors)
        q['rubric']='选项正确 1 分；说明关键计算或匹配规则 1 分；排除一个错误选项 1 分，共 3 分。'
    EXTRA.append(q)
    JAVA_CASES.append(dict(id=id, body=body, expected=expected, invalid=list(invalid)))


add('B01',1,'表达式也可以作实参','parameters argument_count return_use',
    'public static int square(int n) { return n * n; }',
    'For square(2 + 1), name the formal parameter, count the arguments, and determine the value received by the parameter. Then determine the returned value.',
    '形参为 n；只有 1 个实参表达式 2+1；n 收到 3，返回 9。',
    ['先计算整个实参表达式 2+1=3。','一次传入一个值，n*n=9。'],
    ['把表达式中的两个数字当成两个实参。'], '让学生先圈出逗号分隔的实参位置，再计算每个表达式。',
    'System.out.print(square(2 + 1));','9')

add('B02',1,'int 实参传给 double 参数','argument_types',
    'public static double half(double value) { return value / 2; }',
    'Do half(5) and half(5.0) both compile? State the value returned by each and explain the argument conversion.',
    '两次都可编译，均返回 2.5。int 5 可拓宽为 double 5.0。',
    ['参数类型为 double。','调用 half(5) 时先发生 int 到 double 的拓宽，因此不是整型除法。'],
    ['认为实参类型必须与参数逐字相同，忽略合法拓宽。'], '对照 double 参数和 int 参数的声明，先定类型再算除法。',
    'System.out.print(half(5) + "," + half(5.0));','2.5,2.5',prerequisites='int 与 double、自动拓宽、浮点除法')

add('B03',1,'实参数量与类型分别检查','argument_count argument_types',
    'public static void mark(int row, int column) { System.out.print(row + ":" + column); }',
    'Consider each call independently: I. mark(2, 7); II. mark(2); III. mark(2, 7, 9); IV. mark(2.0, 7). Which calls compile? Explain each rejection.',
    '仅 I 可编译；II 少一个实参，III 多一个实参，IV 不能把 double 隐式缩窄为 int。',
    ['声明要求两个 int。','数量匹配后还要检查每个位置的类型。'],
    ['只检查数量，不检查 2.0 的类型。'], '使用“数量→位置→类型”的三步检查表。',
    'mark(2,7);','2:7',invalid=['mark(2);','mark(2,7,9);','mark(2.0,7);'])

add('B04',1,'void 调用产生的屏幕输出','void',
    'public static void show(int n) { System.out.print(n + "!"); }',
    'What is printed by the following code? Does show return the printed text?\n\nshow(4);\nshow(2);',
    '打印 4!2!，没有换行；show 不返回任何值。',
    ['print 不自动换行。','void 与打印行为可以同时存在。'],
    ['将屏幕文字当成返回值。'], '用两列分别记录屏幕输出与返回值。',
    'show(4);show(2);','4!2!')

add('B05',2,'返回值不会自动打印','return_use',
    'public static int triple(int n) { return 3 * n; }',
    'Give the final value of result and the exact output.\n\nint result = triple(4);\ntriple(9);\nSystem.out.print(result);',
    'result 为 12，屏幕仅打印 12。第二次调用返回的 27 被忽略。',
    ['赋值把第一次返回值保存为 result。','return 本身不打印，第二次调用也未重新赋值。'],
    ['回答打印 1227，混淆 return 与 print。'], '让学生仅给 System.out.print 语句标记输出。',
    'int result=triple(4);triple(9);System.out.print(result);','12')

add('B06',2,'同名参数和调用方变量','parameters',
    'public static void change(int n) { n = 20; }',
    'Find the final value of n. Explain why the same name does not make the variables identical.\n\nint n = 6;\nchange(n);\nSystem.out.print(n);',
    '调用方 n 仍为 6，打印 6。形参是独立的 int 副本。',
    ['实参当前值 6 被复制给形参 n。','给形参赋值 20 不修改调用方变量。'],
    ['因名称相同而认为共享存储。'], '分别画调用方 n 和方法内 n 两个格子。',
    'int n=6;change(n);System.out.print(n);','6')

add('B07',2,'位置匹配不看变量名','parameters argument_order',
    'public static void pair(int first, int second) { System.out.print(first + ":" + second); }',
    'Give the exact output and the value received by each parameter.\n\nint first = 2;\nint second = 8;\npair(second, first);',
    '输出 8:2；形参 first 收到 8，second 收到 2。',
    ['调用中的第一个位置是变量 second 的值 8。','按位置复制值，不按名字寻找同名形参。'],
    ['按名字配对，错误输出 2:8。'], '用箭头连接调用的第一位置与声明的第一位置。',
    'int first=2;int second=8;pair(second,first);','8:2')

add('A01',3,'赋值以后下一次调用读哪个值','return_use trace',
    'public static int step(int n) { return n - 2; }',
    'Trace x and y after each line. What is printed?\n\nint x = 10;\nint y = step(x);\nx = step(y);\ny = step(x);\nSystem.out.print(x + "," + y);',
    '依次为 (10,8)、(6,8)、(6,4)，输出 6,4。',
    ['第一次保存 8 到 y。','后续读取最新变量值；最后传入 x=6 而不是最初的 10。'],
    ['一直使用 x 的初始值。'], '每条赋值后覆盖表格中该变量的旧值。',
    'int x=10;int y=step(x);x=step(y);y=step(x);System.out.print(x+","+y);','6,4')

add('A02',3,'方法内部打印和返回值的先后','return_use trace',
    'public static int echo(int n) { System.out.print(n + ":"); return n + 1; }',
    'Determine the exact output. Distinguish method output from the output in the calling code.\n\nint x = echo(3);\nSystem.out.print(x);',
    '输出 3:4。内部先打印 3:，返回 4 保存到 x，调用方再打印 4。',
    ['方法体在调用完成前执行。','打印的 n 与返回的 n+1 是不同值。'],
    ['只写 4 或把内部打印也当作 n+1。'], '逐步在一条输出带上追加字符。',
    'int x=echo(3);System.out.print(x);','3:4')

add('A03',3,'两次 void 调用各自的参数副本','parameters void trace',
    'public static void bump(int n) { n = n + 2; System.out.print(n + " "); }',
    'Give the exact output and final x.\n\nint x = 5;\nbump(x);\nbump(x + 1);\nSystem.out.print(x);',
    '输出 7 8 5，最终 x=5。',
    ['第一次形参从 5 增为 7。','第二次先算 x+1=6，再增为 8；两次都未给 x 赋值。'],
    ['把第一次形参更新带回 x。'], '每次调用新建参数框，返回后丢弃该框。',
    'int x=5;bump(x);bump(x+1);System.out.print(x);','7 8 5')

add('A04',3,'整型除法在嵌套调用的哪一步发生','return_use trace',
    'public static int half(int n) { return n / 2; }',
    'Find a and b. Explain why the expressions differ.\n\nint a = half(half(11));\nint b = half(11) + half(11);',
    'a=2，b=10。嵌套把 5 再除以 2；相加是两个 5。',
    ['half(11)=5，因为使用 int 除法。','a=half(5)=2，b=5+5=10。'],
    ['把嵌套调用当作重复结果相加。'], '把每个完整调用替换为单一返回值。',
    'int a=half(half(11));int b=half(11)+half(11);System.out.print(a+","+b);','2,10',prerequisites='整数除法截去小数部分；表达式嵌套')

add('A05',3,'相同方法改变组合顺序','return_use trace',
    'public static int twice(int n) { return 2 * n; }\npublic static int addThree(int n) { return n + 3; }',
    'Find a and b, and explain the order of work.\n\nint a = twice(addThree(4));\nint b = addThree(twice(4));',
    'a=14，b=11；先加再乘与先乘再加不同。',
    ['a 的内层返回 7，外层返回 14。','b 的内层返回 8，外层返回 11。'],
    ['认为调用了相同方法就必有相同结果。'], '将两条式子分别写成自然语言操作顺序。',
    'int a=twice(addThree(4));int b=addThree(twice(4));System.out.print(a+","+b);','14,11')

add('A06',3,'boolean 返回值也需要保存','return_use trace',
    'public static boolean positive(int n) { return n > 0; }',
    'Determine the printed values.\n\nint x = -2;\nboolean a = positive(x);\nx = 3;\nboolean b = !positive(x);\nSystem.out.print(a + "," + b);',
    '输出 false,false。a 不会随 x 后续变化自动更新；b 是否定 true。',
    ['第一次求值时 x=-2，因此 a=false。','第二次 positive(3)=true，取反后 b=false。'],
    ['认为 a 保存的是会持续变化的公式。'], '强调赋值保存本次求值结果；复习 ! 的含义。',
    'int x=-2;boolean a=positive(x);x=3;boolean b=!positive(x);System.out.print(a+","+b);','false,false',prerequisites='boolean、比较运算 >、逻辑非 !')

add('A07',3,'连续调用不继承上次局部状态','parameters return_use trace',
    'public static int update(int n) { n = n * 2; return n + 1; }',
    'Give x, a, and b after all statements. Explain whether the second call starts with the previous parameter value.\n\nint x = 3;\nint a = update(x);\nint b = update(x);',
    'x=3，a=7，b=7。第二次建立新的参数副本，仍从 3 开始。',
    ['第一次参数变 6，返回 7；x 未修改。','第二次再次传入 3，因此结果相同。'],
    ['认为第二次参数从 6 继续。'], '为两次调用分开画参数生命周期。',
    'int x=3;int a=update(x);int b=update(x);System.out.print(x+","+a+","+b);','3,7,7')

add('A08',3,'作为实参的表达式不等于赋值','parameters return_use trace',
    'public static int minusOne(int n) { return n - 1; }',
    'Trace the variables and determine the output.\n\nint x = 4;\nint y = minusOne(x + 3);\nx = minusOne(y + x);\nSystem.out.print(x + "," + y);',
    '输出 9,6。x+3 只是求值，没有先把 x 改成 7。',
    ['y=minusOne(7)=6，x 仍为 4。','随后 x=minusOne(6+4)=9。'],
    ['将 x+3 误当成 x=x+3。'], '只对赋值左侧变量更新表格。',
    'int x=4;int y=minusOne(x+3);x=minusOne(y+x);System.out.print(x+","+y);','9,6')

add('A09',3,'多个实参表达式的位置映射','parameters argument_count argument_order argument_types void',
    'public static void display(int a, int b, int c) { System.out.print(a + ":" + b + ":" + c); }',
    'Find the output and justify all three parameter values.\n\nint a = 2;\nint b = 5;\ndisplay(b - a, a + b, b);',
    '输出 3:7:5，形参依次收到 3、7、5；调用方 a、b 不变。',
    ['在调用方先计算三个 int 表达式。','按第一、第二、第三位置复制到 a、b、c。'],
    ['因形参名与外部变量同名而跳过表达式。'], '给三个实参编号，再填写形参接收表。',
    'int a=2;int b=5;display(b-a,a+b,b);','3:7:5')

add('E01',4,'分组时整除发生的位置','return_use trace',
    'public static int groups(int n) { return n / 3; }\npublic static int addTwo(int n) { return n + 2; }',
    'A teacher adds 2 spare items to 7 items, then forms complete groups of 3. Which expression gives the number of complete groups?',
    'C，groups(addTwo(7))=groups(9)=3。',
    ['先补充物品，再对总物品数整除。','先整除再加 2 是给组数加数，不是增加物品。'],
    ['混淆物品数与组数的单位。'], '为每个中间值写上“物品”或“组”的单位。',
    'System.out.print(groups(addTwo(7)));','3',
    options=['addTwo(groups(7))','groups(7 + groups(2))','groups(addTwo(7))','groups(groups(7))'],key='C',
    distractors={'A':'先算 2 组再加 2 得 4，单位不符。','B':'groups(2)=0，结果仍为 2。','D':'先得 2 再整除，结果为 0。'},prerequisites='正整数除法与单位含义')

add('E02',4,'输出顺序与基本类型传值','parameters void trace',
    'public static void alter(int n) { n = n + 3; System.out.print(n + " "); }',
    'Which is the exact output?\n\nint n = 4;\nalter(n);\nalter(n * 2);\nSystem.out.print(n);',
    'B：7 11 4。调用方 n 始终为 4。',
    ['第一次打印 7。','第二次实参为 8，打印 11；最后外部打印 4。'],
    ['把局部参数的赋值带回调用方。'], '分别追踪参数框与输出带。',
    'int n=4;alter(n);alter(n*2);System.out.print(n);','7 11 4',
    options=['7 17 17','7 11 4','7 11 11','4 8 4'],key='B',
    distractors={'A':'错误地让第一次调用改变外部 n，再连续改写它。','C':'把第二次形参结果保存到了外部。','D':'忽略方法内部加 3。'})

add('E03',4,'嵌套调用的类型与 void 使用','argument_count argument_order argument_types void return_use',
    'public static double half(int value) { return value / 2.0; }\npublic static void record(double value, int count) { System.out.print(value + ":" + count); }',
    'Which single statement compiles? Consider the return types of inner calls and the context of the outer call. Consider each option independently.',
    'D。half(5) 返回 double，可传入第一位置；第二位置接收 int。record 返回 void，合法调用不能赋给变量。',
    ['先确定内层 half 的返回类型 double。','再核对外层实参位置、数量，以及是否把 void 当作值。'],
    ['只看原始数字都是整数，忽略内层方法返回 double。'], '为每个调用先标返回类型，再把整个内层调用替换为类型占位符。',
    'record(half(5),2);','2.5:2',
    options=['record(2, half(5));','record(half(5));','double result = record(half(5), 2);','record(half(5), 2);'],key='D',
    distractors={'A':'half(5) 返回 double，不能隐式传给第二个 int 参数。','B':'少了第二个实参。','C':'外层 record 返回 void，不能赋给 double 变量。'},
    invalid=['record(2,half(5));','record(half(5));','double result=record(half(5),2);'],prerequisites='嵌套调用的返回类型；double 不可隐式缩窄为 int；void 不能作为值')

add('E04',4,'用调用表达式表达一般关系','return_use trace',
    'public static int twice(int n) { return 2 * n; }\npublic static int next(int n) { return n + 1; }',
    'For every integer n from 0 through 100, which expression has value 2*n + 1?',
    'A，next(twice(n))；先得 2n，再加 1。',
    ['按照嵌套顺序替换方法作用。','要求对范围内所有 n 成立，不能只测一个偶然相等的值。'],
    ['只看方法名，不看组合顺序。'], '先用代数替换，再用 n=2 检查反例。',
    'System.out.print(next(twice(2))+","+next(twice(7)));','5,15',
    options=['next(twice(n))','twice(next(n))','next(next(n))','twice(twice(n))'],key='A',
    distractors={'B':'结果为 2n+2。','C':'结果为 n+2，只在某些值偶然一致。','D':'结果为 4n。'})

add('E05',4,'嵌套方法中的打印与最终输出','return_use trace',
    'public static int f(int n) { System.out.print(n + " "); return n - 1; }',
    'Which is the exact output?\n\nSystem.out.print(f(f(5)));',
    'C：5 4 3。',
    ['内层 f(5) 打印 5 并返回 4。','外层 f(4) 打印 4 并返回 3；最外面的 print 打印 3。'],
    ['认为最外层调用先获得并打印最终返回值。'], '给每个调用画一层括号，完成内层再向外移动。',
    'System.out.print(f(f(5)));','5 4 3',
    options=['3 4 5','5 3','5 4 3','4 3'],key='C',
    distractors={'A':'颠倒执行顺序。','B':'漏掉外层 f 自身的打印。','D':'漏掉内层 f 的打印。'})

add('E06',4,'多层调用中的负数整数除法','return_use trace',
    'public static int half(int n) { return n / 2; }\npublic static int shift(int n) { return n - 4; }',
    'Java integer division truncates toward zero. What value is stored in result?\n\nint result = half(shift(half(-3)));',
    'D：-2。依次为 half(-3)=-1，shift(-1)=-5，half(-5)=-2。',
    ['从最内层向外替换，每次 int 除法都向零截断。','先完成内部截断再传入 shift，不能一直保留小数到最后。'],
    ['用向下取整规则，或把全部步骤都按小数计算。'], '逐层写出方法实参、返回值和类型，比较两次截断的发生位置。',
    'System.out.print(half(shift(half(-3))));','-2',
    options=['-3','-2.75','-4','-2'],key='D',
    distractors={'A':'两次都错误向负无穷取整：先 -2，再 -6，最后 -3。','B':'将两次除法都当成浮点计算：-1.5→-5.5→-2.75。','C':'把顺序改成 shift(half(half(-3)))，得到 0-4。'},prerequisites='负数运算；题干明确给出的向零截断规则；多层嵌套')

add('E07',4,'多实参调用的求值顺序','argument_order return_use trace',
    'public static int echo(int n) { System.out.print(n); return n + 1; }\npublic static int join(int a, int b) { return 10 * a + b; }',
    'Java evaluates arguments from left to right. Which is the exact output?\n\nSystem.out.print(":" + join(echo(1), echo(2)));',
    'A：12:23。两个 echo 先打印 1、2，再将返回值 2、3 传给 join。',
    ['左实参 echo(1) 返回 2；右实参 echo(2) 返回 3。','join(2,3)=23，最外层打印 :23。'],
    ['将 echo 打印的数作为传入 join 的返回值。'], '建立“打印内容”和“返回值”双列表。',
    'System.out.print(":"+join(echo(1),echo(2)));','12:23',
    options=['12:23','21:23','12:12',':2312'],key='A',
    distractors={'B':'反转实参求值顺序。','C':'把打印值 1、2 当作返回值。','D':'错误地先执行外层打印，再执行参数调用。'},prerequisites='题干给出的从左至右求值；字符串拼接')

add('E08',4,'用嵌套调用完成布尔检查','argument_order argument_types return_use',
    'public static int bonus(int score) { return score + 5; }\npublic static boolean within(int score, int limit) { return score <= limit; }',
    'A score of 18 receives a 5-point bonus. The adjusted score must not exceed 20. Which expression correctly tests this requirement?',
    'B，within(bonus(18),20)，求值为 false，因为 23>20。',
    ['先调整分数，限额保持 20。','将调整后分数作为第一实参、限额作为第二实参。'],
    ['给限额也加奖励，或把比较两侧颠倒。'], '给每个实参写上“分数”“限额”，再代入。',
    'System.out.print(within(bonus(18),20));','false',
    options=['within(18, bonus(20))','within(bonus(18), 20)','within(20, bonus(18))','within(bonus(18), bonus(20))'],key='B',
    distractors={'A':'改变限额而非分数，18<=25 为 true。','C':'颠倒分数和限额，20<=23 为 true。','D':'同时提高限额，23<=25 为 true。'},prerequisites='boolean 返回值和 <= 比较运算')

QUESTIONS = deepcopy(ORIGINAL) + EXTRA
for question in QUESTIONS:
    question.setdefault('prerequisites', '变量、基本数据类型、赋值、四则运算和字符串拼接输出')
    if question['id'] == 'Q4':
        question['prerequisites'] = '正整数除法、嵌套表达式、按位置匹配实参'
