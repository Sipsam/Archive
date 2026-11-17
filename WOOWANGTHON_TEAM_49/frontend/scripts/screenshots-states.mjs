// Run after screenshots-capture.mjs; supplements the archive using real UI interactions.
import {chromium} from 'playwright';
import fs from 'node:fs/promises';
import path from 'node:path';
const base=process.env.ARCHIVE_URL||'http://localhost:3100';
const root='docs/imagesv2';
const manifest=JSON.parse(await fs.readFile(`${root}/manifest.json`,'utf8'));
const browser=await chromium.launch({args:['--no-proxy-server']});
for(const [device,viewport] of Object.entries({desktop:{width:1440,height:900},mobile:{width:390,height:844}})){
 const c=await browser.newContext({viewport,locale:'ko-KR',reducedMotion:'reduce'});
 await c.route('**/*',r=>new URL(r.request().url()).origin===base?r.continue():r.abort());
 const p=await c.newPage();p.setDefaultTimeout(8000);
 let navigationError; const go=async url=>{navigationError=undefined;try{await p.goto(base+url,{waitUntil:'domcontentloaded'});await p.getByText('샘플 데이터 초기화',{exact:true}).waitFor();await p.waitForLoadState('networkidle',{timeout:15000}).catch(()=>{});if(url==='/cases/99999')await p.locator('main [role=alert]').first().waitFor();else await p.locator('main h1').first().waitFor();}catch(e){navigationError=e;}};
 const shot=async(name,state,action)=>{
  const imagePath=`${device}/${name}/${state}.png`;const rec={pageName:name,url:p.url(),device,state,imagePath,success:false};
  try{if(navigationError)throw navigationError;if(action)await action();if(!['streaming','processing'].includes(state))await p.waitForLoadState('networkidle',{timeout:10000}).catch(()=>{});await p.evaluate(()=>document.fonts.ready);await p.addStyleTag({content:'*,*::before,*::after{animation:none!important;transition:none!important;caret-color:transparent!important} nextjs-portal{display:none!important}'});await fs.mkdir(path.dirname(`${root}/${imagePath}`),{recursive:true});await p.screenshot({path:`${root}/${imagePath}`,fullPage:true,animations:'disabled'});rec.success=true;rec.url=p.url();}catch(e){rec.failureReason=e.message;}manifest.captures=manifest.captures.filter(r=>!(r.device===device&&r.imagePath===imagePath));manifest.captures.push(rec);console.log(device,name,state,rec.success);
 };
 await go('/signup');
 await shot('signup','success',async()=>{await p.locator('input[name="name"]').fill('가상 기록');await p.locator('input[type=email]').fill('archive@example.com');await p.locator('input[type=password]').fill('password1234');await p.locator('button[type=submit]').click();await p.waitForURL('**/login*');});
 await shot('login','mock-empty-account',async()=>{await p.locator('input[type=email]').fill('archive@example.com');await p.locator('input[type=password]').fill('password1234');await p.locator('button[type=submit]').click();await p.waitForURL('**/dashboard');});
 for(const url of ['/cases','/library','/workplaces'])await shot(url.slice(1),'empty',async()=>{
  if(url==='/workplaces') {
   if(device==='mobile'&&!await p.locator('a[href="/workplaces/new"]:visible').count())await p.locator('button[aria-haspopup="dialog"]:visible').first().click();
   await p.locator('a[href="/workplaces/new"]:visible').first().click();await p.waitForURL('**/workplaces/new');
   await p.locator('a[href="/workplaces"]:visible').first().click();
  }else {
   const link=p.locator(`a[href="${url}"]`).first();
   // Invoke the existing Next Link handler to retain the in-memory empty fixture.
   // Mobile can hide the same shortcut; no routes or DTOs are injected.
   await link.evaluate(el=>el.click());
  }
  await p.waitForURL('**'+url);
 });
 await c.addCookies([{name:'wageitda_mock_session',value:'worker%40example.com',url:base}]);
 await go('/cases/99999');await shot('cases/case-detail','not-found');
 await go('/cases/15/conditions');
 await shot('cases/case-detail/conditions','question',async()=>{await p.getByRole('button',{name:'조건 확인하기',exact:true}).click();});
 await shot('cases/case-detail/conditions','answer-review',async()=>{await p.getByRole('button',{name:/답변 검토|답변 확인/}).last().click();});
 await go('/workplaces/3/chats');
 await shot('workplaces/workplace-detail/chats/chat-detail','created',async()=>{await p.locator('main select').first().selectOption({index:1});await p.locator('input[maxlength="200"]').first().fill('가상 급여 기록 질문');await p.getByRole('button',{name:'대화 시작',exact:true}).click();await p.waitForURL('**/chats/*');});
 await shot('workplaces/workplace-detail/chats/chat-detail','conversation-input',async()=>{await p.locator('#chat-question').fill('급여명세서에서 확인할 항목을 알려주세요.');});
 await shot('workplaces/workplace-detail/chats/chat-detail','streaming',async()=>{await p.getByRole('button',{name:'전송',exact:true}).click();await p.getByRole('button',{name:'답변 중지',exact:true}).waitFor();});
 await shot('workplaces/workplace-detail/chats/chat-detail','response-complete',async()=>{await p.getByRole('button',{name:'답변 중지',exact:true}).waitFor({state:'hidden',timeout:30000});await p.locator('.v2-chat-bubble').last().waitFor();});
 await go('/forgot-password');
 await shot('forgot-password','success',async()=>{await p.locator('input[type=email]').fill('worker@example.com');await p.locator('form button').click();});
 await go('/cases/15/reports');
 await shot('cases/case-detail/reports','selected-documents',async()=>{for(const checkbox of await p.locator('main input[type=checkbox]').all())await checkbox.check();});
 await shot('cases/case-detail/reports','processing',async()=>{await p.getByRole('button',{name:'보고서 생성 요청',exact:true}).click();await p.getByText('현재 생성 요청',{exact:true}).waitFor();});
 await shot('cases/case-detail/reports','generated',async()=>{await p.getByRole('button',{name:'PDF 다운로드',exact:true}).waitFor({timeout:30000});});
 await go('/cases/15/upload');
 await shot('cases/case-detail/upload','invalid-file',async()=>{await p.locator('input[type=file]').first().setInputFiles({name:'invalid.txt',mimeType:'text/plain',buffer:Buffer.from('Synthetic invalid file')});await p.locator('main [role=alert]').first().waitFor();});
 await shot('cases/case-detail/upload','file-selected',async()=>{await p.locator('input[type=file]').first().setInputFiles({name:'archive-sample.png',mimeType:'image/png',buffer:Buffer.from('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+aD1sAAAAASUVORK5CYII=','base64')});});
 await shot('cases/case-detail/upload','upload-success',async()=>{await p.locator('input[type=file]').first().locator('xpath=ancestor::form').locator('button[type=submit]').click();await p.getByText(/업로드.*목록.*처리 상태/).first().waitFor({timeout:15000});});
 for(const route of ['/workplaces/new','/cases/new']) {
  await go(route==='/cases/new'?'/cases/new?workplaceId=3':route);
  await shot(route.slice(1),'validation-error',async()=>{await p.locator('main button[type=submit]').first().click();await p.locator('main [aria-invalid=true], main [role=alert]').first().waitFor();});
 }
 await go('/cases/15/manual-records');
 const steps=p.locator('[data-ui="common-stepFormNavigation_ariaLabel_nav"] ol button');
 for(let i=0;i<await steps.count();i++)await shot('cases/case-detail/manual-records',`form-step-${i+1}`,()=>steps.nth(i).click());
 await c.close();
}
await browser.close();
manifest.recoveredFailures??=[];
for(const device of ['desktop','mobile']) {
 if(manifest.captures.some(r=>r.device===device&&r.state==='created'&&r.success)) {
  manifest.recoveredFailures.push(...manifest.captures.filter(r=>r.device===device&&r.pageName.includes('[chatId]')&&!r.success));
  manifest.captures=manifest.captures.filter(r=>!(r.device===device&&r.pageName.includes('[chatId]')&&!r.success));
 }
}
await fs.writeFile(`${root}/manifest.json`,JSON.stringify(manifest,null,2));
await fs.appendFile(`${root}/README.md`,'\n# Supplementary states\n\n'+manifest.captures.filter(r=>['success','empty','not-found','question','answer-review','created','mock-empty-account'].includes(r.state)).map(r=>`## ${r.device} · ${r.pageName} · ${r.state}\n\n${r.success?`![${r.state}](${r.imagePath})`:`Failed: ${r.failureReason}`}\n`).join('\n'));
