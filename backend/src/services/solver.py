"""碳感知排程求解器：纯 Python 实现，无外部依赖，可单测。

规则：
- 每项实验只排一次且不中断（连续 hours 小时）；
- 开工小时须落在任一可开工窗口内，且整段不超出电网画像时域；
- 逐小时叠加 基础负荷+实验负荷 不得超过容量上限；
- 目标为总排放最低：Σ 逐小时(基础负荷+实验负荷)×电力因子；
- 同分按实验编号顺序取最早开工序列（开工小时字典序最小）。

实现：实验按编号排序后做分支限界深度优先搜索，开工小时升序枚举，
整数化（×1000）保证同分判定精确；下界=已排排放+剩余实验各自最小排放。
state 可 JSON 序列化，求解中断后可从检查点恢复，重试不新增方案。
"""
import time

SCALE = 1000  # kW→W、kgCO2e→gCO2e 的整数化比例，排放内部单位为 1e-6 kg

METHOD = ('分支限界搜索：实验按编号排序、开工小时升序枚举；逐小时叠加基础负荷与实验负荷，'
          '任一小时超容量即剪枝；以“已排排放+剩余实验各自最小排放”为下界剪枝；'
          '总排放=Σ逐小时(基础负荷+实验负荷)×电力因子；同分保留按实验编号顺序最早开工的序列。')


def _span_starts(exp, horizon):
    """窗口与时域求交后的全部候选开工小时（不考虑容量）。"""
    starts = set()
    for lo, hi in exp['windows']:
        for s in range(lo, hi + 1):
            if 0 <= s and s + exp['hours'] <= horizon:
                starts.add(s)
    return sorted(starts)


def _candidates(grid, experiments):
    """每个实验的候选开工小时：窗口∩时域，且单实验叠加基础负荷不超容量。"""
    horizon = len(grid)
    base_w = [int(round(g['base_load'] * SCALE)) for g in grid]
    cap_w = [int(round(g['capacity'] * SCALE)) for g in grid]
    spans, cands = [], []
    for e in experiments:
        pw = int(round(e['power'] * SCALE))
        span = _span_starts(e, horizon)
        spans.append(span)
        cands.append([s for s in span
                      if all(base_w[h] + pw <= cap_w[h] for h in range(s, s + e['hours']))])
    return spans, cands


def solve(grid, experiments, state=None, budget=100000):
    """执行求解。返回 (done, state, result)；done=False 时 result 为 None，可凭 state 续算。

    grid: [{'hour','factor','base_load','capacity'}...] 按 hour 升序且从0连续；
    experiments: [{'code','name','windows','hours','power'}...] 按 code 升序；
    budget: 本次调用允许的搜索节点数（切片求解，便于检查点持久化与中断恢复）。
    """
    horizon = len(grid)
    n = len(experiments)
    base_w = [int(round(g['base_load'] * SCALE)) for g in grid]
    cap_w = [int(round(g['capacity'] * SCALE)) for g in grid]
    fac = [int(round(g['factor'] * SCALE)) for g in grid]
    pref = [0] * (horizon + 1)
    for h in range(horizon):
        pref[h + 1] = pref[h] + fac[h]
    pw = [int(round(e['power'] * SCALE)) for e in experiments]
    dur = [e['hours'] for e in experiments]
    _, cands = _candidates(grid, experiments)
    if state is None:
        state = {'starts': [], 'ptrs': [0], 'best_cost': None, 'best': None,
                 'nodes': 0, 'elapsed': 0.0}
    if any(base_w[h] > cap_w[h] for h in range(horizon)):
        # 基础负荷自身已超限：任何排程都不可行
        return True, state, _result(grid, experiments, None, None, state)
    starts, ptrs = state['starts'], state['ptrs']
    best_cost, best = state['best_cost'], state['best']
    loads = [0] * horizon
    for i, s in enumerate(starts):  # 续算时按检查点重放部分排程
        for h in range(s, s + dur[i]):
            loads[h] += pw[i]
    partial = sum((base_w[h] + loads[h]) * fac[h] for h in range(horizon))
    minc = [0] * n
    for i in range(n):
        if cands[i]:
            minc[i] = min(pref[s + dur[i]] - pref[s] for s in cands[i]) * pw[i]
    suffix = [0] * (n + 1)
    for i in range(n - 1, -1, -1):
        suffix[i] = suffix[i + 1] + minc[i]
    t0 = time.perf_counter()
    done = False
    used = 0
    while True:
        if used >= budget:
            break
        d = len(starts)
        if d == n:  # 叶子：完整排程，严格更优才替换 ⇒ 同分保留字典序最小者
            state['nodes'] += 1
            used += 1
            if best_cost is None or partial < best_cost:
                best_cost, best = partial, list(starts)
            s = starts.pop()
            ptrs.pop()
            i = d - 1
            for h in range(s, s + dur[i]):
                loads[h] -= pw[i]
            partial -= (pref[s + dur[i]] - pref[s]) * pw[i]
            ptrs[-1] += 1
            continue
        i = d
        placed = False
        while ptrs[d] < len(cands[i]):
            s = cands[i][ptrs[d]]
            feasible = True
            for h in range(s, s + dur[i]):
                if base_w[h] + loads[h] + pw[i] > cap_w[h]:
                    feasible = False
                    break
            if feasible:
                add = (pref[s + dur[i]] - pref[s]) * pw[i]
                if best_cost is None or partial + add + suffix[i + 1] < best_cost:
                    placed = True
                    break
            ptrs[d] += 1
        if placed:
            starts.append(s)
            ptrs.append(0)
            for h in range(s, s + dur[i]):
                loads[h] += pw[i]
            partial += add
            state['nodes'] += 1
            used += 1
            continue
        if d == 0:
            done = True
            break
        s = starts.pop()
        ptrs.pop()
        i = d - 1
        for h in range(s, s + dur[i]):
            loads[h] -= pw[i]
        partial -= (pref[s + dur[i]] - pref[s]) * pw[i]
        ptrs[-1] += 1
    state['elapsed'] = state.get('elapsed', 0.0) + (time.perf_counter() - t0)
    state['starts'], state['ptrs'] = starts, ptrs
    state['best_cost'], state['best'] = best_cost, best
    if not done:
        return False, state, None
    return True, state, _result(grid, experiments, best, best_cost, state)


