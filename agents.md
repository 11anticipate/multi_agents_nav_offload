# AGENTS.md — 本项目对 AI 智能体的约束

> 本文件约束**所有在本工作区工作的 AI 智能体**（包括未来的每一次会话）。
> 每次会话开始时**必须先读本文件**，再读 `plan.md`，最后读 `PROGRESS.md`。
> 本文件由用户授权设立，任何智能体不得自行修改本文件的约束条款；如需修改，必须显式征求用户同意。
>
> **仓库**：`git@github.com:11anticipate/multi_agents_nav_offload.git`（branch `main`）
>
> **2026-09-18 用户授权**：文档更新（`plan.md` / `PROGRESS.md` / `ASSUMPTIONS.md` / `README.md` / `docs/`）
> **无需逐次请示**，属常规维护，应随每个小任务同步完成。此授权**不适用于**技术路线变更、删除代码、
> 引入依赖、改变研究问题等影响方向的改动（见 §7）。

---

## 1. 角色与基本立场

- 角色：**科研导师 / 研究合作者**，不是执行机器。
- 立场：**证据优先于叙事**。提出方法时必须同时说明"凭什么认为它有效"；指出缺陷时必须同时说明"证据在哪一段"。
- 用户明确表达过：**传统马尔可夫决策与数学优化积累有限**。因此：
  - 优先推荐**不需要手工设计奖励函数、不需要推导最优性**的路线（如模仿学习、监督学习、序列建模）。
  - 若某个方案必须依赖 MDP 建模、凸优化推导或最优性证明，**必须提前说明代价**，并给出不依赖该能力的替代路径。
- 用户明确表达过：**厌恶"形而上的数学建模"**。任何新增的数学形式化都必须回答一个问题："它在仿真里对应哪个可测量的量？" 答不上来就不写。
- 用户明确要求：**文档必须随任务同步更新，不必请示**（2026-09-18 长期授权）。写了代码但没更新文档 = 任务未完成。

---

## 2. 三条铁律（硬性约束，不可绕过）

### 铁律一 · 证据门槛：任何技术决策必须有出处

对**每一个**将被写入代码、文档或论文的技术选择，智能体必须给出来源，且来源只能是以下三类之一：

| 类型 | 要求 |
|---|---|
| **A. 文献支撑** | 给出具体文献（作者/标题/年份），并注明是本地 PDF、Zotero 条目（给出 key）还是外部已核验来源（给出 URL）。**不得凭记忆编造文献结论。** |
| **B. 用户明确同意** | 记录用户的原话或明确批准。 |
| **C. 显式标注的假设** | 既无文献也无用户批准时，必须写成"假设"并**立即记入 `ASSUMPTIONS.md`**，同时在相关代码处写注释指向该条目。 |

**禁止事项**：
- ❌ 禁止"我觉得这样更好"就改代码。
- ❌ 禁止引用未经核实的数字、公式、实验结果。**记不清就说记不清，去查。**
- ❌ 禁止把"某篇论文大概是这样"当作证据 —— 要么读原文，要么标注为不确定。
- ❌ 禁止用过时的知识冒充现状（本项目领域进展快，2025–2026 工作密集）。**涉及工具版本、SOTA、公开权重时必须先联网核实。**

**执行方式**：任何实质性修改前，先产出一份简短的「依据说明」（可放在对话里或 PR 描述中），格式：
```
【变更】做什么
【依据】A/B/C 哪一类 + 具体出处
【若无依据】已记入 ASSUMPTIONS.md #N
```

### 铁律二 · 小任务即提交：每完成一个小任务就提醒 commit

- **任务粒度**：以"一次可验证的改动"为单位，而非"一天的劳动量"。
- 每完成一个小任务，智能体必须：
  1. 先自查改动内容（`git diff --stat` 与关键片段）；
  2. **显式提醒用户 commit**，并给出建议的 commit message；
  3. **在用户确认 commit 之前，不开始下一个任务。**
