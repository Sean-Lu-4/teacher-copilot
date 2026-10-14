"""Deterministic, time-bounded assembly from the local Methods question bank."""
import json
import re
from pathlib import Path

from .expanded_bank import QUESTIONS as METHODS, BANK_VERSION as METHODS_VERSION
from .conditionals_bank import QUESTIONS as CONDITIONALS, BANK_VERSION as CONDITIONALS_VERSION
from .questions import create_record, content_hash
from .csa_bank import QUESTIONS as CSA
from .csa_curriculum import GROUPS, LABELS, UNITS, VERSION as CSA_VERSION, objective
from .homework_bank import QUESTIONS as HOMEWORK, VERSION as HOMEWORK_VERSION
from .gap_bank import QUESTIONS as GAP, VERSION as GAP_VERSION

QUESTIONS = METHODS + CONDITIONALS + CSA + HOMEWORK + GAP
BANK_VERSION = METHODS_VERSION + '+' + CONDITIONALS_VERSION + '+' + CSA_VERSION + '+' + HOMEWORK_VERSION + '+' + GAP_VERSION

TOPICS = {'methods': '方法调用（Methods）',
          'method-calls': '方法调用（Methods）· 参数与调用',
          'method-returns': '方法调用（Methods）· 返回值与跟踪',
          'conditionals': '条件判断与逻辑运算'}
TOPIC_CONTENTS = {'methods': ['parameters', 'calls', 'returns', 'tracing'],
                  'method-calls': ['parameters', 'calls'],
                  'method-returns': ['returns', 'tracing'],
                  'conditionals': ['conditions', 'branches', 'logic', 'nested']}
CONTENT = {
    'parameters': ('参数与实参', {'parameters', 'argument_count', 'argument_order', 'argument_types'}),
    'calls': ('方法调用与 void', {'void'}),
    'returns': ('返回值的使用', {'return_use'}),
    'tracing': ('代码执行跟踪', {'trace'}),
    'conditions': ('比较与边界条件', {'if_conditions'}),
    'branches': ('if / else 与多分支', {'if_branches'}),
    'logic': ('逻辑运算与短路', {'if_logic'}),
    'nested': ('嵌套条件判断', {'if_nested'}),
}
TOPICS.update({key: title for key, (title, _) in GROUPS.items()})
TOPIC_CONTENTS.update({key: [objective(t) for t in topics] for key, (_, topics) in GROUPS.items()})
CONTENT.update({objective(t): (t + ' ' + title, {objective(t)}) for t, title in LABELS.items()})
BANKS = {'methods': METHODS, 'method-calls': METHODS, 'method-returns': METHODS,
         'conditionals': CONDITIONALS}
BANKS.update({key: [q for q in CSA if q['ced_topics'][0] in topics] for key, (_, topics) in GROUPS.items()})
DIFFICULTIES = {'basic': ('基础', {1, 2}), 'advanced': ('巩固', {3}),
                'exam': ('考试', {4})}
EXAM_TYPES = {'trace': '代码跟踪', 'write': '编程实现', 'concept': '概念与设计'}
CORE = set().union(*(v[1] for v in CONTENT.values()))

# Legacy identifiers remain readable, but are not separate navigation entries.
VISIBLE_TOPICS = {key: title.split(' · ',1)[-1] for key,(title,_) in GROUPS.items() if key!='csa-logic'}
VISIBLE_TOPICS.update({'csa-calls':'方法调用（Methods）','csa-math':'数学运算（Math）',
                       'csa-strings':'字符串（String）','csa-selection':'条件判断与逻辑运算'})
TOPICS.update(VISIBLE_TOPICS)
TOPIC_CONTENTS['csa-calls']=['ced_1_9','parameters','calls','returns','tracing']
TOPIC_CONTENTS['csa-selection'] += TOPIC_CONTENTS['csa-logic']
BANKS['csa-calls'] = BANKS['csa-calls'] + METHODS
BANKS['csa-selection'] = BANKS['csa-selection'] + BANKS['csa-logic'] + CONDITIONALS
for key,(_,topics) in GROUPS.items():
    scope=topics + (['2.5','2.6'] if key=='csa-selection' else [])
    BANKS[key] += [q for q in HOMEWORK + GAP if q['ced_topics'][0] in scope]
