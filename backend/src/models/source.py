from sqlalchemy import Column,Integer,String,JSON,Float
from src.config.database import Base
class GridHour(Base):
 __tablename__='grid_hours'
 id=Column(Integer,primary_key=True); hour=Column(Integer,unique=True); factor=Column(Float); base_load=Column(Float); capacity=Column(Float)
class Experiment(Base):
 __tablename__='experiments'
 id=Column(Integer,primary_key=True); code=Column(String(40),unique=True); name=Column(String(120)); windows=Column(JSON); hours=Column(Integer); power=Column(Float)
class Meta(Base):
 __tablename__='plan_meta'
 key=Column(String(40),primary_key=True); version=Column(Integer); active_run_id=Column(Integer)
