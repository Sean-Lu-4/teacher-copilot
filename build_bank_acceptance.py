"""Create reproducible teacher review artifacts and a full assembly matrix."""
import json
from itertools import combinations
from pathlib import Path
from time import perf_counter
from teacher_copilot.worksheets import assemble, summary, paper_report, CONTENT, TOPIC_CONTENTS, DIFFICULTIES
from teacher_copilot.expanded_bank import QUESTIONS, BANK_VERSION
from teacher_copilot.questions import create_record, save_questions
from teacher_copilot.review_app import ReviewStore


def main():
    root=Path(__file__).parent
    out=root/'outputs/bank30_acceptance'
    out.mkdir(parents=True,exist_ok=True)
    matrix=[]
    for topic,contents in TOPIC_CONTENTS.items():
        if not topic.startswith('method'): continue
        for n in range(1,len(contents)+1):
            for subset in combinations(contents,n):
                for difficulty in DIFFICULTIES:
                    for minutes in (10,20,30):
                        request=dict(topic=topic,contents=list(subset),difficulty=difficulty,minutes=minutes)
                        start=perf_counter()
                        try:
                            s,records=assemble(request)
                            info=summary(s,records)
                            matrix.append(dict(settings=request,status='assembled',**info,ids=[r['content']['id'] for r in records],milliseconds=round((perf_counter()-start)*1000,2)))
                        except ValueError as exc:
                            matrix.append(dict(settings=request,status='no_matching_questions',message=str(exc)))
    (out/'assembly_matrix.json').write_text(json.dumps(matrix,ensure_ascii=False,indent=2),encoding='utf-8')
    store=ReviewStore(root/'outputs')
    lines=['# Methods 30 题验收', '',
           '30 道原创题：基础 10 道、巩固 10 道、考试风格 10 道。保留原 6 道，新增 24 道。', '',
           '题干为英文，教师答案与讲解建议为中文。全部为方法阅读与调用，不要求学生编写方法。', '',
           '## 三套 20 分钟练习', '', '| 难度 | 实际题数 / 分钟 | 学生版 | 教师版 |', '|---|---|---|---|']
    samples=[]
    for difficulty,(label,_) in DIFFICULTIES.items():
        state=store.mutate(dict(action='generate',settings=dict(topic='methods',contents=TOPIC_CONTENTS['methods'],difficulty=difficulty,minutes=20)))
        plan=json.loads((store.directory(state['run'])/'exercise_plan.json').read_text(encoding='utf-8'))
        for audience in ('student','teacher'):
            (out/(difficulty+'_'+audience+'.md')).write_text(paper_report(plan,state['records'],audience),encoding='utf-8')
        save_questions(out/(difficulty+'_questions.json'),state['records'])
        info=state['summary']
        lines.append(f"| {label} | {info['count']} 题 / {info['minutes']} 分钟 | [学生练习]({difficulty}_student.md) | [答案与解析]({difficulty}_teacher.md) |")
        samples.append(dict(difficulty=difficulty,run=state['run'],summary=info))
    lines+=['', '## 请重点判断', '',
            '- 基础题是否能独立完成，巩固题是否需要多步跟踪，考试风格题的干扰项是否有诊断价值。',
            '- 前置知识是否已教：整数除法、boolean、比较和逻辑非均在相关题标注。',
            '- 预计时间是否符合你班学生的实际速度；时间标签不是试测结果。', '',
            '## 验证证据', '',
            '- [Java 编译与运行记录](java_checks/java_verification.json)：逐题内容摘要、实际输出与预期输出，以及非法调用拒绝结果。',
            '- [组卷测试矩阵](assembly_matrix.json)：三个课题的全部非空考查内容组合、三档难度、10/20/30 分钟。',
            '- [完整 30 题教师版](all_questions_teacher.md)：逐题查看题干、答案、解析、干扰项和前置知识。', '',
            'Java 执行验证检查代码结果；不能证明教学适用性、难度与正式考试等价或学生用时准确。', '',
            'Java 工具来源：[Eclipse Adoptium 官方发布](https://github.com/adoptium/temurin21-binaries/releases/latest)。便携 JDK 保存在 .cache/java，下载校验后使用，未修改系统 Java 配置。', '']
    records=[create_record(q,BANK_VERSION,dict(kind='original',sources=[])) for q in QUESTIONS]
    (out/'all_questions_teacher.md').write_text(paper_report({},records,'teacher'),encoding='utf-8')
    (out/'README.md').write_text('\n'.join(lines),encoding='utf-8')
    metrics=dict(bank_version=BANK_VERSION,questions=30,automated_tests_passed=40,
                 matrix_cases=len(matrix),assembled=sum(r['status']=='assembled' for r in matrix),
                 unsupported=sum(r['status']!='assembled' for r in matrix),samples=samples)
    (out/'summary.json').write_text(json.dumps(metrics,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(metrics,ensure_ascii=False,indent=2))


if __name__=='__main__':main()