ALL_CSA_CONTENTS = list(CONTENT)
BANKS['all-csa'] = QUESTIONS
APPROVED_QUESTIONS = []


def _load_imported_ap_questions():
    """Convert the teacher-supplied AP PDFs into normal, selectable bank rows.

    The source-bank page remains the audit view.  These rows are the teacher-facing
    view: each item has a Unit/topic, readable stem/options, answer, timing and
    the same schema as the built-in questions so it can be selected for a paper.
    """
    path = Path(__file__).parent / 'imported_bank' / 'bank.json'
    if not path.is_file():
        return []
    try:
        raw = json.loads(path.read_text(encoding='utf-8'))
    except (OSError, ValueError):
        return []
    result = []
    for source in raw.get('questions', []):
        source_topic = source.get('topic_id')
        target_topic = source_topic if source_topic in GROUPS else 'csa-selection'
        objective_id = objective(GROUPS[target_topic][1][0])
        options = source.get('options') or {}
        task_text = source.get('text', '').strip()
        # PDF extraction often leaves the answer choices in the raw stem.  The
        # browser renders parsed choices separately, so keep only the prompt
        # here to avoid showing every option twice.
        if options:
            option_start = re.search(r'(?m)^\s*\(A\)\s*', task_text)
            if option_start:
                task_text = task_text[:option_start.start()].rstrip()
        content = {
            'id': 'AP-' + str(source.get('id', '')).replace('-', ''),
            'title': source.get('title') or f"AP Unit {source.get('unit', '')} · 题目 {source.get('number', '')}",
            'origin': 'AP Progress Check / Question Bank（教师提供资料）',
            'code': '// AP source question; see the task text and linked original PDF.',
            'task': task_text,
            'answer': source.get('answer', '').strip() or '请查看原版评分指南。',
            'rubric': '选择题按答案键判定；FRQ 请按原版评分指南逐小问评分。',
            'intervention': '先让学生独立作答，再对照英文评分指南定位错误原因。',
            'objectives': [objective_id],
            'reasoning': ['阅读题干和给定代码。', '逐步检查条件、数据变化或算法过程。', '用答案和评分指南核对结论。'],
            'errors': ['忽略题目中的边界条件。', '只看最终选项，没有检查中间步骤。'],
            'level': int(source.get('level', 2)),
            'minutes': int(source.get('minutes', 2 if source.get('kind') == 'MCQ' else 12)),
            'question_kind': source.get('question_kind') or ('concept' if source.get('kind') == 'MCQ' else 'write'),
            'ced_topics': [objective_id],
            'ap_unit': str(source.get('unit', '')),
            'ap_topic': source.get('topic_title') or '未命名 Topic',
            'source_item_id': source.get('id'),
        }
        if options and source.get('answer_key') in options:
            content['options'] = options
            content['answer_key'] = source['answer_key']
            content['distractors'] = {key: '请结合原版英文解析复盘该选项。'
                                      for key in options if key != source['answer_key']}
        content['_ap_sources'] = source.get('sources', [])
        result.append(content)
    return result


# Imported rows stay outside the deterministic legacy bank by default. This
# keeps existing coverage audits stable; selected AP rows are added on demand
# when a teacher chooses them from the browser.
IMPORTED_AP = _load_imported_ap_questions()
_imported_topic_by_id = {q.get('id'): q.get('topic_id') for q in json.loads(
    (Path(__file__).parent / 'imported_bank' / 'bank.json').read_text(encoding='utf-8')
).get('questions', [])}
for _question in IMPORTED_AP:
    _source_topic = _imported_topic_by_id.get(_question.get('source_item_id'))
    _target = _source_topic if _source_topic in VISIBLE_TOPICS and _source_topic != 'all-csa' else 'csa-selection'
    _question['_bank_topic'] = _target

IMPORTED_BY_TOPIC = {}
for _question in IMPORTED_AP:
    IMPORTED_BY_TOPIC.setdefault(_question['_bank_topic'], []).append(_question)


