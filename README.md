# multi_agents_nav_offload

**星地网络下多机器人「路径规划 × 计算卸载」联合决策——在真实物理仿真中求解。**

---

## 研究问题

多机器人在移动中要把 SLAM、目标识别等任务送到边缘/卫星去算，但**移动会改变网络覆盖，覆盖又决定卸载能不能成**。DAOMAN（IEEE TVT 2026）首次把这个问题形式化并给出 attention-MATD3 + PPO 的解法，但它在无动力学的二维质点玩具环境里验证。

本项目保留它的问题，替换它的求解栈，并把整个问题搬进 NVIDIA Isaac Sim 的真实刚体动力学中。

### 核心假设

> 卸载决策的质量不由"每一步选本地/BS/卫星"决定，而由**路径层面的覆盖驻留机会**决定。
> 因此不应把卸载做成与导航并列的第二个 MDP（DAOMAN 的做法），而应把"覆盖—卸载效用"编码进**导航的观测表示**里，用一个统一的去中心化策略同时输出移动与卸载动作。

三条可证伪假设见 `plan.md` §3.2。

---

## 技术路线（三层）

| 层 | 内容 | 状态 |
|---|---|---|
| **L3 学习层** | 中心化专家（覆盖感知 LaCAM + 卸载分配）→ tokenize 成定长序列 → decoder-only Transformer 模仿学习 → 去中心化联合输出 move + offload ρ | 待 P3 |
| **L2 桥接层** | 栅格 MAPF ↔ 真实动力学的映射、局部轨迹跟踪、死锁恢复、时变覆盖图、任务队列与链路时延模型 | 待 P2 |
| **L1 物理层** | Isaac Sim 6.0.1 + GPU 物理（Warp/PhysX），差速 AGV 刚体，真实碰撞，域随机化，ROS 2 桥接 | 已验证可用 |

**为什么用模仿学习而不是强化学习**：不需要手工设计奖励函数，绕开了 DAOMAN 把"米"和"秒"直接加权相加（`w·r_move + (1-w)·r_offload`）的量纲难题，也不需要机器人在真实物理环境里做大规模 RL 探索。参考 MAPF-GPT（AAAI 2025）与 MAPF-GPT-DDG（IROS 2025）。

---

## 起点文献

| 文献 | 角色 |
|---|---|
| Dong et al. **DAOMAN**, IEEE TVT 75(3), 2026 | 问题起点 + 主要批判对象 |
| Andreychuk et al. **MAPF-GPT**, AAAI 2025 (arXiv:2409.00134) | 方法论来源（表示 + 数据 + 蒸馏） |
| Andreychuk et al. **MAPF-GPT-DDG**, IROS 2025 (arXiv:2506.23793) | 微调范式（避开 1B 数据集，显存受限下的主路线） |

完整清单见 `plan.md` §13。精读笔记在 `参考文献/notes/`。

---

## 本机环境（已实测，非文档值）

```
OS      Ubuntu 24.04.5 LTS
CPU     32 线程
RAM     30 GB
GPU     NVIDIA RTX 4060 Laptop, 8 GB VRAM, sm_89
驱动    595.84 / CUDA 12.9
Isaac Sim  6.0.1-rc.7  (/home/gsh/isaacsim, 27 GB)
IsaacLab   3.0.0        (/home/gsh/IsaacLab, 11 GB)  venv: env_isaaclab
ROS 2      未安装（Isaac Sim 的 ros2 bridge 扩展已就位）
磁盘       65 GB 可用
```

### 已完成的物理保真度扫描

零重力自由空间、dt = 1/60 s、0.2 m 立方体：

| 速度 m/s | 每步位移 | 最小中心间距 | 判定 |
|---|---|---|---|
| 1 / 2 / 4 / 8 / 16 | 0.017 – 0.267 m | ≈ 0.200 m（= 接触距离） | 正确碰撞 |
| 25 | 0.417 m | 0.037 m | 穿透 |

→ **AGV 真实速度区间（0.5–3 m/s）远在安全区内，无需开启 CCD。** 该数据可直接用作论文的仿真保真度验证。

---

## 仓库结构

```
plan.md            研究总方案（阶段 P0–P6、假设、Baseline、风险）
agents.md          对 AI 智能体的约束（三条铁律）
PROGRESS.md        进度看板
ASSUMPTIONS.md     假设日志（无文献依据的技术决策）
README.md          本文件
参考文献/
  notes/DAOMAN/close-reading.md
  notes/MAPF-GPT/close-reading.md
```

代码目录（`src/`）尚未建立，见 `PROGRESS.md`。

---

## 开发约定

**开工前请先读 `agents.md`。** 摘要：

1. **证据门槛** —— 任何技术决策必须有文献出处、用户批准，或记入 `ASSUMPTIONS.md`。禁止凭记忆引用数字和公式。
2. **小任务即提交** —— 以"一次可验证的改动"为单位，完成后立即提醒 commit，不等攒一堆。
3. **文档同步** —— 改动不落地到文档视为未完成。

不确定的技术决策一律写进 `ASSUMPTIONS.md`，不要默默实现。
