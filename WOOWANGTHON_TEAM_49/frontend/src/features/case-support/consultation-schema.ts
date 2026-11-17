import { z } from 'zod';
import { message } from '@/i18n/message';

const text = (max: number) => z.string().refine(value=>Array.from(value).length<=max, {message:message('caseSupport.prepLimit', { count: max })}).trim();
export const consultationNotesSchema = z.object({
 displayName: text(100), workLocation: text(200),
 startDate: z.iso.date().nullable(), endDate: z.iso.date().nullable(),
 purpose: text(1000), desiredHelp: text(1000), facts: text(2000), unknowns: text(2000), materials: text(2000),
 events: z.array(z.object({date:z.iso.date().nullable(),text:text(500)})).max(20),
 questions: z.array(text(300)).max(20),
}).strict().refine(value => !value.startDate || !value.endDate || value.startDate <= value.endDate, {
 path:['endDate'], message:message('caseSupport.prepDateOrder'),
});
export type ConsultationNotes = z.infer<typeof consultationNotesSchema>;
export const emptyConsultation = (): ConsultationNotes => ({displayName:'',workLocation:'',startDate:null,endDate:null,purpose:'',desiredHelp:'',facts:'',unknowns:'',materials:'',events:[],questions:[]});
export const consultationDraftSchema = z.object({version:z.number().int().nonnegative(),notes:consultationNotesSchema,documentIds:z.array(z.number().int().positive()).max(100),updatedAt:z.string().nullable()});
export type ConsultationDraft = z.infer<typeof consultationDraftSchema>;