def register_approved_question(submission):
    """Add a reviewed teacher submission to the in-process bank."""
    title = str(submission.get('title') or '').strip()
    qid = 'T-' + str(submission.get('id') or 'QUESTION').replace('-', '')[-10:]
    if any(q.get('id') == qid for q in QUESTIONS):
        return qid
    topic_text = str(submission.get('topic') or '').strip()
    topic_id = next((key for key, value in VISIBLE_TOPICS.items() if key == topic_text or value == topic_text), 'all-csa')
    objective_id = (TOPIC_CONTENTS.get(topic_id) or ['practice'])[0]
    content = {
        'id': qid, 'title': title, 'origin': '教师提交并审核通过',
        'code': str(submission.get('code') or ''), 'task': str(submission.get('task') or '').strip(),
        'answer': str(submission.get('answer') or '').strip(), 'rubric': '答案与题目要求一致，过程清晰。',
        'intervention': '请回到题干，先标出输入、步骤和预期输出，再逐步检查。',
        'objectives': [objective_id], 'reasoning': ['先确认题目要求。', '逐步执行代码或推导答案。', '用结果核对题目条件。'],
        'errors': ['跳过题目条件。', '只看最终答案，未检查中间步骤。'],
        'level': int(submission.get('level') or 2), 'minutes': int(submission.get('minutes') or 5),
        'question_kind': 'concept', 'ced_topics': [objective_id]
    }
    QUESTIONS.append(content)
    APPROVED_QUESTIONS.append(content)
    BANKS.setdefault(topic_id, []).append(content)
    QUESTION_VERSIONS[qid] = 'teacher-approved'
    return qid
VISIBLE_TOPICS['all-csa'] = '全课程混合组卷'
QUESTION_VERSIONS = {q['id']:version for bank,version in [(METHODS,METHODS_VERSION),(CONDITIONALS,CONDITIONALS_VERSION),(CSA,CSA_VERSION),(HOMEWORK,HOMEWORK_VERSION),(GAP,GAP_VERSION)] for q in bank}
QUESTION_VERSIONS.update({q['id']: 'ap-import-v2' for q in IMPORTED_AP})
LEGACY_TOPICS={'methods':'csa-calls','method-calls':'csa-calls','method-returns':'csa-calls','conditionals':'csa-selection','csa-logic':'csa-selection'}


def selection_objectives(question, topic):
    ids=set(question['objectives']) & CORE
    if topic=='csa-calls' and ids=={'ced_1_10'}:
        return {'void','return_use','trace'}
    if topic=='csa-selection':
        mapping={'if_conditions':'ced_2_2','if_branches':'ced_2_3','if_logic':'ced_2_5','if_nested':'ced_2_4'}
        if question['id']=='IE03': return {'ced_2_6'}
        return {mapping.get(i,i) for i in ids}
    return ids


def navigation_settings(settings):
    """Presentation-only migration; original saved questions/settings stay intact."""
    if not settings: return None
    result=dict(settings)
    old=result['topic'];result['topic']=LEGACY_TOPICS.get(old,old)
    if old=='conditionals':
        mapping={'conditions':'ced_2_2','branches':'ced_2_3','logic':'ced_2_5','nested':'ced_2_4'}
        result['contents']=[mapping[c] for c in result['contents']]
    if old=='csa-calls' and 'ced_1_10' in result['contents']:
        result['contents']=[c for c in result['contents'] if c!='ced_1_10']+['calls','returns','tracing']
    result['unit']=int(GROUPS[result['topic']][1][0].split('.')[0]) if result['topic'] in GROUPS else 1
    return result


def catalog(include_mixed=False):
    topics=[dict(id=key, title=title, unit=(GROUPS[key][1][0].split('.')[0] if key in GROUPS else '1'), bank_count=len(BANKS[key]),
                            contents=[dict(id=c, title=CONTENT[c][0]) for c in (ALL_CSA_CONTENTS if key=='all-csa' else TOPIC_CONTENTS[key])])
                for key, title in VISIBLE_TOPICS.items() if include_mixed or key!='all-csa']
    return dict(bank_count=len(QUESTIONS), bank_version=BANK_VERSION,
                objective_labels={k: title for k, (title, _) in CONTENT.items()},
                units=[dict(id=str(key),title=f'Unit {key} · {title}') for key,title in UNITS.items()],
                homework_minutes=[10,20],
                topics=topics,
                difficulties=[dict(id=key, title=value[0]) for key, value in DIFFICULTIES.items()])


