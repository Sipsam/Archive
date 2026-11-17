import type { Report } from "@/features/case-support/schemas";
import type {ConsultationNotes} from '@/features/case-support/consultation-schema';
// Synthetic ASCII PDF, generated only in MSW, never a frontend wage engine.
export function reportPdf(r:Report,notes?:ConsultationNotes):Uint8Array<ArrayBuffer>{
 if(notes)return consultationPdf(r,notes);
 const lines=["WAGEITDA MOCK REPORT - NOT AN OFFICIAL DOCUMENT",`Report ${r.reportId} / version ${r.version}`,`Input version ${r.basedOnInputVersion}`,`Original IDs: ${r.selectedDocumentIds.join(", ")}`,JSON.stringify(r.referencedSnapshots)];
 const content="BT /F1 10 Tf 30 740 Td "+lines.map((s,i)=>`${i?"0 -30 Td ":""}(${s.replace(/[()\\]/g," ")}) Tj`).join(" ")+" ET";
 const objects=["<< /Type /Catalog /Pages 2 0 R >>","<< /Type /Pages /Kids [3 0 R] /Count 1 >>","<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>","<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",`<< /Length ${content.length} >>\nstream\n${content}\nendstream`];
 let pdf="%PDF-1.4\n";const offsets=[0];objects.forEach((o,i)=>{offsets.push(pdf.length);pdf+=`${i+1} 0 obj\n${o}\nendobj\n`});const start=pdf.length;pdf+=`xref\n0 6\n0000000000 65535 f \n${offsets.slice(1).map(o=>`${String(o).padStart(10,"0")} 00000 n \n`).join("")}trailer\n<< /Size 6 /Root 1 0 R >>\nstartxref\n${start}\n%%EOF`;return new TextEncoder().encode(pdf);
}
export interface MockOriginal { documentId:number; name:string; bytes:Uint8Array<ArrayBuffer> }
/** Stored ZIP fixture serializer, used exclusively by MSW. */
export function snapshotZip(r:Report, originals:MockOriginal[]=[],notes?:ConsultationNotes,pdf?:Uint8Array<ArrayBuffer>):Uint8Array<ArrayBuffer>{
 const encoder=new TextEncoder();
 const entries=[{name:"result-snapshot.json",bytes:encoder.encode(JSON.stringify(r))},...(notes?[{name:'consultation.json',bytes:encoder.encode(JSON.stringify(notes))}]:[]),...(pdf?[{name:'summary.pdf',bytes:pdf}]:[]),...originals.filter(f=>r.selectedDocumentIds.includes(f.documentId)).map(f=>({name:`originals/${f.documentId}-${f.name.replace(/[\\/\x00-\x1f]/g,"_")}`,bytes:f.bytes}))];
 const locals:Uint8Array[]=[],centrals:Uint8Array[]=[];let offset=0;
 for(const entry of entries){
  const name=encoder.encode(entry.name),data=entry.bytes;let crc=0xffffffff;
  for(const b of data){crc^=b;for(let i=0;i<8;i++)crc=(crc>>>1)^((crc&1)?0xedb88320:0)}crc=(crc^0xffffffff)>>>0;
  const local=new Uint8Array(30+name.length+data.length),central=new Uint8Array(46+name.length);
  const l=new DataView(local.buffer),c=new DataView(central.buffer);
  l.setUint32(0,0x04034b50,true);l.setUint16(4,20,true);l.setUint16(6,0x800,true);l.setUint32(14,crc,true);l.setUint32(18,data.length,true);l.setUint32(22,data.length,true);l.setUint16(26,name.length,true);local.set(name,30);local.set(data,30+name.length);
  c.setUint32(0,0x02014b50,true);c.setUint16(4,20,true);c.setUint16(6,20,true);c.setUint16(8,0x800,true);c.setUint32(16,crc,true);c.setUint32(20,data.length,true);c.setUint32(24,data.length,true);c.setUint16(28,name.length,true);c.setUint32(42,offset,true);central.set(name,46);
  locals.push(local);centrals.push(central);offset+=local.length;
 }
 const centralSize=centrals.reduce((n,v)=>n+v.length,0);const result=new Uint8Array(offset+centralSize+22);let position=0;
 for(const part of [...locals,...centrals]){result.set(part,position);position+=part.length;}
 const end=new DataView(result.buffer,position);end.setUint32(0,0x06054b50,true);end.setUint16(8,entries.length,true);end.setUint16(10,entries.length,true);end.setUint32(12,centralSize,true);end.setUint32(16,offset,true);return result;
}

