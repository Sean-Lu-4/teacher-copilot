"use strict";
const $=id=>document.getElementById(id); let KEY='csa-studio-progress-v1', accountUser=null, progressRevision=0, syncError=false, syncTimer=null, syncing=false, syncAgain=false,progressConflict=false;
let bank=[],catalog=[],progress={},unit='',current=null,revealed=false,storageOK=true,notebookReview=false;
let sessionRows=[],clockState={},clockHidden=false,clockQuestion=null;
const initialView=new URLSearchParams(location.search);
const names={1:'使用对象与方法',2:'选择与循环',3:'类的创建',4:'数据集合'};
function node(tag,text,cls){const e=document.createElement(tag);if(text!==undefined)e.textContent=text;if(cls)e.className=cls;return e;}
async function loadProgress(){
 accountUser=await CSAAccount.ready;
 if(accountUser)KEY+=':'+accountUser.id;
 try{const saved=JSON.parse(localStorage.getItem(KEY)||'{}');if(saved&&typeof saved==='object'&&!Array.isArray(saved))progress=saved;}catch{storageOK=false;}
 if(accountUser){const r=await fetch('/api/account/progress',{headers:{'X-Account-ID':accountUser.id}});if(!r.ok)throw Error('无法加载账号记录，请刷新后重试。');const data=await r.json();progress=data.data;progressRevision=data.revision;
 const pending=JSON.parse(localStorage.getItem(KEY+':pending')||'null');
 if(pending&&JSON.stringify(pending.data)===JSON.stringify(data.data)){localStorage.removeItem(KEY+':pending');}
 else if(pending&&pending.revision===progressRevision){progress=pending.data;setTimeout(syncProgress,0);}
 else if(pending){progressConflict=true;$('practice-area').inert=true;const banner=node('div',undefined,'community-status');banner.append(node('p','有一份尚未同步的本机草稿。账号记录已更新，请先下载备份再继续。'));const download=node('button','下载本机草稿');download.onclick=()=>{const a=node('a');a.href=URL.createObjectURL(new Blob([JSON.stringify(pending.data,null,2)],{type:'application/json'}));a.download='CSA-draft-backup.json';a.click();URL.revokeObjectURL(a.href);};const resume=node('button','使用账号已保存的记录');resume.disabled=true;const downloadDraft=download.onclick;download.onclick=()=>{downloadDraft();resume.disabled=false;};resume.onclick=()=>{localStorage.removeItem(KEY+':pending');progressConflict=false;$('practice-area').inert=false;banner.remove();};banner.append(download,resume);document.querySelector('main').prepend(banner);}
 }
}
function offerGuestImport(){
 if(!accountUser)return;let guest;try{guest=JSON.parse(localStorage.getItem('csa-studio-progress-v1')||'{}');}catch{return;}
 const missing=Object.keys(guest).filter(id=>!progress[id]);if(!missing.length)return;
 const banner=node('div',undefined,'guest-import');banner.append(node('p',`本机还有 ${missing.length} 道游客练习记录，可以保存到当前账号。`));
 const importButton=node('button','导入游客记录');importButton.onclick=async()=>{importButton.disabled=true;for(const id of missing)if(!progress[id])progress[id]=guest[id];save();clearTimeout(syncTimer);await syncProgress();if(!syncError){banner.remove();dashboard();choose();}else importButton.disabled=false;};
 const dismiss=node('button','暂不导入');dismiss.onclick=()=>banner.remove();banner.append(importButton,dismiss);document.querySelector('main').prepend(banner);
}
async function syncProgress(){
 if(!accountUser||progressConflict)return;if(syncing){syncAgain=true;return;}syncing=true;
 const snapshot=JSON.stringify(progress);
 try{const result=await CSAAccount.post('/api/account/progress',{data:JSON.parse(snapshot),revision:progressRevision});progressRevision=result.revision;syncAgain=syncAgain||snapshot!==JSON.stringify(progress);syncError=false;if(!syncAgain)localStorage.removeItem(KEY+':pending');else localStorage.setItem(KEY+':pending',JSON.stringify({data:progress,revision:progressRevision}));}
 catch(e){syncError=true;$('notice').textContent=e.message+' 本机草稿已保留。';syncAgain=false;
 if(e.status===409){progressConflict=true;$('practice-area').inert=true;const banner=node('div',undefined,'community-status');banner.append(node('p','账号或学习记录已在其他页面更新。请刷新页面，核对并恢复本机草稿。'));const reload=node('button','刷新并恢复草稿');reload.onclick=()=>location.reload();banner.append(reload);document.querySelector('main').prepend(banner);}
 }
 finally{syncing=false;if(syncAgain){syncAgain=false;syncProgress();}}
}
function save(){if(progressConflict)return;try{localStorage.setItem(KEY,JSON.stringify(progress));}catch{storageOK=false;$('notice').textContent='浏览器无法保存进度，请勿关闭页面。';}if(accountUser){try{localStorage.setItem(KEY+':pending',JSON.stringify({data:progress,revision:progressRevision}));}catch{}clearTimeout(syncTimer);syncTimer=setTimeout(syncProgress,500);}}
CSAAccount.flush=async()=>{clearTimeout(syncTimer);await syncProgress();if(syncError||syncing||progressConflict)throw Error('学习记录尚未保存，请稍后再退出。');};
window.addEventListener('beforeunload',e=>{if(accountUser&&(syncing||syncError||localStorage.getItem(KEY+':pending'))){e.preventDefault();e.returnValue='';}});
window.addEventListener('online',()=>{if(accountUser){clearTimeout(syncTimer);syncProgress();}});
document.addEventListener('visibilitychange',()=>{if(document.hidden&&accountUser){clearTimeout(syncTimer);syncProgress();}});
function record(q){const r=progress[q.id];return r&&typeof r==='object'?r:{};}
function units(q){return (q.units||[q.ap_unit]).map(String);}
function available(q){return (!unit||units(q).includes(unit))&&q.question_kind===$('kind').value&&(!$('topic').value||(q.ced_topics||[]).includes($('topic').value))&&($('scope').value==='all'||($('scope').value==='runnable'?q.java_check_supported:($('scope').value==='new'?!record(q).done:CSAProgress.isMistake(record(q))&&!record(q).mastered)));}
function dashboard(){
 $('mistake-count').textContent=bank.filter(q=>CSAProgress.isMistake(record(q))&&!record(q).mastered).length;
 $('stats').replaceChildren();const done=bank.filter(q=>record(q).done),mastered=done.filter(q=>record(q).mastered);
 for(const [label,value] of [['可练总题数',bank.length],['已练题数',done.length],['答对 / 自评掌握',mastered.length],['待巩固',done.length-mastered.length]]){const card=node('div',undefined,'stat');card.append(node('span',label),node('strong',String(value)));$('stats').append(card);}
 $('units').replaceChildren();
 const all=node('button','全部单元','unit');all.type='button';all.setAttribute('aria-pressed',String(!unit));all.onclick=()=>{unit='';refreshTopics();dashboard();choose();};$('units').append(all);
 for(const id of ['1','2','3','4']){const rows=bank.filter(q=>units(q).includes(id)),done=rows.filter(q=>record(q).done).length;const b=node('button',undefined,'unit');b.type='button';b.setAttribute('aria-pressed',String(unit===id));b.append(node('b','Unit '+id),node('span',names[id]),node('small',`${done} / ${rows.length} 题 · ${rows.length?Math.round(done/rows.length*1000)/10:0}%`));const p=node('progress');p.max=rows.length||1;p.value=done;p.setAttribute('aria-label',`Unit ${id} 已练 ${done} 题，共 ${rows.length} 题`);b.append(p);b.onclick=()=>{unit=id;refreshTopics();dashboard();choose();$('practice-area').scrollIntoView({behavior:'smooth',block:'start'});};$('units').append(b);}
}
function refreshTopics(){const previous=$('topic').value;$('topic').replaceChildren(new Option('全部课题',''));for(const t of catalog){if(bank.some(q=>(!unit||units(q).includes(unit))&&(q.ced_topics||[]).includes(t.id)))$('topic').append(new Option(`${t.id} · ${t.title}`,t.id));}if([...$('topic').options].some(o=>o.value===previous))$('topic').value=previous;}
function choose(skip){pauseClock();notebookReview=false;sessionRows=bank.filter(available);current=sessionRows.find(q=>q.id!==skip)||null;revealed=false;render();}
function button(text,fn,primary=false){const b=node('button',text,primary?'primary':'');b.type='button';b.onclick=fn;return b;}
function paintNotebookButton(b,q){const added=CSAProgress.isMistake(record(q));b.textContent=added?'已加入错题本 · 移除':'＋ 加入错题本';b.setAttribute('aria-pressed',String(added));b.classList.add('notebook-toggle');}
function render(){
 const box=$('question');box.replaceChildren();$('actions').replaceChildren();updateWorkspace();if(current?.question_kind==='write'&&!revealed){clockState=PracticeClock.start(clockState,Date.now());clockSave();paintClock();}
 if(!current){box.append(node('h2','这个范围已没有待练题目'),node('p','可以切换单元、课题或选择“全部题目”继续练习。'));return;}
 const q=current,r=record(q),mcq=q.question_kind==='concept';
 box.dataset.questionId=q.id; const notebook=button('',()=>{progress[q.id]=CSAProgress.toggleNotebook(record(q));save();dashboard();paintNotebookButton(notebook,q);});paintNotebookButton(notebook,q);box.append(notebook);
 box.append(node('p',`${units(q).map(u=>'Unit '+u).join(' / ')} · ${mcq?'MCQ':'FRQ'}${mcq?' · 预计 '+q.minutes+' 分钟':''}`,'muted'),node('h2',q.title));
 if(q.code&&!q.code.startsWith('// AP source question'))box.append(node('pre',q.code));
 if(q.question_images?.length){
  for(const file of q.question_images){const link=node('a');link.href='/source-image/'+encodeURIComponent(file);link.target='_blank';link.rel='noopener';link.title='打开原题大图';const img=node('img');img.src=link.href;img.alt=q.title+' 原题（含表格和图示）';img.className='question-image';link.append(img);box.append(link);}
  const transcript=node('details');transcript.append(node('summary','题目文字'),node('div',q.task,'task'));box.append(transcript);
 }else box.append(node('div',q.task,'task'));
 const prompt=node('section',undefined,'question-prompt');prompt.setAttribute('aria-label','题目');while(box.firstChild)prompt.append(box.firstChild);box.append(prompt);
 const response=node('section',undefined,'response-pane');response.setAttribute('aria-label','答题区');box.append(response);
 if(mcq){const group=node('fieldset');group.append(node('legend','选择一个答案'));for(const [key,text] of Object.entries(q.options)){const label=node('label',undefined,'option'),input=node('input');input.type='radio';input.name='choice';input.value=key;input.checked=r.draftChoice===key;input.onchange=()=>{progress[q.id]={...record(q),draftChoice:key};save();};input.disabled=revealed;label.append(input,node('span',`${key}. ${text}`));group.append(label);}response.append(node('h3','选择答案'),group);}
 else{
  const parts=q.java_parts||[],selected=Math.min(Number.isInteger(r.javaPart)&&r.javaPart>=0?r.javaPart:0,Math.max(0,parts.length-1));
  if(parts.length){const label=node('label','检查哪一小问'),select=node('select');select.id='java-part';parts.forEach((p,i)=>select.append(new Option(p.label,String(i))));select.value=String(selected);select.onchange=()=>{progress[q.id]={...record(q),javaPart:Number(select.value)};save();revealed=false;render();};label.append(select);response.append(label,node('p','已提供变量：'+parts[selected].args,'muted'));}
  if(parts.length&&r.draft){const old=node('details');old.append(node('summary','查看之前保存的整题草稿'),node('pre',r.draft));response.append(old);}
  const label=node('label','你的 Java 代码');label.htmlFor='draft';const area=node('textarea');area.id='draft';area.maxLength=20000;area.spellcheck=false;
  area.value=parts.length?(r.partDrafts?.[selected]||''):(r.draft||'');
  area.placeholder=q.java_input_kind==='class'?'填写题目要求的完整类，包括字段、构造器和方法。':['fragment','email','parts'].includes(q.java_input_kind)?'填写本题或所选小问的代码片段；不需要外层 class 或方法。':'填写题目要求的方法或构造器；无需重复给定的字段、辅助类或 main。';
  area.addEventListener('keydown',event=>{if(event.key==='Tab'){event.preventDefault();const start=area.selectionStart,end=area.selectionEnd;area.setRangeText('    ',start,end,'end');area.dispatchEvent(new Event('input'));}});
  area.oninput=()=>{const previous=record(q);progress[q.id]={...previous,...(parts.length?{partDrafts:{...previous.partDrafts,[selected]:area.value}}:{draft:area.value}),frqReview:null};save();document.getElementById('code-feedback')?.remove();};
  response.append(label,area,node('p',q.java_check_supported?'检查后查看运行结果和逐项得分。':'本题暂支持语法检查，答案请对照评分指南。','muted'));
  if(q.java_check_note)response.append(node('p',q.java_check_note,'muted'));
 }
 $('actions').append(button(mcq?'提交答案':'查看参考答案',()=>{
  if(mcq){const selected=document.querySelector('input[name=choice]:checked');if(!selected){$('notice').textContent='请先选择一个答案。';return;}const correct=selected.value===q.answer_key;progress[q.id]=CSAProgress.submit(record(q),correct,selected.value);save();dashboard();showAnswer(correct?'回答正确':'这道题还需要巩固');}
  else{showAnswer('参考答案');}
 },mcq));
 if(!mcq)$('actions').prepend(button('检查代码',()=>checkCode(q),true));
 if(notebookReview)$('actions').append(button('返回错题本',()=>setView('mistakes')));
}
function showAnswer(message){pauseClock();if(revealed){$('reference-answer')?.scrollIntoView({behavior:'smooth',block:'start'});return;}revealed=true;if(storageOK)$('notice').textContent='';document.querySelectorAll('input[name=choice]').forEach(e=>e.disabled=true);const q=current,box=node('section',undefined,'answer');box.id='reference-answer';const notebookButton=document.querySelector('.notebook-toggle');if(notebookButton)paintNotebookButton(notebookButton,q);box.append(node('p',message,'result'));box.tabIndex=-1;if(q.question_kind==='write'&&q.scoring_points?.length){const list=node('ol',undefined,'score-summary');for(const point of q.scoring_points)list.append(node('li',`${point.label} · ${point.points} 分：${point.description}`));box.append(node('h3','本题得分点'),list);}
 if(q.answer_key){
  for(const input of document.querySelectorAll('input[name=choice]')){const label=input.closest('label');if(input.value===q.answer_key){label.classList.add('choice-correct');label.append(node('strong','✓ 正确答案','choice-verdict'));}else if(input.checked){label.classList.add('choice-wrong');label.append(node('strong','✕ 你的选择','choice-verdict'));}}
  box.append(node('h3','正确答案：'+q.answer_key));
 }
 for(const [title,text] of [['答案与解析',q.answer],['参考代码',q.reference_solution],['评分标准',q.rubric],['English explanation',q.explanation_en]])if(text){const detail=node('details');detail.open=q.question_kind==='concept'||title==='参考代码'||!q.scoring_pages?.length;detail.append(node('summary',q.scoring_pages?.length?title+'（文字备份）':title),node('pre',text.replace(/^Select a point value to view scoring criteria or to score the response\.\s*$/gm,'')));box.append(detail);}
 if(q.scoring_pages?.length){
  const guide=node('section',undefined,'inline-scoring-guide');guide.append(node('h3','原评分指南'));
  const seen=new Set();
  for(const ref of q.scoring_pages){
   if(!/^[a-f0-9]{64}$/.test(ref.document)||!Number.isInteger(ref.page)||ref.page<1)continue;
   const key=ref.document+':'+ref.page;if(seen.has(key))continue;seen.add(key);
   const figure=node('figure'),img=node('img'),caption=node('figcaption',`原评分指南 · 第 ${ref.page} 页`);
   img.src=`/scoring-page/${ref.document}/${ref.page}.png`;img.alt=caption.textContent;img.loading='lazy';img.decoding='async';
   img.onerror=()=>{img.hidden=true;caption.textContent='原版页面暂未载入，请先查看上方答案与解析。';};
   const link=node('a');link.href=img.src;link.target='_blank';link.rel='noopener';link.title='打开评分指南大图';link.append(img);figure.append(caption,link);guide.append(figure);
  }
  box.append(guide);
 }
 $('question').append(box);$('actions').replaceChildren();
 if(q.question_kind==='write')$('actions').append(button('检查代码',()=>checkCode(q)));
 if(q.question_kind==='write'){for(const [label,mastered] of [['自评：已掌握',true],['自评：还需练习',false]])$('actions').append(button(label,()=>{progress[q.id]=CSAProgress.submit(record(q),mastered);save();dashboard();next();},mastered));}
 else $('actions').append(button(notebookReview?'返回错题本':'下一题',next,true));
 requestAnimationFrame(()=>{box.focus({preventScroll:true});box.scrollIntoView({behavior:'instant',block:'start'});});
}
let checkingCode=false;
async function checkCode(q){
 if(checkingCode)return;
 const code=$('draft')?.value||'',part=$('java-part')?Number($('java-part').value):null;
 if(!code.trim()){$('notice').textContent='请先写下你的 Java 代码。';return;}
 checkingCode=true;const pendingButtons=[...document.querySelectorAll('#actions button')].filter(b=>b.textContent==='检查代码');pendingButtons.forEach(b=>{b.disabled=true;b.textContent='正在检查…';});$('notice').textContent='正在编译和检查代码，请稍候…';
 const controller=new AbortController(),timer=setTimeout(()=>controller.abort(),65000);
 try{
  const stateResponse=await fetch('/api/state',{signal:controller.signal});if(!stateResponse.ok)throw Error('暂时无法连接检查服务。');
  const state=await stateResponse.json();
  const response=await fetch('/api/student/check',{method:'POST',headers:{'Content-Type':'application/json','X-Review-Token':state.token},body:JSON.stringify({question_id:q.id,code,part}),signal:controller.signal});
  const result=await response.json();if(!response.ok)throw Error(result.error||'检查失败，请稍后重试。');
  if(current?.id!==q.id||$('draft')?.value!==code||($('java-part')?Number($('java-part').value):null)!==part)return;
  document.getElementById('code-feedback')?.remove();
  const panel=node('section',undefined,'code-feedback');panel.id='code-feedback';
  const auto=result.automatic||{},executed=['passed','failed','compile_error','runtime_error','timeout'].includes(auto.status),failed=executed?auto.status!=='passed':result.syntax.status==='failed',passed=result.syntax.status==='passed';
  if(executed)result.syntax.diagnostics=auto.diagnostics||[];
  panel.classList.add(failed?'has-errors':auto.status==='passed'?'verified-code':'needs-review');
  panel.append(node('h3',executed?(auto.status==='passed'?'✓ 当前功能测试通过':'需要修改'):failed?'需要修改':passed?'语法检查通过，答案待检查':'暂时无法检查'),node('p',executed?auto.message:failed?'先修改下面标出的代码行，再检查一次。':(auto.message||'还没有运行代码，暂时不能判断答案对错或自动给分。')));
  if(auto.practice_score){panel.append(node('strong',`功能检查：${auto.practice_score.earned} / ${auto.practice_score.possible} 项通过`),node('p','这是功能测试结果，不是 AP 官方得分。','muted'));}
  for(const test of auto.cases||[]){const row=node('div',undefined,'test-result '+(test.status==='passed'?'test-pass':'test-fail'));row.append(node('strong',(test.status==='passed'?'✓ ':'✕ ')+test.label),node('p',test.reason));if(test.detail)row.append(node('pre',test.detail));panel.append(row);}
  const applicableScores=(auto.score_evidence||[]).filter(p=>p.applicable!==false);
  if(applicableScores.length){
   const earned=applicableScores.filter(p=>p.status==='earned').reduce((n,p)=>n+p.points,0),pending=applicableScores.filter(p=>p.status!=='earned').reduce((n,p)=>n+p.points,0);
   panel.append(node('h3',pending?`参考得分：已找到 ${earned} 分依据 · ${pending} 分待复核`:`参考得分：${earned} / ${earned} 分`),node('p',applicableScores.some(p=>p.provenance==='reference')?'依据参考评分建议与测试估计；原题缺正式评分指南，未确认的分值待复核。':'依据原评分指南与当前测试估计，未验证的部分不按零分处理。','muted'));
   const pendingDetails=node('details',undefined,'pending-score-details');pendingDetails.append(node('summary',`${pending} 分待复核 · 查看评分点`));
   for(const point of applicableScores){const row=node('div',undefined,'score-evidence '+(point.status==='earned'?'test-pass':'test-pending'));row.append(node('strong',`${point.status==='earned'?'✓':'待复核'} ${point.label} · ${point.status==='earned'?'+1 分':'1 分待确认'}`),node('span',point.status==='earned'?'':'部分分待复核','muted'));row.title=point.reason;
    for(const line of point.lines||[])row.append(button('第 '+line+' 行',()=>{const area=$('draft'),lines=area.value.split('\n'),start=lines.slice(0,line-1).reduce((n,l)=>n+l.length+1,0);area.focus();area.setSelectionRange(start,start+(lines[line-1]||'').length);}));(point.status==='earned'?panel:pendingDetails).append(row);}
   if(pending)panel.append(pendingDetails);
  }
  if(auto.detail){const detail=node('details');detail.append(node('summary','查看编译 / 运行提示'),node('pre',auto.detail));panel.append(detail);}
  const preview=node('div',undefined,'checked-code'),errorLines=new Set(result.syntax.diagnostics.map(e=>e.line));
  code.split('\n').forEach((text,index)=>{const line=node('div',undefined,errorLines.has(index+1)?'checked-line error-line':'checked-line');line.append(node('span',String(index+1),'line-number'),node('code',text||' '));if(errorLines.has(index+1))line.append(node('span','← 检查此处','line-flag'));preview.append(line);});
  if(failed){const codeDetails=node('details');codeDetails.append(node('summary','查看带行号的代码'),preview);panel.append(codeDetails);}
  for(const error of result.syntax.diagnostics){panel.append(button(`第 ${error.line} 行：${error.message}`,()=>{
   const area=$('draft'),lines=area.value.split('\n'),start=lines.slice(0,error.line-1).reduce((n,line)=>n+line.length+1,0);area.focus();area.setSelectionRange(start,start+(lines[error.line-1]||'').length);
  }));}
  panel.append(button('返回修改',()=>{$('draft').focus();$('draft').scrollIntoView({behavior:'smooth',block:'center'});},true));
  const scoring=node('details',undefined,'scoring-details');scoring.append(node('summary','查看评分细则与自评'),node('p','这是对照评分指南的自评，不是系统判分。'));panel.append(scoring);
  const points=result.scoring_points,previous=record(q).frqReview,review=previous?.code===code?previous.items:{};
  const total=node('p',undefined,'score-total');scoring.append(total);
  function update(){let earned=0,pending=0;for(const p of points){const state=review[p.id]?.status;if(state==='earned')earned+=p.points;else if(state!=='missed')pending+=p.points;}total.textContent=`自评已得 ${earned} 分 · 待复核 ${pending} 分 · 已列出 ${points.length} 个评分点（不代表自动评分或全题总分）`;progress[q.id]={...record(q),frqReview:{code,items:review}};save();}
  if(!points.length){scoring.append(node('p','这道题的评分指南尚未整理为逐项清单，请点击“查看参考答案”对照原评分指南。'));total.hidden=true;}
  for(const point of points){
   const row=node('div',undefined,'score-point');row.append(node('h4',`${point.label} · ${point.points} 分`),node('p',point.description));
   if(point.exceptions){const details=node('details');details.append(node('summary','得分例外与扣分条件'),node('pre',point.exceptions));row.append(details);}
   const label=node('label','我的判断'),select=node('select');select.setAttribute('aria-label',point.label+' 得分状态');for(const [value,text] of [['unverified','待复核'],['earned','自评得分'],['missed','自评未得分']])select.append(new Option(text,value));select.value=review[point.id]?.status||'unverified';label.append(select);
   const evidenceLabel=node('label','依据：代码行号或理由'),evidence=node('input');evidence.maxLength=500;evidence.value=review[point.id]?.evidence||'';evidence.placeholder='例如：第 4–7 行处理了空列表';evidenceLabel.append(evidence);
   const persist=()=>{review[point.id]={status:select.value,evidence:evidence.value};update();};select.onchange=persist;evidence.oninput=persist;row.append(label,evidenceLabel);scoring.append(row);
  }
  if(points.length)update();$('question').append(panel);$('notice').textContent='';panel.scrollIntoView({behavior:'smooth',block:'start'});
 }catch(error){if(current?.id===q.id)$('notice').textContent=error.name==='AbortError'?'检查超时，请稍后重试。':error.message;}
 finally{clearTimeout(timer);checkingCode=false;pendingButtons.forEach(b=>{b.disabled=false;b.textContent='检查代码';});}
}
function next(){if(notebookReview){notebookReview=false;setView('mistakes');return;}moveQuestion(1);}
function mistakeRows(){return bank.filter(q=>CSAProgress.isMistake(record(q))&&(!$('mistake-unit').value||units(q).includes($('mistake-unit').value))&&(!$('mistake-kind').value||q.question_kind===$('mistake-kind').value)&&($('mistake-status').value==='all'||($('mistake-status').value==='mastered'?record(q).mastered:!record(q).mastered))).sort((a,b)=>(record(b).lastWrong||'').localeCompare(record(a).lastWrong||''));}
function setView(view){
 if(view==='mistakes')pauseClock();
 const mistakes=view==='mistakes';document.body.classList.toggle('notebook-mode',mistakes);$('practice-view').hidden=mistakes;$('mistakes-view').hidden=!mistakes;
 $('practice-tab').setAttribute('aria-pressed',String(!mistakes));$('mistakes-tab').setAttribute('aria-pressed',String(mistakes));
 document.querySelectorAll('header nav a').forEach(a=>{const selected=a.getAttribute('href')===(mistakes?'/practice?view=mistakes':'/practice');a.classList.toggle('active',selected);if(selected)a.setAttribute('aria-current','page');else a.removeAttribute('aria-current');});
 const url=new URL(location.href);if(mistakes)url.searchParams.set('view','mistakes');else url.searchParams.delete('view');history.replaceState(null,'',url);
 if(mistakes){notebookReview=false;renderNotebook();}else{render();}
}
function openMistake(q){
 pauseClock();sessionRows=[q];unit='';refreshTopics();$('topic').value='';$('kind').value=q.question_kind;$('scope').value='all';current=q;revealed=false;notebookReview=true;
 dashboard();setView('practice');$('practice-area').scrollIntoView({behavior:'smooth',block:'start'});$('practice-area').focus({preventScroll:true});
}
function renderNotebook(){
 const all=bank.filter(q=>CSAProgress.isMistake(record(q))),pending=all.filter(q=>!record(q).mastered),rows=mistakeRows();
 $('notebook-summary').textContent=`累计收录 ${all.length} 道 · 待巩固 ${pending.length} 道 · 已巩固 ${all.length-pending.length} 道`;
 const review=rows.filter(q=>!record(q).mastered);$('review-pending').disabled=!review.length;$('review-pending').textContent=review.length?`复习待巩固题（${review.length}）`:'暂无待巩固题';$('review-pending').onclick=()=>{if(review[0])openMistake(review[0]);};
 $('mistake-list').replaceChildren();
 if(!rows.length){const empty=node('div',undefined,'notebook-empty');empty.append(node('h3',all.length?'当前筛选下没有题目':'你的错题本，从第一次尝试开始'),node('p',all.length?'试试其他单元、题型或复习状态。':'答错的题会自动加入，也可以在题目上点击“加入错题本”。'));empty.append(button('去练习',()=>{notebookReview=false;unit='';$('scope').value='new';refreshTopics();dashboard();choose();setView('practice');},true));$('mistake-list').append(empty);return;}
 for(const q of rows){const r=record(q),card=node('article',undefined,'mistake-card'),head=node('div',undefined,'mistake-card-head');head.append(node('span',units(q).map(u=>'Unit '+u).join(' / ')+' · '+(q.question_kind==='concept'?'MCQ':'FRQ'),'eyebrow'),node('span',r.mastered?'已巩固':'待巩固',r.mastered?'state-pill mastered':'state-pill pending'));card.append(head,node('h3',q.title));
 card.append(node('p',q.task.replace(/\s+/g,' ').slice(0,160)+(q.task.length>160?'…':''),'mistake-excerpt'));
 const info=[];if(r.manualMistake)info.push('手动加入');if(r.lastWrongChoice||(!r.mastered&&r.choice))info.push('上次错选 '+(r.lastWrongChoice||r.choice));info.push('已尝试 '+(Number(r.attempts)||0)+' 次');if(r.lastWrong){const dt=new Date(r.lastWrong);if(!Number.isNaN(dt.getTime()))info.push(dt.toLocaleDateString('zh-CN'));}card.append(node('p',info.join(' · '),'muted'));
 const actions=node('div',undefined,'actions');actions.append(button(r.mastered?'再练一次':'重新练习',()=>openMistake(q),true));
 actions.append(button('移出错题本',()=>{progress[q.id]=CSAProgress.toggleNotebook(record(q));save();dashboard();renderNotebook();}));
 const notes=node('details',undefined,'review-notes'),summary=node('summary',r.note?'查看 / 修改复习笔记':'记录复习笔记'),label=node('label','这道题提醒了你什么？'),area=node('textarea');area.setAttribute('aria-label','复习笔记：'+q.title);area.value=r.note||'';area.maxLength=3000;area.placeholder='例如：整数除法会舍去小数部分。';area.oninput=()=>{progress[q.id]={...record(q),note:area.value};save();};label.append(area);notes.append(summary,label);card.append(actions,notes);$('mistake-list').append(card);
 }
}
async function init(){try{await loadProgress();offerGuestImport();const response=await fetch('/api/bank');if(!response.ok)throw Error('题库暂时无法加载，请刷新重试。');const data=await response.json();$('bank-count-note').textContent=`教师组卷题库 ${data.total_count??data.questions.length} 题；学生练习只收录有参考答案的 PDF 题。`;catalog=data.ced_topics||[];bank=[...new Map(data.questions.filter(q=>q.source_item_id&&((q.question_kind==='concept'&&q.answer_key&&q.options?.[q.answer_key])||(q.question_kind==='write'&&(q.reference_solution||q.answer||(q.source_refs||[]).some(r=>r.role==='SG'))))).map(q=>[q.id,q])).values()];$('notice').textContent=storageOK?'':'当前浏览器无法保存进度。';unit=['1','2','3','4'].includes(initialView.get('unit'))?initialView.get('unit'):'';refreshTopics();dashboard();choose();setView(initialView.get('view')==='mistakes'?'mistakes':'practice');$('practice-tab').onclick=()=>{notebookReview=false;choose();setView('practice');};$('mistakes-tab').onclick=()=>setView('mistakes');for(const id of ['mistake-status','mistake-unit','mistake-kind'])$(id).onchange=renderNotebook;for(const id of ['kind','scope','topic'])$(id).onchange=()=>{if(id==='scope'&&$('scope').value==='runnable')$('kind').value='write';if(id==='kind'&&$('kind').value==='concept'&&$('scope').value==='runnable')$('scope').value='all';notebookReview=false;choose();};for(const id of ['kind','scope','topic'])$(id).disabled=false;}catch(e){$('notice').textContent=e.message;}}
initWorkspace();
init();