def bank_data():
    """Compact, read-only question-bank view for teacher search and review."""
    topic_by_id={}
    for topic, bank in BANKS.items():
        if topic not in VISIBLE_TOPICS:
            continue
        for question in bank:
            topic_by_id.setdefault(question['id'], topic)
    rows=[]
    for question in QUESTIONS:
        topic=topic_by_id.get(question['id'])
        if not topic:
            continue
        rows.append(dict(id=question['id'], title=question['title'], topic=topic,
                         topic_title=VISIBLE_TOPICS[topic], level=question['level'],
                         minutes=question['minutes'], question_kind=question.get('question_kind') or 'concept',
                         objectives=list(question.get('objectives', [])),
                         origin=question.get('origin',''), code=question.get('code',''),
                         task=question.get('task',''), answer=question.get('answer',''),
                         rubric=question.get('rubric',''), prerequisites=question.get('prerequisites',''),
                         options=question.get('options', {}), answer_key=question.get('answer_key',''),
                         ap_unit=question.get('ap_unit',''), ap_topic=question.get('ap_topic',''),
                         source_item_id=question.get('source_item_id',''), source_refs=question.get('_ap_sources', [])))
    original_count = len(rows)
    # Imported AP material is presented in the same searchable browser, while
    # remaining excluded from automatic generation until a teacher selects it.
    for question in IMPORTED_AP:
        topic = question.get('_bank_topic', 'csa-selection')
        rows.append(dict(id=question['id'], title=question['title'], topic=topic,
                         topic_title=VISIBLE_TOPICS.get(topic, topic), level=question['level'],
                         minutes=question['minutes'], question_kind=question.get('question_kind', 'concept'),
                         question_format='mcq' if question.get('options') else 'frq',
                         objectives=list(question.get('objectives', [])), origin=question.get('origin', ''),
                         code=question.get('code', ''), task=question.get('task', ''), answer=question.get('answer', ''),
                         rubric=question.get('rubric', ''), prerequisites='', options=question.get('options', {}),
                         answer_key=question.get('answer_key', ''), ap_unit=question.get('ap_unit', ''),
                         ap_topic=question.get('ap_topic', ''), source_item_id=question.get('source_item_id', ''),
                         source_refs=question.get('_ap_sources', [])))
    return dict(version=BANK_VERSION, count=original_count, total_count=len(rows), questions=rows,
                topics=[dict(id=t['id'],title=t['title']) for t in catalog()['topics']],
                difficulties=[dict(id=k,title=v[0]) for k,v in DIFFICULTIES.items()],
                question_types=[dict(id='mcq', title='MCQ 选择题'), dict(id='frq', title='FRQ 开放题')])


