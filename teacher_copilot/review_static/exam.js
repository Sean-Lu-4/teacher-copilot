'use strict';
const $=id=>document.getElementById(id),KEY='csa-frq-exam-v1';
let session=null,drafts={},index=0,token='',offset=0,dirty=false,saving=false,grading=false,timerHidden=false,queue=Promise.resolve(),debounce=null,flags={},storageOK=true;
const el=(tag,text,cls)=>{const n=document.createElement(tag);if(text!==undefined)n.textContent=text;if(cls)n.className=cls;return n;};
function persist(){try{localStorage.setItem(KEY,JSON.stringify({id:session.id,drafts,revision:session.revision,flags,index,dirty}));}catch{storageOK=false;$('notice').textContent='浏览器无法保存本地备份，请保持页面打开并确认作答已保存到服务器。';}}
function remaining(){return session?Math.max(0,session.deadline-(Date.now()/1000+offset)):5400;}
function call(action,extra={}){
 const task=async()=>{const controller=new AbortController(),timeout=setTimeout(()=>controller.abort(),75000);try{const response=await fetch('/api/exam',{method:'POST',headers:{'Content-Type':'application/json','X-Review-Token':token},body:JSON.stringify({action,id:session?.id,revision:session?.revision,...extra}),signal:controller.signal});const data=await response.json();if(!response.ok)throw Error(data.error||'请求失败，请重试。');offset=data.server_now-Date.now()/1000;session=data;return data;}finally{clearTimeout(timeout);}};
 const result=queue.then(task);queue=result.catch(()=>{});return result;
}
function drawTabs(){const box=$('question-tabs');box.replaceChildren();session.questions.forEach((q,i)=>{const b=el('button',`${i+1} · ${q.section}${drafts[q.id]?.trim()?' · 已填写':''}${flags[q.id]?' · 待检查':''}`);b.setAttribute('aria-current',String(index===i));b.onclick=()=>{index=i;persist();renderQuestion();};box.append(b);});}
function renderQuestion(){
 const q=session.questions[index],submitted=session.status==='submitted';if(!submitted)$('timer').textContent=timerHidden?'已隐藏':format(remaining());drawTabs();$('question-title').textContent=`第 ${index+1} 题 · ${q.section}`;$('position').textContent=`${index+1} / 4`;
 $('previous').disabled=index===0;$('next').disabled=index===3;$('flag').hidden=submitted;$('flag').setAttribute('aria-pressed',String(!!flags[q.id]));$('flag').textContent=flags[q.id]?'已标记 · 取消':'标记待检查';
 const box=$('prompt');box.replaceChildren();if(q.code&&!q.code.startsWith('// AP source question'))box.append(el('pre',q.code));
 if(q.question_images?.length){for(const file of q.question_images){const img=el('img');img.src='/source-image/'+encodeURIComponent(file);img.alt='第 '+(index+1)+' 题原题（点击放大）';const link=el('a');link.href=img.src;link.target='_blank';link.rel='noopener';link.title='在新窗口放大原题，考试计时继续';link.append(img);box.append(link);}const d=el('details');d.append(el('summary','题目文字'),el('div',q.task,'task'));box.append(d);}else box.append(el('div',q.task,'task'));
 $('code').value=drafts[q.id]||'';$('code').readOnly=submitted||remaining()<=0;
 $('input-note').textContent=q.java_input_kind==='class'?'填写完整的类，包括字段、构造器和方法。':'填写本题要求的所有方法或构造器；无需填写外层 class、给定字段或 main。';
 $('review').hidden=!submitted;if(submitted)renderReview(q);box.scrollTop=0;
}
function renderReview(q){
 const box=$('review');box.replaceChildren();box.append(el('h2','逐项参考得分'));
 const result=session.results[q.id],auto=result?.automatic||{},evidence=auto.score_evidence||[];
 if(!result)box.append(el('p','正在等待检查。本次提交的答案已经锁定。'));
 else if(result.empty)box.append(el('p','本题未作答：0 分。'));
 else box.append(el('p',auto.message||'暂时无法完成评分，请稍后重试。'));
 for(const point of q.scoring_points||[]){const match=evidence.find(e=>e.id===point.id),earned=match?.status==='earned',empty=result?.empty;const row=el('div',undefined,'point '+(earned?'earned':empty?'missed':''));row.append(el('strong',`${point.label} · ${earned?'已得 '+point.points+' 分':empty?'0 分 · 未作答':'待复核'}`),el('p',point.description));if(match?.reason)row.append(el('p',match.reason));if(match?.lines?.length)row.append(el('p','代码位置：第 '+match.lines.join('、')+' 行'));box.append(row);}
 for(const test of auto.cases||[])box.append(el('p',(test.status==='passed'?'✓ ':'✕ ')+test.label+'：'+(test.reason||'')));
 if(auto.detail)box.append(el('pre',auto.detail));
 for(const [title,text] of [['参考答案与解析',q.answer],['参考代码',q.reference_solution],['评分标准',q.rubric],['English explanation',q.explanation_en]])if(text){const d=el('details');d.open=true;d.append(el('summary',title),el('pre',text));box.append(d);}
 if(q.scoring_pages?.length){box.append(el('h3','原评分指南'));for(const ref of q.scoring_pages){const img=el('img');img.src=`/scoring-page/${ref.document}/${ref.page}.png`;img.loading='lazy';img.alt='原评分指南第 '+ref.page+' 页';box.append(img);}}
}
function summary(){let earned=0,pending=0,total=0;for(const q of session.questions){const r=session.results[q.id];for(const p of q.scoring_points||[]){total+=p.points;if(r?.empty)continue;const e=r?.automatic?.score_evidence?.find(x=>x.id===p.id);if(e?.status==='earned')earned+=p.points;else pending+=p.points;}}
 $('result-summary').replaceChildren(el('h2',`已确认 ${earned} 分 · ${pending} 分待复核`),el('p',`本卷评分点合计 ${total} 分。这是参考评分，不是 AP 官方成绩；尚未验证的评分点不按零分处理。`));
}
function submittedView(){clearTimeout(debounce);dirty=false;drafts={...session.drafts};$('submit-dialog').close();$('submit').hidden=true;$('hide-timer').hidden=true;$('result-summary').hidden=false;$('back').hidden=false;$('restart').hidden=false;$('phase').textContent=session.reason==='timeout'?'时间到 · 已自动交卷':'已交卷';$('timer-label').textContent='已用时间';$('timer').textContent=format(Math.min(5400,session.submitted_at-session.started_at));$('save-status').textContent='本次答案已锁定。';persist();summary();renderQuestion();}
function format(sec){sec=Math.max(0,Math.ceil(sec));return String(Math.floor(sec/60)).padStart(2,'0')+':'+String(sec%60).padStart(2,'0');}
async function saveDrafts(){if(!session||session.status!=='active'||saving||!dirty)return;saving=true;dirty=false;const snapshot={...drafts};$('save-status').textContent='正在保存…';try{await call('save',{drafts:snapshot});if(session.status==='submitted'){submittedView();grade();}else{$('save-status').textContent=dirty?'有新修改，正在等待保存…':'已保存到服务器';persist();}}catch(e){dirty=true;$('save-status').textContent='尚未保存到服务器，将重试；请不要关闭页面。';$('notice').textContent=e.message;}finally{saving=false;if(dirty&&session.status==='active')debounce=setTimeout(saveDrafts,2000);}}
async function submit(){if(!session||session.status!=='active')return;clearTimeout(debounce);$('confirm-submit').disabled=true;$('submit').disabled=true;try{await call('submit',{drafts:{...drafts}});submittedView();grade();}catch(e){$('notice').textContent='交卷暂未确认：'+e.message;$('submit').disabled=false;}finally{$('confirm-submit').disabled=false;}}
async function grade(){if(grading||session.status!=='submitted')return;grading=true;$('restart').disabled=true;$('retry').hidden=true;for(const q of session.questions){if(session.results[q.id]&&!session.results[q.id].retryable)continue;$('grading-status').textContent='正在检查第 '+(session.questions.indexOf(q)+1)+' 题，请稍候…';try{await call('grade',{question_id:q.id});persist();summary();renderReview(session.questions[index]);}catch(e){$('notice').textContent=e.message;}}
 grading=false;$('restart').disabled=false;const incomplete=session.questions.some(q=>!session.results[q.id]||session.results[q.id].retryable);$('retry').hidden=!incomplete;$('grading-status').textContent=incomplete?'部分题目未完成检查，可稍后重试；提交的答案已保存。':'本次检查完成。请查看每道题的评分点。';}
