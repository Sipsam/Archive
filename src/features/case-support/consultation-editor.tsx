"use client";
import { useEffect, useRef, useState } from 'react';
import { useMutation, useQuery } from '@tanstack/react-query';
import { zodResolver } from '@hookform/resolvers/zod';
import { useForm } from '@/i18n/use-localized-form';
import { useTranslation } from '@/i18n/use-translation';
import { useSessionScope } from '@/hooks/use-session-scope';
import { useCaseRemoval } from '@/features/cases/queries';
import { businessKeys } from '@/lib/query/business-keys';
import { ApiError } from '@/lib/api/error';
import { QueryFeedback } from '@/components/ui/query-feedback';
import { TextField } from '@/components/ui/text-field';
import { cardStyle, primaryButton, secondaryButton } from '@/components/ui/styles';
import { supportApi } from './api';
import { consultationNotesSchema, emptyConsultation, type ConsultationDraft, type ConsultationNotes } from './consultation-schema';

export function useConsultationDraft(caseId:number, ids:number[], setIds:(ids:number[])=>void) {
 const s=useSessionScope(); const removed=useCaseRemoval(caseId); const {translate}=useTranslation();
 const key=[...businessKeys.case(s.generation,caseId),'consultation-draft'];
 const q=useQuery({queryKey:key,enabled:s.enabled&&!removed.pending&&!removed.removed,queryFn:({signal})=>supportApi(s.api).draft(caseId,signal),refetchOnWindowFocus:false});
 const form=useForm<ConsultationNotes>({resolver:zodResolver(consultationNotesSchema),defaultValues:emptyConsultation()});
 const saved=useRef<ConsultationDraft|null>(null);
 const [conflict,setConflict]=useState<ConsultationDraft|null>(null);
 const {reset}=form;
 useEffect(()=>{if(q.data&&!saved.current){saved.current=q.data;reset(q.data.notes);setIds(q.data.documentIds)}},[q.data,reset,setIds]);
 const dirty=form.formState.isDirty || (!!q.data&&JSON.stringify(ids)!==JSON.stringify(q.data.documentIds));
 useEffect(()=>{
  if(!dirty)return;
  const unload=(e:BeforeUnloadEvent)=>{e.preventDefault()};
  const navigate=(e:MouseEvent)=>{const anchor=(e.target as Element)?.closest?.('a[href]');if(anchor&&!anchor.hasAttribute('download')&&!window.confirm(translate('caseSupport.prepUnsaved'))){e.preventDefault();e.stopPropagation()}};
  window.addEventListener('beforeunload',unload);document.addEventListener('click',navigate,true);
  return ()=>{window.removeEventListener('beforeunload',unload);document.removeEventListener('click',navigate,true)};
 },[dirty,translate]);
 const save=useMutation({gcTime:0,mutationFn:async()=>{
  if(!saved.current)throw new Error('DRAFT_NOT_LOADED');
  if(!await form.trigger())throw new Error('DRAFT_INVALID');
  const notes=consultationNotesSchema.parse(form.getValues());
  const sent={notes,documentIds:[...ids]};
  if(JSON.stringify(notes)===JSON.stringify(saved.current.notes)&&JSON.stringify(ids)===JSON.stringify(saved.current.documentIds))return saved.current;
  try{
   const result=await supportApi(s.api).saveDraft(caseId,saved.current.version,notes,sent.documentIds);
   if(s.session.getSnapshot().generation!==s.generation)throw new Error('SESSION_CHANGED');
   saved.current=result;
   // Only mark exactly the submitted input clean; preserve edits made during the request.
   if(JSON.stringify(consultationNotesSchema.safeParse(form.getValues()).data)===JSON.stringify(notes))reset(result.notes);
   s.queryClient.setQueryData(key,result);setConflict(null);return result;
  }catch(error){
   if(error instanceof ApiError&&error.errorCode==='CONSULTATION_DRAFT_CONFLICT'){
    const latest=await supportApi(s.api).draft(caseId);
    if(s.session.getSnapshot().generation===s.generation)setConflict(latest);
   }throw error;
  }
 }});
 return {form,q,save,dirty,conflict,removed,acceptConflict:(replace:boolean)=>{
  if(!conflict)return;saved.current=conflict;s.queryClient.setQueryData(key,conflict);if(replace){reset(conflict.notes);setIds(conflict.documentIds)}setConflict(null);save.reset();
 }};
}

