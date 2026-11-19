import time,traceback
from pathlib import Path
import redis
from src.config.database import Base,engine,Session
from src.config.settings import REDIS_URL
from src.models import identity,source,run
from src.models.run import SolveRun
from src.services.solver import solve
QUEUE='solve-jobs';SLICE=100000  # 每片搜索节点数：片间持久化检查点，中断可恢复
Base.metadata.create_all(engine)
r=redis.Redis.from_url(REDIS_URL)
with Session() as db:  # 启动恢复：中断的running回到队列，凭progress检查点续算；queued补投，不新增方案
 db.query(SolveRun).filter(SolveRun.status=='running').update({'status':'queued'})
 db.commit()
 ids=[x.id for x in db.query(SolveRun).filter(SolveRun.status=='queued').all()]
 for i in ids: r.rpush(QUEUE,i)
 if ids: print('恢复未完成的求解任务:',ids,flush=True)
while True:
 Path('/tmp/worker-heartbeat').write_text(str(time.time()))
 try:
  item=r.lpop(QUEUE)
  if item:
   with Session() as db:
    job=db.get(SolveRun,int(item))
    if job and job.status=='queued':
     job.status='running';db.commit()
     try:
      state=job.progress
      while True:
       done,state,result=solve(job.snapshot['grid'],job.snapshot['experiments'],state,budget=SLICE)
       job.progress=dict(state)  # 触发JSON列更新，持久化检查点
       Path('/tmp/worker-heartbeat').write_text(str(time.time()))
       if done:
        job.result=result;job.status='completed';break
       db.commit()
      db.commit()
     except Exception as exc:
      db.rollback()
      with Session() as fix:
       broken=fix.get(SolveRun,job.id)
       if broken: broken.status='failed';broken.error=str(exc);fix.commit()
      traceback.print_exc()
 except Exception: traceback.print_exc()
 time.sleep(1)