async function load(){
 try{const r=await fetch('/api/state');if(!r.ok)throw Error('连接失败，请刷新重试。');token=(await r.json()).token;$('start').disabled=false;let cached;try{cached=JSON.parse(localStorage.getItem(KEY)||'null');}catch{}
 if(cached?.id){session={id:cached.id};await call('get');drafts={...session.drafts};flags=cached.flags||{};index=Math.max(0,Math.min(3,Number(cached.index)||0));if(session.status==='active'&&cached.dirty&&cached.revision===session.revision){drafts={...drafts,...cached.drafts};dirty=true;}$('intro').hidden=true;$('exam').hidden=false;if(session.status==='submitted'){submittedView();grade();}else{renderQuestion();saveDrafts();}}
 }catch(e){$('notice').textContent=e.message;session=null;}
}
$('start').onclick=async()=>{if(session)return;$('start').disabled=true;try{await call('start');drafts={};flags={};index=0;persist();$('intro').hidden=true;$('exam').hidden=false;renderQuestion();}catch(e){$('notice').textContent=e.message;$('start').disabled=false;}};
$('code').oninput=()=>{if(session.status!=='active'||remaining()<=0){$('code').readOnly=true;return;}drafts[session.questions[index].id]=$('code').value;dirty=true;persist();drawTabs();$('save-status').textContent='正在等待保存…';clearTimeout(debounce);debounce=setTimeout(saveDrafts,450);};
$('previous').onclick=()=>{index--;persist();renderQuestion();};$('next').onclick=()=>{index++;persist();renderQuestion();};$('flag').onclick=()=>{const q=session.questions[index];flags[q.id]=!flags[q.id];persist();renderQuestion();};
$('submit').onclick=()=>{const blank=session.questions.filter(q=>!drafts[q.id]?.trim()).length;$('submit-description').textContent=blank?`还有 ${blank} 道题未填写答案。`:'四道题均已填写答案。';$('submit-dialog').showModal();};$('cancel-submit').onclick=()=>$('submit-dialog').close();$('confirm-submit').onclick=submit;
$('restart').onclick=()=>{try{const old=JSON.parse(localStorage.getItem('csa-frq-exam-history')||'[]');localStorage.setItem('csa-frq-exam-history',JSON.stringify([...old,session.id]));localStorage.removeItem(KEY);}catch{}session=null;drafts={};dirty=false;index=0;flags={};$('exam').hidden=true;$('intro').hidden=false;$('start').disabled=false;$('submit').hidden=false;$('submit').disabled=false;$('hide-timer').hidden=false;$('result-summary').hidden=true;$('review').hidden=true;$('phase').textContent='FRQ 模拟考试';$('timer-label').textContent='剩余时间';$('timer').textContent='90:00';$('timer').classList.remove('urgent');$('back').hidden=true;$('restart').hidden=true;$('retry').hidden=true;$('grading-status').textContent='';$('notice').textContent='';$('save-status').textContent='';};
$('retry').onclick=grade;$('hide-timer').onclick=()=>{timerHidden=!timerHidden;$('hide-timer').textContent=timerHidden?'显示时间':'隐藏时间';};
$('reference-open').onclick=()=>$('reference').showModal();$('reference-close').onclick=()=>$('reference').close();
let expiring=false;
setInterval(()=>{if(!session||session.status!=='active')return;const left=remaining();if(left<=300){timerHidden=false;$('hide-timer').hidden=true;$('timer').classList.add('urgent');}$('timer').textContent=timerHidden?'已隐藏':format(left);if(left<=0&&!expiring){expiring=true;$('code').readOnly=true;submit().finally(()=>{expiring=false;});}},1000);
setInterval(()=>{if(session?.status==='active'&&!saving&&!dirty){const revision=session.revision;call('get').then(()=>{if(session.status==='submitted'){submittedView();grade();}else if(session.revision!==revision&&!dirty){drafts={...session.drafts};renderQuestion();persist();$('notice').textContent='另一页面更新了作答，已同步最新内容。';}}).catch(()=>{});}},15000);
window.addEventListener('beforeunload',e=>{if(dirty){e.preventDefault();e.returnValue='';}});
load();
