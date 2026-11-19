from fastapi import HTTPException
from src.models.source import GridHour,Experiment,Meta
from src.services.validation import validate_grid,validate_experiment
from src.services.audit import log
def get_meta(db,lock=False):
 meta=db.get(Meta,'source',with_for_update=lock) if lock else db.get(Meta,'source')
 if not meta: meta=Meta(key='source',version=1,active_run_id=None);db.add(meta);db.flush()
 return meta
def bump(db):
 # 源数据每次变更都推进版本：待生效方案随之失效；与启用共用同一行锁，杜绝并发采纳过期排程
 meta=get_meta(db,lock=True);meta.version+=1;return meta
def save_grid(db,user,data,id=None):
 d=validate_grid(data);meta=bump(db)
 obj=db.get(GridHour,id) if id else GridHour()
 if not obj: raise HTTPException(404,'电网画像不存在')
 clash=db.query(GridHour).filter(GridHour.hour==d['hour'],GridHour.id!=(id or 0)).first()
 if clash: raise HTTPException(409,f"第{d['hour']}小时已有画像，请编辑该记录")
 for k,v in d.items(): setattr(obj,k,v)
 db.add(obj);log(db,user.email,'grid.save' if id else 'grid.create',f"hour={d['hour']} 源数据版本→v{meta.version}");db.commit();return obj
def delete_grid(db,user,id):
 obj=db.get(GridHour,id)
 if not obj: raise HTTPException(404,'电网画像不存在')
 meta=bump(db);db.delete(obj);log(db,user.email,'grid.delete',f"hour={obj.hour} 源数据版本→v{meta.version}");db.commit()
def save_experiment(db,user,data,id=None):
 d=validate_experiment(data);meta=bump(db)
 obj=db.get(Experiment,id) if id else Experiment()
 if not obj: raise HTTPException(404,'实验不存在')
 clash=db.query(Experiment).filter(Experiment.code==d['code'],Experiment.id!=(id or 0)).first()
 if clash: raise HTTPException(409,f"实验编号{d['code']}已存在")
 for k,v in d.items(): setattr(obj,k,v)
 db.add(obj);log(db,user.email,'experiment.save' if id else 'experiment.create',f"{d['code']} 源数据版本→v{meta.version}");db.commit();return obj
def delete_experiment(db,user,id):
 obj=db.get(Experiment,id)
 if not obj: raise HTTPException(404,'实验不存在')
 meta=bump(db);db.delete(obj);log(db,user.email,'experiment.delete',f"{obj.code} 源数据版本→v{meta.version}");db.commit()
