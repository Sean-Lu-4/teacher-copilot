"""Build reproducible review artifacts without overwriting teacher feedback."""
import json
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED
from teacher_copilot.csa_bank import QUESTIONS
from teacher_copilot.csa_curriculum import LABELS, UNITS, GROUPS, SOURCE, VERSION
from teacher_copilot.questions import create_record, content_hash, save_questions
from teacher_copilot.worksheets import paper_report, assemble, TOPIC_CONTENTS, summary
from teacher_copilot.csa_review import review_data


def build(root):
    out=root/'outputs/csa_full_review'
    out.mkdir(parents=True,exist_ok=True)
    records=[create_record(q,VERSION,dict(kind='original',sources=[])) for q in QUESTIONS]
    report=json.loads((out/'java_checks/verification.json').read_text(encoding='utf-8'))
    passed={r['id']:r for r in report['results'] if r['passed']}
    for q in QUESTIONS:
        if q['question_kind']!='concept':
            assert passed[q['id']]['content_hash']==content_hash(q), 'Stale verification: '+q['id']
    files=[]
    for unit,title in UNITS.items():
        rows=[r for r in records if r['content']['ced_topics'][0].startswith(str(unit)+'.')]
        for audience in ['teacher','student']:
            path=out/f'unit{unit}_{audience}.md'
            path.write_text(paper_report(dict(report_title=f'Unit {unit} · {title} · 题库'),rows,audience),encoding='utf-8')
            files.append(path)
    save_questions(out/'questions.json',records)
    data=review_data(root/'outputs')
    coverage=[]
    for topic,title in LABELS.items():
        rows=[r for r in data['questions'] if r['content']['ced_topics']==[topic]]
        coverage.append(dict(topic=topic,title=title,questions=[dict(id=r['content']['id'],level=r['content']['level'],kind=r['content']['question_kind'],technical_status=r['technical_status']) for r in rows],scope='Topic-level representative tasks, not exhaustive essential-knowledge coverage'))
    metadata=dict(version=VERSION,source=SOURCE,checked_on='2026-09-30',new_questions=159,existing_questions=42,total_questions=201,
                  topic_count=53,java_cases=123,conceptual_cases=36,teacher_review='pending',classroom_trial='pending',coverage=coverage)
    (out/'coverage.json').write_text(json.dumps(metadata,ensure_ascii=False,indent=2),encoding='utf-8')
    lines=['# AP CSA 全课程首批题库 · 集中审核', '',
           '4 个单元，53 个 Topic，每个新增基础、巩固、考试风格各 1 道，共 159 道；保留原有 42 道，总计 201 道。', '',
           '**这是覆盖全部 Topic 的第一批代表题，不是每条知识要求均已充分覆盖，也不是完整模拟考试。** 难度与用时待课堂校准。', '',
           '[打开本地集中审核页](http://127.0.0.1:8765/curriculum) · [打开练习生成页](http://127.0.0.1:8765/)', '',
           '## 怎样反馈', '',
           '1. 先在审核页筛选你最熟悉的单元和考试层，抽查代表题。',
           '2. 标记“适合目前学生 / 偏简单 / 偏难 / 表述需改进 / 答案或代码有问题”，可写具体意见。',
           '3. 在左侧填写整体方向并点击“保存全部反馈”；也可以在对话里按题号反馈。',
           '4. 保存文件为本目录 teacher_feedback.json；重建报告不会覆盖它。', '',
           '## 分单元完整题目', '', '| 单元 | 新增题数 | 学生版 | 教师版 |', '|---|---:|---|---|']
    for unit,title in UNITS.items():
        count=sum(q['ced_topics'][0].startswith(str(unit)+'.') for q in QUESTIONS)
        lines.append(f'| Unit {unit} · {title} | {count} | [学生版](unit{unit}_student.md) | [教师版](unit{unit}_teacher.md) |')
    lines += ['', '## 检查范围与结果', '',
              '- 123 道含代码的题：给定代码或参考实现经过 Java 编译执行，包含文件输入和部分边界断言。',
              '- 36 道解释题：提供参考要点和逐点评分；不把它们标成 Java 已通过。',
              '- 50 项自动测试通过，包括每个 Topic 三档可组卷、学生版答案隔离、修改参考实现后导出、反馈保存冲突和本机请求验证。',
              '- 验证结果绑定题目内容摘要；题目改变后不能沿用旧通过标记。',
              '- [执行证据](java_checks/verification.json) · [覆盖数据](coverage.json) · [题目档案](questions.json)', '',
              '## 题型与审核标准', '',
              '- 基础：识别概念或单步求值。巩固：多步跟踪、解释机制、定位错误。考试风格：边界分析、反例、算法设计或短代码实现。',
              '- 本批 95 道跟踪/解释题、28 道代码实现题、36 道概念分析题。尚未系统扩展为 MCQ 干扰项题库或完整计时 FRQ 模拟卷。',
              '- Java 检查证明可执行部分符合给定预期，不能代替教师判断全部文字解释、难度、教学适用性与作答时间。',
              '- 递归题要求阅读和跟踪，没有要求学生从零编写递归算法。',
              '- 每个 Topic 每档仅一道新代表题，组卷会如实提示题量不足；不能把这当作充足的随机题库。',
              '- 题库由 AI 辅助编写，全部为原创；本次没有调用付费生成 API，也没有复制官方试题。', '',
              '## 课程范围依据', '', f'[College Board AP CSA CED（2025 秋季生效）]({SOURCE})，2026-09-30 核对 Topic 列表。中文标题为便于选课的简写。', '',
              '## 53 个 Topic 的题目映射', '', '| Topic | 内容 | 基础 | 巩固 | 考试风格 |', '|---|---|---|---|---|']
    for item in coverage:
        ids={q['level']:q['id'] for q in item['questions']}
        lines.append(f"| {item['topic']} | {item['title']} | {ids[2]} | {ids[3]} | {ids[4]} |")
    (out/'README.md').write_text('\n'.join(lines),encoding='utf-8')
    # Each group/tier can generate a useful, scope-limited paper at 20 minutes.
    matrix=[]
    for group in GROUPS:
        for difficulty in ['basic','advanced','exam']:
            settings,rows=assemble(dict(topic=group,contents=TOPIC_CONTENTS[group],difficulty=difficulty,minutes=20))
            matrix.append(dict(settings=settings,summary=summary(settings,rows),ids=[r['content']['id'] for r in rows]))
    (out/'assembly_samples.json').write_text(json.dumps(matrix,ensure_ascii=False,indent=2),encoding='utf-8')
    with ZipFile(out/'AP_CSA_Review_Pack.zip','w',ZIP_DEFLATED) as archive:
        for path in files+[out/'README.md',out/'coverage.json',out/'questions.json',out/'assembly_samples.json',out/'java_checks/verification.json']:
            archive.write(path,path.relative_to(out))
    print(f'Built {len(coverage)} topic records and {len(files)} student/teacher documents in {out}')


if __name__=='__main__':build(Path(__file__).resolve().parent)