export function ConsultationEditor({preparation,disabled=false,onEdit}:{preparation:ReturnType<typeof useConsultationDraft>;disabled?:boolean;onEdit:()=>void}) {
 const {translate:t}=useTranslation();const {form,q,save,dirty,conflict,acceptConflict}=preparation;
 const values=form.watch();const {register,formState:{errors}}=form;
 const labels={displayName:'caseSupport.prepDisplayName',workLocation:'caseSupport.prepLocation',purpose:'caseSupport.prepPurpose',desiredHelp:'caseSupport.prepHelp',facts:'caseSupport.prepFacts',unknowns:'caseSupport.prepUnknowns',materials:'caseSupport.prepMaterials'} as const;
 if(q.isPending)return <QueryFeedback pending/>;
 if(q.isError)return <QueryFeedback error={q.error} retry={()=>void q.refetch()}/>;
 return <section data-consultation-notes className={`${cardStyle} min-w-0 space-y-4`} aria-label={t('caseSupport.prepEditor')}>
  <h2 className="text-title font-bold">{t('caseSupport.prepEditor')}</h2>
  <p>{t('caseSupport.prepGuidance')}</p><p>{t('caseSupport.prepLanguage')}</p>
  <form noValidate onChange={onEdit} onSubmit={e=>{e.preventDefault();void save.mutateAsync().catch(()=>{})}} className="space-y-5">
   <fieldset disabled={disabled||save.isPending||preparation.removed.pending||preparation.removed.removed} className="min-w-0 space-y-4">
   <div className="grid min-w-0 gap-4 sm:grid-cols-2">{(['displayName','workLocation'] as const).map(name=><TextField key={name} id={`prep-${name}`} label={t(labels[name])} {...register(name)} error={errors[name]?.message}/>)}
    {(['startDate','endDate'] as const).map(name=><TextField key={name} id={`prep-${name}`} type="date" label={t(name==='startDate'?'caseSupport.prepStart':'caseSupport.prepEnd')} {...register(name,{setValueAs:v=>v||null})} error={errors[name]?.message}/>)}</div>
   {(['purpose','desiredHelp','facts','unknowns','materials'] as const).map(name=><div key={name}><label className="block font-bold" htmlFor={`prep-${name}`}>{t(labels[name])}</label><textarea id={`prep-${name}`} className="ui-control min-h-24 w-full" rows={3} {...register(name)} aria-invalid={!!errors[name]} aria-describedby={errors[name]?`prep-${name}-error`:undefined}/>{errors[name]&&<p id={`prep-${name}-error`} role="alert">{errors[name]?.message}</p>}</div>)}
   <fieldset className="min-w-0 space-y-3"><legend className="font-bold">{t('caseSupport.prepEvents')}</legend>
    {values.events.map((_,i)=><div className="grid min-w-0 gap-2 sm:grid-cols-[10rem_minmax(0,1fr)_auto]" key={i}>
     <TextField id={`prep-event-date-${i}`} type="date" label={t('caseSupport.prepEventDate',{number:i+1})} {...register(`events.${i}.date`,{setValueAs:v=>v||null})} error={errors.events?.[i]?.date?.message}/>
     <div><label htmlFor={`prep-event-${i}`}>{t('caseSupport.prepEventText',{number:i+1})}</label><textarea id={`prep-event-${i}`} className="ui-control w-full" {...register(`events.${i}.text`)} aria-invalid={!!errors.events?.[i]?.text} aria-describedby={`prep-event-error-${i}`}/><p id={`prep-event-error-${i}`} role={errors.events?.[i]?.text?'alert':undefined}>{errors.events?.[i]?.text?.message}</p></div>
     <button type="button" className={secondaryButton} aria-label={t('caseSupport.prepRemoveEvent',{number:i+1})} onClick={()=>{form.setValue('events',values.events.filter((_,n)=>n!==i),{shouldDirty:true});onEdit()}}>{t('caseSupport.prepRemoveEvent',{number:i+1})}</button>
    </div>)}<button type="button" className={secondaryButton} disabled={values.events.length>=20} onClick={()=>{form.setValue('events',[...values.events,{date:null,text:''}],{shouldDirty:true});onEdit()}}>{t('caseSupport.prepAddEvent')}</button>
   </fieldset>
   <fieldset className="min-w-0 space-y-3"><legend className="font-bold">{t('caseSupport.prepQuestions')}</legend>{values.questions.map((_,i)=><div key={i} className="flex min-w-0 flex-wrap items-end gap-2"><div className="min-w-0 flex-1"><TextField id={`prep-question-${i}`} label={t('caseSupport.prepQuestion',{number:i+1})} {...register(`questions.${i}`)} error={errors.questions?.[i]?.message}/></div><button type="button" className={secondaryButton} aria-label={t('caseSupport.prepRemoveQuestion',{number:i+1})} onClick={()=>{form.setValue('questions',values.questions.filter((_,n)=>n!==i),{shouldDirty:true});onEdit()}}>{t('caseSupport.prepRemoveQuestion',{number:i+1})}</button></div>)}<button type="button" className={secondaryButton} disabled={values.questions.length>=20} onClick={()=>{form.setValue('questions',[...values.questions,''],{shouldDirty:true});onEdit()}}>{t('caseSupport.prepAddQuestion')}</button></fieldset>
   </fieldset>
   <p role="status">{save.isPending?t('caseSupport.prepSaving'):dirty?t('caseSupport.prepDirty'):t('caseSupport.prepSaved')}</p>
   {save.isError&&!conflict&&<><QueryFeedback error={save.error}/><p role="alert">{t('caseSupport.prepSaveFailed')}</p></>}
   {conflict&&<section className="space-y-3" aria-label={t('caseSupport.prepConflict')}><p role="alert">{t('caseSupport.prepConflict')}</p><ConsultationSummary notes={conflict.notes}/><button type="button" className={secondaryButton} onClick={()=>acceptConflict(true)}>{t('caseSupport.prepLoadRemote')}</button><button type="button" className={secondaryButton} onClick={()=>acceptConflict(false)}>{t('caseSupport.prepKeepLocal')}</button></section>}
   <button className={primaryButton} disabled={disabled||save.isPending||!!conflict||preparation.removed.pending||preparation.removed.removed}>{t('caseSupport.prepSave')}</button>
  </form>
  <details><summary>{t('caseSupport.prepReview')}</summary><p>{t('caseSupport.prepUserWritten')}</p><ConsultationSummary notes={values}/></details>
 </section>;
}