def validate_settings(settings):
    if not isinstance(settings, dict):
        raise ValueError('请选择列表中的课题。')
    topics = settings.get('topics', [])
    if (not topics and settings.get('topic') not in TOPICS and settings.get('topic') != 'all-csa'):
        raise ValueError('请选择列表中的课题。')
    if not isinstance(topics, list) or len(topics) > 24 or any(t not in VISIBLE_TOPICS or t == 'all-csa' for t in topics):
        raise ValueError('请选择有效的课题。')
    topics = list(dict.fromkeys(topics))
    if topics:
        settings = dict(settings, topic=topics[0] if len(topics) == 1 else 'all-csa')
    contents = settings.get('contents')
    if not isinstance(contents, list) or not contents or any(not isinstance(k, str) or k not in CONTENT for k in contents):
        raise ValueError('请至少选择一项考查内容。')
    valid_contents = ALL_CSA_CONTENTS if settings['topic']=='all-csa' else TOPIC_CONTENTS[settings['topic']]
    if topics:
        valid_contents = set().union(*(set(TOPIC_CONTENTS[t]) for t in topics))
    if any(k not in valid_contents for k in contents):
        raise ValueError('考查内容不属于当前课题，请重新选择。')
    purpose = settings.get('purpose')
    if settings['topic']=='all-csa' and purpose!='exam' and not topics:
        raise ValueError('跨课题组卷请选择正式试卷模式。')
    if purpose not in {None, 'homework', 'exam'}:
        raise ValueError('请选择快速练习或正式试卷。')
    difficulty = settings.get('difficulty')
    if not isinstance(difficulty, str) or (difficulty not in DIFFICULTIES and not (purpose=='exam' and difficulty=='mixed')):
        raise ValueError('请选择有效的难度。')
    minutes = settings.get('minutes')
    limit = (3, 90) if purpose in {None, 'homework'} else (30, 180)
    if type(minutes) is not int or not limit[0] <= minutes <= limit[1]:
        raise ValueError(f'时间应为 {limit[0]} 至 {limit[1]} 分钟的整数。')
    homework=purpose in {None, 'homework'}
    if purpose=='homework' and minutes not in (10,20):
        raise ValueError('请选择 10 分钟或 20 分钟作业。')
    normalized=dict(topic=settings['topic'], contents=list(dict.fromkeys(contents)), difficulty=difficulty, minutes=minutes)
    if topics:
        normalized['topics']=topics
    if purpose=='homework':
        normalized['purpose']='homework'
    elif purpose=='exam':
        question_count=settings.get('question_count')
        total_marks=settings.get('total_marks')
        question_types=settings.get('question_types')
        if type(question_count) is not int or not 3 <= question_count <= 30:
            raise ValueError('正式试卷题量应为 3 至 30 题。')
        if type(total_marks) is not int or not 10 <= total_marks <= 100:
            raise ValueError('正式试卷总分应为 10 至 100 分。')
        if total_marks < question_count:
            raise ValueError('每道题至少 1 分，总分不能少于题目数量。请提高总分或减少题量。')
        if not isinstance(question_types,list) or not question_types or any(t not in EXAM_TYPES for t in question_types):
            raise ValueError('请至少选择一种题型。')
        normalized.update(purpose='exam', question_count=question_count, total_marks=total_marks,
                          question_types=list(dict.fromkeys(question_types)))
        selected_ids=settings.get('selected_ids', [])
        if not isinstance(selected_ids,list) or len(selected_ids)>30 or any(not isinstance(qid,str) for qid in selected_ids):
            raise ValueError('自选题目清单无效。')
        if selected_ids:
            normalized['selected_ids']=list(dict.fromkeys(selected_ids))
    return normalized


def selected_bank(settings):
    selected_ids = set(settings.get('selected_ids') or [])
    imported_selected = [q for q in IMPORTED_AP if q['id'] in selected_ids]
    if settings.get('topics'):
        bank = list({q['id']: q for t in settings['topics'] for q in BANKS[t]}.values())
    else:
        bank = list(BANKS[settings['topic']])
    if imported_selected:
        bank.extend(q for q in imported_selected if q['id'] not in {item['id'] for item in bank})
    return bank


