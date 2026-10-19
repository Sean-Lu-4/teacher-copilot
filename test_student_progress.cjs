const test=require('node:test');
const assert=require('node:assert/strict');
const {submit,isMistake}=require('./teacher_copilot/review_static/progress.js');
test('incorrect MCQ is retained after successful review',()=>{
 const wrong=submit({},false,'A','2026-10-19T01:00:00Z');
 assert.equal(wrong.wrongCount,1);assert.equal(isMistake(wrong),true);
 const correct=submit({...wrong,note:'Check integer division'},true,'B');
 assert.equal(correct.mastered,true);assert.equal(isMistake(correct),true);
 assert.equal(correct.lastWrongChoice,'A');assert.equal(correct.choice,'B');
 assert.equal(correct.note,'Check integer division');assert.equal(correct.attempts,2);
 const relapse=submit(correct,false,'C');assert.equal(relapse.mastered,false);
 assert.equal(relapse.wrongCount,2);assert.equal(relapse.firstWrong,wrong.firstWrong);
});
test('old pending records migrate without inventing old correct history',()=>{
 assert.equal(isMistake({done:true,mastered:false}),true);
 assert.equal(isMistake({done:true,mastered:true}),false);
 assert.equal(isMistake(submit({done:true,mastered:false,attempts:2},true,'D')),true);
});
test('correct first attempt never enters notebook',()=>{
 assert.equal(isMistake(submit({},true,'B')),false);
});
test('FRQ self assessment retains code and note',()=>{
 const r=submit({draft:'return max;',note:'Check negatives'},false);
 assert.equal(r.draft,'return max;');assert.equal(r.note,'Check negatives');
 assert.equal(r.choice,undefined);assert.equal(isMistake(r),true);
 assert.equal(submit(r,true).mastered,true);
});
test('submission does not mutate the stored record',()=>{
 const old=Object.freeze({done:true,mastered:false,note:'keep',attempts:1});
 submit(old,true,'A');assert.equal(old.mastered,false);
});
