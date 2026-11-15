// Isolated archive runner. Never starts or contacts a backend.
import { spawn } from 'node:child_process';
const base = process.env.ARCHIVE_URL || 'http://localhost:3100';
if(!['localhost','127.0.0.1','[::1]'].includes(new URL(base).hostname))throw new Error('ARCHIVE_URL must point to a local Mock frontend.');
let server;
async function run(file) {
  await new Promise((resolve, reject) => {
    const child = spawn(process.execPath, [file], { stdio: 'inherit' });
    child.on('error', reject);
    child.on('exit', code => code === 0 ? resolve() : reject(new Error(`${file}: ${code}`)));
  });
}
try {
  if (!process.env.ARCHIVE_URL) {
    server = spawn(process.execPath, ['node_modules/next/dist/bin/next', 'dev', '--port', '3100'], {stdio:'inherit', env:{...process.env,NEXT_PUBLIC_MOCK_API:'true',NEXT_PUBLIC_API_BASE_URL:`${base}/api/v1`}});
    for(let i=0;i<120;i++) {
      try { if((await fetch(base)).ok) break; } catch {}
      await new Promise(resolve=>setTimeout(resolve,500));
    }
  }
  await run('scripts/screenshots-capture.mjs');
  await run('scripts/screenshots-states.mjs');
  await run('scripts/screenshots-verify.mjs');
  await run('scripts/screenshots-report.mjs');
} finally { if(server) { if(process.platform==='win32') spawn('taskkill',['/pid',String(server.pid),'/t','/f']); else server.kill(); } }