def _result(grid, experiments, best, best_cost, state):
    horizon = len(grid)
    base_cost = sum(int(round(g['base_load'] * SCALE)) * int(round(g['factor'] * SCALE))
                    for g in grid)
    summary_base = {'实验数': len(experiments), '搜索节点': state['nodes'],
                    '求解毫秒': round(state['elapsed'] * 1000, 1)}
    if best is None:
        return {'feasible': False, 'conflicts': diagnose(grid, experiments),
                'summary': summary_base, 'method': METHOD}
    exp_load = [0] * horizon
    who = [[] for _ in range(horizon)]
    schedule = []
    for e, s in zip(experiments, best):
        span_factor = sum(g['factor'] for g in grid[s:s + e['hours']])
        emissions = e['power'] * span_factor
        schedule.append({'code': e['code'], 'name': e['name'], 'start': s,
                         'end': s + e['hours'], 'hours': e['hours'], 'power': e['power'],
                         'emissions': round(emissions, 6)})
        for h in range(s, s + e['hours']):
            exp_load[h] += e['power']
            who[h].append(e['code'])
    hourly = []
    for h, g in enumerate(grid):
        total = g['base_load'] + exp_load[h]
        hourly.append({'hour': g['hour'], 'factor': g['factor'],
                       'base_load': g['base_load'], 'exp_load': round(exp_load[h], 3),
                       'total': round(total, 3), 'capacity': g['capacity'],
                       'slack': round(g['capacity'] - total, 3),
                       'experiments': ','.join(who[h]) if who[h] else '—',
                       'emissions': round(total * g['factor'], 6)})
    summary = {'总排放kgCO2e': round(best_cost / SCALE ** 2, 6),
               '基础负荷排放kgCO2e': round(base_cost / SCALE ** 2, 6),
               '实验用电排放kgCO2e': round((best_cost - base_cost) / SCALE ** 2, 6)}
    summary.update(summary_base)
    return {'feasible': True, 'schedule': schedule, 'hourly': hourly,
            'summary': summary, 'method': METHOD}


def diagnose(grid, experiments):
    """无解时的冲突说明：先查单点冲突，再查窗口强制叠加冲突，最后给兜底说明。"""
    horizon = len(grid)
    spans, cands = _candidates(grid, experiments)
    issues = []
    for g in grid:
        if g['base_load'] > g['capacity']:
            issues.append(f"第{g['hour']}小时基础负荷{g['base_load']}kW已超过容量上限{g['capacity']}kW")
    for e, span, cand in zip(experiments, spans, cands):
        if not span:
            issues.append(f"实验{e['code']}的可开工窗口在{horizon}小时时域内容纳不下连续{e['hours']}小时")
        elif not cand:
            issues.append(f"实验{e['code']}功率{e['power']}kW叠加基础负荷后，在所有可开工时段均超容量上限")
    if issues:
        return issues
    for h in range(horizon):
        forced = [e for e, cand in zip(experiments, cands)
                  if all(s <= h < s + e['hours'] for s in cand)]
        need = sum(e['power'] for e in forced)
        g = grid[h]
        if forced and g['base_load'] + need > g['capacity']:
            codes = '、'.join(e['code'] for e in forced)
            issues.append(f"第{g['hour']}小时：{codes}的可开工窗口均覆盖该小时，"
                          f"叠加后负荷{round(g['base_load'] + need, 3)}kW超容量上限{g['capacity']}kW")
    if not issues:
        issues.append('各实验单独均可安排，但叠加负荷约束下不存在可行排程；'
                      '请放宽可开工窗口、下调功率或提高容量上限')
    return issues
