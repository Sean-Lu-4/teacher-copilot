"""Reviewed local exercise bank for methods-calling; no API or random generation."""
from copy import deepcopy

CED_URL = 'https://apcentral.collegeboard.org/media/pdf/ap-computer-science-a-course-and-exam-description.pdf'
BANK_VERSION = 'methods-calling-20260917-v1'

QUESTIONS = [
    dict(id='Q1', level=1, title='识别合法调用', minutes=3, origin='原创基础题',
         objectives=['parameters', 'argument_count', 'argument_types', 'void'],
         code='''public static int total(int x, int y) { return x + y; }
public static void display(int n) { System.out.println(n); }''',
         task='''Assume both methods are in the same class as the code below.
Consider each statement independently. Which statements compile?
For the first statement, identify the parameters and arguments.

I.   int result = total(3, 5);
II.  int result = total(3);
III. int result = display(8);
IV.  int result = total(3.5, 5);''',
         answer='只有 I 可以编译。参数是 x、y，实参是 3、5；result 为 8。',
         reasoning=['I 的实参数量和类型匹配，返回 int 可赋给 result。',
                    'II 缺少一个实参。III 的 display 返回 void，不能作为赋值右侧的值。',
                    'IV 的 3.5 为 double，不能通过此调用隐式缩窄为 int。'],
         errors=['把“打印了 8”误认为“返回了 8”。', '只核对参数个数，忽略类型兼容。'],
         rubric='判断四句各 1 分；正确区分参数与实参 1 分，共 5 分。',
         intervention='若误选 III，让学生分别标出“屏幕输出”和“交还调用方的值”。'),
    dict(id='Q2', level=2, title='交换实参为什么改变结果', minutes=4, origin='原创应用题',
         objectives=['argument_order', 'return_use'],
         code='''public static int difference(int first, int second)
{
    return first - second;
}''',
         task='''The following code is in the same class. Determine a, b, and c.
Explain how the first argument is matched to a parameter.

int a = difference(9, 4);
int b = difference(4, 9);
int c = difference(a, b);''',
         answer='a = 5，b = -5，c = 10。',
         reasoning=['difference(9, 4)：first=9，second=4，返回 5。',
                    'difference(4, 9)：first=4，second=9，返回 -5。',
                    '第三次传入当前 a、b 的值：5 - (-5) = 10。实参按位置对应，而非变量名。'],
         errors=['认为相同的两个数交换顺序仍然返回相同值。', '把 5 - (-5) 算成 0。'],
         rubric='a、b、c 各 1 分；解释位置对应 1 分，共 4 分。',
         intervention='画 first、second 两个框，每次调用先填值再计算。此题补充检索未命中的顺序知识点。'),
    dict(id='Q3', level=3, title='参数副本与忽略返回值', minutes=6, origin='原创综合跟踪题',
         objectives=['parameters', 'return_use', 'trace'],
         code='''public static int increase(int value)
{
    value = value + 3;
    return value;
}''',
         task='''Determine the final values of x and y. Make a trace table after each line.
All code is in the same class.

int x = 4;
int y = increase(x);
increase(x);
x = increase(y);''',
         answer='最终 x = 10，y = 7。第二次调用返回 7，但返回值被忽略。',
         reasoning=['初始化：x=4。第一次调用内 value=4→7；返回后 x=4，y=7。',
                    '第二次调用仍传入 4，返回 7；没有赋值语句接收它，因此 x=4，y=7。',
                    '第三次传入 y 的值 7，返回 10；赋给 x 后 x=10，y=7。'],
         errors=['认为修改 int 参数就会修改调用方的 x。', '认为任何方法调用都会自动保存返回值。'],
         rubric='三次调用后的 x/y 状态各 1 分；解释副本与忽略返回值各 1 分，共 5 分。',
         intervention='将调用方变量和本次调用参数画在不同区域；没有赋值语句就不改调用方变量。'),
    dict(id='Q4', level=4, title='嵌套调用与整数运算', minutes=6, origin='原创 AP 风格题',
         objectives=['argument_order', 'return_use', 'trace'],
         code='''public static int combine(int a, int b)
{
    return 2 * a - b;
}

public static int half(int n)
{
    return n / 2;
}''',
         task='''Assume the following code appears in the same class as these methods.
What value is stored in result after the code executes?

int x = 5;
int y = 3;
int result = combine(half(x + y), combine(y, half(x)));''',
         options={'A': '4.5', 'B': '4', 'C': '-2', 'D': '5'}, answer_key='B',
         answer='B：4。',
         reasoning=['x+y=8，所以 half(8)=4。', 'half(5)=2，因为 int 除法截去小数部分。',
                    '右侧内层 combine(3,2)=6-2=4。', '外层 combine(4,4)=8-4=4。'],
         distractors={'A': '把 half(5) 当成 2.5，内层结果为 3.5，外层结果为 4.5；也忽略了 int 类型。',
                      'C': '两次都把 combine 的位置反过来理解为 2*b-a：内层为 1，外层为 -2。',
                      'D': '算出 half(8)=4，却把整个右侧内层调用错误地换成 y=3，得到 8-3=5。'},
         errors=['没有从内层调用逐步向外替换返回值。', '把整型除法当作小数除法。'],
         rubric='选 B 1 分；写出两个 half、内层 combine、外层 combine 各 1 分，共 5 分。',
         intervention='先让学生给每个调用画括号；若未学整数除法，在讲解阶段先教 5/2=2，否则不用该题作独立达标判断。'),
    dict(id='Q5', level=4, title='按需求选择调用表达式', minutes=5, origin='原创 AP 风格题',
         objectives=['argument_order', 'argument_types', 'return_use'],
         code='''// Returns the total cost for quantity items at unitPrice each,
// followed by a single discount of discount dollars.
public static int price(int quantity, int unitPrice, int discount)
{
    return quantity * unitPrice - discount;
}

// Returns the given amount plus a fixed service fee of 2 dollars.
public static int withFee(int amount)
{
    return amount + 2;
}''',
         task='''A customer buys 3 items at 8 dollars each. A single 5-dollar discount
is applied to the total, and then one 2-dollar service fee is added.
Which expression calculates the final cost? All calls occur in the same class.''',
         options={'A': 'withFee(price(3, 8, 5))', 'B': 'price(3, withFee(8), 5)',
                  'C': 'withFee(price(3, 5, 8))', 'D': 'price(3, 8, withFee(5))'},
         answer_key='A', answer='A：最终费用为 21。四个选项均可编译，但只有 A 符合需求。',
         reasoning=['先计算总价并减一次优惠：3*8-5=19。',
                    '再把结果作为 withFee 的实参：19+2=21。',
                    '选择依据是参数含义与操作顺序，不只是方法名或编译是否合法。'],
         distractors={'B': '把服务费加到单价，等于收三次：3*(8+2)-5=25。',
                      'C': '单价和优惠传错位置：3*5-8+2=9。',
                      'D': '把服务费加到折扣里，实际变成多减：3*8-(5+2)=17。'},
         errors=['认为能编译就符合任务要求。', '把固定总费用和每件费用混淆。'],
         rubric='选 A 1 分；费用 21 为 1 分；说明为什么 B 不对 1 分，共 3 分。',
         intervention='先用自然语言排列“乘数量→减折扣→加服务费”，再将每一步替换为方法调用。'),
    dict(id='EXIT', level=2, title='独立离堂检查', minutes=2, origin='原创达标题',
         objectives=['return_use', 'trace'],
         code='''public static int next(int n)
{
    return n + 1;
}''',
         task='''All code is in the same class. Determine the final values of a and b.
Explain why the middle method call does or does not change a.

int a = 2;
next(a);
int b = next(next(a));''',
         answer='a = 2，b = 4。next(a) 返回 3，但没有赋值给 a。',
         reasoning=['中间调用的返回值被忽略，所以 a 仍是 2。',
                    '最后一行先算 next(2)=3，再算 next(3)=4，保存到 b。'],
         errors=['把中间调用误当成 a = next(a)。'],
         rubric='a、b 各 1 分；解释忽略返回值 1 分，共 3 分。3 分视为本次检查达标，低于 3 分再做短跟踪题。',
         intervention='离堂题独立完成，不与前面讨论分数混算。'),
]

