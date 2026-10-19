/* Persistent learning history. Older pending records remain usable. */
(function(root){
  const count = value => Number.isFinite(Number(value)) ? Math.max(0,Number(value)) : 0;
  const isMistake = r => !!(r && (r.wasWrong || (r.done && !r.mastered)));
  function submit(previous, mastered, choice, now = new Date().toISOString()) {
    const old = previous || {};
    const result = {...old, done:true, mastered:!!mastered,
      wasWrong:isMistake(old) || !mastered,
      attempts:count(old.attempts)+1, lastAttempt:now};
    if (choice !== undefined) result.choice=choice;
    if (!mastered) {
      result.wrongCount=Math.max(count(old.wrongCount),isMistake(old)?1:0)+1;
      result.firstWrong=old.firstWrong||now;
      result.lastWrong=now;
      if (choice !== undefined) result.lastWrongChoice=choice;
    }
    return result;
  }
  const api={isMistake,submit};
  if(typeof module!=='undefined'&&module.exports)module.exports=api;
  else root.CSAProgress=api;
})(globalThis);
