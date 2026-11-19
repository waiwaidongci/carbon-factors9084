# 初始结构

SQLAlchemy启动创建以下业务表：grid_hours（逐小时电力因子/基础负荷/容量上限，hour唯一）、experiments（实验编号/可开工窗口/连续小时/功率，code唯一）、solve_runs（求解任务：冻结快照、SHA256、源数据版本、结果、断点检查点）、plan_meta（单行：源数据版本号与现行方案run id）、users、audits。专属字段由validation严格校验；Run排队即冻结输入快照；plan_meta行锁串行化“源数据更新”和“启用方案”，版本不一致即拒绝启用过期排程。已有数据库升级需先备份，后续字段演进应以独立迁移执行。
