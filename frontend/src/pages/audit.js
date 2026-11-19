import {heading} from '../components/common/header.js';import {table} from '../components/common/table.js';import {time} from '../utils/format.js';
export function audit(c,d){return heading('PROCESS RECORD / 05','过程留痕','画像与实验修改、求解排队与重试、方案启用均记录操作者、动作与源数据版本。')+table(d.audits.map(a=>({时间:time(a.at),操作者:a.actor,动作:a.action,内容:a.detail})))}