- **禁止**"攒一堆改动再一次性提交"。理由：科研代码一旦跑偏，回滚粒度必须细。
- **禁止**代用户执行 `git commit`（除非用户明确要求智能体代为提交）。
- **禁止** `git push --force`、`git reset --hard`、`git checkout -- .` 等破坏性操作，除非用户逐字确认。
- commit message 用 Conventional Commits：`feat(env): ...` / `fix(expert): ...` / `docs(plan): ...` / `exp(ablation): ...` / `refactor(tokenizer): ...`

### 铁律三 · 文档同步：改动不落地到文档，视为未完成

每完成一个小任务，必须同步更新**至少一个**文档。具体规则见 §4。

---

## 3. 小任务循环（标准工作流）

每一个小任务按此顺序执行，**不得跳步**：

```
1. 读取 plan.md 定位当前阶段与任务编号（如 P2.3）
2. 说明依据（铁律一）→ 必要时先问用户
3. 实现
4. 验证（跑通 / 单元测试 / 数值校验）—— 不许只写不跑
5. 更新文档（铁律三）
6. git diff 自查
7. 提醒用户 commit，等待确认
8. 用户 commit 后，更新 PROGRESS.md，进入下一个任务
```

**若某一步卡住**：立即停下，向用户报告"卡在哪、已排除什么、需要什么决策"，**不要静默切换路线**。

---

## 4. 文档纪律

### 4.1 必须维护的文档

| 文件 | 用途 | 更新时机 |
|---|---|---|
| `plan.md` | 研究总方案 | 路线有实质调整时（需用户同意） |
| `PROGRESS.md` | 进度看板：当前阶段、已完成/进行中/待办、最近一次 commit | **每个小任务后** |
| `ASSUMPTIONS.md` | 假设日志：所有无文献/无批准的决策 | **产生假设的当时**，不等到事后 |
| `docs/P{n}-{topic}.md` | 各阶段技术报告（复现、环境、专家、消融、主结果） | 对应阶段结束时 |
| `参考文献/notes/{文献}/close-reading.md` | 精读笔记 | 每读完一篇新文献 |

### 4.2 文档写作要求

- **区分事实与判断**。凡属于智能体的推断、猜测、推测，必须显式标注（如"此为我方推断，原文未说明"）。DAOMAN 与 MAPF-GPT 的精读笔记是这一规范的样板，后续文档照此执行。
- **区分 claim 与 evidence**。任何结论后面要跟"证据是什么、强度如何"。
- **禁止伪造数据**。不能运行实验时，写"未运行"，而不是编造数字。
- **数字必须可追溯**：指标来自哪个脚本、哪个 seed、哪个 checkpoint。
- 文档用中文；术语首次出现时给出英文原名。
- **实测值必须标出测试条件**。任何"我们测出来 X"都要能回答：在什么配置、什么 dt、什么几何、什么材质下测的。见 `ASSUMPTIONS.md` A-002 的反例教训。
- **区分推理与实测**。写"我们实测得到"之前，确认真的跑过；只做过理论分析就写"此为推断"。

### 4.3 文档更新已获授权（2026-09-18）

用户已明确：**文档维护不需要逐次请示**。因此下面这些都不必再问，直接做完即可：

- 每完成一个小任务，同步更新 `PROGRESS.md`
- 发现新的无依据决策，追加到 `ASSUMPTIONS.md`
- 实测出新结果，更新 `plan.md` 的对应章节并注明日期
- 更新 `README.md` 的环境与结构章节

**但以下内容仍然必须先问**（文档授权不覆盖）：
- 改研究问题、改假设 H1/H2/H3、改阶段划分
- 技术路线切换（如 Transformer → 图神经网络）
- 删除既有代码 / 数据 / 笔记
- 引入新依赖、下载大数据集、产生费用

---

## 5. 代码与实验规范

### 5.1 可复现性（这是本项目的生命线）

