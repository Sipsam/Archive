/** Run against `NEXT_PUBLIC_MOCK_API=true NEXT_PUBLIC_API_BASE_URL=http://localhost:3100/api/v1 npm run dev -- --port 3100`.
 * Requires Playwright (npm install --no-save --package-lock=false playwright). Uses installed Edge.
 */
import { chromium } from 'playwright';
import fs from 'node:fs/promises';
import path from 'node:path';
const base = process.env.ARCHIVE_URL || 'http://localhost:3100';
const out = path.resolve('docs/images');
await fs.mkdir(out, {recursive:true});
const records=[];
const routes=[];
async function discover(dir, parts=[]) {
 for(const e of await fs.readdir(dir,{withFileTypes:true})) {
  if(e.isDirectory()) await discover(path.join(dir,e.name), [...parts,e.name]);
  else if(e.name==='page.tsx') routes.push('/'+parts.filter(p=>!p.startsWith('(')).join('/'));
 }
}
await discover('src/app');
const browser=await chromium.launch({channel:'msedge',args:['--no-proxy-server']});
async function persist(){
 await fs.writeFile(path.join(out,'manifest.json'),JSON.stringify({generatedAt:new Date().toISOString(),base, routes, captures:records},null,2));
 const ok=records.filter(r=>r.success).length;
 await fs.writeFile(path.join(out,'README.md'),`# UI/UX screenshot archive\n\nDevelopment MSW synthetic fixtures only. Edge, fullPage PNG, desktop 1440×900 / mobile 390×844.\n\n${records.length} captures: ${ok} succeeded, ${records.length-ok} failed.\n\nRun: start the mock dev server as described in scripts/archive-ui.mjs, then node scripts/archive-ui.mjs. Existing named captures are overwritten.\n\nCoverage: all page.tsx routes discovered automatically; visible tabs, details, step navigation and safe dialog/edit triggers explored. Native select popups cannot reliably appear in browser PNGs. Exhaustive combinations, real backend behavior and physical mobile devices are not verified. Loading captures intentionally freeze a real pending API request; no DTOs are synthesized. Failed entries and browser errors are retained in manifest.json.\n\n`+records.map(r=>`## ${r.device} · ${r.pageName} · ${r.state}\n\nURL: ${r.url}\n\n${r.success?`[PNG](${r.imagePath})\n\n![${r.state}](${r.imagePath})`:`Failed: ${r.failureReason}`}\n`).join('\n'));
}
for(const [device,viewport] of Object.entries({desktop:{width:1440,height:900},mobile:{width:390,height:844}})) {
 const context=await browser.newContext({viewport,locale:'ko-KR',reducedMotion:'reduce'});
 // Block external traffic, including any accidental real API fallback.
 await context.route('**/*',r=>new URL(r.request().url()).origin===base?r.continue():r.abort());
 const page=await context.newPage(); page.setDefaultTimeout(3500);
 let errors=[];page.on('pageerror',e=>errors.push(e.message));
 page.on('dialog',d=>d.dismiss());
 async function settle(){await page.waitForTimeout(650);await page.evaluate(()=>document.fonts.ready);await page.addStyleTag({content:'*,*::before,*::after{animation:none!important;transition:none!important;caret-color:transparent!important}'});}
 async function shot(route,state,action){
  const folder=route.replaceAll('[caseId]','case-detail').replaceAll('[workplaceId]','workplace-detail').replaceAll('[chatId]','chat-detail').replace(/^\//,'')||'landing';
  const imagePath=`${device}/${folder}/${state}.png`;const record={pageName:route,url:page.url(),state,device,imagePath,success:false};
  try{if(action)await action();await settle();record.url=page.url();await fs.mkdir(path.dirname(path.join(out,imagePath)),{recursive:true});await page.screenshot({path:path.join(out,imagePath),fullPage:true,animations:'disabled',timeout:20000});record.success=true;record.horizontalOverflow=await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth);record.browserErrors=[...errors];}
  catch(e){record.failureReason=e.message;}records.push(record);console.log(device,route,state,record.success?'OK':'FAIL');await persist();
 }
 async function go(url){errors=[];await page.goto(base+url,{waitUntil:'domcontentloaded',timeout:60000});await settle();await page.getByText('샘플 데이터 초기화',{exact:true}).waitFor({timeout:15000});await settle();}
 // Marker is explicitly an inert development cookie, not a credential.
 await context.addCookies([{name:'wageitda_mock_session',value:'worker%40example.com',url:base}]);
 for(const route of routes.sort((a,b)=>a.includes('[chatId]')-b.includes('[chatId]'))) {
  const publicRoute=['/','/login','/signup','/forgot-password','/reset-password','/account-deletion'].includes(route);
  await context.clearCookies();
  if(!publicRoute)await context.addCookies([{name:'wageitda_mock_session',value:'worker%40example.com',url:base}]);
  let url=route.replace('[caseId]','15').replace('[workplaceId]','3').replace('[chatId]','101');
  try {
   if(route.includes('[chatId]')){
    await go('/workplaces/3/chats');
    const selects=page.locator('main select');if(await selects.count())await selects.first().selectOption({index:1});
    await page.locator('input[maxlength="200"]').first().fill('Mock screenshot chat');
    await page.getByRole('button',{name:'대화 시작',exact:true}).click();await settle();url=new URL(page.url()).pathname;
   }
   if(!route.includes('[chatId]'))await go(url);
   if(!publicRoute&&new URL(page.url()).pathname==='/login')throw new Error('Mock authentication redirected to login');
   await shot(route,'default');
   const selectors=['[role="tab"]','summary','[data-ui="common-stepFormNavigation_ariaLabel_nav"] ol button'];
   for(const selector of selectors){
    const count=await page.locator(selector).count();
    for(let i=0;i<count;i++){
     const item=page.locator(selector).nth(i);if(!await item.isVisible()||!await item.isEnabled())continue;
     if(await item.getAttribute('aria-selected')==='true'||await item.getAttribute('aria-current')==='step')continue;
     await shot(route,`${selector==='summary'?'expanded':selector.includes('tab')?'tab':'step'}-${i+1}`,async()=>{await item.click();});
     if(selector==='summary')await item.click().catch(()=>{});
    }
   }
   const buttons=page.locator('button');
   const triggers=[];
   for(let i=0;i<await buttons.count();i++) {const b=buttons.nth(i);const label=(await b.getAttribute('aria-label'))||await b.innerText();if(await b.isVisible()&&await b.isEnabled()&&(/수정|삭제|언어|메뉴.*열기|기록 도우미/.test(label))&&!/확인|초기화|로그아웃/.test(label))triggers.push({i,label});}
   for(const {i} of triggers){await shot(route,`action-${i+1}`,async()=>{await buttons.nth(i).click();});await page.keyboard.press('Escape');await go(url);}
   if(publicRoute&&await page.locator('form button[type="submit"]').count())await shot(route,'validation-error',()=>page.locator('form button[type="submit"]').first().click());
  }catch(e){records.push({pageName:route,url:base+url,state:'default',device,imagePath:null,success:false,failureReason:e.message});await persist();}
 }
 await context.close();
}
await browser.close();await persist();
console.log(JSON.stringify({total:records.length,success:records.filter(r=>r.success).length,failed:records.filter(r=>!r.success).length}));
