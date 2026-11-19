// API实体字段约定：电网画像{id,hour,factor,base_load,capacity}、实验{id,code,name,windows,hours,power}、求解任务{id,name,status,snapshot,checksum,source_version,result,error,progress,created,active,stale}、meta{version,active_run_id}。
export const ENTITY_KEYS=['grid','experiments','runs'];
