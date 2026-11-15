import fs from 'node:fs/promises';
import {chromium} from 'playwright';
const root='docs/imagesv2';
const m=JSON.parse(await fs.readFile(`${root}/manifest.json`,'utf8'));
m.captures=[...new Map(m.captures.map(r=>[`${r.device}:${r.pageName}:${r.state}`,r])).values()];
// The implemented compare route redirects to result. Preserve route coverage
// when identical screenshots are represented by a shared PNG.
for(const device of ['desktop','mobile']) {
 if(!m.captures.some(r=>r.pageName==='/cases/[caseId]/compare'&&r.device===device&&r.success)) {
  const result=m.captures.find(r=>r.pageName==='/cases/[caseId]/result'&&r.device===device&&r.state==='default'&&r.success);
  if(result)m.captures.push({...result,pageName:'/cases/[caseId]/compare',duplicateOf:result.imagePath,description:'Implemented redirect to result; identical PNG shared.'});
 }
}
const browser=await chromium.launch();
const page=await browser.newPage();
for(const r of m.captures.filter(r=>r.success)) {
 const bytes=await fs.readFile(`${root}/${r.imagePath}`);
 const result=await page.evaluate(async data=>{
  const img=new Image();img.src=data;await img.decode();
  const canvas=document.createElement('canvas');canvas.width=64;canvas.height=64;
  const ctx=canvas.getContext('2d');ctx.drawImage(img,0,0,64,64);
  const pixels=ctx.getImageData(0,0,64,64).data;const colors=new Set();
  for(let i=0;i<pixels.length;i+=4)colors.add(`${pixels[i]},${pixels[i+1]},${pixels[i+2]}`);
  return {width:img.naturalWidth,height:img.naturalHeight,colors:colors.size};
 },`data:image/png;base64,${bytes.toString('base64')}`);
 r.pngValidation=result;
 if(result.colors<8){r.success=false;r.failureReason='PNG appears blank (fewer than eight sampled colors)';}
}
await browser.close();
m.browser='Chromium';
m.summary={total:m.captures.length,success:m.captures.filter(r=>r.success).length,failed:m.captures.filter(r=>!r.success).length,uniquePngs:new Set(m.captures.filter(r=>r.success).map(r=>r.imagePath)).size};
m.routeCoverage=m.routes.map(route=>({route,desktop:m.captures.some(r=>r.pageName===route&&r.device==='desktop'&&r.success),mobile:m.captures.some(r=>r.pageName===route&&r.device==='mobile'&&r.success)}));
m.limitations=['개발용 MSW 가상 데이터만 사용. 실제 백엔드는 실행·접속하지 않음.','네이티브 select 팝업은 브라우저 PNG에 포함되지 않을 수 있음.','데이터 조합 및 모든 서버 오류·로딩 변형을 전수 검증하지 않음.','실제 모바일 기기 및 Edge 별도 해상도 검증은 수행하지 않음. 요청한 Chromium 1440×900 / 390×844 캡처.','fullPage는 문서 전체를 포함하며 내부 스크롤 패널은 실제 UI의 스크롤 구조를 유지.'];
await fs.writeFile(`${root}/manifest.json`,JSON.stringify(m,null,2));
await fs.writeFile(`${root}/README.md`,`# 월급잇다 UI/UX 아카이브 v2\n\n총 ${m.summary.total}개 대상: 성공 ${m.summary.success}, 실패 ${m.summary.failed}. 중복 제외 PNG ${m.summary.uniquePngs}개.\n\n## 재실행\n\n\`npm ci\`, \`npx playwright install chromium\`, \`npm run screenshots\`. 기존 Mock 서버 사용 시 PowerShell에서 \`$env:ARCHIVE_URL='http://localhost:3100'\` 설정. PNG와 manifest는 갱신되며 docs/images는 수정하지 않습니다.\n\n## 완료 조건 및 조사\n\n- [x] src/app/page.tsx 라우트 자동 탐색: ${m.routes.length}개\n- [x] 양쪽 viewport에서 실제 브라우저 실행\n- [x] 성공 PNG 디코딩, 크기 및 비어 있는 이미지 검사\n- [x] 탭·상세·메뉴·단계·검증·빈 계정·채팅 흐름 탐색\n- [ ] 모든 가능한 UI 상태 조합 전수 검증\n\n## 라우트 조사 결과\n\n| 라우트 | Desktop | Mobile |\n|---|---|---|\n${m.routeCoverage.map(r=>`| ${r.route} | ${r.desktop?'성공':'누락'} | ${r.mobile?'성공':'누락'} |`).join('\n')}\n\n## 실패 및 미검증\n\n${m.captures.filter(r=>!r.success).map(r=>`- ${r.device} ${r.pageName} ${r.state}: ${r.failureReason}`).join('\n')||'캡처 실행 실패 없음.'}\n\n${m.limitations.map(x=>'- '+x).join('\n')}\n\n## 화면 목록\n\n${m.captures.map(r=>`### ${r.device} / ${r.pageName} / ${r.state}\n\n${r.state} UI 상태. 실제 URL: ${r.url}\n\n${r.success?`![${r.pageName} ${r.state}](${r.imagePath})`:`실패: ${r.failureReason}`}\n`).join('\n')}`);
console.log(m.summary);
