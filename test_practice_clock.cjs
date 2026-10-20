const assert=require('node:assert/strict'),c=require('./teacher_copilot/review_static/practice-clock.js');
let s=c.restore(null);s=c.start(s,1000);assert.equal(c.elapsed(s,6000),5000);
const restored=c.restore(JSON.parse(JSON.stringify(s)));assert.equal(c.elapsed(restored,61000),60000);
s=c.pause(s,11000);assert.equal(c.elapsed(s,91000),10000);
s=c.start(s,91000);s=c.start(s,95000);assert.equal(c.elapsed(s,101000),20000);
s=c.pause(s,101000);assert.equal(c.format(c.elapsed(s,999999)), '00:20');
assert.equal(c.format(1350000),'22:30');assert.equal(c.restore({target:-2,startedAt:'x'}).startedAt,null);assert.equal(c.restore({target:999}).target,null);
console.log('Timer: start, pause, resume, reload and formatting passed');
