const $=id=>document.getElementById(id);
const el=(tag,text,cls)=>{const n=document.createElement(tag);if(text!==undefined)n.textContent=text;if(cls)n.className=cls;return n;};
let data,items={},revision,dirty=false,saving=false;
const tiers={2:'基础',3:'巩固',4:'考试风格'};
const decisions={unreviewed:'未审核',suitable:'适合目前学生',too_easy:'偏简单',too_hard:'偏难',unclear:'表述需改进',incorrect:'答案或代码有问题'};
const checks={java_passed:'代码或参考实现已通过 Java 检查',conceptual:'解释题 · 需人工判断',unverified:'代码检查待更新'};
function setStatus(text,error=false){$('status').textContent=text;$('status').className=error?'error':'hint';}
function changed(){dirty=true;setStatus('有未保存反馈，完成后点击“保存全部反馈”。');}
function selectTopics(){const previous=$('topic').value;$('topic').replaceChildren(el('option','全部 Topic'));$('topic').firstChild.value='';for(const [id,title] of Object.entries(data.labels)){if($('unit').value && !id.startsWith($('unit').value+'.'))continue;const opt=el('option',id+' '+title);opt.value=id;$('topic').append(opt);}if(Array.from($('topic').options).some(o=>o.value===previous))$('topic').value=previous;render();}
function render(){
 const selected=data.questions.filter(r=>(!$('unit').value||r.content.ced_topics[0].startsWith($('unit').value+'.'))&&(!$('topic').value||r.content.ced_topics[0]===$('topic').value)&&(!$('tier').value||r.content.level===Number($('tier').value)));
 $('count').textContent=`当前 ${selected.length} 道 · 全部 ${data.questions.length} 道新增题`;$('review-questions').replaceChildren();
 for(const r of selected){const q=r.content;const card=el('article',undefined,'question');card.id=q.id;card.append(el('span',`Topic ${q.ced_topics[0]} · ${tiers[q.level]} · 预计 ${q.minutes} 分钟`,'badge'),el('h3',q.title),el('p',q.id+' · '+checks[r.technical_status],'hint'),el('pre',q.code),el('pre',q.task,'task'));
 const answer=el('details',undefined,'answer');answer.append(el('summary','查看答案、参考代码与评分点'),el('p',q.answer,'text'));if(q.reference_solution)answer.append(el('pre',q.reference_solution));const list=el('ol');for(const point of q.reasoning)list.append(el('li',point));answer.append(list,el('p','评分：'+q.rubric),el('p','常见错误：'+q.errors.join('；')),el('p','讲解建议：'+q.intervention));card.append(answer);
 const current=items[q.id]?.content_hash===r.content_hash?items[q.id]:{decision:'unreviewed',comment:'',content_hash:r.content_hash};
 const label=el('label','你的判断');const select=el('select');for(const [value,title] of Object.entries(decisions)){const option=el('option',title);option.value=value;select.append(option);}select.value=current.decision;label.append(select);const noteLabel=el('label','具体意见（可选）');const note=el('textarea');note.rows=2;note.maxLength=4000;note.value=current.comment;note.placeholder='例如：希望增加一个边界条件；预计需要 12 分钟。';noteLabel.append(note);
 const update=()=>{items[q.id]={decision:select.value,comment:note.value,content_hash:r.content_hash};changed();};select.onchange=update;note.oninput=update;card.append(label,noteLabel);$('review-questions').append(card);
 }
}
$('unit').onchange=()=>selectTopics();$('topic').onchange=render;$('tier').onchange=render;$('overall').oninput=changed;
$('save').onclick=async()=>{if(saving||!data)return;saving=true;$('save').disabled=true;document.querySelector('main').inert=true;try{const response=await fetch('/api/action',{method:'POST',headers:{'Content-Type':'application/json','X-Review-Token':data.token},body:JSON.stringify({action:'bank-feedback',bank_version:data.version,revision,overall:$('overall').value,items})});const result=await response.json();if(!response.ok)throw Error(result.error);revision=result.revision;dirty=false;setStatus('全部反馈已保存到本机。你可以继续筛选、补充，也可以直接在对话里告诉我修改方向。');}catch(e){setStatus(e.message,true);}finally{saving=false;$('save').disabled=false;document.querySelector('main').inert=false;}};
window.addEventListener('beforeunload',e=>{if(dirty){e.preventDefault();e.returnValue='';}});
async function init(){const response=await fetch('/api/curriculum');data=await response.json();if(!response.ok)throw Error(data.error);revision=data.feedback.revision;items=data.feedback.data.items;$('overall').value=data.feedback.data.overall;$('overview').textContent=`4 个单元 · ${Object.keys(data.labels).length} 个 Topic · ${data.questions.length} 道新增原创题，每个 Topic 基础、巩固、考试风格各 1 道。原有 42 道仍可在练习页使用。`;$('scope').textContent=data.scope;$('source').href=data.source;for(const [id,title] of Object.entries(data.units)){const o=el('option','Unit '+id+' · '+title);o.value=id;$('unit').append(o);}selectTopics();$('save').disabled=false;}
init().catch(e=>setStatus('无法载入审核页：'+e.message,true));