SCHEDULE = [
    ('Starter Activity', 5, 'Q1 作答 3 分钟＋反馈 2 分钟'),
    ('Teacher Explanation', 10, '参数位置、类型、返回值、int 参数副本；复习基本运算及整数除法'),
    ('Student Activity', 6, 'Q2 作答 4 分钟＋讨论 2 分钟'),
    ('Practice', 8, 'Q3 作答 6 分钟＋纠错 2 分钟'),
    ('Higher-Order / Exam-Style Question', 12, 'Q4 作答 6 分钟＋Q5 作答 5 分钟＋反馈 1 分钟'),
    ('Assessment', 4, 'EXIT 独立作答 2 分钟＋收集和小结 2 分钟'),
]


def make_plan(course, coverage):
    return dict(version=BANK_VERSION, mode='local_review_bank',
                note='预先编写的本课原创题库，由本地模板输出；没有调用模型自动出题。',
                course=dict(course), reference_minutes=45,
                needs_rescheduling=course['duration'] != 45,
                questions=deepcopy(QUESTIONS), schedule=deepcopy(SCHEDULE),
                textbook_evidence=[dict(id=i['id'], title=i['title'], status=i['status'],
                    sources=[dict(file=c['file'], page=c['page']) for c in i['candidates']]) for i in coverage],
                official_reference=CED_URL,
                validation='算术答案与选项已做离线检查；未使用 Java 编译器验证。难度未经学生试测。')


