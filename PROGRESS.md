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

## 进行中

无。（等待「下一步」的决策）

---

## 待办（按推荐顺序）

| 优先级 | 任务 | 前置 |
|---|---|---|
| 1 | **定 Isaac Sim core API 选型**（`A-001`：新 `experimental.*` vs 废弃中的 `core.api`） | 写代码前必须定 |
| 2 | **P1.0 垂直切片**：一台差速 AGV + 最小场景 + ROS 2 `/cmd_vel` 闭环 | 决策 1 + 装 ROS 2 Jazzy |
| 3 | P0.2–P0.4 DAOMAN 复现（可与 2 并行，纯 PyTorch） | 无 |
| 4 | 精读 Nagai & Okumura 2026《From Gridworlds to Warehouses》 | 无 |
| 5 | P1.2 场景搭建（室内仓库 + 室外堆场） | `A-006` 拍板 |
| 6 | P1.5/P1.6 覆盖与通信模型、计算任务模型 | P1.0 |

---

## 待用户拍板的决策（`plan.md` §12）

| # | 问题 | 状态 |
|---|---|---|
| 1 | 场景：室内仓库+室外堆场混合 vs 纯室外 | ⏳ 未答（`A-006`） |
| 2 | Isaac Sim core API：新 vs 旧 | ⏳ 未答（`A-001`） |
| 3 | ROS 2 Jazzy 还是 Humble | ⏳ 未答（倾向 Jazzy） |
| 4 | 目标机器人数（建议先 8 台） | ⏳ 未答 |
| 5 | 是否要求实机验证 | ⏳ 未答 |
| 6 | P5 进阶技术做几项 | ⏳ 未答 |
| 7 | 目标 venue / deadline | ⏳ 未答 |

---

## 最近 commit

```
（尚未产生 commit —— 首次提交待用户确认）
```

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
