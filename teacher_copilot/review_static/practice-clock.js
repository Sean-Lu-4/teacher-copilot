(function(root){
 'use strict';
 const elapsed=(s,now)=>Math.max(0,Number(s.accumulated)||0)+(s.startedAt!==null?Math.max(0,now-s.startedAt):0);
 const api={
 restore(s){return {accumulated:Math.max(0,Number(s?.accumulated)||0),startedAt:Number.isFinite(s?.startedAt)?s.startedAt:null,target:Number.isFinite(s?.target)&&s.target>=1&&s.target<=180?s.target:null};},
 elapsed,
 start(s,now){return {...s,startedAt:s.startedAt===null?now:s.startedAt};},
 pause(s,now){return {...s,accumulated:elapsed(s,now),startedAt:null};},
 format(ms){const secs=Math.floor(ms/1000);return String(Math.floor(secs/60)).padStart(2,'0')+':'+String(secs%60).padStart(2,'0');}
 };
 if(typeof module!=='undefined'&&module.exports)module.exports=api;else root.PracticeClock=api;
})(typeof window==='undefined'?globalThis:window);
