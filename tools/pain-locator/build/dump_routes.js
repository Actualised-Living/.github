const { chromium } = require('/opt/node22/lib/node_modules/playwright');
const fs = require('fs');
(async () => {
  const b = await chromium.launch({ args:['--use-gl=swiftshader','--enable-unsafe-swiftshader','--no-sandbox'] });
  const pg = await b.newPage({ viewport:{width:900,height:700} });
  pg.on('pageerror',e=>console.log('[err]',String(e)));
  await pg.goto('http://127.0.0.1:8741/index.html');
  await pg.waitForFunction(() => window.__t && window.__t.ANAT.loaded, null, {timeout:240000});
  const out = await pg.evaluate(() => {
    const T=window.__t, res={};
    for (const name in T.NERVE_ROUTES) {
      res[name]={};
      [[1,'left'],[-1,'right']].forEach(([sd,lbl])=>{
        res[name][lbl]=T.NERVE_ROUTES[name].map(([m,pick,off,grp])=>{
          const p=T.resolveAnchor(m,pick,off,sd,grp);
          return p?{m:m,p:[+p.x.toFixed(4),+p.y.toFixed(4),+p.z.toFixed(4)]}:{m:m,p:null};
        });
      });
    }
    return res;
  });
  fs.writeFileSync(__dirname+'/routes.json', JSON.stringify(out,null,1));
  console.log('dumped routes for', Object.keys(out).join(', '));
  await b.close();
})();
