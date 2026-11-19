from sqlalchemy import Column,Integer,String,JSON,Text,Float
from src.config.database import Base
class SolveRun(Base):
 __tablename__='solve_runs'
 id=Column(Integer,primary_key=True); name=Column(String(120)); status=Column(String(20)); snapshot=Column(JSON); checksum=Column(String(64)); source_version=Column(Integer); result=Column(JSON); error=Column(Text); progress=Column(JSON); created=Column(Float)