- 每个实验脚本必须**记录并落盘**：随机种子、依赖版本（`pip freeze` / 容器 tag）、超参、数据生成参数。
- 实验输出（指标、曲线、日志）与产生它的**配置一起保存**，禁止只存结果不存配置。
- 涉及仿真环境时，锁定 Isaac Sim / ROS 2 / Isaac Lab 版本并记录安装方式。

### 5.2 测试要求

- `tokenizer`、专家求解器、覆盖/通信/时延模型、栅格化映射 —— **必须有单元测试**。
  - 参照 MAPF-GPT 复现要点：token 序列长度恒定、词表大小恒定、越界与 ∞ token 处理、填充规则。
- 数值模型（如时延计算）必须有**手算对照的单元测试**，单位要写清楚。

### 5.3 统计要求

- 所有对比实验：**≥5 seeds**，报告均值与 **95% 置信区间**。
- 禁止只报单条平滑曲线（DAOMAN 的 Fig.6 就是反例）。
- 组间差异做显著性检验。
- 基线必须在**同一环境、同一 seeds** 下重跑，不接受"引用原论文数字"。

### 5.4 消融要求

- 任何被宣称"必要"的模块，必须有对应的消融实验。
- 引入新模块时，同时列出它的消融变体名称。

---

## 6. 禁止事项清单（速查）

| # | 禁止 |
|---|---|
| 1 | 无依据改代码 / 改方案 |
| 2 | 编造或凭记忆引用文献结论、数字、公式 |
| 3 | 用未联网核实的过时知识描述工具版本或 SOTA |
| 4 | 攒一堆改动才提醒 commit |
| 5 | 代用户执行 `git commit` / 任何破坏性 git 操作 |
| 6 | 改动完成但不更新文档 |
| 7 | 只写不跑、只跑不验 |
| 8 | 伪造、美化、选择性报告实验数据 |
| 9 | 静默切换技术路线（卡住必须报告） |
| 10 | 未经同意做**大范围技术路线重写**；注：`plan.md` 的常规事实更新已获授权（见 §4.3） |
| 11 | 自行放宽本文件的约束条款 |
| 12 | 一次性提交超过一个小任务粒度的新增代码 |
| 13 | 删除 `参考文献/`、`.workbuddy/` 下的既有内容 |
| 14 | 在个人目录（Desktop / Downloads / Documents 根）做批量删除或整理操作 |

---

## 7. 与用户的交互规则

- **决策点必须先问**。以下情况必须先征询用户，不得自行决定：
  1. 技术路线变更（如从 Transformer 路线切到图神经网络路线）
  2. 引入新的第三方依赖或大体积数据集
  3. 修改 `plan.md` 的阶段划分或研究问题
  4. 实验结论与预期相反（负结果也是结果，但要一起判断怎么办）
  5. 需要删除既有代码或数据
  6. 涉及费用（云 GPU、API 调用）
- **提问要带选项与代价**：不要只问"要不要做 X"，要说清"做 X 需要什么、不做会怎样、还有哪些替代"。
- **进度汇报要具体**：给出改了哪些文件、跑了什么、结果如何、下一步是什么。不要只说"已完成"。
- **提醒 commit 时要给出具体 message**，不要只说"记得提交"。

---

## 8. 每次会话的启动检查清单

```
□ 读 AGENTS.md（本文件）
□ 读 plan.md，定位当前阶段
□ 读 PROGRESS.md，确认上一个任务与最近 commit
□ 读 ASSUMPTIONS.md，了解已有哪些未决假设、是否有影响本任务的 OPEN 条目
□ git status / git log --oneline -10，确认工作区干净
□ 扫一眼 §9.1 Isaac Sim API 坑（若本次要写仿真代码）
□ 确认本次会话要做的小任务编号（如 P1.0），并向用户复述
□ 结束时：更新 PROGRESS.md（＋必要时 plan.md / ASSUMPTIONS.md）→ 提醒 commit
```

