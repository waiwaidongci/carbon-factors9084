from fastapi import APIRouter,Depends,HTTPException
from fastapi.responses import Response
from src.config.database import database
from src.controllers.auth import current,editor,admin
from src.models.run import SolveRun
from src.schemas.requests import RunInput
from src.services.plan import queue,retry,activate,enrich
from src.services.source import get_meta
from src.services.export import csv_text
router=APIRouter()
@router.get('/runs')
def runs(db=Depends(database),u=Depends(current)):
 meta=get_meta(db)
 return [enrich(x,meta) for x in db.query(SolveRun).order_by(SolveRun.id.desc()).all()]
@router.post('/runs')
def create(b:RunInput,db=Depends(database),u=Depends(editor)):
 obj=queue(db,u,b);return enrich(obj,get_meta(db))
@router.get('/runs/{id}')
def detail(id:int,db=Depends(database),u=Depends(current)):
 obj=db.get(SolveRun,id)
 if not obj: raise HTTPException(404,'任务不存在')
 return enrich(obj,get_meta(db))
@router.post('/runs/{id}/retry')
def rerun(id:int,db=Depends(database),u=Depends(editor)):
 meta=get_meta(db);return enrich(retry(db,u,id),meta)
@router.post('/runs/{id}/activate')
def enable(id:int,db=Depends(database),u=Depends(admin)):
 meta=get_meta(db);return enrich(activate(db,u,id),meta)
@router.get('/runs/{id}/csv')
def download(id:int,db=Depends(database),u=Depends(current)):
 obj=db.get(SolveRun,id)
 if not obj or obj.status!='completed' or not (obj.result or {}).get('feasible'): raise HTTPException(409,'仅可导出求解完成且可行的方案')
 rows=[{'实验编号':x['code'],'实验名称':x['name'],'开工小时':x['start'],'结束小时':x['end'],'连续小时':x['hours'],'功率kW':x['power'],'排放kgCO2e':x['emissions']} for x in obj.result['schedule']]
 return Response(csv_text(rows),media_type='text/csv',headers={'Content-Disposition':f'attachment; filename="schedule-{id}.csv"'})
