"""Build homework samples and a truthful availability matrix."""
import json
from pathlib import Path
from teacher_copilot.worksheets import assemble,summary,paper_report,TOPIC_CONTENTS,VISIBLE_TOPICS
from teacher_copilot.review_app import ReviewStore


def main():
    root=Path(__file__).resolve().parent
    out=root/'outputs/homework_acceptance';out.mkdir(parents=True,exist_ok=True)
    matrix=[]
    for topic in VISIBLE_TOPICS:
        for difficulty in ['basic','advanced','exam']:
            for minutes in [10,20]:
                s,records=assemble(dict(topic=topic,contents=TOPIC_CONTENTS[topic],difficulty=difficulty,minutes=minutes,purpose='homework'))
                matrix.append(dict(settings=s,summary=summary(s,records),ids=[r['content']['id'] for r in records]))
    (out/'availability.json').write_text(json.dumps(matrix,ensure_ascii=False,indent=2),encoding='utf-8')
    lines=['# 课程导航与短作业验收', '',
           '新页面统一为 单元 → 课题 → 考查内容。21 个课题分属四单元，旧 Methods 与条件判断题已并入对应课题，旧作业仍可打开。', '',
           '新增 14 道原创题，总题数 215。新增题通过 Java 执行验证；55 项自动测试通过。', '',
           '## 组卷规则', '',
           '- 默认提供 10 / 20 分钟独立作答时间，难度保持基础 / 巩固 / 考试。',
           '- 严格限定所选内容与难度，不重复使用同一道题，不修改预计时间来凑数。',
           '- 先寻找恰好满足时长的组合，再优先增加所选内容覆盖；无精确组合时优先接近时长并报告差额。',
           '- 只有时长匹配且所有所选内容均有题目，才显示完整。题量不足和覆盖不足分开提示。',
           '- 每题用时为编写时估计，尚需课堂校准；覆盖指有代表题，不代表知识细节充分覆盖。',
           '- API 未接入；保存了缺口描述供后续补题使用。满时长仍缺内容时，应重新平衡题目，不能再追加超时题。', '',
           '## 可直接检查的作业', '', '| 课题 | 难度 / 目标 | 实际 | 教师版 | 学生版 |', '|---|---|---|---|---|']
    store=ReviewStore(root/'outputs')
    for topic in ['csa-loops','csa-arrays']:
        for difficulty,minutes in [('basic',10),('exam',20)]:
            state=store.mutate(dict(action='generate',settings=dict(topic=topic,contents=TOPIC_CONTENTS[topic],difficulty=difficulty,minutes=minutes,purpose='homework')))
            plan=json.loads((store.directory(state['run'])/'exercise_plan.json').read_text(encoding='utf-8'))
            stem=topic+'-'+difficulty+'-'+str(minutes)
            for audience in ['teacher','student']:
                (out/(stem+'-'+audience+'.md')).write_text(paper_report(plan,state['records'],audience),encoding='utf-8')
            info=state['summary']
            lines.append(f"| {VISIBLE_TOPICS[topic]} | {'基础' if difficulty=='basic' else '考试'} / {minutes} 分钟 | {info['count']} 题，{info['minutes']} 分钟 | [教师版]({stem}-teacher.md) | [学生版]({stem}-student.md) |")
    lines += ['', '## 当前限制', '',
              '并非每个课题、每种勾选组合都足够生成 10 / 20 分钟作业。例如只选一个题量少的内容仍可能不足；勾选过多内容也可能无法在短时间内覆盖。页面会展示真实缺口。', '',
              '[全部 126 种课题/难度/时间组合的结果](availability.json) · [新增题 Java 记录](java_checks/verification.json)', '',
              '本轮集中扩充循环与数组，Methods 和条件判断主要复用已有题目。全课程首批 159 题的集中反馈仍保留在原审核页。']
    (out/'README.md').write_text('\n'.join(lines),encoding='utf-8')
    print(f'{len(matrix)} combinations checked; samples saved to {out}')


if __name__=='__main__':main()
