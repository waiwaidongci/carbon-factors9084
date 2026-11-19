// 可开工窗口编辑器：动态[起,止]小时行
export function readWindows(form){return [...form.querySelectorAll('.window-row')].map(r=>[Number(r.querySelector('[name=wstart]').value),Number(r.querySelector('[name=wend]').value)])}
export function fillWindows(root,windows){root.innerHTML=windows.map(([a,b])=>row(a,b)).join('')}
export const row=(a=8,b=18)=>`<div class="window-row"><label>起始小时<input name="wstart" type="number" min="0" max="47" value="${a}" required></label><label>截止小时<input name="wend" type="number" min="0" max="47" value="${b}" required></label><button type="button" class="remove-window">删除窗口</button></div>`;
export function bindWindowRows(){const root=document.querySelector('#window-rows');if(!root)return;root.onclick=e=>{if(e.target.classList.contains('remove-window')){const rows=root.querySelectorAll('.window-row');if(rows.length>1)e.target.closest('.window-row').remove()}};const add=document.querySelector('#add-window');if(add)add.onclick=()=>root.insertAdjacentHTML('beforeend',row())}