def prompt_requirements(plan):
    return '''
DIFFERENTIATED PRACTICE REQUIREMENTS
Build four levels: (1) identify valid calls, (2) apply a single method and argument
order, (3) trace several calls including an ignored return value, (4) original
AP-style four-option questions combining nested calls or specification-based
expression selection. End with a separate short independent exit check.
Supply each question in full, its level, minutes, objective, answer, reasoning,
misconceptions and teacher intervention. Explain EVERY incorrect MCQ option.
Use only the lesson scope. Do not require writing methods, loops, arrays or recursion.
Do not make higher difficulty merely larger numbers. State any extra prerequisite
and teach it first; integer division must be reviewed before using it in a challenge.
Label provenance as textbook original (exact source/page), adapted from textbook
(source/page and changes), or original AP-style. Never label original work an AP exam question.
Avoid unsupported claims of exam-equivalent difficulty: these are teacher-review drafts.
Allocate all practice within the lesson duration; do not add it on top of that duration.
For the 45-minute lesson allocate stages 3–8 as 5,10,6,8,12,4 minutes respectively.
For other durations redesign the allocation to sum to the requested duration.
The locally saved exercise_report.md is a fixed original sample bank, not retrieved
textbook evidence. Its existence does not close textbook coverage gaps.
'''