function clockSave(){if(!clockQuestion)return;progress[clockQuestion]={...(progress[clockQuestion]||{}),timer:clockState};save();}
function pauseClock(){if(!clockQuestion)return;clockState=PracticeClock.pause(clockState,Date.now());clockSave();paintClock();}
function updateWorkspace(){
 if(!current){$('question-position').textContent='暂无题目';for(const id of ['clock-toggle','flag-question','previous-question','next-question','question-menu-toggle','target-minutes'])$(id).disabled=true;return;}
 const q=current;
 if(clockQuestion!==q.id){pauseClock();clockQuestion=q.id;clockState=PracticeClock.restore(record(q).timer);}
 const index=sessionRows.findIndex(x=>x.id===q.id);
 $('question-position').textContent=`${q.question_kind==='write'?'FRQ':'MCQ'} · 第 ${index+1} / ${sessionRows.length} 题`;
 for(const id of ['clock-toggle','flag-question','question-menu-toggle','target-minutes'])$(id).disabled=false;
 $('previous-question').disabled=index<=0;$('next-question').disabled=index>=sessionRows.length-1;
 $('flag-question').setAttribute('aria-pressed',String(!!record(q).flagged));$('flag-question').textContent=record(q).flagged?'已标记 · 取消标记':'标记待检查';
 $('target-minutes').value=clockState.target|| (q.question_kind==='write'?22.5:Math.max(1,Number(q.minutes)||2));
 $('timing-note').textContent=q.question_kind==='write'?'完整 FRQ 可参考平均 22.5 分钟；单个小问请自行缩短。这是练习目标，不是官方逐题限时。':'按自己的节奏练习；目标时间可调整。';
 $('question-menu').hidden=true;$('question-menu-toggle').setAttribute('aria-expanded','false');paintClock();
}
function paintClock(){
 const elapsed=PracticeClock.elapsed(clockState,Date.now()),target=Number($('target-minutes').value)*60000,over=elapsed>=target;
 $('clock-display').textContent=clockHidden?'已隐藏':PracticeClock.format(elapsed);
 $('clock-toggle').textContent=clockState.startedAt!==null?'暂停':elapsed?'继续计时':'开始计时';
 $('clock-display').classList.toggle('time-over',over);
 const message=over?'已达到练习目标时间，你可以继续作答。':'';
 if($('clock-notice').textContent!==message)$('clock-notice').textContent=message;
 if(current?.question_kind==='write'&&clockQuestion===current.id&&!revealed&&PracticeClock.shouldNotify(clockState,Date.now(),target/60000)){clockState.notifiedTarget=target/60000;clockSave();$('time-reminder-text').textContent=`本题已达到设定的 ${target/60000} 分钟。你的作答会保留，关闭提示后可以继续，计时不会停止。`;$('time-reminder').showModal();}
}
function moveQuestion(step){const index=sessionRows.findIndex(q=>q.id===current?.id);const q=sessionRows[index+step];if(q)visitQuestion(q);}
function visitQuestion(q){pauseClock();current=q;revealed=false;render();$('practice-area').scrollIntoView({behavior:'smooth',block:'start'});}
function initWorkspace(){
 $('overview-units').append($('unit-progress'));

 const reminder=node('dialog');reminder.id='time-reminder';reminder.setAttribute('aria-labelledby','time-reminder-title');const title=node('h2','练习时间到了');title.id='time-reminder-title';const text=node('p');text.id='time-reminder-text';reminder.append(title,text,button('继续作答',()=>reminder.close(),true));document.body.append(reminder);
 clockState=PracticeClock.restore(null);
 $('clock-toggle').onclick=()=>{if(!current)return;clockState=clockState.startedAt!==null?PracticeClock.pause(clockState,Date.now()):PracticeClock.start(clockState,Date.now());clockSave();paintClock();};
 $('clock-hide').onclick=()=>{clockHidden=!clockHidden;$('clock-hide').textContent=clockHidden?'显示时间':'隐藏时间';paintClock();};
 $('target-minutes').onchange=()=>{const n=Number($('target-minutes').value);if(!Number.isFinite(n)||n<1||n>180){$('target-minutes').value=clockState.target||22.5;return;}clockState.target=n;clockSave();paintClock();};
 $('setup-toggle').onclick=()=>{const compact=document.body.classList.toggle('compact-practice');$('setup-toggle').textContent=compact?'练习设置':'收起设置';$('setup-toggle').setAttribute('aria-expanded',String(!compact));$('practice-area').scrollIntoView({block:'start'});};
 $('flag-question').onclick=()=>{if(!current)return;progress[current.id]={...record(current),flagged:!record(current).flagged};save();updateWorkspace();};
 $('previous-question').onclick=()=>moveQuestion(-1);$('next-question').onclick=()=>moveQuestion(1);
 $('question-menu-toggle').onclick=()=>{const menu=$('question-menu');menu.hidden=!menu.hidden;$('question-menu-toggle').setAttribute('aria-expanded',String(!menu.hidden));menu.replaceChildren();if(!menu.hidden){menu.append(node('p','实心为当前题 · 已答为已提交 · 标记为待检查'));sessionRows.forEach((q,i)=>{const r=record(q),b=button(`${i+1}${r.done?' · 已答':''}${r.flagged?' · 标记':''}`,()=>visitQuestion(q));b.setAttribute('aria-current',q.id===current?.id?'true':'false');menu.append(b);});menu.scrollIntoView({behavior:'smooth',block:'nearest'});}};
 $('reference-toggle').onclick=()=>{$('java-reference').showModal();};
 $('reference-close').onclick=()=>$('java-reference').close();
 setInterval(()=>{if(current)paintClock();},1000);
 window.addEventListener('pagehide',clockSave);
}