function ConsultationSummary({notes}:{notes:ConsultationNotes}) {
 const {translate:t}=useTranslation();
 const fields=[['displayName','caseSupport.prepDisplayName'],['workLocation','caseSupport.prepLocation'],['startDate','caseSupport.prepStart'],['endDate','caseSupport.prepEnd'],['purpose','caseSupport.prepPurpose'],['desiredHelp','caseSupport.prepHelp'],['facts','caseSupport.prepFacts'],['unknowns','caseSupport.prepUnknowns'],['materials','caseSupport.prepMaterials']] as const;
 return <div className="space-y-4 break-words"><dl className="space-y-3">{fields.map(([name,label])=><div key={name}><dt className="font-bold">{t(label)}</dt><dd className="whitespace-pre-wrap">{notes[name]||t('common.notProvided')}</dd></div>)}</dl><h3 className="font-bold">{t('caseSupport.prepEvents')}</h3><ul>{notes.events.map((event,i)=><li key={i}>{event.date||t('common.notProvided')} · {event.text||t('common.notProvided')}</li>)}</ul><h3 className="font-bold">{t('caseSupport.prepQuestions')}</h3><ul>{notes.questions.map((question,i)=><li key={i}>{question||t('common.notProvided')}</li>)}</ul></div>;
}
