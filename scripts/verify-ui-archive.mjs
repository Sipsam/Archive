import fs from 'node:fs/promises';
import {chromium} from 'playwright';
import {createHash} from 'node:crypto';
const root='docs/images';
const m=JSON.parse(await fs.readFile(`${root}/manifest.json`,'utf8'));
const browser=await chromium.launch({channel:'msedge',args:['--no-proxy-server']});
const p=await browser.newPage();const hashes=new Map();let removedDuplicates=0;
for(const r of m.captures.filter(r=>r.success)){
 try{
  const bytes=await fs.readFile(`${root}/${r.imagePath}`);
  const decoded=await p.evaluate(async data=>{const img=new Image();img.src=data;await img.decode();return {width:img.naturalWidth,height:img.naturalHeight};},`data:image/png;base64,${bytes.toString('base64')}`);
  if(decoded.width!==(r.device==='desktop'?1440:390)||!decoded.height)throw new Error(`Unexpected PNG size ${JSON.stringify(decoded)}`);
  r.pngValidation=decoded;
  const hash=createHash('sha256').update(bytes).digest('hex');
  if(hashes.has(hash)&&hashes.get(hash)!==r.imagePath){const old=r.imagePath;r.imagePath=hashes.get(hash);r.duplicateOf=r.imagePath;await fs.unlink(`${root}/${old}`);removedDuplicates++;}else hashes.set(hash,r.imagePath);
 }catch(e){r.success=false;r.failureReason=`PNG validation: ${e.message}`;}
}
await browser.close();
const success=m.captures.filter(r=>r.success).length;
m.summary={total:m.captures.length,success,failed:m.captures.length-success,uniquePngs:new Set(m.captures.filter(r=>r.success).map(r=>r.imagePath)).size,removedDuplicates};
m.limitations=['MSW synthetic data only; no live backend access.','Native OS select menus, browser tooltips and every possible data permutation are not covered.','Transient loading and all server error variants are not exhaustively captured.','Physical mobile device, 320/375/768/1280 widths and comprehensive keyboard navigation were not verified; this archive uses the requested 1440/390 widths.','Inner scroll panes retain the actual application layout; fullPage captures the document height.'];
await fs.writeFile(`${root}/manifest.json`,JSON.stringify(m,null,2));
const states={default:'페이지 기본 화면',empty:'새 Mock 계정의 데이터 없음',success:'폼 처리 성공',question:'근무 조건 질문',created:'가상 대화 생성', 'validation-error':'필수 입력값 검증 오류','not-found':'존재하지 않는 가상 사건 오류'};
const text=`# 월급잇다 UI/UX 스크린샷\n\n${m.summary.total}회 캡처: 성공 ${success}, 실패 ${m.summary.failed}, 중복 제외 PNG ${m.summary.uniquePngs}개. 모든 성공 이미지는 Edge Image.decode()로 PNG 해상도 및 디코딩 검증.\n\nNext.js 16.4.5 App Router, src/app/page.tsx 파일 기반 라우트 ${m.routes.length}개 조사. 동적 ID는 개발용 근무지 3 / 사건 15 및 UI로 생성한 채팅 사용. 인증은 기존 inert Mock session marker 사용.\n\n## 재실행\n\nPowerShell:\n\n\`\`\`powershell\n$env:NEXT_PUBLIC_MOCK_API='true'\n$env:NEXT_PUBLIC_API_BASE_URL='http://localhost:3100/api/v1'\nnpm run dev -- --port 3100\n# 별도 터미널\nnode scripts/archive-ui.mjs\nnode scripts/archive-ui-states.mjs\nnode scripts/verify-ui-archive.mjs\n\`\`\`\n\nPlaywright와 설치된 Microsoft Edge 필요. Playwright가 없다면 npm install --no-save --package-lock=false playwright 실행. 환경 파일과 앱 구현은 변경하지 않음. 기존 이름의 이미지를 갱신하며 실패해도 다음 캡처 진행. docs 전체는 기존 .gitignore 규칙에 따라 Git 제외.\n\n## 한계 및 미검증\n\n${m.limitations.map(x=>'- '+x).join('\n')}\n\n## 실패 목록\n\n${m.captures.filter(r=>!r.success).map(r=>`- ${r.device} ${r.pageName} ${r.state}: ${r.failureReason}`).join('\n')||'없음'}\n\n## 화면 목록\n\n`;
await fs.writeFile(`${root}/README.md`,text+m.captures.map(r=>`### ${r.device} · ${r.pageName} · ${r.state}\n\n${states[r.state]|| (r.state.startsWith('expanded')?'아코디언 또는 상세 영역 펼침':r.state.startsWith('tab')?'탭 전환':r.state.startsWith('step')?'다단계 입력 단계':'버튼 상호작용으로 열린 UI')}. URL: ${r.url}\n\n${r.success?`[PNG 보기](${r.imagePath})${r.duplicateOf?' (동일 이미지 재사용)':''}\n\n![${r.pageName} ${r.state}](${r.imagePath})`:`실패: ${r.failureReason}`}\n`).join('\n'));
console.log(m.summary);
