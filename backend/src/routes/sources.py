from fastapi import APIRouter,Depends
from src.config.database import database
from src.controllers.auth import current,editor
from src.models.source import GridHour,Experiment
from src.schemas.requests import DataInput
from src.services.source import save_grid,delete_grid,save_experiment,delete_experiment,get_meta
from src.utils.serialize import row
router=APIRouter()
@router.get('/grid')
def grid(db=Depends(database),u=Depends(current)): return [row(x) for x in db.query(GridHour).order_by(GridHour.hour).all()]
@router.post('/grid')
def grid_create(b:DataInput,db=Depends(database),u=Depends(editor)): return row(save_grid(db,u,b.data))
@router.put('/grid/{id}')
def grid_update(id:int,b:DataInput,db=Depends(database),u=Depends(editor)): return row(save_grid(db,u,b.data,id))
@router.delete('/grid/{id}')
def grid_delete(id:int,db=Depends(database),u=Depends(editor)): delete_grid(db,u,id);return {'deleted':id}
@router.get('/experiments')
def experiments(db=Depends(database),u=Depends(current)): return [row(x) for x in db.query(Experiment).order_by(Experiment.code).all()]
@router.post('/experiments')
def experiment_create(b:DataInput,db=Depends(database),u=Depends(editor)): return row(save_experiment(db,u,b.data))
@router.put('/experiments/{id}')
def experiment_update(id:int,b:DataInput,db=Depends(database),u=Depends(editor)): return row(save_experiment(db,u,b.data,id))
@router.delete('/experiments/{id}')
def experiment_delete(id:int,db=Depends(database),u=Depends(editor)): delete_experiment(db,u,id);return {'deleted':id}
@router.get('/meta')
def meta(db=Depends(database),u=Depends(current)):
 m=get_meta(db);return {'version':m.version,'active_run_id':m.active_run_id}
