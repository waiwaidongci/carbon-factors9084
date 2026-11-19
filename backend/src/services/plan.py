import hashlib,json,time
import redis
from fastapi import HTTPException
from src.config.settings import REDIS_URL,CONFIG
from src.models.source import GridHour,Experiment
from src.models.run import SolveRun
from src.services.source import get_meta
from src.services.audit import log
from src.utils.serialize import row
QUEUE='solve-jobs'
def snapshot_now(db):
 hours=db.query(GridHour).order_by(GridHour.hour).all()
 if not hours: raise HTTPException(422,'请先录入逐小时电网画像')
 nums=[g.hour for g in hours]
 if nums!=list(range(len(nums))):
  missing=sorted(set(range(nums[-1]+1))-set(nums))
  raise HTTPException(422,'电网画像小时须从0开始连续，缺失：'+','.join(map(str,missing)))
 if len(nums)>CONFIG['limits']['max_hours']: raise HTTPException(422,'时域长度超出上限')
 exps=db.query(Experiment).order_by(Experiment.code).all()
 if not exps: raise HTTPException(422,'请先登记实验清单')
 if len(exps)>CONFIG['limits']['max_experiments']: raise HTTPException(422,'实验数量超出上限')
 grid=[{'hour':g.hour,'factor':g.factor,'base_load':g.base_load,'capacity':g.capacity} for g in hours]
 experiments=[{'code':e.code,'name':e.name,'windows':e.windows,'hours':e.hours,'power':e.power} for e in exps]
 return {'grid':grid,'experiments':experiments}
def checksum_of(snapshot):
 return hashlib.sha256(json.dumps(snapshot,sort_keys=True,ensure_ascii=False).encode()).hexdigest()
def queue(db,user,body):
 meta=get_meta(db,lock=True)  # 与源数据更新共用行锁：冻结快照与版本号一致，不采纳过期输入
 snapshot=snapshot_now(db);checksum=checksum_of(snapshot)
 existing=db.query(SolveRun).filter(SolveRun.checksum==checksum,SolveRun.status.in_(('queued','running'))).first()
 if existing: return existing  # 相同冻结输入已在求解：直接复用，不新增方案
 obj=SolveRun(name=body.name,status='queued',snapshot=snapshot,checksum=checksum,source_version=meta.version,created=time.time())
 db.add(obj);db.flush();log(db,user.email,'run.queue',f"#{obj.id} {body.name} 快照{checksum[:12]} 版本v{meta.version}");db.commit()
 redis.Redis.from_url(REDIS_URL).rpush(QUEUE,obj.id)
 return obj
def retry(db,user,id):
 obj=db.get(SolveRun,id)
 if not obj: raise HTTPException(404,'任务不存在')
 if obj.status!='failed': raise HTTPException(409,'仅失败任务可重试；重试沿用原任务与冻结快照，不新增方案')
 obj.status='queued';obj.error=None
 log(db,user.email,'run.retry',f"#{obj.id}");db.commit()
 redis.Redis.from_url(REDIS_URL).rpush(QUEUE,obj.id)
 return obj
def activate(db,user,id):
 meta=get_meta(db,lock=True)  # 与源数据更新共用行锁：并发启用/更新不会采纳过期排程
 obj=db.get(SolveRun,id)
 if not obj: raise HTTPException(404,'方案不存在')
 if obj.status!='completed' or not (obj.result or {}).get('feasible'): raise HTTPException(409,'仅可启用求解完成且可行的方案')
 if meta.active_run_id==obj.id: raise HTTPException(409,'该方案已是现行方案')
 if obj.source_version!=meta.version: raise HTTPException(409,'源数据已更新，该待生效方案已失效，请重新求解')
 meta.active_run_id=obj.id
 log(db,user.email,'run.activate',f"#{obj.id} {obj.name} 版本v{meta.version}");db.commit();return obj
def enrich(obj,meta):
 d=row(obj);d['active']=meta.active_run_id==obj.id
 d['stale']=not d['active'] and obj.source_version!=meta.version
 return d