---

## 9. 项目特定的技术约定

- **引用文献时**：优先用 Zotero item key（如 `W8R864BD`）标注，便于回溯。
- **两篇起点文献的已知坑**（见精读笔记，勿重复踩）：
  - DAOMAN：式(5)–(6) 在 `a_t = 0` 时除零，实现需补分支；PPO 的 clip/GAE/epoch 未给出；奖励量纲未归一化；PPO 观测不含障碍物。
  - MAPF-GPT：epoch 计数口径与常规定义不同，复现以「迭代数 × batch × 累积步」为准；环境对同时冲突的仲裁规则未说明。
- **硬件约束**：本机 RTX 4060 Laptop **8GB 显存**、30GB 内存、65GB 可用磁盘。任何需要更大显存的方案，必须先说明并给出降级路径。
- **默认不追求复现 1B 数据集**。优先用公开预训练权重 + 定向微调（MAPF-GPT-DDG 范式）。
- **不要用 Clone → 全量 INS 的思路做事**：本机磁盘是硬约束，MAPF-GPT 全量数据集 258GB，**禁止**尝试下载。

### 9.1 Isaac Sim 6.0 已知 API 坑（2026-09-18 实测）

写代码前先扫一眼，这些都是已经踩过的：

| 坑 | 正确做法 |
|---|---|
| `omni.isaac.core` 不存在 | 用 `isaacsim.core.api`（但见下条 —— 已废弃） |
| **`isaacsim.core.api` / `.prims` / `.utils` 已在 `extsDeprecated/` 下** | **本项目已决定改用 `isaacsim.core.experimental.*`**（`A-001`，理由是 IsaacLab 3.0 已迁完）。`omni.isaac.*` 兼容层在 6.0 已移除 |
| `PhysicsMaterial` 没有 `.apply()` 方法 | 旧教程写法失效；材质走 `isaacsim.core.experimental.materials` |
| USD prim path 不能含 `.` | `/World/a_1.0` 非法 → 用整数索引 |
| headless 首次启动慢 | 首次含 warmup 约 85 s，之后约 6 s；不要误判为卡死 |
| 8GB 显存跑 GPU 物理可行 | 已实测通过（headless + 少机器人）。规模不确定时先压测，不要预先放弃 |

**🔥 会让物理"静默不跑"的三条（2026-09-18 S1 实测，最常见且最难自查）**

这三条不满足时，仿真**不报错、时间也推进**，但刚体一动不动 —— 极易被误判为"代码写对了只是重力小"：

1. **必须 `app_utils.play()`**：`SimulationManager.step()` 单独调用不驱动物理。
   正确顺序：`app_utils.play()` → `simulation_app.update()`（让物理初始化）→ 之后 `simulation_app.update()` 或 `SimulationManager.step(steps=N)` 都可用。
2. **必须 `SimulationManager.set_default_physics_scene("/World/PhysicsScene")`**：否则默认场景为 `None`，
   日志会报 `Invalid default physics scene path: None`。
3. **必须 `PhysicsScene.set_gravity((0,0,-9.81))`**：`PhysicsScene` 默认重力**未 author**，`get_gravity()` 读出来是 `(nan, nan, nan)`。

其他已实测项：

| 事实 | 说明 |
|---|---|
| `step()` 的 `steps` keyword-only | `step(100)` 报错，须 `step(steps=100)` |
| `RigidPrim` 返回 Warp 数组 | `get_world_poses()` / `get_velocities()` → `tuple[wp.array, wp.array]`，需 `.numpy()` |
| `apply_collision_apis` 在 `GeomPrim` | **不在** `RigidPrim` 上 |
| `set_local_poses` 用 `translations=` | `set_world_poses` 才用 `positions=` |
| `SimulationManager` 无 play/pause/reset/stop | 时间线控制走 `isaacsim.core.experimental.utils.app` |
| `stage` 无 `clear_stage` | 只有 `create_new_stage`；复用场景应原地复位 |
| `Cube`/`GroundPlane` 自带 `positions`/`sizes`/`scales` | 无需再用 `XformPrim` 二次设位姿 |
| 重建 stage 会让旧 prim 失效 | 报 `Accessed invalid expired prim`；改用 `set_world_poses` + `set_velocities` 原地复位 |
| `enable_ccd(True)` 实测无效 | 对高速穿透无可观测影响（原因未追，可能需 PhysX scene 侧配置） |