def assemble(settings, recent=None):
    settings = validate_settings(settings)
    contents, difficulty, minutes = settings['contents'], settings['difficulty'], settings['minutes']
    homework = settings.get('purpose') == 'homework'
    wanted = set().union(*(CONTENT[c][1] for c in contents))
    levels = DIFFICULTIES[difficulty][1]
    bank = selected_bank(settings)
    version = (CSA_VERSION if settings['topic'] in GROUPS or settings['topic']=='all-csa' else
               CONDITIONALS_VERSION if settings['topic'] == 'conditionals' else METHODS_VERSION)
    eligible = [q for q in bank if q['level'] in levels and selection_objectives(q,settings['topic'])
                and selection_objectives(q,settings['topic']) <= wanted]
    recent = recent or {}
    def reuse_cost(group):
        return sum(recent.get(eligible[i]['id'], 0) for i in group)
    # Bounded dynamic programming: retain one subset for each time/coverage/level
    # state instead of materializing every subset of an expanding bank.
    bits = {key: 1 << i for i, key in enumerate(sorted(CORE))}
    states = {(0, 0, 0): ()}
    for index, question in enumerate(eligible):
        mask = sum(bits[key] for key in selection_objectives(question,settings['topic']))
        for (used, covered, level_mask), group in list(states.items()):
            total = used + question['minutes']
            if total <= minutes:
                key = (total, covered | mask, level_mask | (1 << question['level']))
                proposal = group + (index,)
                if key not in states or reuse_cost(proposal) < reuse_cost(states[key]):
                    states[key] = proposal
    candidates = [key for key in states if key[0]]
    if not candidates:
        raise ValueError('本地题库暂时没有同时符合这些内容、难度和时间的题目。可增加考查内容、调整难度或延长时间。')
    # Homework first fits the requested duration, then maximizes coverage.
    best = max(candidates, key=lambda key: (((key[0]==minutes, key[0]>=minutes*.9, key[1].bit_count(),key[0]) if homework else
                                          (key[1].bit_count(), key[2].bit_count(), key[0])) + (-reuse_cost(states[key]),)))
    chosen = sorted((eligible[i] for i in states[best]), key=lambda q: q['level'])
    records = [create_record(q, QUESTION_VERSIONS[q['id']], dict(kind='original', sources=[])) for q in chosen]
    normalized=dict(topic=settings['topic'], contents=list(dict.fromkeys(contents)), difficulty=difficulty, minutes=minutes)
    if settings.get('topics'): normalized['topics']=settings['topics']
    if homework: normalized['purpose']='homework'
    return normalized, records


def assemble_exam(settings, recent=None):
    """Choose an exact-size formal paper while maximizing coverage and time use."""
    settings=validate_settings(dict(settings, purpose='exam'))
    wanted=set().union(*(CONTENT[c][1] for c in settings['contents']))
    levels=DIFFICULTIES.get(settings['difficulty'], ('混合',{1,2,3,4}))[1]
    kinds=set(settings['question_types'])
    bank=selected_bank(settings)
    eligible=[q for q in bank if q['level'] in levels and (q.get('question_kind') or 'concept') in kinds
              and selection_objectives(q,settings['topic']) and selection_objectives(q,settings['topic']) <= wanted]
    if settings.get('selected_ids'):
        selected=set(settings['selected_ids'])
        if not selected <= {q['id'] for q in bank}:
            raise ValueError('自选清单包含其他课题或已失效题目。当前仅支持同一课题组卷，请返回题库调整清单。')
        if len(selected) < settings['question_count']:
            raise ValueError(f'清单只有 {len(selected)} 道题，无法生成 {settings["question_count"]} 道题。请减少题量或返回题库继续选题。')
        eligible=[q for q in eligible if q['id'] in selected]
        if len(eligible) < settings['question_count']:
            raise ValueError(f'清单中只有 {len(eligible)} 道题符合所选内容、难度和题型，少于要求的 {settings["question_count"]} 道。请放宽筛选条件或补充选题。')
    if not eligible:
        raise ValueError('题库中没有符合当前内容、难度和题型的题目。')
    count = settings['question_count']
    if len(eligible) < count:
        raise ValueError(f'符合当前内容、难度和题型的题目只有 {len(eligible)} 道，无法生成 {count} 道题。请减少题量，或选择混合难度、增加考查内容和题型。')
    minimum_minutes = sum(sorted(q['minutes'] for q in eligible)[:count])
    if minimum_minutes > settings['minutes']:
        raise ValueError(f'当前条件下，{count} 道题至少需要 {minimum_minutes} 分钟，超过设定的 {settings["minutes"]} 分钟。请将考试时间调至至少 {minimum_minutes} 分钟，或减少题量。')
    recent=recent or {}
    bits={key:1<<i for i,key in enumerate(sorted(CORE))}
    states={(0,0,0):((),0)}
    for question in eligible:
        mask=sum(bits[key] for key in selection_objectives(question,settings['topic']))
        for (count,used,covered),(group,cost) in list(states.items()):
            if count >= settings['question_count'] or used + question['minutes'] > settings['minutes']:
                continue
            key=(count+1,used+question['minutes'],covered|mask)
            proposal=group+(question,)
            proposal_cost=cost+recent.get(question['id'],0)
            if key not in states or proposal_cost < states[key][1]:
                states[key]=(proposal,proposal_cost)
        # Bound cross-course coverage search; keep the cheapest path for each
        # count/time pair as well as diverse high-coverage paths.
        if len(states)>12000:
            cheapest={}
            for key,value in states.items():
                pair=key[:2]
                if pair not in cheapest or value[1]<cheapest[pair][1][1]:
                    cheapest[pair]=(key,value)
            best=sorted(states.items(),key=lambda x:(x[0][2].bit_count(),-x[1][1]),reverse=True)[:8000]
            states=dict(best)
            states.update(dict(cheapest.values()))
    candidates=[(key,value) for key,value in states.items() if key[0]==settings['question_count']]
    if not candidates:
        raise ValueError('当前条件无法组成指定题量和时长的正式试卷，请增加考试时间或减少题量。')
    key,(chosen,_) = max(candidates,key=lambda item:(item[0][2].bit_count(),item[0][1],-item[1][1]))
    records=[create_record(q,QUESTION_VERSIONS[q['id']],dict(kind='original',sources=[])) for q in sorted(chosen,key=lambda q:(q['level'],q['id']))]
    weights={'write': 6, 'trace': 4, 'concept': 3}
    total_weight=sum(weights.get(r['content'].get('question_kind') or 'concept',3) for r in records)
    remaining=settings['total_marks']
    for i,record in enumerate(records):
        base=weights.get(record['content'].get('question_kind') or 'concept',3)
        marks=max(1,round(settings['total_marks']*base/total_weight)) if i < len(records)-1 else max(1,remaining)
        marks=min(marks,remaining-(len(records)-i-1))
        record['content']['marks']=marks
        record['content_hash']=content_hash(record['content'])
        remaining-=marks
    return settings,records


