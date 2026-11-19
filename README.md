# 澄湖实验室碳感知排程台

实验用电避开高碳时段：录入逐小时电力因子/基础负荷/容量上限与实验窗口→冻结排队求解→核对时段与排放→启用现行方案

## 业务场景与工作流
模拟客户：澄湖研究协作组，12位实验与分析人员。实验室多台设备集中在傍晚高碳时段开工，月度用电排放居高不下。现由分析师录入逐小时电网画像（电力因子、基础负荷、容量上限）和实验清单（可开工窗口、连续小时数、功率），发起求解后由 Redis worker 用 Python 分支限界搜索**总排放最低**的排程，负责人核对各实验时段与排放量后启用为现行方案。原有流程靠人工抄表排班，痛点为高碳时段扎堆、容量叠加靠估算、方案变更无版本可追溯。

模块：业务总览、电网画像、实验清单、求解与方案、过程留痕。画像与实验可增改删；求解任务排队即冻结输入快照（SHA256+源数据版本）；每项实验只排一次且不中断，逐小时叠加负荷不超容量上限；同分按实验编号取最早开工序列；无解时给出冲突说明并保留现行方案；源数据更新后待生效方案失效，启用时校验版本，并发更新不采纳过期排程；求解分片落检查点，中断可恢复，重试沿用原任务不新增方案。

## 算法口径
分支限界搜索：实验按编号排序、开工小时升序枚举；逐小时叠加基础负荷与实验负荷，任一小时超容量即剪枝；以“已排排放+剩余实验各自最小排放”为下界剪枝；总排放=Σ逐小时（基础负荷+实验负荷）×电力因子；同分保留按实验编号顺序最早开工的序列（开工小时字典序最小）。因子与功率按×1000整数化，同分判定精确。算法实现在`backend/src/services/solver.py`（纯Python无依赖），输入校验在`validation.py`。无解时`diagnose`输出冲突：基础负荷自身超限、窗口容不下、功率处处超限、窗口强制叠加超限。未对接真实电网系统。

## 一天的验收剧本
1. 09:00 admin查看24小时电网画像（凌晨低、傍晚高的因子曲线）与8项seed实验。
2. 09:10 analyst修改13:00的电力因子，审计页可见源数据版本推进。
3. 09:20 analyst在“求解与方案”命名任务并排队：输入即冻结，worker数秒内完成。
4. 09:25 众人核对各实验开工/结束时段、单项排放量与逐小时叠加负荷（不超容量）。
5. 09:30 admin启用该方案为现行方案，总览页展示现行排程。
6. 09:40 analyst再次修改画像：未启用的已完成方案标记“已失效”，启用被拒绝；现行方案保留。
7. 09:50 analyst把某小时容量上限调到基础负荷之下重新求解：任务完成但无解，页面列出冲突说明，现行方案不变。
8. 10:00 重启worker容器：排队/求解中的任务自动恢复续算；对失败任务点重试，沿用原任务不新增方案。

## 快速启动
```sh
cp .env.example .env
docker compose up -d --build
docker compose exec -T backend python -m scripts.seed_demo
```
前端 http://localhost:18254 ，后端 http://localhost:19254/docs ，数据库宿主端口17754。中文父目录可用。恰好5服务frontend/backend/worker/db/redis；均有真实healthcheck。停止并清空演示数据：`docker compose down -v --remove-orphans`。

|角色|邮箱|密码|权限|
|---|---|---|---|
|admin|admin@demo.local|Demo2026!|画像与实验增改删、发起求解、启用方案|
|analyst|analyst@demo.local|Demo2026!|画像与实验增改删、发起求解与重试；无启用权限|
|viewer|viewer@demo.local|Demo2026!|只读；可查看方案与下载时段CSV|

## 工程结构与开发
Python3.11/FastAPI/SQLAlchemy/Redis，PostgreSQL16；前端原生HTML/CSS/JS ES modules，Nginx代理`/api/`剥前缀至后端。`frontend/src`按api/stores/pages/components/hooks/utils/router/constants/types拆分；`backend/src`按models/schemas/services/controllers/routes/middlewares/config/utils/constants拆分；`backend/scripts/seed_demo.py`自然键（hour/code）幂等且不覆盖用户修改。SQLAlchemy启动创建初始结构，迁移说明在backend/migrations。

后端开发：在backend安装requirements，设置DATABASE_URL/REDIS_URL/JWT_SECRET，`uvicorn src.main:app --reload`；前端可用Nginx或带同等代理的静态开发服务器。前后端全部业务计算在Python。

环境变量：COMPOSE_PROJECT_NAME、FRONTEND_PORT、BACKEND_PORT、DB_PORT、JWT_SECRET（部署替换）、DATABASE_URL、REDIS_URL、SEED_DEMO。`.env`不入Git。数据库/Redis/共享产物为命名卷。共享角色枚举admin/analyst/viewer与状态queued/running/completed/failed分别定义于backend/src/constants/enums.py和frontend/src/constants/enums.js。两个中间件：统一可恢复校验错误、每IP每分钟360请求限流。

## 已知边界
一名worker串行求解，任务FIFO；搜索按10万节点分片落检查点。时域上限48小时、实验12项、每实验8段窗口（project.json limits）。相同冻结输入重复排队会复用在途任务；已完成历史不查重。方案启用为单行元数据互斥，不保留多份现行方案。时间显示Asia/Shanghai。Google Fonts不可用时回退serif。JWT演示有效期2小时。

MIT License。

## 实际实体映射
电网画像（GridHour，hour唯一）、实验（Experiment，code唯一）、求解任务（SolveRun，冻结快照+源数据版本+断点检查点）、方案元数据（plan_meta单行：版本号与现行方案）均经数据库→模型→请求schema→service→route→frontend API→store→page。版本号随任何源数据变更递增；启用与源数据更新共用plan_meta行锁，过期排程不被采纳。

实际表：grid_hours、experiments、solve_runs、plan_meta、users、audits。
