import {request} from './client.js';
export const loadAll=async()=>Object.fromEntries(await Promise.all(['grid','experiments','runs','audits','meta'].map(async k=>[k,await request('/'+k)])));
export const saveGrid=(data,id)=>request('/grid'+(id?'/'+id:''),id?'PUT':'POST',{data});
export const deleteGrid=id=>request('/grid/'+id,'DELETE');
export const saveExperiment=(data,id)=>request('/experiments'+(id?'/'+id:''),id?'PUT':'POST',{data});
export const deleteExperiment=id=>request('/experiments/'+id,'DELETE');
export const queueRun=name=>request('/runs','POST',{name});
export const retryRun=id=>request('/runs/'+id+'/retry','POST',{});
export const activateRun=id=>request('/runs/'+id+'/activate','POST',{});
