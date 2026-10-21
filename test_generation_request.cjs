const {test}=require('node:test'),assert=require('node:assert/strict'),vm=require('node:vm'),fs=require('node:fs');
const text=fs.readFileSync('teacher_copilot/review_static/app.js','utf8');
const source=text.slice(text.indexOf('async function request('),text.indexOf('async function history('));
test('stalled generation times out and clears timer',async()=>{
 let expire,cleared=false;const ctx={AbortController,Error,JSON,token:'test',state:null,crypto:{randomUUID:()=> 'test-id'},CSAAccount:{ready:Promise.resolve(null)},setTimeout:fn=>{expire=fn;return 1},clearTimeout:()=>cleared=true,fetch:async(_,options)=>new Promise((_,reject)=>options.signal.addEventListener('abort',()=>reject(Object.assign(Error('abort'),{name:'AbortError'}))))};
 vm.createContext(ctx);vm.runInContext(source,ctx);const request=vm.runInContext("request({action:'generate'})",ctx);await new Promise(setImmediate);expire();await assert.rejects(request,/30 秒/);assert.equal(cleared,true);
});
test('successful generation clears timeout and sends PDF source',async()=>{
 let cleared=false,body;const ctx={AbortController,Error,JSON,token:'test',state:null,crypto:{randomUUID:()=> 'test-id'},CSAAccount:{ready:Promise.resolve({id:'a'})},setTimeout:()=>1,clearTimeout:()=>cleared=true,fetch:async(_,options)=>{body=JSON.parse(options.body);return {ok:true,json:async()=>({run:'saved'})}}};
 vm.createContext(ctx);vm.runInContext(source,ctx);const result=await vm.runInContext("request({action:'generate',source:'local'})",ctx);assert.equal(result.run,'saved');assert.equal(body.source,'local');assert.equal(cleared,true);
});