def replace_question(settings, records, index, recent=None):
    """Preserve assessed coverage and difficulty without exceeding the time budget."""
    if not settings or (settings.get('difficulty') not in DIFFICULTIES and not (settings.get('purpose')=='exam' and settings.get('difficulty')=='mixed')):
        raise ValueError('这份旧练习不支持换题，请使用当前设置生成一份新作业。')
    old = records[index]
    if old['locked']:
        raise ValueError('这道题已锁定，请先解锁再换题。')
    topic = settings['topic']
    wanted = set().union(*(CONTENT[c][1] for c in settings['contents']))
    required = selection_objectives(old['content'], topic)
    other_coverage = set().union(*(selection_objectives(r['content'], topic) for i, r in enumerate(records) if i != index))
    other_minutes = sum(r['content']['minutes'] for i, r in enumerate(records) if i != index)
    used = {r['content']['id'] for r in records}
    for record in records:
        for event in record['history']:
            if event.get('action') == 'replace':
                used.add(event['detail']['previous_content']['id'])
    levels=DIFFICULTIES.get(settings['difficulty'], ('混合',{1,2,3,4}))[1]
    candidates = [q for q in selected_bank(settings) if q['id'] not in used
                  and q['level'] in levels
                  and other_minutes + q['minutes'] <= settings['minutes']
                  and required & selection_objectives(q, topic)
                  and required <= (selection_objectives(q, topic) | other_coverage)
                  and selection_objectives(q, topic) <= wanted]
    if not candidates:
        raise ValueError('暂无兼顾考查内容、难度和作业时长的新题可替换；本次作业保持不变。可以修改原题，或调整设置生成新作业。')
    candidate = min(candidates, key=lambda q: (abs(q['minutes'] - old['content']['minutes']), (recent or {}).get(q['id'], 0)))
    return create_record(candidate, QUESTION_VERSIONS[candidate['id']], dict(kind='original', sources=[]))


