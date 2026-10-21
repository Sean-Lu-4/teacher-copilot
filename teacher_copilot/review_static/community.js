/* Shared account and support controls. All user text is rendered as text. */
(() => {
  const make=(tag,text,cls)=>{const e=document.createElement(tag);if(text)e.textContent=text;if(cls)e.className=cls;return e;};
  let user=null,emailEnabled=false,token='',lastFocus=null,contactInfo={email:'15652805681@163.com',wechat:'15652805681'};
  const ready=fetch('/api/account').then(async r=>{if(!r.ok)throw Error('账号服务暂时不可用');const d=await r.json();user=d.user;emailEnabled=!!d.email_enabled;token=d.token;contactInfo=d.contact||contactInfo;return user;});
  async function post(path,data){await ready;const r=await fetch(path,{method:'POST',headers:{'Content-Type':'application/json','X-Review-Token':token,'X-Account-ID':user?.id||'guest'},body:JSON.stringify(data)});const d=await r.json();if(!r.ok){const error=Error(d.error||'暂时无法完成，请重试。');error.status=r.status;throw error;}return d;}
  window.CSAAccount={ready,post};
  const dialog=make('dialog',null,'community-dialog');document.body.append(dialog);
  function open(title){document.body.classList.add('modal-open');dialog.oncancel=null;lastFocus=document.activeElement;dialog.replaceChildren();const head=make('div',null,'community-heading');const close=make('button','×','community-close');close.type='button';close.setAttribute('aria-label','关闭窗口');close.onclick=()=>dialog.close();head.append(make('h2',title),close);dialog.append(head);if(!dialog.open)dialog.showModal();}
  dialog.addEventListener('close',()=>{document.body.classList.remove('modal-open');lastFocus?.focus();});
  function field(form,title,name,type='text',required=true){const label=make('label',title),input=make(type==='textarea'?'textarea':'input');input.name=name;input.required=required;if(type!=='textarea')input.type=type;input.maxLength=type==='textarea'?2000:128;label.append(input);form.append(label);return input;}
  function action(text,fn,cls=''){const b=make('button',text,cls);b.type='button';b.onclick=fn;return b;}
  function auth(mode='login'){
    open(mode==='register'?'创建账号':mode==='reset'?'重设密码':'欢迎回来');
    const form=make('form'),status=make('p',null,'community-status');status.setAttribute('role','status');
    const username=field(form,'用户名','username');username.autocomplete='username';username.pattern='[a-zA-Z0-9_]{3,32}';username.placeholder='3–32 位字母、数字或下划线';
    if(mode==='register'){const label=make('label','你的身份'),select=make('select');select.name='role';select.append(new Option('学生','student'),new Option('教师','teacher'));label.append(select);form.append(label);}
    if(mode==='reset'){
      const recovery=field(form,'账号恢复码','recovery');recovery.autocomplete='off';
      form.append(make('p','输入注册时保存的恢复码。重设密码后，其他设备会退出登录。','community-help'));
      if(emailEnabled){const code=field(form,'邮箱验证码','email_code','text',false);code.inputMode='numeric';code.pattern='[0-9]{6}';code.parentElement.hidden=true;const challenge=make('input');challenge.type='hidden';challenge.name='challenge';form.append(challenge);const send=action('改用绑定邮箱找回',async()=>{send.disabled=true;try{const d=await post('/api/account/email-request',{purpose:'reset',username:username.value});challenge.value=d.challenge;recovery.required=false;recovery.value='';recovery.parentElement.hidden=true;code.parentElement.hidden=false;code.required=true;status.textContent=d.message;send.textContent='重新发送验证码';}catch(e){status.textContent=e.message;}finally{send.disabled=false;}});form.append(send);}
    }
    const pass=field(form,mode==='reset'?'新密码':'密码','password','password');pass.minLength=10;pass.autocomplete=mode==='login'?'current-password':'new-password';
    const reveal=action('显示密码',()=>{pass.type=pass.type==='password'?'text':'password';reveal.textContent=pass.type==='password'?'显示密码':'隐藏密码';},'community-text-button');form.append(reveal);
    if(mode!=='login'){const confirm=field(form,'确认密码','confirm','password');confirm.minLength=10;confirm.autocomplete='new-password';}
    const submit=make('button',mode==='register'?'注册并登录':mode==='reset'?'保存新密码':'登录','primary');submit.type='submit';form.append(status,submit);
    form.onsubmit=async e=>{e.preventDefault();status.textContent='';const data=Object.fromEntries(new FormData(form));if(data.confirm!==undefined&&data.confirm!==data.password){status.textContent='两次输入的密码不一致。';return;}submit.disabled=true;try{const result=await post('/api/account/'+mode,data);if(result.recovery){open('请保存账号恢复码');dialog.append(make('p','忘记密码时，用此恢复码找回账号。请存入密码管理器，不要提供给其他人。'));const code=make('input');code.readOnly=true;code.value=result.recovery;code.setAttribute('aria-label','账号恢复码');dialog.append(code,action('复制恢复码',async()=>{try{await navigator.clipboard.writeText(result.recovery);code.select();}catch{code.select();}}),action('已保存，开始使用',()=>location.reload(),'primary'));dialog.oncancel=e=>e.preventDefault();dialog.querySelector('.community-close').hidden=true;}else location.reload();}catch(err){status.textContent=err.message;submit.disabled=false;}};
    dialog.append(form);
    const links=make('div',null,'community-links');links.append(action(mode==='register'?'已有账号？登录':'创建账号',()=>auth(mode==='register'?'login':'register')),action('忘记密码',()=>auth('reset')));dialog.append(links,make('p','可以继续以游客身份练习。注册后，学习记录与教师练习归属你的账号。','community-help'));
    username.focus();
  }
  function bindEmail(){open('绑定找回邮箱');const form=make('form'),email=field(form,'邮箱地址','email','email'),pass=field(form,'当前密码','password','password'),code=field(form,'验证码','email_code','text',false),status=make('p',null,'community-status');pass.autocomplete='current-password';code.inputMode='numeric';code.pattern='[0-9]{6}';let challenge='';const send=action('发送验证码',async()=>{send.disabled=true;try{const result=await post('/api/account/email-request',{purpose:'bind',email:email.value,password:pass.value});challenge=result.challenge;status.textContent=result.message;}catch(e){status.textContent=e.message;}finally{send.disabled=false;}});const verify=make('button','确认绑定','primary');verify.type='submit';form.append(send,status,verify);form.onsubmit=async e=>{e.preventDefault();verify.disabled=true;try{await post('/api/account/email-verify',{challenge,email_code:code.value});location.reload();}catch(e){status.textContent=e.message;verify.disabled=false;}};dialog.append(form);}
  function support(){
    open('反馈与联系');
    const form=make('form');const label=make('label','你遇到了什么？'),kind=make('select');kind.name='kind';kind.append(new Option('功能不好用 / 页面问题','bug'),new Option('题目或答案有误','question'),new Option('建议与其他反馈','experience'));label.append(kind);form.append(label);
    const comment=field(form,'具体问题或建议','comment','textarea');comment.rows=4;comment.placeholder='例如：哪道题、哪个操作出了问题？';
    const q=field(form,'题目编号（可选）','question_id','text',false);q.value=document.querySelector('[data-question-id]')?.dataset.questionId||'';q.parentElement.hidden=kind.value!=='question';kind.onchange=()=>q.parentElement.hidden=kind.value!=='question';
    const contact=field(form,'联系方式（可选）','contact','text',false);contact.placeholder='希望收到回复时，可留下邮箱或微信';
    form.append(make('p','提交时附带当前页面地址。请勿填写密码、身份证号等敏感信息。','community-help'));
    const status=make('p',null,'community-status');status.setAttribute('role','status');const submit=make('button','提交反馈','primary');submit.type='submit';form.append(status,submit);
    form.onsubmit=async e=>{e.preventDefault();submit.disabled=true;try{const data=Object.fromEntries(new FormData(form));data.page=location.pathname;const result=await post('/api/feedback',data);form.replaceChildren(make('h3','收到，谢谢你的帮助！'),make('p','反馈编号：'+result.id),make('p','如果留下联系方式，我们会在需要进一步了解时联系你。'));}catch(err){status.textContent=err.message;submit.disabled=false;}};
    const contacts=make('section',null,'community-contacts');contacts.append(make('h3','联系我们'));
    const email=make('a',contactInfo.email);email.href='mailto:'+contactInfo.email;contacts.append(email,make('p','微信：'+contactInfo.wechat),action('复制微信号',async()=>{try{await navigator.clipboard.writeText(contactInfo.wechat);}catch{}},'community-text-button'));
    dialog.append(form,contacts);comment.focus();
  }
  const nav=document.querySelector('header nav');
  if(nav){
    const teaching=['/teacher','/library','/bank'].includes(location.pathname);
    const links=[['学生练习','/practice'],['教师组卷','/teacher'],['浏览题库','/bank']];
    if(teaching)links.push(['我的练习','/library']);
    else if(['/practice','/exam'].includes(location.pathname))links.push(['模拟考试','/exam']);
    nav.replaceChildren();
    for(const [title,href] of links){const link=make('a',title,'nav-link');link.href=href;if(location.pathname===href){link.classList.add('active');link.setAttribute('aria-current','page');}nav.append(link);}
  }
  if(nav){nav.id='site-navigation';const toggle=action('菜单',()=>{const expanded=toggle.getAttribute('aria-expanded')!=='true';toggle.setAttribute('aria-expanded',String(expanded));nav.classList.toggle('mobile-open',expanded);},'mobile-menu-toggle');toggle.setAttribute('aria-controls',nav.id);toggle.setAttribute('aria-expanded','false');nav.before(toggle);}
  const accountButton=action('登录 / 注册',()=>auth(),'community-account');nav?.append(accountButton);
  ready.then(u=>{if(u){accountButton.textContent=u.username;accountButton.onclick=()=>{open('我的账号');if(emailEnabled)dialog.append(action(u.email?'更换找回邮箱':'绑定找回邮箱',bindEmail));dialog.append(make('p',`${u.username} · ${u.role==='teacher'?'教师':'学生'}`),make('p',u.email?'已绑定找回邮箱：'+u.email:'请妥善保存账号恢复码，用于忘记密码时找回账号。'),action('退出登录',async()=>{try{if(window.CSAAccount.flush)await window.CSAAccount.flush();await post('/api/account/logout',{});location.reload();}catch(err){dialog.append(make('p',err.message,'community-status'));}}));};}}).catch(()=>{accountButton.textContent='登录暂不可用';accountButton.disabled=true;});
  let footer=document.querySelector('footer');if(!footer){footer=make('footer');document.body.append(footer);}
  footer.textContent='CSA Studio · AP CSA 学习与教学';
  footer.append(action('反馈与联系',support,'community-text-button'),action('隐私说明',()=>{open('隐私说明');dialog.append(make('p','我们保存用户名、加密后的密码校验信息、学习记录和你主动提交的反馈，用于登录、跨设备学习和改进产品。游客记录保存在当前浏览器。'),make('p','Java 代码检查会把提交的代码发送至第三方运行服务。请勿在代码或反馈中包含个人敏感信息。'),make('p','如需删除账号或相关数据，请联系 15652805681@163.com，并提供账号归属证明。'),make('p','本网站为独立学习工具，与 College Board 无隶属关系。'));},'community-text-button'));
  document.addEventListener('click',event=>{const link=event.target.closest('a');if(!link||!link.querySelector('img'))return;const url=new URL(link.href,location.href);if(url.origin!==location.origin||!/^\/(source-image|scoring-page)\//.test(url.pathname))return;event.preventDefault();open('原题与评分指南');dialog.classList.add('image-reader');let width=100;const tools=make('div',null,'reader-tools'),viewport=make('div',null,'reader-viewport'),image=make('img');image.src=url.href;image.alt=link.querySelector('img').alt;const zoom=delta=>{width=Math.max(100,Math.min(300,width+delta));image.style.width=width+'%';};tools.append(action('放大',()=>zoom(25)),action('缩小',()=>zoom(-25)),action('适合窗口',()=>{width=100;zoom(0);}));viewport.append(image);dialog.append(tools,viewport);dialog.addEventListener('close',()=>dialog.classList.remove('image-reader'),{once:true});});
  const supportButton=action('反馈',support,'community-feedback');supportButton.setAttribute('aria-label','反馈问题或联系我们');document.body.append(supportButton);
})();