def render_report(plan):
    lines = ['# Methods 练习难度梯度报告', '',
             '**设计结论：基础识别 → 单步应用 → 综合跟踪 → 原创 AP 风格挑战。**', '',
             '适用目标：Grade 10，调用已有方法、传递参数、使用返回值和跟踪执行；不要求独立编写方法。', '',
             plan['note'], '',
             '**来源说明：以下全部为原创题，不是教材原题、教材改编题或 AP 真题。**', '',
             '题干使用英语，教师解析使用中文。学生作答前先隐藏答案部分。', '',
             '前置检查：需会赋值、基本四则运算及负数；Q4 还需整数除法。若未学，先在讲解阶段补齐。', '',
             '## 45 分钟课堂安排', '',
             '| 环节 | 分钟 | 内容 |', '|---|---:|---|']
    for stage, minutes, detail in plan['schedule']:
        lines.append(f'| {stage} | {minutes} | {detail} |')
    if plan['needs_rescheduling']:
        lines += ['', f"注意：本次指定 {plan['course']['duration']} 分钟，上表是 45 分钟参考方案，需要重新分配时间。"]
    lines += ['', 'Q4、Q5 是本课范围内的考试形式挑战；不代表覆盖完整 AP 试卷难度。', '',
              '## 难度为什么逐步提高', '',
              '| 题目 | 层级 | 推理要求 |', '|---|---|---|',
              '| Q1 | 1 基础 | 识别声明与调用，区分 void 和有返回值 |',
              '| Q2 | 2 应用 | 处理参数位置，并将返回值用于下一次调用 |',
              '| Q3 | 3 综合 | 跟踪参数副本、调用方变量和被忽略的返回值 |',
              '| Q4 | 4 挑战 | 跨多个嵌套调用传递结果，保持参数位置与类型语义 |',
              '| Q5 | 4 迁移 | 从需求选择正确调用组合，排除能编译但语义错误的表达式 |',
              '| EXIT | 独立检查 | 用新数据检查学生是否真正理解返回值 |', '',
              '## 学生题目', '',
              '所有方法和调用均位于同一个类中；已给出的声明供阅读，不要求学生编写方法。', '']
    for q in plan['questions']:
        labels = {i['id']: i['title'] for i in plan['textbook_evidence']}
        lines += [f"### {q['id']} {q['title']}", '',
                  f"层级 {q['level']} · {q['minutes']} 分钟 · {q['origin']}", '',
                  '考查目标：' + '、'.join(labels.get(key, key) for key in q['objectives']), '',
                  '```java', q['code'], '```', '', '```text', q['task'], '```', '']
        for key, value in q.get('options', {}).items():
            lines.append(f'{key}. `{value}`')
        lines.append('')
    lines += ['## 教师答案与教学处理', '']
    for q in plan['questions']:
        lines += [f"### {q['id']} 答案", '', q['answer'], '', '**推理步骤**', '']
        lines += [f'{i}. {step}' for i, step in enumerate(q['reasoning'], 1)]
        if q.get('distractors'):
            lines += ['', '**干扰项解释**', '']
            lines += [f'- {key}：{value}' for key, value in q['distractors'].items()]
        lines += ['', '**常见错误**', ''] + [f'- {e}' for e in q['errors']]
        lines += ['', f"评分：{q['rubric']}", '', f"教师处理：{q['intervention']}", '']
    lines += ['## 教材依据与补充关系', '',
              '教材候选用于支持概念讲解；原创题是另外设计的，不把它们计为教材已经覆盖。', '',
              '| 知识点 | 教材检索状态 | 候选页码 |', '|---|---|---|']
    from .profiles import STATUS_LABELS
    for item in plan['textbook_evidence']:
        sources = '；'.join(f"{s['file']} 第{s['page']}页" for s in item['sources']) or '无'
        lines.append(f"| {item['title']} | {STATUS_LABELS[item['status']]} | {sources} |")
    lines += ['', 'Q2 专门补充实参顺序示例；它不会把覆盖报告中“未找到候选”改成“已覆盖”。', '',
              '## 官方形式参照与验收', '',
              f'[College Board AP CSA CED]({plan["official_reference"]})：Topic 1.9，及印刷第149页起的选择题样例。',
              '参考其代码阅读、结果判断和四选一形式；未复制官方题干。Q5 用调用表达式选择代替本课尚未教授的方法编写。', '',
              plan['validation'], '',
              '- [ ] 题目只要求已教知识；整数除法等前置条件已满足',
              '- [ ] Q4、Q5 的干扰项有诊断价值且只有一个正确答案',
              '- [ ] 通过学生实际用时与错误分布调整难度、题量和时间',
              '- [ ] 确认所有题的答案和表述后再用于正式评价', '']
    return '\n'.join(lines)
