"use strict";
const $=id=>document.getElementById(id), KEY='csa-studio-progress-v1';
let bank=[],catalog=[],progress={},unit='',current=null,revealed=false,storageOK=true,notebookReview=false;
const initialView=new URLSearchParams(location.search);
const names={1:'使用对象与方法',2:'选择与循环',3:'类的创建',4:'数据集合'};
function node(tag,text,cls){const e=document.createElement(tag);if(text!==undefined)e.textContent=text;if(cls)e.className=cls;return e;}
try{const saved=JSON.parse(localStorage.getItem(KEY)||'{}');if(saved&&typeof saved==='object'&&!Array.isArray(saved))progress=saved;}catch{storageOK=false;}
function save(){try{localStorage.setItem(KEY,JSON.stringify(progress));}catch{storageOK=false;$('notice').textContent='浏览器无法保存进度。本次仍可练习，关闭页面后记录可能丢失。';}}
function record(q){const r=progress[q.id];return r&&typeof r==='object'?r:{};}
function units(q){return (q.units||[q.ap_unit]).map(String);}
function available(q){return (!unit||units(q).includes(unit))&&q.question_kind===$('kind').value&&(!$('topic').value||(q.ced_topics||[]).includes($('topic').value))&&($('scope').value==='all'||($('scope').value==='new'?!record(q).done:record(q).done&&!record(q).mastered));}
function dashboard(){
 $('mistake-count').textContent=bank.filter(q=>CSAProgress.isMistake(record(q))&&!record(q).mastered).length;
 $('stats').replaceChildren();const done=bank.filter(q=>record(q).done),mastered=done.filter(q=>record(q).mastered);
 for(const [label,value] of [['可练总题数',bank.length],['已练题数',done.length],['答对 / 自评掌握',mastered.length],['待巩固',done.length-mastered.length]]){const card=node('div',undefined,'stat');card.append(node('span',label),node('strong',String(value)));$('stats').append(card);}
 $('units').replaceChildren();
 const all=node('button','全部单元','unit');all.type='button';all.setAttribute('aria-pressed',String(!unit));all.onclick=()=>{unit='';refreshTopics();dashboard();choose();};$('units').append(all);
 for(const id of ['1','2','3','4']){const rows=bank.filter(q=>units(q).includes(id)),done=rows.filter(q=>record(q).done).length;const b=node('button',undefined,'unit');b.type='button';b.setAttribute('aria-pressed',String(unit===id));b.append(node('b','Unit '+id),node('span',names[id]),node('small',`${done} / ${rows.length} 题 · ${rows.length?Math.round(done/rows.length*1000)/10:0}%`));const p=node('progress');p.max=rows.length||1;p.value=done;p.setAttribute('aria-label',`Unit ${id} 已练 ${done} 题，共 ${rows.length} 题`);b.append(p);b.onclick=()=>{unit=id;refreshTopics();dashboard();choose();$('practice-area').scrollIntoView({behavior:'smooth',block:'start'});};$('units').append(b);}
}
function refreshTopics(){const previous=$('topic').value;$('topic').replaceChildren(new Option('全部课题',''));for(const t of catalog){if(bank.some(q=>(!unit||units(q).includes(unit))&&(q.ced_topics||[]).includes(t.id)))$('topic').append(new Option(`${t.id} · ${t.title}`,t.id));}if([...$('topic').options].some(o=>o.value===previous))$('topic').value=previous;}
function choose(skip){notebookReview=false;const rows=bank.filter(available);current=rows.find(q=>q.id!==skip)||null;revealed=false;render();}
function button(text,fn,primary=false){const b=node('button',text,primary?'primary':'');b.type='button';b.onclick=fn;return b;}
function render(){
 const box=$('question');box.replaceChildren();$('actions').replaceChildren();
 if(!current){box.append(node('h2','这个范围已没有待练题目'),node('p','可以切换单元、课题或选择“全部题目”继续练习。'));return;}
 const q=current,r=record(q),mcq=q.question_kind==='concept';
 box.append(node('p',`${units(q).map(u=>'Unit '+u).join(' / ')} · ${mcq?'MCQ':'FRQ'} · 预计 ${q.minutes} 分钟`,'muted'),node('h2',q.title));
 if(q.code&&!q.code.startsWith('// AP source question'))box.append(node('pre',q.code));
 if(q.question_images?.length){
  for(const file of q.question_images){const link=node('a');link.href='/source-image/'+encodeURIComponent(file);link.target='_blank';link.rel='noopener';link.title='打开原题大图';const img=node('img');img.src=link.href;img.alt=q.title+' 原题（含表格和图示）';img.className='question-image';link.append(img);box.append(link);}
  const transcript=node('details');transcript.append(node('summary','题目文字'),node('div',q.task,'task'));box.append(transcript);
 }else box.append(node('div',q.task,'task'));
 if(mcq){const group=node('fieldset');group.append(node('legend','选择一个答案'));for(const [key,text] of Object.entries(q.options)){const label=node('label',undefined,'option'),input=node('input');input.type='radio';input.name='choice';input.value=key;input.disabled=revealed;label.append(input,node('span',`${key}. ${text}`));group.append(label);}box.append(group);}
 else{const label=node('label','你的 Java 代码');label.htmlFor='draft';const area=node('textarea');area.id='draft';area.spellcheck=false;area.value=r.draft||'';area.placeholder='在这里写下你的实现…';area.oninput=()=>{progress[q.id]={...record(q),draft:area.value};save();};box.append(label,area);}
 $('actions').append(button(mcq?'提交答案':'查看参考答案',()=>{
  if(mcq){const selected=document.querySelector('input[name=choice]:checked');if(!selected){$('notice').textContent='请先选择一个答案。';return;}const correct=selected.value===q.answer_key;progress[q.id]=CSAProgress.submit(record(q),correct,selected.value);save();dashboard();showAnswer(correct?'回答正确':'这道题还需要巩固');}
  else{if(!$('draft').value.trim()){$('notice').textContent='请先写下你的解题尝试，再对照参考答案。';return;}showAnswer('对照评分标准，检查自己的实现');}
 },true));
 if(notebookReview)$('actions').append(button('返回错题本',()=>setView('mistakes')));
}
function showAnswer(message){if(revealed)return;revealed=true;if(storageOK)$('notice').textContent='';document.querySelectorAll('input[name=choice]').forEach(e=>e.disabled=true);const q=current,box=node('section',undefined,'answer');box.append(node('p',message,'result'));
 if(q.answer_key)box.append(node('h3','正确答案：'+q.answer_key));
 for(const [title,text] of [['答案与解析',q.answer],['参考代码',q.reference_solution],['评分标准',q.rubric],['English explanation',q.explanation_en]])if(text){box.append(node('h3',title),node('pre',text.replace(/^Select a point value to view scoring criteria or to score the response\.\s*$/gm,'')));}
 for(const ref of (q.source_refs||[]).filter(r=>r.role==='SG')){if(!/^[a-f0-9]{64}$/.test(ref.document))continue;const a=node('a','查看原评分指南');a.href=`/source-pdf/${ref.document}.pdf#page=${Number(ref.page)||1}`;a.target='_blank';a.rel='noopener';box.append(a);}
 $('question').append(box);$('actions').replaceChildren();
 if(q.question_kind==='write'){for(const [label,mastered] of [['自评：已掌握',true],['自评：还需练习',false]])$('actions').append(button(label,()=>{progress[q.id]=CSAProgress.submit(record(q),mastered);save();dashboard();next();},mastered));}
 else $('actions').append(button(notebookReview?'返回错题本':'下一题',next,true));
}
function next(){if(notebookReview){notebookReview=false;setView('mistakes');return;}const old=current?.id;choose(old);}
function mistakeRows(){return bank.filter(q=>CSAProgress.isMistake(record(q))&&(!$('mistake-unit').value||units(q).includes($('mistake-unit').value))&&(!$('mistake-kind').value||q.question_kind===$('mistake-kind').value)&&($('mistake-status').value==='all'||($('mistake-status').value==='mastered'?record(q).mastered:!record(q).mastered))).sort((a,b)=>(record(b).lastWrong||'').localeCompare(record(a).lastWrong||''));}
function setView(view){
 const mistakes=view==='mistakes';document.body.classList.toggle('notebook-mode',mistakes);$('practice-view').hidden=mistakes;$('mistakes-view').hidden=!mistakes;
 $('practice-tab').setAttribute('aria-pressed',String(!mistakes));$('mistakes-tab').setAttribute('aria-pressed',String(mistakes));
 document.querySelectorAll('header nav a').forEach(a=>{const selected=a.getAttribute('href')===(mistakes?'/practice?view=mistakes':'/practice');a.classList.toggle('active',selected);if(selected)a.setAttribute('aria-current','page');else a.removeAttribute('aria-current');});
 const url=new URL(location.href);if(mistakes)url.searchParams.set('view','mistakes');else url.searchParams.delete('view');history.replaceState(null,'',url);
 if(mistakes){notebookReview=false;renderNotebook();}else{render();}
}
function openMistake(q){
 unit='';refreshTopics();$('topic').value='';$('kind').value=q.question_kind;$('scope').value='all';current=q;revealed=false;notebookReview=true;
 dashboard();setView('practice');$('practice-area').scrollIntoView({behavior:'smooth',block:'start'});$('practice-area').focus({preventScroll:true});
}
function renderNotebook(){
 const all=bank.filter(q=>CSAProgress.isMistake(record(q))),pending=all.filter(q=>!record(q).mastered),rows=mistakeRows();
 $('notebook-summary').textContent=`累计收录 ${all.length} 道 · 待巩固 ${pending.length} 道 · 已巩固 ${all.length-pending.length} 道`;
 const review=rows.filter(q=>!record(q).mastered);$('review-pending').disabled=!review.length;$('review-pending').textContent=review.length?`复习待巩固题（${review.length}）`:'暂无待巩固题';$('review-pending').onclick=()=>{if(review[0])openMistake(review[0]);};
 $('mistake-list').replaceChildren();
 if(!rows.length){const empty=node('div',undefined,'notebook-empty');empty.append(node('h3',all.length?'当前筛选下没有题目':'你的错题本，从第一次尝试开始'),node('p',all.length?'试试其他单元、题型或复习状态。':'答错的选择题和需要再练的 FRQ 会自动出现在这里。'));empty.append(button('去练习',()=>{notebookReview=false;unit='';$('scope').value='new';refreshTopics();dashboard();choose();setView('practice');},true));$('mistake-list').append(empty);return;}
 for(const q of rows){const r=record(q),card=node('article',undefined,'mistake-card'),head=node('div',undefined,'mistake-card-head');head.append(node('span',units(q).map(u=>'Unit '+u).join(' / ')+' · '+(q.question_kind==='concept'?'MCQ':'FRQ'),'eyebrow'),node('span',r.mastered?'已巩固':'待巩固',r.mastered?'state-pill mastered':'state-pill pending'));card.append(head,node('h3',q.title));
 card.append(node('p',q.task.replace(/\s+/g,' ').slice(0,160)+(q.task.length>160?'…':''),'mistake-excerpt'));
 const info=[];if(r.lastWrongChoice||(!r.mastered&&r.choice))info.push('上次错选 '+(r.lastWrongChoice||r.choice));info.push('已尝试 '+(Number(r.attempts)||1)+' 次');if(r.lastWrong){const dt=new Date(r.lastWrong);if(!Number.isNaN(dt.getTime()))info.push(dt.toLocaleDateString('zh-CN'));}card.append(node('p',info.join(' · '),'muted'));
 const actions=node('div',undefined,'actions');actions.append(button(r.mastered?'再练一次':'重新练习',()=>openMistake(q),true));
 const notes=node('details',undefined,'review-notes'),summary=node('summary',r.note?'查看 / 修改复习笔记':'记录复习笔记'),label=node('label','这道题提醒了你什么？'),area=node('textarea');area.setAttribute('aria-label','复习笔记：'+q.title);area.value=r.note||'';area.maxLength=3000;area.placeholder='例如：整数除法会舍去小数部分。';area.oninput=()=>{progress[q.id]={...record(q),note:area.value};save();};label.append(area);notes.append(summary,label);card.append(actions,notes);$('mistake-list').append(card);
 }
}
async function init(){try{const response=await fetch('/api/bank');if(!response.ok)throw Error('题库暂时无法加载，请刷新重试。');const data=await response.json();catalog=data.ced_topics||[];bank=[...new Map(data.questions.filter(q=>q.source_item_id&&((q.question_kind==='concept'&&q.answer_key&&q.options?.[q.answer_key])||(q.question_kind==='write'&&(q.reference_solution||q.answer||(q.source_refs||[]).some(r=>r.role==='SG'))))).map(q=>[q.id,q])).values()];$('notice').textContent=storageOK?'':'当前浏览器无法保存进度。';unit=['1','2','3','4'].includes(initialView.get('unit'))?initialView.get('unit'):'';refreshTopics();dashboard();choose();setView(initialView.get('view')==='mistakes'?'mistakes':'practice');$('practice-tab').onclick=()=>{notebookReview=false;choose();setView('practice');};$('mistakes-tab').onclick=()=>setView('mistakes');for(const id of ['mistake-status','mistake-unit','mistake-kind'])$(id).onchange=renderNotebook;for(const id of ['kind','scope','topic'])$(id).onchange=()=>{notebookReview=false;choose();};}catch(e){$('notice').textContent=e.message;}}
init();