// Development-only Unicode PDF. The Korean standard CID font is substituted by
// the PDF viewer; production PDFs embed the server's licensed Hangul font.
function consultationPdf(r:Report,n:ConsultationNotes):Uint8Array<ArrayBuffer>{
 const text=(s:string)=>Array.from(s).flatMap(c=>Array.from({length:c.length},(_,i)=>c.charCodeAt(i).toString(16).padStart(4,'0'))).join('');
 const wrap=(s:string)=>s.split('\n').flatMap(line=>{const chars=Array.from(line);return Array.from({length:Math.max(1,Math.ceil(chars.length/44))},(_,i)=>chars.slice(i*44,i*44+44).join(''))});
 const summary=['근로·급여 상담 준비서','개발용 가상 자료 · 공식 문서가 아닙니다',`보고서 ${r.reportId} · 입력 버전 ${r.basedOnInputVersion}`,`작성 기준 ${r.createdAt}`,
  ...[['상담하려는 문제',n.purpose],['원하는 도움',n.desiredHelp],['표시명',n.displayName],['실제 근무 장소',n.workLocation],['입사일',n.startDate],['퇴사일',n.endDate],['핵심 사실',n.facts],['미확인 사항',n.unknowns]].map(([label,value])=>`${label}: ${value||'미확인'}`),
  '표시된 차이만으로 체불 또는 법 위반을 확정하지 않습니다.'].flatMap(wrap);
 const detail=['기간별 급여·지급 비교','아래는 개발용 양식 예시이며 실제 사용자의 계산 결과가 아닙니다.','약정·명세·계산 금액: 미확인','실제 지급: 자료 없음 · 비교 차이: 비교 보류','미확인 금액은 0원으로 바꾸지 않습니다.','사용자 작성 경위',...n.events.map(e=>`${e.date||'날짜 미확인'}: ${e.text}`),'사용자 상담 질문',...n.questions,'추가 자료',n.materials||'미기재','선택 원본',...r.selectedDocumentIds.map((id,i)=>`증빙 ${i+1}: 문서 ${id} / ZIP 포함`)].flatMap(wrap);
 const pages:string[][]=[];for(const lines of [summary,detail])for(let i=0;i<lines.length;i+=42)pages.push(lines.slice(i,i+42));
 const cmap='/CIDInit /ProcSet findresource begin 12 dict begin begincmap /CIDSystemInfo << /Registry (Adobe) /Ordering (UCS) /Supplement 0 >> def /CMapName /Unicode def /CMapType 2 def 1 begincodespacerange <0000> <FFFF> endcodespacerange 1 beginbfrange <0000> <FFFF> <0000> endbfrange endcmap CMapName currentdict /CMap defineresource pop end end';
 const objects=['<< /Type /Catalog /Pages 2 0 R >>','',`<< /Type /Font /Subtype /Type0 /BaseFont /HYGoThic-Medium /Encoding /UniKS-UCS2-H /DescendantFonts [4 0 R] /ToUnicode 5 0 R >>`,'<< /Type /Font /Subtype /CIDFontType0 /BaseFont /HYGoThic-Medium /CIDSystemInfo << /Registry (Adobe) /Ordering (Korea1) /Supplement 1 >> /DW 1000 >>',`<< /Length ${cmap.length} >>\nstream\n${cmap}\nendstream`];
 const pageIds:number[]=[];
 pages.forEach((lines,i)=>{const id=objects.length+1;pageIds.push(id);const content=`BT /F1 10 Tf 36 792 Td ${[...lines,`월급잇다 · ${i+1} / ${pages.length}`].map((line,j)=>`${j?'0 -17 Td ':''}<${text(line)}> Tj`).join(' ')} ET`;
  objects.push(`<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] /Resources << /Font << /F1 3 0 R >> >> /Contents ${id+1} 0 R >>`,`<< /Length ${content.length} >>\nstream\n${content}\nendstream`);
 });
 objects[1]=`<< /Type /Pages /Kids [${pageIds.map(id=>`${id} 0 R`).join(' ')}] /Count ${pages.length} >>`;
 let pdf=`%PDF-1.4\n% Input version ${r.basedOnInputVersion}\n`;const offsets=[0];objects.forEach((o,i)=>{offsets.push(pdf.length);pdf+=`${i+1} 0 obj\n${o}\nendobj\n`});const start=pdf.length;pdf+=`xref\n0 ${objects.length+1}\n0000000000 65535 f \n${offsets.slice(1).map(o=>`${String(o).padStart(10,'0')} 00000 n \n`).join('')}trailer\n<< /Size ${objects.length+1} /Root 1 0 R >>\nstartxref\n${start}\n%%EOF`;return new TextEncoder().encode(pdf);
}
