"""Original selection questions; executable fixtures are trusted author content."""
BANK_VERSION = 'conditionals-12-20260930-v1'
QUESTIONS = []
JAVA_CASES = []


def add(id, level, title, objective, code, task, expected, answer, steps, error, guidance):
    QUESTIONS.append(dict(
        id=id, level=level, title=title, objectives=[objective], code=code,
        task=task, answer=answer, reasoning=steps, errors=[error], intervention=guidance,
        minutes=3 if level < 3 else 4 if level == 3 else 5,
        origin='原创考试风格题' if level == 4 else '原创巩固题' if level == 3 else '原创基础题',
        prerequisites='Java 变量、赋值、整数运算和布尔表达式；条件判断语法',
        rubric='输出或结论正确 1 分；条件判断过程正确 1 分；解释关键规则或边界正确 1 分，共 3 分。'))
    JAVA_CASES.append(dict(id=id, expected=expected))


add('IB01',1,'等号处的边界','if_conditions',
    'int score = 60;\nSystem.out.print(score > 60);\nSystem.out.print(",");\nSystem.out.print(score >= 60);',
    'State the exact output. Explain the difference between the two comparisons.',
    'false,true','false,true。60 不大于 60，但大于等于 60。',
    ['分别判断两个表达式。','>= 包含等于边界。'],
    '忽略 > 和 >= 的边界差异。','用 59、60、61 三个数画出边界。')

add('IB02',1,'if / else 只执行一个分支','if_branches',
    'int n = 7;\nif (n % 2 == 0) {\n    System.out.print("even");\n} else {\n    System.out.print("odd");\n}',
    'State the exact output and identify the branch that executes.',
    'odd','打印 odd；执行 else 分支。',
    ['7 % 2 为 1。','条件为 false，只进入 else。'],
    '认为 if 后的代码总会执行。','先写出条件真值，再标出唯一执行路径。')

add('IB03',2,'闭区间的逻辑条件','if_logic',
    'int age = 12;\nboolean allowed = age >= 12 && age <= 17;\nSystem.out.print(allowed);',
    'State the output. Would allowed be true for ages 11, 17, and 18? Explain.',
    'true','输出 true；11 为 false，17 为 true，18 为 false。',
    ['&& 要求两侧同时成立。','下界 12 和上界 17 都包含在范围内。'],
    '用 || 判断区间，导致区间外也通过。','在数轴上标出两个条件的交集。')

add('IB04',2,'嵌套条件的入口','if_nested',
    'int x = 4, y = 9;\nif (x > 0) {\n    if (y < 5) { System.out.print("A"); }\n    else { System.out.print("B"); }\n} else { System.out.print("C"); }',
    'State the output. Explain which two conditions are evaluated.',
    'B','打印 B；先判断 x > 0，再判断 y < 5。',
    ['外层为 true，进入内层。','内层为 false，执行内层 else。'],
    '把内层 else 误看成外层 else。','给每一层的大括号使用一种颜色。')

add('IA01',3,'重叠边界的优先顺序','if_conditions',
    'int score = 90;\nif (score >= 80) { System.out.print("B"); }\nelse if (score >= 90) { System.out.print("A"); }\nelse { System.out.print("C"); }',
    'State the output. Rewrite the conditions so scores at least 90 print A, scores from 80 to 89 print B, and lower scores print C.',
    'B','原输出 B。修正：先 if (score >= 90) 打印 A，再 else if (score >= 80) 打印 B，最后 else 打印 C。',
    ['90 已满足第一个条件，后续分支不会判断。','从较高阈值开始检查可避免高分被提前截住。'],
    '以为后面的更精确条件会覆盖前面的分支。','用 79、80、89、90 逐项检查修正后的路径。')

add('IA02',3,'独立 if 会读取新值','if_branches',
    'int x = 4;\nif (x < 5) { x += 3; }\nif (x > 6) { x -= 2; }\nSystem.out.print(x);',
    'State the output. What would the output be if the second if were replaced by else if? Explain.',
    '5','原输出 5；改为 else if 后输出 7。',
    ['第一个分支把 x 改为 7，第二个独立 if 再把它改为 5。','else if 在第一个分支已执行后被跳过。'],
    '始终用初始 x 判断后续条件。','画出每条赋值后的 x 值，再比较两种结构。')

