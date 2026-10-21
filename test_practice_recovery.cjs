const {test}=require('node:test'),assert=require('node:assert/strict'),vm=require('node:vm'),fs=require('node:fs');
const source=fs.readFileSync('teacher_copilot/review_static/practice.js','utf8').split('function record(q)')[0];
function boot(post){
 const storage=new Map(),nodes={},element=()=>({inert:false,textContent:'',append(){},prepend(){},classList:{},remove(){}});
 const ctx={console,JSON,Promise,Error,Blob,URL,setTimeout:()=>1,clearTimeout(){},localStorage:{getItem:k=>storage.get(k)||null,setItem:(k,v)=>storage.set(k,v),removeItem:k=>storage.delete(k)},location:{search:'',reload(){}},URLSearchParams,document:{getElementById:id=>nodes[id]??=element(),createElement:element,querySelector:element,addEventListener(){}},window:{addEventListener(){}},CSAAccount:{post}};
 vm.createContext(ctx);vm.runInContext(source,ctx);vm.runInContext("accountUser={id:'a'};KEY='progress:a';progress={q:{draft:'first'}}",ctx);
 return {ctx,nodes,storage,run:s=>vm.runInContext(s,ctx)};
}
test('revision conflict retains local draft and stops subsequent writes',async()=>{
 let calls=0;const t=boot(async()=>{calls++;throw Object.assign(Error('conflict'),{status:409})});
 t.run('save()');const saved=t.storage.get('progress:a:pending');await t.run('syncProgress()');
 assert.equal(t.run('progressConflict'),true);assert.equal(t.nodes['practice-area'].inert,true);
 t.run("progress.q.draft='later';save()");await t.run('syncProgress()');assert.equal(calls,1);assert.equal(t.storage.get('progress:a:pending'),saved);
});
test('network failure preserves pending draft; retry clears it after success',async()=>{
 const t=boot(async()=>{throw Error('offline')});t.run('save()');await t.run('syncProgress()');assert.equal(t.run('progressConflict'),false);assert.ok(t.storage.get('progress:a:pending'));
 t.ctx.CSAAccount.post=async()=>({revision:1});await t.run('syncProgress()');assert.equal(t.storage.has('progress:a:pending'),false);assert.equal(t.run('progressRevision'),1);
});
test('edits during request are saved again using the new revision',async()=>{
 let finish;const calls=[];const t=boot(async(_,data)=>{calls.push(data);if(calls.length===1)return new Promise(r=>finish=r);return {revision:2}});
 const request=t.run('syncProgress()');t.run("progress.q.draft='second';save()");finish({revision:1});await request;await new Promise(setImmediate);
 assert.equal(calls.length,2);assert.equal(calls[1].revision,1);assert.equal(calls[1].data.q.draft,'second');assert.equal(t.storage.has('progress:a:pending'),false);
});
