const { chromium } = require('playwright');
(async()=>{
  const path='file://'+process.cwd()+'/ClinicalTrialFinder_NSCLC_MVP.html';
  const b=await chromium.launch({executablePath:'/opt/pw-browsers/chromium'});
  const pg=await b.newPage({viewport:{width:1300,height:950}});
  const errs=[]; pg.on('pageerror',e=>errs.push(e.message));
  await pg.goto(path); await pg.waitForTimeout(300);
  async function loadCase(idx){
    const c=(await pg.$$('.case'))[idx]; await c.click(); await pg.waitForTimeout(150);
    return await pg.evaluate(()=>{
      const summ=[...document.querySelectorAll('.summary')].map(s=>s.textContent).find(t=>t.includes('candidate trials'))||'';
      const met=[...document.querySelectorAll('.rank-g')].map(e=>e.textContent);
      const nTrials=document.querySelectorAll('.trial').length;
      const nStaleBadges=document.querySelectorAll('.trial .dim[title]').length;
      const firstBio=document.querySelector('.trial .bio .row');
      return {summ:summ.slice(0,180),nTrials,nStaleBadges,firstBio:firstBio?firstBio.innerText.replace(/\n/g,' ').slice(0,130):'(none)'};
    });
  }
  for(const [idx,name] of [[0,'P01 EGFR alt'],[6,'P07 MET ex14'],[3,'P04 driver-neg']]){
    console.log('\n=== '+name+' (hide-stale ON) ===', JSON.stringify(await loadCase(idx)));
  }
  // toggle stale off, re-run P01
  await pg.uncheck('#hideStale'); await pg.waitForTimeout(200);
  const withStale=await pg.evaluate(()=>({n:document.querySelectorAll('.trial').length,
     summ:[...document.querySelectorAll('.summary')].map(s=>s.textContent).find(t=>t.includes('candidate'))?.slice(0,150)}));
  console.log('\n=== P04 with stale INCLUDED ===', JSON.stringify(withStale));
  console.log('\nerrors:', errs);
  await pg.check('#hideStale'); await (await pg.$$('.case'))[0].click(); await pg.waitForTimeout(200);
  await pg.screenshot({path:'tool_v2.png'});
  await b.close();
})();
