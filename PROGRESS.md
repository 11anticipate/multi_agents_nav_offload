# PROGRESS.md — 进度看板

> 每个小任务完成后更新本文件。**最近一次同步**：2026-09-18

---

## 当前状态

**阶段**：P0 / P1 交界
**已完成**：立项、文献精读、环境可行性验证、仓库搭建
**下一步**：见文末「下一步」

```
P0 立项与基线      ▓▓▓░░░░░░░  文献精读完成，DAOMAN 代码复现未开始
P1 物理仿真底座    ▓▓▓▓░░░░░░  可行性已验证，垂直切片未开始
P2 栅格与专家      ░░░░░░░░░░  未开始
P3 表示与模型      ░░░░░░░░░░  未开始
P4 闭环评估        ░░░░░░░░░░  未开始
P5 进阶技术        ░░░░░░░░░░  未开始
P6 论文            ░░░░░░░░░░  未开始
```

---

## 已完成的小任务

| # | 日期 | 内容 | 产出 |
|---|---|---|---|
| P0.0a | 2026-09-18 | 精读 DAOMAN 与 MAPF-GPT（既有笔记） | 两份 close-reading（早于本次） |
| P0.0b | 2026-09-18 | Zotero 文献调研，筛出 13 篇直接相关 | `plan.md` §13 |
| P0.0c | 2026-09-18 | 外部核验：Isaac Sim 6.0 GA、MAPF-GPT-DDG、STEAM、HMAGAT | `plan.md` §2 |
| P0.0d | 2026-09-18 | 撰写研究方案与智能体约束 | `plan.md`、`agents.md` |
| **P1.1** | **2026-09-18** | **环境可行性验证** —— headless 启动 / GPU 物理 / 刚体碰撞全部通过 | `plan.md` §10.2 |
| P1.1b | 2026-09-18 | 碰撞保真度速度扫描（1–25 m/s） | `plan.md` §10.2、`ASSUMPTIONS.md` A-002 |
| P0.1 | 2026-09-18 | 仓库初始化并接入 `multi_agents_nav_offload` | `.git`、`.gitignore` |
| P0.1b | 2026-09-18 | 建立项目文档骨架 | `README.md`、`ASSUMPTIONS.md`、本文件 |

---

## 已完成（S1 合同测试全部跑完，2026-09-18）

| # | 日期 | 内容 | 结果 |
|---|---|---|---|
| S1.0 | 2026-09-18 | 新 Core API 面 + 签名核对 | PASS，13 个类全部存在 |
| S1.1 | 2026-09-18 | Falling Cube（含 T1/T1b/T5） | **ALL PASS**，确定性 max\|Δ\|=0 |
| S1.2 | 2026-09-18 | 1–25 m/s 碰撞扫描（含 CCD 对照） | 记录；低速区间结论成立 |
| S1.3 | 2026-09-18 | 生命周期（Restart / Existing Stage） | **ALL PASS** |
| S1.4 | 2026-09-18 | 基线报告落盘 | `docs/P1.0-core-probe.md` |

**关键结论**：新 Core 可独立支撑 P1.0。推进方式定为 **先 `app_utils.play()`，
之后 `simulation_app.update()`（主）或 `SimulationManager.step(steps=N)`（需手动步进时）**。

⚠️ **推进方式原计划是 (a) `step()`，实测必须改为 (b) 前置 `play()`** —— 单独 `step()` 不驱动物理。
这一条已写入 `agents.md` §9.1，后续所有仿真代码都要遵守。

## 进行中

无。（S1 已完成，等 S2–S7 放行）

---

## 待办（按推荐顺序）

| 优先级 | 任务 | 前置 |
|---|---|---|
| 1 | 装 ROS 2 Jazzy（发行版确认：强烈倾向 Jazzy） | 用户确认 |
| 2 | S2 差速 AGV 选型与导入 | 用户确认资产来源 |
| 3 | S3 最小场景 / S4 差速控制（含 `DifferentialController` contract） | S2 |
| 4 | S5 ROS 2 桥接 / S6 闭环验收 | ROS 2 装好 |
| 5 | P0.2–P0.4 DAOMAN 复现（可并行，纯 PyTorch） | 无 |
| 6 | 精读 Nagai & Okumura 2026《From Gridworlds to Warehouses》 | 无 |
| 7 | P1.2 场景搭建（室内仓库 + 室外堆场） | `A-006` 拍板 |

---

## 待用户拍板的决策（`plan.md` §12）

| # | 问题 | 状态 |
|---|---|---|
| 1 | 场景：室内仓库+室外堆场混合 vs 纯室外 | ⏳ 未答（`A-006`） |
| 2 | ~~Isaac Sim core API：新 vs 旧~~ | ✅ **已定：新 core**（`A-001` 已 RESOLVED） |
| 3 | ROS 2 Jazzy 还是 Humble | ⏳ 未答（**强烈倾向 Jazzy**，Humble 有静默丢数据风险） |
| 4 | 目标机器人数（建议先 8 台） | ⏳ 未答 |
| 5 | 是否要求实机验证 | ⏳ 未答 |
| 6 | P5 进阶技术做几项 | ⏳ 未答 |
| 7 | 目标 venue / deadline | ⏳ 未答 |
| 8 | S1 产物归属：`/tmp` 还是进仓库（建议分层） | ⏳ 未答（`A-009`） |

---

## 最近 commit

```
7579620  feat(project): 立项并建立「导航 × 计算卸载」研究仓库   → origin/main
         2026-09-18 · 9 files, +2207
```

**提醒**：以上为**初始化提交**，属一次性特例。此后的每个小任务按 `agents.md` 铁律二处理 ——
由智能体 `git diff` 自查后**提醒你提交并等待确认**，不再代提交。

## 环境快照

```
远程  origin → git@github.com:11anticipate/multi_agents_nav_offload.git (main)
本地  /home/gsh/Documents/多智能体强化学习
Isaac Sim 6.0.1-rc.7  |  IsaacLab 3.0.0  |  RTX 4060 Laptop 8GB  |  Ubuntu 24.04
ROS 2                 未安装
磁盘                  65 GB 可用
```

---

## 下一步

**推荐做 P1.0 垂直切片**（一台 AGV + ROS 2 `/cmd_vel` 端到端跑通），而不是先铺开整个仓库场景。
理由：单独抠"碰撞检测"容易滚成没有研究产出的环境工程；垂直切片才能暴露真正未知的
Isaac Sim ↔ ROS 2 ↔ 低层控制环节。开始前需先定决策 #2（core API）并安装 ROS 2 Jazzy。