def summary(settings, records):
    total = sum(r['content']['minutes'] for r in records)
    warnings = []
    if settings:
        target = settings['minutes']
        if total < target:
            warnings.append(f'符合条件的练习共约 {total} 分钟，少于设定的 {target} 分钟；未重复题目凑时长。')
        if total > target:
            warnings.append(f'修改后预计用时 {total} 分钟，超过设定的 {target} 分钟，请调整。')
        covered = set().union(*(selection_objectives(r['content'],settings['topic']) for r in records))
        if 'ced_1_10' in settings['contents'] and any('ced_1_10' in r['content']['objectives'] for r in records):
            covered.add('ced_1_10')
        for key in settings['contents']:
            title, objectives = CONTENT[key]
            if not objectives <= covered:
                warnings.append(f'“{title}”尚未完整覆盖，可增加练习时间或调整难度。')
        if settings['difficulty'] == 'mixed' and len({r['content']['level'] for r in records}) < 4:
            warnings.append('本次未包含全部四个难度层级；当前题目已按由易到难排列。')
    result=dict(minutes=total, count=len(records), warnings=warnings)
    if settings and settings.get('purpose')=='exam':
        actual_marks=sum(r['content'].get('marks',0) for r in records)
        if actual_marks != settings['total_marks']:
            warnings.append(f'当前题目合计 {actual_marks} 分，与设定的 {settings["total_marks"]} 分不一致，请核对后再发给学生。')
        result['exam']=dict(target_minutes=settings['minutes'],question_count=settings['question_count'],
                            total_marks=settings['total_marks'],actual_marks=sum(r['content'].get('marks',0) for r in records),
                            question_types=sorted({r['content'].get('question_kind') or 'concept' for r in records}))
    if settings and settings.get('purpose')=='homework':
        missing=[c for c in settings['contents'] if not CONTENT[c][1] <= covered]
        result['homework']=dict(target_minutes=settings['minutes'],actual_minutes=total,
            shortfall_minutes=max(0,settings['minutes']-total),missing_contents=missing,
            status='complete' if total==settings['minutes'] and not missing else 'partial',
            source='local',api_enabled=False,
            supplement_request=(dict(topic=settings['topic'],contents=missing or settings['contents'],
                                    strategy='rebalance' if missing else 'add',target_minutes=settings['minutes'],
                                    difficulty=settings['difficulty'],minutes=max(0,settings['minutes']-total),
                                    excluded_ids=[r['content']['id'] for r in records]) if missing or total<settings['minutes'] else None))
    return result


def paper_report(plan, records, audience):
    from .review_app import fence
    teacher = audience == 'teacher'
    settings = plan.get('worksheet_settings')
    info = summary(settings, records)
    topic = plan.get('report_title') or TOPICS.get((settings or {}).get('topic')) or VISIBLE_TOPICS.get((settings or {}).get('topic'), 'Methods')
    paper_kind=' 作业' if (settings or {}).get('purpose')=='homework' else (' 正式试卷' if (settings or {}).get('purpose')=='exam' else ' 练习')
    lines = ['# AP CSA · ' + topic + paper_kind + ('（教师版）' if teacher else '（学生版）'), '',
             f"共 {info['count']} 题 · 预计作答 {info['minutes']} 分钟", '']
    if not teacher:
        lines += ['姓名：________________　班级：________________　日期：________________', '']
    for n, r in enumerate(records, 1):
        q = r['content']
        lines += [f"## 第 {n} 题 · {q['title']}", '', f"建议用时：{q['minutes']} 分钟" + (f" · 分值：{q['marks']} 分" if q.get('marks') else ''), '',
                  fence(q['code'], 'text' if q.get('question_kind')=='concept' else 'java'), '', fence(q['task']), '']
        for key, value in q.get('options', {}).items():
            lines += [f'{key}.', '', fence(value), '']
        if teacher:
            lines += ['### 答案与解析', '', q['answer'], '',
                      '正确选项：' + q['answer_key'] if q.get('answer_key') else '', '']
            lines += [f'{i}. {v}' for i, v in enumerate(q['reasoning'], 1)]
            if q.get('reference_solution'):
                lines += ['', '**参考实现**', '', fence(q['reference_solution'], 'java'), '']
            lines += ['', '**干扰项解释**', ''] if q.get('distractors') else []
            lines += [f'- {k}：{v}' for k, v in q.get('distractors', {}).items()]
            lines += ['', '评分：' + q['rubric'], '']
        else:
            lines += ['作答：', '', '____________________________________________________________', '',
                      '____________________________________________________________', '']
    return '\n'.join(lines)
