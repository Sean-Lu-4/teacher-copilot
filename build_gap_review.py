"""Audit all 126 full-topic scenarios and publish a teacher-readable local report."""
import json
from html import escape
from pathlib import Path
from teacher_copilot.worksheets import (VISIBLE_TOPICS, DIFFICULTIES, TOPIC_CONTENTS,
    assemble, summary, replace_question, paper_report, CONTENT)
from teacher_copilot.gap_bank import QUESTIONS, VERSION
from teacher_copilot.questions import create_record


def audit():
    rows=[]
    for topic in VISIBLE_TOPICS:
        if topic == 'all-csa':
            continue
        for difficulty in DIFFICULTIES:
            for minutes in [10,20]:
                settings, records=assemble(dict(topic=topic,contents=TOPIC_CONTENTS[topic],
                    difficulty=difficulty,minutes=minutes,purpose='homework'))
                info=summary(settings,records)
                replaceable=0
                for i in range(len(records)):
                    try:replace_question(settings,records,i);replaceable+=1
                    except ValueError:pass
                _, second=assemble(settings,{r['content']['id']:1000 for r in records})
                rows.append(dict(topic=topic,difficulty=difficulty,target=minutes,actual=info['minutes'],
                    missing=info['homework']['missing_contents'],replaceable=replaceable,count=len(records),
                    new_second=len({r['content']['id'] for r in second}-{r['content']['id'] for r in records})))
    return rows