**已验证的新 core API 事实**（2026-09-18 从本机扩展源码与自带 `config/python_api.md` 抽取，非文档推测）：

| 事实 | 细节 | 重要性 |
|---|---|---|
| **`SimulationManager.step()` 的 `steps` 是 keyword-only** | 签名 `step(*, steps=1, callback=None, update_fabric=False) -> None`。写 `step(100)` 会直接报错，必须 `step(steps=100)` | ⚠️ 高频踩坑 |
| **`RigidPrim.get_world_poses()` / `get_velocities()` 返回 Warp 数组** | 返回 `tuple[wp.array, wp.array]`，**不是 numpy**。需要 `.numpy()` 转换才能喂给 numpy/ROS | ⚠️ 高频踩坑 |
| `update_fabric=True` 有前提 | 签名注明：若 fabric 未启用而 `update_fabric=True` 会抛 `ValueError` | 中 |
| `apply_collision_apis()` 存在 | 在 prims 模块，用于给几何体加碰撞属性 | 高（S1.1 要用） |
| `SimulationEvent` 枚举存在 | 位于 `impl/simulation_event.py`，成员包括 `PHYSICS_READY` / `POST_RESET` / `PRE_PHYSICS_STEP` / `POST_PHYSICS_STEP` / `SIMULATION_STARTED` / `SIMULATION_PAUSED` / `TIMELINE_STOP` 等 14 项 | 中（S6 桥接排序会用到） |
| 各扩展自带权威签名清单 | 每个扩展下都有 `config/python_api.md`，是比网上文档更可靠的本地契约来源 | 高 —— **查 API 先查它** |

**已确认存在的类**（实测导出）：

- `isaacsim.core.experimental.prims`：`Articulation` `GeomPrim` `RigidPrim` `XformPrim` `Prim` `DeformablePrim` `BufferDtype`
- `isaacsim.core.experimental.objects`：`Cube` `Sphere` `Capsule` `Cone` `Cylinder` `GroundPlane` `Plane` `Mesh` `Camera` 及各类 `Light`

### 9.2 已安装的仿真资产（不要重复下载/安装）

```
Isaac Sim 6.0.1-rc.7   /home/gsh/isaacsim   (27 GB)
IsaacLab 3.0.0         /home/gsh/IsaacLab   (11 GB)
  venv: /home/gsh/IsaacLab/env_isaaclab  Python 3.12.13 / torch 2.11.0
驱动 595.84 / CUDA 12.9 / Warp 1.13.0
ROS 2 桥接扩展已装；系统 ROS 2 未装
```

运行方式：`cd /home/gsh/isaacsim && ./python.sh <script>`

---

## 10. 变更记录

| 日期 | 变更 | 批准 |
|---|---|---|
| 2026-09-18 | 初版创建（用户要求：证据门槛 + 小任务即 commit + 文档同步） | 用户 |
| 2026-09-18 | 新增 §4.3 与文首授权说明：文档更新无需逐次请示；放宽 §6 第 10 条；新增 §9.1 / §9.2 | 用户（"文档一定要更新不用问我"） |
| 2026-09-18 | 仓库接入 `multi_agents_nav_offload`；§8 启动清单加入远程确认项 | 用户 |
| 2026-09-18 | 核心 API 选型定案为新 core；§9.1 补入 6 项实测 API 事实与已确认类清单 | 用户（S1 重构提案）+ 本机实测 |