add('IA03',3,'短路避免整数除零','if_logic',
    'int count = 0, total = 12;\nboolean ok = count != 0 && total / count > 2;\nSystem.out.print(ok);',
    'State the output and explain why no exception occurs. What happens if the operands of && are reversed?',
    'false','输出 false。左侧为 false，右侧不执行；交换两侧后先进行整数除零，抛出 ArithmeticException。',
    ['&& 左侧为 false 时会短路。','保护条件必须位于危险计算前面。'],
    '认为 && 两侧总会求值。','从左到右标出实际被求值的表达式。')

add('IA04',3,'没有括号时 else 属于谁','if_nested',
    'int x = 2, y = -1;\nif (x > 0)\n    if (y > 0)\n        System.out.print("A");\n    else\n        System.out.print("B");',
    'State the output. Add braces without changing behavior. What is printed if x is changed to -2?',
    'B','输出 B。等价结构：if (x > 0) { if (y > 0) { print A; } else { print B; } }。x = -2 时无输出。',
    ['else 匹配最近的尚未匹配 else 的 if，即 y > 0。','外层为 false 时整个内层结构都被跳过。'],
    '按缩进而不是语法匹配 else。','先给内层 if / else 加括号，再给外层加括号。')

add('IE01',4,'费用规则的边界修复','if_conditions',
    'int hours = 3;\nint fee;\nif (hours < 3) { fee = 6; }\nelse { fee = 6 + (hours - 2) * 4; }\nSystem.out.print(fee);',
    'For positive integer hours, the first 3 hours cost 6 in total; each additional hour costs 4. State the current output. Correct both boundary errors and give fees for hours 1, 3, 4, and 6.',
    '10','当前输出 10。修正：if (hours <= 3) fee = 6; else fee = 6 + (hours - 3) * 4;。1、3、4、6 小时分别为 6、6、10、18。',
    ['3 小时应仍属于首段，边界应包含 3。','追加小时数应减去已包含的 3 小时。'],
    '只修改比较符号，没有修改追加小时数。','分别检查分段边界和每段公式，再试边界两侧。')

add('IE02',4,'两个分支更新同一变量','if_branches',
    'int a = 5, b = 2;\nif (a > b) { a = a - b; }\nif (a > b) { b = a + b; }\nelse { b = a - b; }\nSystem.out.print(a + "," + b);',
    'State the output and trace a and b after each statement that changes a value. Would replacing the second if with else if change the result?',
    '3,5','输出 3,5；a 从 5 变为 3，b 从 2 变为 5。改为 else if 后输出 3,2。',
    ['第二个独立 if 使用更新后的 a = 3，仍大于 b = 2。','改成同一条 if / else if / else 链后，首分支执行即跳过其余分支。'],
    '把独立 if 当成同一条互斥分支链。','用两列表格跟踪变量，并在每个条件前更新状态。')

add('IE03',4,'德摩根律与区间排除','if_logic',
    'int x = 10;\nboolean inside = !(x < 10 || x > 20);\nboolean outside = x < 10 || x > 20;\nSystem.out.print(inside + "," + outside);',
    'State the output. Rewrite inside without ! using comparisons and &&. Explain why replacing && with || in your rewrite is incorrect, using a counterexample.',
    'true,false','输出 true,false。等价式为 x >= 10 && x <= 20。若用 ||，例如 x = 5，右侧 x <= 20 为 true，错误地允许区间外的数。',
    ['对析取取反时，两侧比较都取反，|| 变为 &&。','10 和 20 应包含在区间内；反例需选区间外。'],
    '只翻转比较符号而不交换逻辑运算符。','对 9、10、20、21 建立真值表比较两个表达式。')

add('IE04',4,'嵌套分类的执行路径','if_nested',
    'int x = -2, y = 3;\nString label = "";\nif (x >= 0) {\n    if (y >= 0) { label = "I"; }\n    else { label = "IV"; }\n} else {\n    if (y >= 0) { label = "II"; }\n    else { label = "III"; }\n}\nSystem.out.print(label);',
    'State the output. Rewrite the nested structure as a single if / else if / else chain with the same result for every integer x and y, including zero.',
    'II','输出 II。等价链：if (x >= 0 && y >= 0) label = "I"; else if (x >= 0) label = "IV"; else if (y >= 0) label = "II"; else label = "III";。',
    ['x 为负，进入外层 else；y 非负，得到 II。','链中较早条件失败已提供信息，后续不必重复所有条件；零按 >= 0 处理。'],
    '把 >= 换成 >，造成零的分类改变。','列出正负两轴的四种组合，再单独验证含零情况。')