def main():
    out=Path(__file__).resolve().parent/'outputs/gap_review'
    before=json.loads((out/'before.json').read_text(encoding='utf-8'))
    after=audit()
    (out/'after.json').write_text(json.dumps(after,ensure_ascii=False,indent=2),encoding='utf-8')
    detail_rows=[]
    for row in after:
        detail_rows.append([VISIBLE_TOPICS[row['topic']], DIFFICULTIES[row['difficulty']][0],
            f'{row["actual"]}/{row["target"]} 分钟',
            '；'.join(CONTENT[key][0] for key in row['missing']) or '已覆盖所选标签',
            f'{row["replaceable"]}/{row["count"]}',str(row['new_second'])])
    details=['# 126 种组卷条件明细','',
        '可替换为可替换题位数／当前题数；第二套新题数仅与第一套比较，不保证多轮无重复。','',
        '| 课题 | 难度 | 实际／目标 | 缺失考查内容 | 可替换 | 第二套新题数 |','|---|---|---|---|---|---|']
    details += ['| '+' | '.join(row)+' |' for row in detail_rows]
    (out/'scenario-details.md').write_text('\n'.join(details),encoding='utf-8')
    complete=lambda rows:sum(r['actual']==r['target'] and not r['missing'] for r in rows)
    lines=['# 题库缺口检查与两轮补题报告','',
        '检查范围：21 个课题 × 3 档难度 × 10／20 分钟，共 126 种组合。每次勾选该课题的全部内容。', '',
        f'完整组卷组合由 {complete(before)}/126 增至 {complete(after)}/126。两轮累计新增 60 道原创题，总题量从 215 增至 275。本轮新增字符串算法与文本文件各 15 题。', '',
        '## 本轮优先补题', '',
        '首轮已补 Math、String；本轮补字符串算法与文本文件。四个课题各新增 15 题，每档难度各 5 题。首轮后完整组合为 31/126，本轮结果见下表。', '',
        '第二批涵盖逐字符遍历、重叠与非重叠匹配、连续字符段、对称比较，以及文件的 token/行读取、空行、哨兵、无效 token、筛选统计。文本文件题均配真实文件验证。', '',
        '## 全课题前后对比', '',
        '完整组合数为每课题 6 种条件中时长匹配且所选内容均覆盖的数量。换题数是各场景可替换题位的合计，不是不同题目的数量。', '',
        '| 课题 | 完整组合 前→后 | 时长缺口合计 前→后 | 可换题位 前→后 |',
        '|---|---|---|---|']
    table=[]
    for topic,title in VISIBLE_TOPICS.items():
        b=[r for r in before if r['topic']==topic];a=[r for r in after if r['topic']==topic]
        values=[title,f'{complete(b)} → {complete(a)} / 6',
                f'{sum(r["target"]-r["actual"] for r in b)} → {sum(r["target"]-r["actual"] for r in a)} 分钟',
                f'{sum(r["replaceable"] for r in b)} → {sum(r["replaceable"] for r in a)}']
        table.append(values);lines.append('| '+' | '.join(values)+' |')
    lines+=['','## 仍然存在的缺口','',
        '下一轮优先组为 API 与文档、嵌套循环、类设计、数据伦理、查找排序和递归。四个已补课题的组卷改善不代表全课程补齐，也不保证连续作业完全不重复。', '',
        '审查范围未穷举所有勾选子集；“覆盖”仅指题目的内容标签覆盖，不等于每条知识细节都充分考查。预计时间需要课堂试用，考试风格不是官方试题，难度尚未校准。', '',
        '## 代表性作业与审核重点','',
        '请重点判断题干是否明确、解析是否足够、难度梯度是否合适，以及编程题预计时间是否合理。新增题仍为待教师审核状态。','']
    for topic in ['csa-math','csa-strings','csa-string-algorithms','csa-files']:
        for difficulty,minutes in [('basic',10),('advanced',20),('exam',20)]:
            settings,records=assemble(dict(topic=topic,contents=TOPIC_CONTENTS[topic],difficulty=difficulty,minutes=minutes,purpose='homework'))
            stem=f'{topic}-{difficulty}-{minutes}'
            for audience in ['student','teacher']:
                (out/f'{stem}-{audience}.md').write_text(paper_report(dict(worksheet_settings=settings),records,audience),encoding='utf-8')
            lines.append(f'- {VISIBLE_TOPICS[topic]} {DIFFICULTIES[difficulty][0]} {minutes} 分钟：[学生版]({stem}-student.md) · [教师版]({stem}-teacher.md)')
    lines+=['','## 技术验证','',
        '两轮 60 道新增题均通过 Java 编译与执行核对。16 道方法实现题附额外断言；文本文件题读取隔离测试目录内的真实文件。技术验证不等于教学质量审核。', '',
        '[逐场景缺口明细](scenario-details.md) · [原始结果](after.json) · [Java 检查明细](java_checks/verification.json)']
    (out/'report.md').write_text('\n'.join(lines),encoding='utf-8')
    html=['<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>题库缺口与本轮补题</title>',
        '<style>body{font:16px/1.7 system-ui,sans-serif;max-width:1000px;margin:32px auto;padding:0 20px;color:#22352c}h1,h2{line-height:1.4}table{border-collapse:collapse;width:100%}td,th{padding:8px;border:1px solid #ccc;text-align:left}pre{white-space:pre-wrap;overflow-wrap:anywhere;background:#f3f5f3;padding:16px;font:14px/1.6 Consolas,monospace}details{border:1px solid #ccd6cd;margin:12px 0;padding:14px}summary{cursor:pointer;font-weight:bold}.table{overflow:auto}.note{background:#f5f0df;padding:16px}</style>',
        '<a href="/">← 返回生成作业</a><h1>题库缺口与本轮补题</h1>',
        f'<p>完整组卷条件 <b>{complete(before)} → {complete(after)} / 126</b>。两轮累计补充 60 题，题库共 275 题；本轮新增字符串算法、文本文件各 15 题，完整组合从上一轮的 31 增至当前结果。</p>',
        '<p>范围：21 课题、3 档难度、10／20 分钟，勾选课题全部考查内容。四个原先最缺题的课题均已完成首批扩充。剩余缺口如实保留在下表。</p>',
        '<p class="note">用时为估计，考试风格非真题，新增题仍待教师审核。60 道 Java 验证通过不代表难度和课堂适用性已经确认。</p>',
        '<h2>全课题前后对比</h2><p>每课题共 6 种条件；“可换题位”是场景中的题位合计。完整组卷同时要求时间匹配、所选内容覆盖。</p><div class="table"><table><tr><th>课题</th><th>完整组合</th><th>时长缺口</th><th>可换题位</th></tr>']
    html += ['<tr>'+''.join('<td>'+escape(v)+'</td>' for v in row)+'</tr>' for row in table]
    html += ['</table></div><details><summary>展开全部 126 种条件的具体缺口</summary><p>可替换为可替换题位数／当前题数；第二套新题数仅与第一套比较。</p><div class="table"><table><tr><th>课题</th><th>难度</th><th>实际／目标</th><th>缺失内容</th><th>可替换</th><th>第二套新题</th></tr>']
    html += ['<tr>'+''.join('<td>'+escape(v)+'</td>' for v in row)+'</tr>' for row in detail_rows]
    html += ['</table></div></details><h2>两轮新增 60 题集中审核</h2><p>展开查看题目、答案、参考实现与逐项评分。请反馈题号，以及题干、难度或时间需要怎样调整。</p>']
    ordered=sorted(QUESTIONS,key=lambda q: (0 if q['id'].startswith(('GA_','GF_')) else 1, QUESTIONS.index(q)))
    for q in ordered:
        html.append('<details><summary>'+escape(f'{q["id"]}　{q["title"]}　'+{2:'基础',3:'巩固',4:'考试风格'}[q['level']]+f'　{q["minutes"]} 分钟')+'</summary>')
        for label,value in [('题目代码',q['code']),('题目要求',q['task']),('参考答案',q['answer']),('参考实现',q.get('reference_solution','')),('解析','\n'.join(q['reasoning'])),('评分标准',q['rubric']),('常见错误','\n'.join(q['errors'])),('讲解建议',q['intervention'])]:
            if value:html.append('<h3>'+label+'</h3><pre>'+escape(value)+'</pre>')
        html.append('</details>')
    html.append('</html>')
    style=next(item for item in html if item.startswith('<style>'))
    (out/'report.css').write_text(style[len('<style>'):-len('</style>')],encoding='utf-8')
    html[html.index(style)]='<link rel="stylesheet" href="/gap-review.css">'
    (out/'report.html').write_text('\n'.join(html),encoding='utf-8')
    print(f'Complete scenarios: {complete(before)} -> {complete(after)} / 126')


if __name__=='__main__':main()
