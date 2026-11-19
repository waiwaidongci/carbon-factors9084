import {esc,fmt,hour,time} from '../utils/format.js';import {table} from './common/table.js';import {status} from './common/status.js';
export function plan(run,role){
 if(!run)return '<p class="empty">选择左侧任务查看排程结果。</p>';
 const r=run.result;
 let html=`<section class="report"><div class="report-top"><h2>${esc(run.name)}</h2><div>${status(run.status)}${run.active?'<span class="badge active">现行方案</span>':''}${run.stale?'<span class="badge stale">已失效</span>':''}</div></div><p>排队冻结于 ${time(run.created)} · 源数据版本 v${run.source_version} · 冻结 ${run.snapshot.experiments.length} 项实验 / ${run.snapshot.grid.length} 小时画像</p><p class="checksum">SHA256 ${esc(run.checksum)}</p>`;
 if(run.error)html+='<p class="error">'+esc(run.error)+'</p>';
 if(r&&r.feasible){
  html+=`<div class="metrics">${Object.entries(r.summary).map(([k,v])=>`<div><small>${esc(k)}</small><strong>${fmt(v)}</strong></div>`).join('')}</div><p class="method">${esc(r.method)}</p><h3>各实验时段与排放量</h3>${table(r.schedule.map(x=>({编号:x.code,名称:x.name,开工:hour(x.start),结束:hour(x.end),连续小时:x.hours,'功率kW':x.power,'排放kgCO₂e':x.emissions})))}<details open><summary>逐小时负荷叠加核对</summary>${table(r.hourly.map(x=>({小时:hour(x.hour),'因子kg/kWh':x.factor,'基础kW':x.base_load,'实验kW':x.exp_load,'合计kW':x.total,'容量kW':x.capacity,'余量kW':x.slack,实验:x.experiments,'排放kg':x.emissions})))}</details>`;
 }else if(r&&!r.feasible){
  html+=`<h3>无解：冲突说明</h3><ul class="conflicts">${r.conflicts.map(c=>'<li>'+esc(c)+'</li>').join('')}</ul><p class="warning">该冻结输入下不存在可行排程，现行方案保持不变。请调整可开工窗口、功率或容量上限后重新发起求解。</p><div class="metrics">${Object.entries(r.summary).map(([k,v])=>`<div><small>${esc(k)}</small><strong>${fmt(v)}</strong></div>`).join('')}</div>`;
 }else if(run.status==='queued'||run.status==='running'){
  html+=`<p class="method">worker 求解中，已搜索 ${fmt(run.progress?.nodes??0)} 个节点；求解分片落盘，中断后自动从检查点恢复。</p>`;
 }
 html+=`<details><summary>排队时冻结的输入快照</summary><pre class="snapshot">${esc(JSON.stringify(run.snapshot,null,2))}</pre></details>`;
 if(run.status==='completed'&&r?.feasible){
  html+='<div class="report-actions">';
  if(role==='admin'){
   if(run.active)html+='<button disabled>已是现行方案</button>';
   else if(run.stale)html+='<button disabled>源数据已更新·不可启用</button>';
   else html+=`<button id="activate" data-id="${run.id}">启用为现行方案</button>`;
  }
  html+=`<button id="export" data-id="${run.id}" class="ghost">下载时段CSV</button></div>`;
 }
 if(run.status==='failed')html+=`<div class="report-actions"><button id="retry" data-id="${run.id}">重试（沿用原任务，不新增方案）</button></div>`;
 return html+'</section>';
}
