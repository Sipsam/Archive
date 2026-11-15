// @vitest-environment jsdom
import '@testing-library/jest-dom/vitest';
import {cleanup,fireEvent,render,screen,waitFor} from '@testing-library/react';
import {afterEach,beforeEach,expect,it,vi} from 'vitest';
import {QueryClientProvider} from '@tanstack/react-query';
import {AppServicesContext} from '@/hooks/use-app-services';
import {createAppServices} from '@/lib/app-services';
import {server,testApiUrl} from '@/test/server';
import {createDevelopmentScenario} from '@/mocks/development';
import {ReportsScreen} from './screens';
import {supportApi} from './api';
import {emptyConsultation} from './consultation-schema';
import {ReportPdfPreview} from './report-pdf-preview';

vi.mock('next/navigation',()=>({usePathname:()=>'/cases/15/reports'}));
vi.mock('@/features/documents/review/components/pdf-canvas',()=>({default:()=>null}));
let services:ReturnType<typeof createAppServices>;
beforeEach(async()=>{
 server.use(...createDevelopmentScenario(testApiUrl).handlers);
 services=createAppServices(testApiUrl);await services.auth.login({email:'worker@example.com',password:'password1234'});
 HTMLDialogElement.prototype.showModal=function(){this.open=true};HTMLDialogElement.prototype.close=function(){this.open=false};
});
afterEach(()=>{cleanup();services.session.clear();services.queryClient.clear();vi.restoreAllMocks();vi.unstubAllGlobals()});
function mount(node=<ReportsScreen caseId={15}/>){return render(<AppServicesContext value={services}><QueryClientProvider client={services.queryClient}>{node}</QueryClientProvider></AppServicesContext>)}

it('saves user-authored notes and restores them after reopening',async()=>{
 const view=mount();const purpose=await screen.findByLabelText('상담하려는 문제');
 fireEvent.change(purpose,{target:{value:'급여 차이를 상담하고 싶습니다'}});
 fireEvent.click(screen.getByRole('button',{name:'경위 추가'}));
 fireEvent.change(screen.getByLabelText('경위 1 내용'),{target:{value:'지급을 요청했습니다'}});
 fireEvent.click(screen.getByRole('button',{name:'초안 저장'}));
 await waitFor(()=>expect(screen.getByText('저장된 초안과 같은 내용입니다.')).toBeVisible());
 expect((await supportApi(services.api).draft(15)).notes.events[0].text).toBe('지급을 요청했습니다');
 view.unmount();mount();expect(await screen.findByLabelText('상담하려는 문제')).toHaveValue('급여 차이를 상담하고 싶습니다');
});

it('preserves local input on a draft conflict and supports explicit reapplication',async()=>{
 mount();const purpose=await screen.findByLabelText('상담하려는 문제');
 fireEvent.change(purpose,{target:{value:'현재 입력'}});
 await supportApi(services.api).saveDraft(15,0,{...emptyConsultation(),purpose:'다른 화면의 입력'},[]);
 fireEvent.click(screen.getByRole('button',{name:'초안 저장'}));
 await screen.findByRole('button',{name:'현재 입력 유지 후 다시 저장'});
 expect(purpose).toHaveValue('현재 입력');
 fireEvent.click(screen.getByRole('button',{name:'현재 입력 유지 후 다시 저장'}));
 fireEvent.click(screen.getByRole('button',{name:'초안 저장'}));
 await waitFor(()=>expect(screen.getByText('저장된 초안과 같은 내용입니다.')).toBeVisible());
 expect((await supportApi(services.api).draft(15)).notes.purpose).toBe('현재 입력');
});

it('validates dates and text limits without discarding input',async()=>{
 mount();const purpose=await screen.findByLabelText('상담하려는 문제');
 fireEvent.change(purpose,{target:{value:'x'.repeat(1001)}});
 fireEvent.change(screen.getByLabelText('입사일'),{target:{value:'2026-11-02'}});
 fireEvent.change(screen.getByLabelText('퇴사일'),{target:{value:'2026-11-01'}});
 fireEvent.click(screen.getByRole('button',{name:'초안 저장'}));
 expect(await screen.findByText('1000자 이내로 입력해 주세요.')).toBeVisible();
 expect(await screen.findByText('퇴사일은 입사일 이후여야 합니다.')).toBeVisible();
 expect(purpose).toHaveValue('x'.repeat(1001));expect((await supportApi(services.api).draft(15)).version).toBe(0);
});

it('pins notes in the Mock PDF and ZIP and rejects stale draft versions',async()=>{
 const api=supportApi(services.api);const saved=await api.saveDraft(15,0,{...emptyConsultation(),purpose:'고정된 상담 내용'},[]);
 const report=await api.create(15,[],'frozen-notes',saved.version);
 await api.saveDraft(15,saved.version,{...emptyConsultation(),purpose:'나중에 바꾼 내용'},[]);
 expect((await api.create(15,[],'frozen-notes',saved.version)).reportId).toBe(report.reportId);
 await expect(api.create(15,[],'stale-draft',saved.version)).rejects.toMatchObject({errorCode:'CONSULTATION_DRAFT_CONFLICT'});
 for(let i=0;i<3;i++)await api.report(15,report.reportId);
 const file=await services.api.requestDownload(`/cases/15/reports/${report.reportId}/pdf`,'application/pdf','report.pdf');
 const pdf=new TextDecoder().decode(await file.blob.arrayBuffer());
 const hex=(s:string)=>Array.from(s).map(c=>c.charCodeAt(0).toString(16).padStart(4,'0')).join('');
 expect(pdf).toContain(hex('고정된 상담 내용'));expect(pdf).not.toContain(hex('나중에 바꾼 내용'));expect(pdf).toContain('/Count 2');
});

it('releases preview blob URLs when closed',async()=>{
 const create=vi.fn(()=> 'blob:test-preview'),revoke=vi.fn();vi.stubGlobal('URL',class extends URL {static createObjectURL=create;static revokeObjectURL=revoke});
 const file={blob:new Blob(['%PDF-1.4 sample'],{type:'application/pdf'}),filename:'report.pdf'};
 const view=mount(<ReportPdfPreview file={file} onClose={()=>{}}/>);
 await waitFor(()=>expect(document.querySelector('iframe')).toHaveAttribute('src','blob:test-preview'));view.unmount();expect(revoke).toHaveBeenCalledWith('blob:test-preview');
});
