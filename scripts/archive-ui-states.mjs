// Run after archive-ui.mjs; supplements the archive using real UI interactions.
import {chromium} from 'playwright';
import fs from 'node:fs/promises';
import path from 'node:path';
const base=process.env.ARCHIVE_URL||'http://localhost:3100';
const root='docs/images';
const manifest=JSON.parse(await fs.readFile(`${root}/manifest.json`,'utf8'));
const browser=await chromium.launch({channel:'msedge',args:['--no-proxy-server']});
for(const [device,viewport] of Object.entries({desktop:{width:1440,height:900},mobile:{width:390,height:844}})){
 const c=await browser.newContext({viewport,locale:'ko-KR',reducedMotion:'reduce'});
 await c.route('**/*',r=>new URL(r.request().url()).origin===base?r.continue():r.abort());
 const p=await c.newPage();p.setDefaultTimeout(8000);
 const go=async url=>{await p.goto(base+url,{waitUntil:'domcontentloaded'});await p.getByText('샘플 데이터 초기화',{exact:true}).waitFor();await p.waitForTimeout(1200);};
 const shot=async(name,state,action)=>{
  const imagePath=`${device}/${name}/${state}.png`;const rec={pageName:name,url:p.url(),device,state,imagePath,success:false};
  try{if(action)await action();await p.waitForTimeout(700);await p.evaluate(()=>document.fonts.ready);await p.addStyleTag({content:'*,*::before,*::after{animation:none!important;transition:none!important;caret-color:transparent!important}'});await fs.mkdir(path.dirname(`${root}/${imagePath}`),{recursive:true});await p.screenshot({path:`${root}/${imagePath}`,fullPage:true,animations:'disabled'});rec.success=true;rec.url=p.url();}catch(e){rec.failureReason=e.message;}manifest.captures=manifest.captures.filter(r=>!(r.device===device&&r.imagePath===imagePath));manifest.captures.push(rec);console.log(device,name,state,rec.success);
 };
 await go('/signup');
 await shot('signup','success',async()=>{await p.locator('input[name="name"]').fill('가상 기록');await p.locator('input[type=email]').fill('archive@example.com');await p.locator('input[type=password]').fill('password1234');await p.locator('button[type=submit]').click();await p.waitForURL('**/login*');});
 await shot('login','mock-empty-account',async()=>{await p.locator('input[type=email]').fill('archive@example.com');await p.locator('input[type=password]').fill('password1234');await p.locator('button[type=submit]').click();await p.waitForURL('**/dashboard');});
 for(const url of ['/cases','/workplaces','/library'])await shot(url.slice(1),'empty',async()=>{if(!await p.locator(`a[href="${url}"]:visible`).count()&&device==='mobile')await p.locator('button[aria-haspopup="dialog"]:visible').first().click();const link=p.locator(`a[href="${url}"]:visible`).first();await link.click();await p.waitForURL('**'+url);});
 await c.addCookies([{name:'wageitda_mock_session',value:'worker%40example.com',url:base}]);
 await go('/cases/99999');await shot('cases/case-detail','not-found');
 await go('/cases/15/conditions');
 await shot('cases/case-detail/conditions','question',async()=>{await p.getByRole('button',{name:'조건 확인하기',exact:true}).click();});
 await shot('cases/case-detail/conditions','answer-review',async()=>{await p.getByRole('button',{name:/답변 검토|답변 확인/}).last().click();});
 await go('/workplaces/3/chats');
 await shot('workplaces/workplace-detail/chats/chat-detail','created',async()=>{await p.locator('main select').first().selectOption({index:1});await p.locator('input[maxlength="200"]').first().fill('가상 급여 기록 질문');await p.getByRole('button',{name:'대화 시작',exact:true}).click();await p.waitForURL('**/chats/*');});
 await go('/forgot-password');
 await shot('forgot-password','success',async()=>{await p.locator('input[type=email]').fill('worker@example.com');await p.locator('form button').click();});
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
