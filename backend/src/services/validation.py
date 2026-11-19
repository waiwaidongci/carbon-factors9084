import math,re
from src.config.settings import CONFIG
LIMITS=CONFIG['limits']
def number(value,name,minimum=0,maximum=None,integer=False):
 if isinstance(value,bool) or not isinstance(value,(int,float)) or not math.isfinite(value): raise ValueError(name+'需为有限数值')
 if value<minimum or (maximum is not None and value>maximum): raise ValueError(name+'超出允许范围')
 if integer and int(value)!=value: raise ValueError(name+'需为整数')
 if not integer and abs(value*1000-round(value*1000))>1e-6: raise ValueError(name+'最多三位小数')
 return int(value) if integer else round(value,3)
def validate_grid(d):
 if not isinstance(d,dict) or set(d)!={'hour','factor','base_load','capacity'}: raise ValueError('电网画像字段需为 hour/factor/base_load/capacity')
 return {'hour':number(d['hour'],'小时',0,LIMITS['max_hours']-1,integer=True),'factor':number(d['factor'],'电力因子',0,5),'base_load':number(d['base_load'],'基础负荷',0,100000),'capacity':number(d['capacity'],'容量上限',0,100000)}
def validate_experiment(d):
 if not isinstance(d,dict) or set(d)!={'code','name','windows','hours','power'}: raise ValueError('实验字段需为 code/name/windows/hours/power')
 code=d['code']
 if not isinstance(code,str) or not re.fullmatch(r'[0-9A-Za-z\-_]{1,40}',code): raise ValueError('实验编号需为1-40位字母、数字、连字符')
 name=d['name']
 if not isinstance(name,str) or not 1<=len(name.strip())<=120: raise ValueError('实验名称需为1-120字')
 hours=number(d['hours'],'连续小时数',1,LIMITS['max_hours'],integer=True)
 power=number(d['power'],'功率',0.001,100000)
 windows=d['windows']
 if not isinstance(windows,list) or not 1<=len(windows)<=LIMITS['max_windows']: raise ValueError('可开工窗口需为1-'+str(LIMITS['max_windows'])+'段')
 norm=set()
 for w in windows:
  if not isinstance(w,(list,tuple)) or len(w)!=2: raise ValueError('可开工窗口需为[起始小时,截止小时]')
  lo=number(w[0],'窗口起始',0,LIMITS['max_hours']-1,integer=True);hi=number(w[1],'窗口截止',0,LIMITS['max_hours']-1,integer=True)
  if lo>hi: raise ValueError('窗口起始小时不能晚于截止小时')
  norm.add((lo,hi))
 return {'code':code,'name':name.strip(),'windows':[list(w) for w in sorted(norm)],'hours':hours,'power':power}
