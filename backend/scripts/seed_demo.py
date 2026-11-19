import json
from src.config.database import Base,engine,Session
from src.models.identity import User
from src.models.source import GridHour,Experiment,Meta
from src.models import run
from src.utils.security import password_hash
from src.services.validation import validate_grid,validate_experiment
FACTORS=[0.42,0.40,0.38,0.38,0.40,0.45,0.52,0.58,0.55,0.48,0.40,0.34,0.30,0.30,0.33,0.42,0.52,0.62,0.78,0.82,0.75,0.62,0.52,0.46]
BASE=[12,11,10,10,11,12,14,15,16,15,14,13,13,13,14,14,15,16,16,15,14,13,12,12]
EXPERIMENTS=[
 {'code':'EXP-01','name':'材料烧结炉','windows':[[8,18]],'hours':3,'power':6.5},
 {'code':'EXP-02','name':'真空镀膜','windows':[[0,23]],'hours':4,'power':5},
 {'code':'EXP-03','name':'恒温老化','windows':[[0,6],[20,23]],'hours':2,'power':8},
 {'code':'EXP-04','name':'光谱标定','windows':[[9,17]],'hours':2,'power':4},
 {'code':'EXP-05','name':'电池循环测试','windows':[[0,23]],'hours':6,'power':7.5},
 {'code':'EXP-06','name':'超净间通风测试','windows':[[6,20]],'hours':3,'power':9},
 {'code':'EXP-07','name':'低温贮存复温','windows':[[12,23]],'hours':2,'power':3.5},
 {'code':'EXP-08','name':'振动台试验','windows':[[8,12],[14,19]],'hours':2,'power':11},
]
def seed():
 Base.metadata.create_all(engine)
 with Session() as db:
  for role in ('admin','analyst','viewer'):
   if not db.query(User).filter_by(email=role+'@demo.local').first():db.add(User(email=role+'@demo.local',role=role,password=password_hash('Demo2026!')))
  if not db.get(Meta,'source'):db.add(Meta(key='source',version=1,active_run_id=None))
  for hour in range(24):
   data=validate_grid({'hour':hour,'factor':FACTORS[hour],'base_load':BASE[hour],'capacity':40})
   if not db.query(GridHour).filter_by(hour=hour).first():db.add(GridHour(**data))
  for e in EXPERIMENTS:
   data=validate_experiment(e)
   if not db.query(Experiment).filter_by(code=data['code']).first():db.add(Experiment(**data))
  db.commit();print(json.dumps({'users':db.query(User).count(),'grid_hours':db.query(GridHour).count(),'experiments':db.query(Experiment).count()},ensure_ascii=False))
if __name__=='__main__':seed()
