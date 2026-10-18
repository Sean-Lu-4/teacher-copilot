const $ = id => document.getElementById(id);
let data = null;
let page = 0;
const pageSize = 20;
let selected = new Set();
try { const saved = JSON.parse(localStorage.getItem('teacher-copilot-picked') || '[]'); if (Array.isArray(saved)) selected = new Set(saved.filter(id => typeof id === 'string')); } catch {}
const levelNames = {1: '基础识别', 2: '单步应用', 3: '巩固应用', 4: '考试风格'};
function updateSelected() {
  const rows = data.questions.filter(q => selected.has(q.id)); selected = new Set(rows.map(q => q.id));
  try { localStorage.setItem('teacher-copilot-picked', JSON.stringify([...selected])); } catch {}
  let panel = $('selection-panel'); if (!panel) { panel = document.createElement('section'); panel.id = 'selection-panel'; panel.className = 'bank-card'; $('results').before(panel); }
  panel.replaceChildren(); panel.append(Object.assign(document.createElement('h2'), {textContent: `组卷清单 · ${rows.length} 道题 · 预计 ${rows.reduce((n, q) => n + q.minutes, 0)} 分钟`}));
  const topics = new Set(rows.map(q => q.topic)); const hint = document.createElement('p'); hint.className = 'hint'; hint.textContent = topics.size > 1 ? '当前自选清单跨越多个课题；正式试卷会保留这些题目。' : rows.length < 3 ? '至少选择 3 道题后组卷。' : rows.length > 30 ? '最多带入 30 道候选题。' : '所选题目会带入正式试卷的候选范围。'; panel.append(hint);
  const list = document.createElement('ul'); for (const q of rows) { const li = document.createElement('li'); li.textContent = `${q.title} · ${q.topic_title} · ${q.minutes} 分钟 `; const remove = document.createElement('button'); remove.textContent = '移除'; remove.onclick = () => { selected.delete(q.id); render(); }; li.append(remove); list.append(li); } panel.append(list);
  const clear = document.createElement('button'); clear.textContent = '清空清单'; clear.disabled = !rows.length; clear.onclick = () => { selected.clear(); render(); }; panel.append(clear);
  const link = document.createElement('a'); link.id = 'use-selected'; link.className = 'primary bank-use'; link.textContent = `使用所选题目组卷（${rows.length}）`; link.href = rows.length >= 3 && rows.length <= 30 ? `/teacher?picked=${encodeURIComponent([...selected].join(','))}` : '#'; link.setAttribute('aria-disabled', String(rows.length < 3 || rows.length > 30)); panel.append(link);
}
function sourceLinks(q) { const box = document.createElement('div'); box.className = 'source-links'; for (const ref of (q.source_refs || [])) { const a = document.createElement('a'); a.target = '_blank'; a.rel = 'noopener'; a.href = `/source-pdf/${ref.document}.pdf#page=${ref.page}`; a.textContent = `${ref.role === 'SG' ? '答案/评分指南' : '原题'} · PDF 第 ${ref.page} 页`; box.append(a); } return box; }
function card(q) {
  const article = document.createElement('article'); article.className = 'bank-card'; const head = document.createElement('div'); head.className = 'bank-card-head'; const title = document.createElement('h2'); title.textContent = q.title; const meta = document.createElement('span'); meta.className = 'badge'; meta.textContent = `${q.units?.length ? 'Unit ' + q.units.join(' / ') + ' · ' : ''}${q.difficulty_status === 'unrated' ? '难度尚未标定' : (levelNames[q.level] || '')} · 预计 ${q.minutes} 分钟 · ${Object.keys(q.options || {}).length >= 4 && q.answer_key ? 'MCQ 选择题' : 'FRQ 编程题'}`; head.append(title, meta); article.append(head);
  const info = document.createElement('p'); info.className = 'hint'; info.textContent = `${(q.topic_titles || [q.topic_title]).join(' / ')}`; article.append(info); if(q.ced_topics?.length){const topics=document.createElement('p');topics.className='ced-topic-labels';topics.textContent=q.ced_topics.map(c=>`Topic ${c} · ${(data.ced_topics||[]).find(t=>t.id===c)?.title||''}`).join(' / ');article.append(topics);} article.append(sourceLinks(q)); const pick = document.createElement('button'); pick.className = 'secondary bank-pick'; pick.textContent = selected.has(q.id) ? '已加入组卷清单' : '加入组卷清单'; pick.onclick = () => { if (selected.has(q.id)) selected.delete(q.id); else selected.add(q.id); updateSelected(); pick.textContent = selected.has(q.id) ? '已加入组卷清单' : '加入组卷清单'; }; article.append(pick);
  if (q.code && !String(q.code).startsWith('// AP source question')) { const codeLabel = document.createElement('h3'); codeLabel.textContent = '代码'; article.append(codeLabel); const code = document.createElement('pre'); code.className = 'source-text code-text'; code.textContent = q.code; article.append(code); }
  const taskLabel = document.createElement('h3'); taskLabel.textContent = '题目'; article.append(taskLabel); const task = document.createElement('pre'); task.className = 'source-text'; task.textContent = q.task; if(q.question_images?.length){for(const filename of q.question_images){const img=document.createElement('img');img.src='/source-image/'+encodeURIComponent(filename);img.alt=q.title+' 原题页面';img.className='question-page';img.loading='lazy';article.append(img);}const transcript=document.createElement('details');const label=document.createElement('summary');label.textContent='题目文字';transcript.append(label,task);article.append(transcript);}else article.append(task);
  if (q.options && Object.keys(q.options).length) { const options = document.createElement('div'); options.className = 'ap-options'; for (const [key, value] of Object.entries(q.options)) { const p = document.createElement('p'); p.textContent = `(${key}) ${value}`; options.append(p); } article.append(options); }
  const details = document.createElement('details'); const summary = document.createElement('summary'); summary.textContent = q.reference_solution ? '参考答案与评分（非官方原版）' : '答案与评分指南'; details.append(summary); const answer = document.createElement('pre'); answer.className = 'source-text answer-text'; answer.textContent = q.answer || '请查看原版评分指南。'; details.append(answer); if(q.reference_solution){for(const text of [q.reference_solution,q.rubric]){const pre=document.createElement('pre');pre.className='source-text';pre.textContent=text;details.append(pre);}} if (q.answer_key) { const key = document.createElement('p'); key.className = 'answer-key'; key.textContent = `正确答案：${q.answer_key}`; details.append(key); } article.append(details); return article;
}
function matches(q, skip='') {
  const query=$('search').value.trim().toLowerCase(), topic=$('topic').value, unit=$('unit').value, level=$('level').value, kind=$('kind').value;
  const max=Number($('minutes').value);
  return (!query || [q.id,q.title,q.task,q.code,q.ap_topic,...(q.ced_topics||[])].join(' ').toLowerCase().includes(query))
    && (skip==='unit' || !unit || (q.units || [q.ap_unit]).map(String).includes(unit))
    && (skip==='topic' || !topic || (topic.startsWith('ced:') ? (q.ced_topics||[]).includes(topic.slice(4)) : (q.topics || [q.topic]).includes(topic)))
    && (skip==='level' || !level || (q.difficulty_status==='unrated' ? level==='unrated' : String(q.level)===level))
    && (skip==='kind' || !kind || q.question_kind===kind)
    && (!max || max<1 || q.minutes<=max);
}
function refreshFacets(){
  for(const id of ['unit','topic','level','kind']){
    for(const option of $(id).options){
      if(!option.value)continue;
      option.dataset.label ||= option.textContent;
      const count=data.questions.filter(q=>matches(q,id) && (id==='unit' ? (q.units||[q.ap_unit]).map(String).includes(option.value) : id==='topic' ? (option.value.startsWith('ced:') ? (q.ced_topics||[]).includes(option.value.slice(4)) : (q.topics||[q.topic]).includes(option.value)) : id==='level' ? (q.difficulty_status==='unrated' ? option.value==='unrated' : String(q.level)===option.value) : q.question_kind===option.value)).length;
      option.textContent=`${option.dataset.label}（${count}）`;
      option.disabled=count===0 && !option.selected;
    }
  }
}
function render(){
  const rows=data.questions.filter(q=>matches(q));refreshFacets();
  const totalPages=Math.max(1,Math.ceil(rows.length/pageSize));page=Math.min(page,totalPages-1);
  $('count').textContent=`显示 ${rows.length} 道题 · 第 ${page+1}/${totalPages} 页`;
  $('previous').disabled=page===0;$('next').disabled=page>=totalPages-1;$('results').replaceChildren();
  if(!rows.length){const empty=document.createElement('div');empty.className='empty-bank';empty.textContent='当前组合没有匹配题目。选项后的数字显示可用题量；PDF 题目未标定难度时请选择“全部难度”或“尚未标定”。';const reset=document.createElement('button');reset.textContent='清除筛选，查看全部题目';reset.onclick=clearFilters;empty.append(document.createElement('br'),reset);$('results').append(empty);}
  else rows.slice(page*pageSize,(page+1)*pageSize).forEach(q=>$('results').append(card(q)));
  updateSelected();
}
function clearFilters(){['search','unit','topic','level','kind','minutes'].forEach(id=>$(id).value='');page=0;render();}
async function init() { try { const response = await fetch('/api/bank'); data = await response.json(); if (!response.ok) throw Error(data.error || '题库载入失败'); for (const t of data.topics) { const o = document.createElement('option'); o.value = t.id; o.textContent = t.title; $('topic').append(o); } const exact=document.createElement('optgroup');exact.label='具体 CED Topic'; for(const t of (data.ced_topics||[])){const o=document.createElement('option');o.value='ced:'+t.id;o.textContent=`${t.id} · ${t.title}`;exact.append(o);} $('topic').append(exact); for (const k of data.question_types) { const o = document.createElement('option'); o.value = k.id; o.textContent = k.title; $('kind').append(o); } for (const id of ['search', 'unit', 'topic', 'level', 'kind', 'minutes']) $(id).addEventListener(['search','minutes'].includes(id) ? 'input' : 'change', () => { page = 0; render(); }); $('previous').onclick = () => { page--; render(); }; $('next').onclick = () => { page++; render(); }; $('clear').onclick = clearFilters; $('filter-toggle').onclick=()=>{const open=$('filter-toggle').getAttribute('aria-expanded')!=='true';$('filter-toggle').setAttribute('aria-expanded',String(open));$('filter-toggle').closest('aside').classList.toggle('filters-open',open);}; render(); } catch (error) { $('count').textContent = error.message; } }
init();

