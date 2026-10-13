const $=id=>document.getElementById(id);
let catalogData;let pendingPicked=new URLSearchParams(location.search).get('picked')?.split(',').filter(Boolean)||[];let pendingTopic=new URLSearchParams(location.search).get('picked_topic')||'';
let token,state=null,busy=false,editing=null,dirty=false,answersExpanded=false;
const levels={1:'基础识别',2:'单步应用',3:'巩固应用',4:'考试风格'};
const goals={if_conditions:'比较与边界条件',if_branches:'if / else 与多分支',if_logic:'逻辑运算与短路',if_nested:'嵌套条件判断',parameters:'参数与实参',argument_count:'实参数量匹配',argument_order:'实参顺序匹配',argument_types:'实参类型兼容',void:'void 与非 void 方法',return_use:'返回值的使用',trace:'方法调用过程跟踪',errors:'常见错误',practice:'练习与达标检查'};
const specs=[['title','题目标题'],['minutes','预计作答分钟','number'],['level','难度层级（1–4）','number'],['objectives','考查内容（每行一项）','list'],['code','Java 代码','code'],['task','题干与要求','text'],['answer','参考答案','text'],['reasoning','解析步骤（每行一步）','list'],['errors','常见错误（每行一项）','list'],['rubric','评分标准','text']];
function el(tag,text,cls){const node=document.createElement(tag);if(text!==undefined)node.textContent=text;if(cls)node.className=cls;return node;}
function message(text,error=false){$('message').textContent=text;$('message').className=error?'error':'';let inline=$('operation-status');if(!inline){inline=el('p',undefined,'hint');inline.id='operation-status';inline.setAttribute('role','status');$('generate').after(inline);}inline.textContent=text;inline.className=error?'operation-error':'hint';}
function setBusy(value){busy=value;document.querySelector('main').inert=value;$('generate').textContent=value?'处理中，请稍候…':($('mode').value==='exam'?'生成正式试卷 →':'生成作业 →');$('setup').setAttribute('aria-busy',String(value));}
function canLeave(){return !dirty||confirm('还有未保存的修改，是否放弃？');}
async function request(payload){const response=await fetch('/api/action',{method:'POST',headers:{'Content-Type':'application/json','X-Review-Token':token},body:JSON.stringify({run:state?.run,version:state?.version,request_id:crypto.randomUUID(),...payload})});const data=await response.json();if(!response.ok)throw Error(data.error);return data;}
async function history(){const response=await fetch('/api/state');const data=await response.json();if(!response.ok)throw Error(data.error);token=data.token;$('source').querySelector('option[value=ai]').disabled=!data.ai.ready;$('ai-status').textContent=data.ai.message+(data.usage?` 今日请求 ${data.usage.attempts}/${data.usage.limit} 次，剩余 ${data.usage.remaining} 次。`:'');$('ai-model-stat').textContent=data.ai.ready?`AI 实时生成已启用 · ${data.ai.model}`:'本地题库可用 · AI 实时生成暂未开放';$('catalog-stats').textContent=`${data.catalog.bank_count} 道题 · ${data.catalog.topics.length} 个课题 · 4 个单元`;if(!catalogData)initCatalog(data.catalog);const previous=$('runs').value;$('runs').replaceChildren();for(const run of data.runs){const o=el('option',run===state?.run?'当前练习':run.replace(/_worksheet_.*/,' · 自选练习'));o.value=run;$('runs').append(o);}if(state)$('runs').value=state.run;else if(previous)$('runs').value=previous;$('load').disabled=!data.runs.length;}
function settings(){const exam=$('mode').value==='exam';const topics=Array.from($('topic').selectedOptions).map(o=>o.value);return {purpose:exam?'exam':'homework',topic:topics[0],topics,contents:Array.from(document.querySelectorAll('input[name="contents"]:checked')).map(e=>e.value),difficulty:$('difficulty').value,minutes:Number(exam?$('exam-minutes').value:$('minutes').value),...(exam?{question_count:Number($('exam-count').value),total_marks:Number($('exam-marks').value),question_types:Array.from(document.querySelectorAll('input[name="question-types"]:checked')).map(e=>e.value),selected_ids:pendingPicked}:{})};}
function setContents(checked=[]){const selected=Array.from($('topic').selectedOptions).map(o=>o.value);const topics=catalogData.topics.filter(t=>selected.includes(t.id));if(!topics.length){$('content-options').replaceChildren();$('bank-note').textContent='请选择至少一个课题。';return;}const topic={bank_count:topics.reduce((n,t)=>n+t.bank_count,0),contents:[...new Map(topics.flatMap(t=>t.contents).map(c=>[c.id,c])).values()]};$('bank-note').textContent=`当前选中 ${topics.length} 个课题，共约 ${topic.bank_count} 道原创题，按所选内容与难度组卷。优先避开最近 5 份作业中的题目；题量不足时会说明重复与时长缺口。`;$('content-options').replaceChildren();for(const c of topic.contents){const label=el('label',undefined,'check');const input=el('input');input.type='checkbox';input.name='contents';input.value=c.id;input.checked=checked.includes(c.id);label.append(input,document.createTextNode(c.title));$('content-options').append(label);}}
function renderChoiceOptions(selectId,boxId,kind){
  const select=$(selectId), box=$(boxId); if(!select||!box)return;
  box.replaceChildren();
  Array.from(select.options).forEach(option=>{
    const label=el('label',undefined,'choice-option');
    const input=el('input'); input.type='checkbox'; input.name=kind; input.value=option.value; input.checked=option.selected;
    input.setAttribute('aria-label',option.textContent);
    input.onchange=()=>{option.selected=input.checked; select.dispatchEvent(new Event('change'));};
    label.append(input,el('span',option.textContent)); box.append(label);
  });
}
function renderUnitOptions(){renderChoiceOptions('unit','unit-options','units');}
function renderTopicOptions(){renderChoiceOptions('topic','topic-options','topics');}
function renderSelections(){
  const chips=(box,items,select)=>{if(!$(box))return;$(box).replaceChildren();items.forEach(item=>{const chip=el('span',undefined,'selected-chip');chip.append(document.createTextNode(item.text));const x=el('button','×');x.type='button';x.title='移除 '+item.text;x.onclick=()=>{item.option.selected=false;select.dispatchEvent(new Event('change'));};chip.append(x);$(box).append(chip);});};
  chips('unit-selected',Array.from($('unit').selectedOptions).map(o=>({text:o.textContent,option:o})),$('unit'));
  chips('topic-selected',Array.from($('topic').selectedOptions).map(o=>({text:o.textContent,option:o})),$('topic'));
}
function setTopics(units,selected){$('topic').replaceChildren();const chosenUnits=Array.isArray(units)?units:[units];const options=catalogData.topics.filter(t=>chosenUnits.includes(t.unit));for(const [i,t] of options.entries()){const o=el('option',t.title);o.value=t.id;o.selected=Array.isArray(selected)?selected.includes(t.id):selected===t.id||(!selected&&i===0);$('topic').append(o);}renderTopicOptions();setContents();renderSelections();}
function initCatalog(data){catalogData=data;Object.assign(goals,data.objective_labels||{});for(const u of data.units){const o=el('option',u.title);o.value=u.id;$('unit').append(o);}for(const d of data.difficulties){const o=el('option',d.title);o.value=d.id;$('difficulty').append(o);}$('unit').disabled=false;$('topic').disabled=false;$('difficulty').disabled=false;$('generate').disabled=false;$('unit').options[0].selected=true;renderUnitOptions();setTopics([data.units[0].id]);setContents(catalogData.topics[0].contents.map(c=>c.id));renderSelections();}
const baseInitCatalog=initCatalog;
initCatalog=function(data){baseInitCatalog(data);if(pendingTopic){const picked=catalogData.topics.find(t=>t.id===pendingTopic);if(picked){$('unit').value=picked.unit;renderUnitOptions();setTopics([picked.unit],[picked.id]);setContents(picked.contents.map(c=>c.id));}}if(pendingPicked.length>=3&&pendingPicked.length<=30){ensureCount(pendingPicked.length);$('exam-count').value=String(pendingPicked.length);}showPicked();};
function ensureCount(count){/* Numeric input accepts saved and selected counts directly. */}
$('setup').addEventListener('submit',event=>{if($('mode').value!=='exam')return;const selectedTopics=Array.from($('topic').selectedOptions).map(o=>o.value);const topicCount=selectedTopics.reduce((n,id)=>n+(catalogData?.topics.find(t=>t.id===id)?.bank_count||0),0);const count=Number($('exam-count').value);if(Number($('exam-marks').value)<count){event.preventDefault();event.stopImmediatePropagation();message('每道题至少 1 分，请提高总分或减少题目数量。',true);return;}if(topicCount&&count>topicCount&&!pendingPicked.length){event.preventDefault();event.stopImmediatePropagation();message(`当前选中课题共约 ${topicCount} 道题，无法生成 ${count} 道正式试卷。请减少题量或增加课题。`,true);}},true);
function showPicked(){let panel=$('picked-info');if(!panel){panel=el('div',undefined,'note');panel.id='picked-info';$('setup').prepend(panel);}panel.replaceChildren();if(!pendingPicked.length)return;panel.append(el('p',`自选候选范围：${pendingPicked.length} 道题。仅在正式试卷模式生效。`));const edit=el('a','返回题库调整清单');edit.href='/bank';const clear=el('button','取消自选，使用整个课题题库');clear.type='button';clear.onclick=()=>{pendingPicked=[];pendingTopic='';showPicked();message('已取消本次组卷的自选限制。');};panel.append(edit,clear);}
const baseRestoreSettings=restoreSettings;
restoreSettings=function(){const s=state.navigation_settings||state.settings;pendingPicked=s?.selected_ids||[];pendingTopic=pendingPicked.length?s.topic:'';if(s?.question_count)ensureCount(s.question_count);baseRestoreSettings();showPicked();};
$('setup').addEventListener('submit',event=>{if($('mode').value!=='exam'||!pendingPicked.length)return;let error='';if($('source').value!=='local')error='自选题组卷请使用本地题库。';else if(pendingTopic&&!Array.from($('topic').selectedOptions).map(o=>o.value).includes(pendingTopic))error='当前课题与自选题不同，请返回题库调整清单，或取消自选限制。';else if(Number($('exam-count').value)>pendingPicked.length)error=`清单只有 ${pendingPicked.length} 道题，请减少题量或返回题库继续选题。`;if(error){event.preventDefault();event.stopImmediatePropagation();message(error,true);}},true);
$('unit').onchange=()=>{renderUnitOptions();const units=Array.from($('unit').selectedOptions).map(o=>o.value);const keep=Array.from($('topic').selectedOptions).map(o=>o.value).filter(id=>catalogData.topics.find(t=>t.id===id)&&units.includes(catalogData.topics.find(t=>t.id===id).unit));setTopics(units,keep.length?keep:undefined);renderSelections();message('已更新单元，请选择课题和考查内容。'+(state?' 当前预览仍为上一份作业。':''));};
$('topic').onchange=()=>{renderTopicOptions();setContents();renderSelections();message('已更新课题，请勾选本次要练习的考查内容，再生成作业。'+(state?' 当前预览仍为上一套练习。':''));};
$('difficulty').onchange=()=>{if(state)message('难度设置已改变，请点击“生成作业”应用新条件。当前预览未改变。');};
function restoreSettings(){$('source').value=state.source||'local';const s=state.navigation_settings||state.settings;if(!s)return;$('mode').value=s.purpose==='exam'?'exam':'homework';toggleMode();const topic=catalogData.topics.find(t=>t.id===s.topic);if(!topic)return;const savedTopics=s.topics||[s.topic];const savedUnits=[...new Set(savedTopics.map(id=>catalogData.topics.find(t=>t.id===id)?.unit).filter(Boolean))];Array.from($('unit').options).forEach(o=>o.selected=savedUnits.includes(o.value));renderUnitOptions();setTopics(savedUnits,savedTopics);$('difficulty').value=s.difficulty||'basic';if(s.purpose==='exam'){$('exam-minutes').value=String(s.minutes);$('exam-count').value=String(s.question_count);$('exam-marks').value=String(s.total_marks);document.querySelectorAll('input[name="question-types"]').forEach(e=>e.checked=(s.question_types||[]).includes(e.value));}else $('minutes').value=[10,20].includes(s.minutes)?String(s.minutes):'20';setContents(s.contents);}
function previewTitle(){const s=state.navigation_settings||state.settings;const ids=s?.topics||[s?.topic];return catalogData.topics.filter(t=>ids.includes(t.id)).map(t=>t.title).join(' + ')||'已保存练习';}
function render(){editing=null;dirty=false;$('empty').hidden=true;$('preview').hidden=false;$('paper').replaceChildren();$('paper-title').textContent=previewTitle()+' · '+({local:'本地作业',mock:'AI 模拟作业',ai:'AI 生成作业'}[state.source||'local']);$('stats').textContent=`${state.summary.count} 道题 · 预计 ${state.summary.minutes} 分钟 · ${state.settings?'设定 '+state.settings.minutes+' 分钟':'已有练习'}`;$('warnings').replaceChildren();if(state.generation_notice)$('warnings').append(el('p','组卷时：'+state.generation_notice));for(const w of state.summary.warnings)$('warnings').append(el('p',w));if(state.summary.homework){const h=state.summary.homework;$('warnings').append(el('p',h.status==='complete'?'已按设定时长组卷，所选内容均有题目。':'当前为部分作业：请查看上方时长或内容缺口。可调整设置后重新生成。'));}for(const [index,r] of state.records.entries()){const q=r.content;const card=el('article',undefined,'question');card.id='q-'+q.id;const top=el('div',undefined,'qtop');const heading=el('div');heading.append(el('span',`第 ${index+1} 题 · ${levels[q.level]} · 约 ${q.minutes} 分钟`,'badge'),el('h3',q.title));const edit=el('button',r.locked?'已锁定 · 解锁修改':'修改这道题','secondary');edit.onclick=async()=>{if(busy||!canLeave())return;if(r.locked){if(!confirm('这道题已锁定，是否解锁以便修改？'))return;setBusy(true);try{state=await request({action:'lock',id:q.id,locked:false,actor:'本地教师'});render();openEditor(state.records.find(x=>x.content.id===q.id));}catch(e){message(e.message,true);}finally{setBusy(false);}}else{render();openEditor(r);}};const swap=el('button','换一道题','secondary');swap.disabled=r.locked||!state.settings;swap.title=r.locked?'请先解锁再换题':'保留考查覆盖与难度，不超出设定时长';swap.onclick=()=>replaceOne(q.id);const actions=el('div',undefined,'buttons');actions.append(swap,edit);top.append(heading,actions);card.append(top,el('pre',q.code),el('pre',q.task,'task'));const options=el('div',undefined,'options');for(const [k,v] of Object.entries(q.options||{}))options.append(el('p',`${k}. ${v}`));card.append(options);if(q.prerequisites)card.append(el('p','前置知识：'+q.prerequisites,'hint'));const answer=el('details',undefined,'answer');answer.append(el('summary','查看答案与解析'),el('p',q.answer,'text'));const list=el('ol');q.reasoning.forEach(v=>list.append(el('li',v)));if(q.reference_solution)answer.append(el('pre',q.reference_solution));answer.append(list);for(const [k,v] of Object.entries(q.distractors||{}))answer.append(el('p',`${k}：${v}`));answer.append(el('p','常见错误：'+q.errors.join('；')),el('p','评分：'+q.rubric));const help=el('details');help.append(el('summary','学生答错时的讲解建议'),el('p',q.intervention));answer.append(help);card.append(answer);$('paper').append(card);}}
const baseRender=render;
render=function(){baseRender();const exam=state?.summary?.exam;if(exam){$('paper-title').textContent=previewTitle()+' · 正式试卷';$('stats').textContent=`${state.summary.count} 道题 · ${exam.actual_marks}/${exam.total_marks} 分 · 预计 ${state.summary.minutes}/${exam.target_minutes} 分钟`;for(const r of state.records){const badge=$('q-'+r.content.id).querySelector('.badge');badge.textContent+=` · ${r.content.marks} 分`;}}};
function toggleMode(){const exam=$('mode').value==='exam';if(exam&&!Array.from($('difficulty').options).some(o=>o.value==='mixed')){const option=el('option','混合');option.value='mixed';$('difficulty').append(option);}if(!exam){const mixed=$('difficulty').querySelector('option[value="mixed"]');if(mixed)mixed.remove();if($('difficulty').value==='mixed')$('difficulty').value='basic';}$('exam-fields').hidden=!exam;$('exam-fields').querySelectorAll('input').forEach(input=>input.disabled=!exam);$('homework-time').hidden=exam;$('time-help').textContent=exam?'正式试卷会按题量、总分、题型和考试时间组卷；分值是教师组卷权重，不代表官方 AP 分数。':'按预计独立作答时间组卷，不含讲解。题量不足会明确提示。';$('generate').textContent=exam?'生成正式试卷 →':'生成作业 →';$('mode-help').textContent=exam?'适合测验、单元测试或正式考试试卷。':'适合一节课或课后 10/20 分钟练习。';}
function field(parent,key,label,value,type){const l=el('label',label);const input=el(type==='number'||!type?'input':'textarea');input.name=key;input.value=type==='list'?(key==='objectives'?value.map(v=>goals[v]||v):value).join('\n'):value;if(type==='number'){input.type='number';input.min=1;if(key==='level')input.max=4;}if(type==='code')input.className='code';if(input.tagName==='TEXTAREA')input.rows=type==='code'?7:3;l.append(input);parent.append(l);}
function openEditor(r){editing=r.content.id;const form=el('form',undefined,'edit-form');form.append(el('h3','调整这道题'));for(const [k,label,type] of specs)field(form,k,label,r.content[k],type);if(r.content.reference_solution!==undefined)field(form,'reference_solution','参考实现（与答案同步修改）',r.content.reference_solution,'code');const help=el('details');help.append(el('summary','学生答错时的讲解建议（可选修改）'));field(help,'intervention','讲解建议',r.content.intervention,'text');form.append(help);if(r.content.options){for(const [k,v] of Object.entries(r.content.options))field(form,'option-'+k,'选项 '+k,v,'text');field(form,'answer_key','正确选项',r.content.answer_key);for(const k of Object.keys(r.content.options))field(form,'distractor-'+k,'选项 '+k+' 错误原因（正确选项可留空）',r.content.distractors[k]||'','text');}const buttons=el('div',undefined,'buttons');const save=el('button','保存并返回预览','primary');save.type='submit';const cancel=el('button','取消');cancel.type='button';cancel.onclick=()=>{if(canLeave())render();};buttons.append(save,cancel);form.append(buttons,el('p','保存后保留修改记录，原始练习不变。','hint'));form.oninput=()=>{dirty=true;};form.onsubmit=async e=>{e.preventDefault();if(busy)return;const changes={};for(const [k,,type] of specs){let v=form.elements.namedItem(k).value;if(type==='number')v=Number(v);if(type==='list')v=v.split('\n').map(s=>s.trim()).filter(Boolean);if(k==='objectives')v=v.map(label=>Object.keys(goals).find(key=>goals[key]===label)||label);changes[k]=v;}if(r.content.reference_solution!==undefined)changes.reference_solution=form.elements.namedItem('reference_solution').value;const guidance=form.elements.namedItem('intervention').value.trim();if(guidance)changes.intervention=guidance;if(r.content.options){changes.options={};changes.distractors={};changes.answer_key=form.elements.namedItem('answer_key').value.trim();for(const k of Object.keys(r.content.options)){changes.options[k]=form.elements.namedItem('option-'+k).value;if(k!==changes.answer_key)changes.distractors[k]=form.elements.namedItem('distractor-'+k).value;}}setBusy(true);try{state=await request({action:'revise',id:r.content.id,actor:'本地教师',reason:'教师在练习预览中调整题目',changes});render();message('修改已保存，导出时会使用最新内容。');}catch(e){message(e.message,true);}finally{setBusy(false);}};$('q-'+r.content.id).append(form);form.scrollIntoView({behavior:'smooth',block:'start'});}
$('setup').onsubmit=async e=>{e.preventDefault();if(busy||!canLeave())return;setBusy(true);message($('source').value==='ai'?'AI 正在生成，请稍候（最长约 45 秒）…':'正在准备作业…');try{const next=await request({action:'generate',settings:settings(),source:$('source').value});state=next;render();await history();message(state.summary.homework?.status==='partial'?'已生成部分作业，请先查看题量与覆盖提示。':(state.source==='mock'?'模拟作业已生成，使用本地题目，未调用 AI。':'作业已生成。先预览，需要时再修改单题。'));}catch(e){message(e.message+(state?' 当前预览仍为上一套练习。':''),true);}finally{setBusy(false);}};
$('load').onclick=async()=>{if(busy||!canLeave())return;setBusy(true);try{const response=await fetch('/api/state?run='+encodeURIComponent($('runs').value));const data=await response.json();if(!response.ok)throw Error(data.error);state=data.state;token=data.token;restoreSettings();render();message(state.settings?.difficulty==='mixed'?'已打开旧版混合难度练习。旧内容保留；再次生成将使用所选的新难度。':'已打开保存的练习。');}catch(e){message(e.message,true);}finally{setBusy(false);}};
async function exportPaper(audience){if(busy)return;if(dirty){message('请先保存修改，再导出。',true);return;}setBusy(true);try{const data=await request({action:'export',audience,format:'docx',language:$('export-language')?.value||'bilingual'});const url=URL.createObjectURL(new Blob([Uint8Array.from(atob(data.download),c=>c.charCodeAt(0))],{type:data.mime}));const a=el('a');a.href=url;a.download=previewTitle().replace(/[<>:"/\\|?*]/g,'-')+'-'+(audience==='student'?'学生练习':'教师答案')+'.docx';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);message('已导出'+(audience==='student'?'学生版（不含答案）':'教师版（含答案与解析）')+'，并保存在本地练习文件夹。');}catch(e){message(e.message,true);}finally{setBusy(false);}}
$('student').onclick=()=>exportPaper('student');$('teacher').onclick=()=>exportPaper('teacher');window.addEventListener('beforeunload',e=>{if(dirty){e.preventDefault();e.returnValue='';}});history().then(loadRequestedRun).catch(e=>message('无法载入本地服务：'+e.message,true));

async function replaceOne(id){
  if(busy)return;
  if(dirty){message('请先保存或取消当前修改，再换题。',true);return;}
  setBusy(true);
  try{state=await request({action:'replace',id});render();message('已换题并保存。考查覆盖与难度已保留，预计用时已更新；导出会使用替换后的题目。');}
  catch(e){message(e.message,true);}
  finally{setBusy(false);}
}
$('regenerate').onclick=async()=>{
  if(busy)return;
  if(dirty){message('请先保存或取消当前修改，再重新组卷。',true);return;}
  if(!state.settings){message('请在左侧选择条件并生成新作业。',true);return;}
  setBusy(true);
  try{state=await request({action:'generate',settings:state.settings,source:state.source||'local'});restoreSettings();render();await history();message('已按当前预览的条件生成新作业；上一份保留在历史记录中。'+state.generation_notice);}
  catch(e){message(e.message,true);}
  finally{setBusy(false);}
};

$('source').onchange=()=>{message($('source').value==='ai'?'AI 实时生成会消耗额度，每次最多请求一次。':$('source').value==='mock'?'模拟体验使用本地题目，不会调用 AI。':'已选择免费本地题库。');};
$('mode').onchange=()=>{toggleMode();message($('mode').value==='exam'?'已切换到正式试卷，可使用本地题库或 AI 实时生成。请设置时间、题量、总分和题型。':'已切换到快速练习：适合 10/20 分钟课堂或作业。');};
if(pendingPicked.length)$('mode').value='exam';
toggleMode();
if(pendingPicked.length)message(`已从题库带入 ${pendingPicked.length} 道自选题${pendingTopic?'，并选中对应课题':''}。请检查试卷时间、题量和总分后生成。`);

/* Final review controls: lock reviewed questions and manage answer visibility. */
const reviewRender=render;
render=function(){
  reviewRender();
  if(!state)return;
  if(state.generation?.model && !$('stats').textContent.includes(state.generation.model))$('stats').textContent+=` · ${state.generation.model}`;
  for(const record of state.records){
    const card=$('q-'+record.content.id);if(!card)continue;
    const actions=card.querySelector('.qtop .buttons');
    if(actions&&!actions.querySelector('.lock-control')){
      const lock=el('button',record.locked?'解锁本题':'锁定本题','secondary');lock.className+=' lock-control';
      lock.title=record.locked?'解锁后才可以修改或换题':'审核完成后锁定，避免导出前误改';
      lock.onclick=()=>toggleLock(record.content.id,record.locked);
      actions.append(lock);
    }
    const answer=card.querySelector('.answer');if(answer)answer.open=answersExpanded;
    if(answer&&!answer.querySelector('.english-explanation')){
      const english=record.content.explanation_en;
      if(english){const block=el('div',undefined,'english-explanation');block.append(el('strong','English explanation'),el('p',english));answer.append(block);}
      else if(!record.locked){const translate=el('button','生成英文解析（AI）','secondary');translate.className+=' translate-control';translate.onclick=async()=>{if(busy)return;setBusy(true);try{state=await request({action:'translate',id:record.content.id,actor:'本地教师'});render();message('英文解析已生成并保存，导出教师版时会一并包含。');}catch(e){message(e.message,true);}finally{setBusy(false);}};answer.append(translate);}
    }
  }
};
async function toggleLock(id,locked){
  if(busy)return;
  if(locked&&!confirm('确定解锁这道题吗？'))return;
  setBusy(true);
  try{state=await request({action:'lock',id,locked:!locked,actor:'本地教师'});render();message(locked?'已解锁本题，可以继续修改。':'已锁定本题，修改和换题已暂停。');}
  catch(e){message(e.message,true);}
  finally{setBusy(false);}
}
$('toggle-answers').onclick=()=>{answersExpanded=!answersExpanded;$('toggle-answers').textContent=answersExpanded?'收起全部答案':'展开全部答案';if(state)render();};
$('print').onclick=()=>{if(state)window.print();else message('请先生成一套练习。',true);};

async function loadRequestedRun(){
  const run=new URLSearchParams(location.search).get('run');
  if(!run||state)return;
  const response=await fetch('/api/state?run='+encodeURIComponent(run));
  const payload=await response.json();
  if(!response.ok||!payload.state)throw Error(payload.error||'练习不存在。');
  state=payload.state;token=payload.token;restoreSettings();render();$('runs').value=run;message('已打开练习，可以继续修改或导出。');
}

if($('quality'))$('quality').onclick=async()=>{
  if(!state||busy){if(!state)message('请先生成一套练习。',true);return;}
  setBusy(true);
  try{
    const report=await request({action:'quality-check'});
    $('warnings').replaceChildren();
    if(report.warnings.length){
      const box=el('div',undefined,'warning-box');box.append(el('strong','质量检查发现：'));
      report.warnings.forEach(w=>box.append(el('p','• '+w)));$('warnings').append(box);
      message(`质量检查发现 ${report.warnings.length} 项需要确认。`,true);
    }else message('结构质量检查通过：未发现重复题目或缺少答案字段。');
  }catch(e){message(e.message,true);}finally{setBusy(false);}
};

/* Teacher trial intake: feedback and question proposals are kept out of the live bank until review. */
function formPayload(form){return Object.fromEntries(new FormData(form).entries());}
async function submitTeacherForm(form, action, success){
  const button=form.querySelector('button[type="submit"]');
  button.disabled=true;
  try{
    const payload=formPayload(form); payload.action=action;
    if(state){payload.run=state.run;}
    const response=await fetch('/api/action',{method:'POST',headers:{'Content-Type':'application/json','X-Review-Token':token},body:JSON.stringify(payload)});
    const data=await response.json(); if(!response.ok) throw Error(data.error||'提交失败。');
    form.reset(); message(success+' 编号：'+data.id);
  }catch(error){message(error.message,true)}finally{button.disabled=false}
}
if($('feedback-form'))$('feedback-form').addEventListener('submit',event=>{event.preventDefault();submitTeacherForm(event.currentTarget,'teacher-feedback','感谢反馈。');});
if($('question-form'))$('question-form').addEventListener('submit',event=>{event.preventDefault();submitTeacherForm(event.currentTarget,'submit-question','题目已提交，等待审核。');});
