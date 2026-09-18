# ASSUMPTIONS.md — 假设日志

> 记录所有**没有文献依据、也没有用户明确批准**的技术决策。
> 按 `agents.md` 铁律一：任何落到代码或论文里的选择，来源只能是 **A 文献** / **B 用户同意** / **C 显式假设**。C 类必须登记在此。
> **新假设请追加编号，不要回头改历史条目；条目被推翻时改状态为 SUPERSEDED 并指向新条目。**

状态约定：`OPEN` 待验证 · `RESOLVED` 已消解 · `SUPERSEDED` 已被取代

---

## A-001 · Isaac Sim core API 选型
**状态**：`RESOLVED` → **采用新 core `isaacsim.core.experimental.*`** · **日期**：2026-09-18

原探针脚本使用 `isaacsim.core.api`（`World` / `DynamicCuboid`），但该包落在
`/home/gsh/isaacsim/extsDeprecated/isaacsim.core.api/`。

**决策依据（本机实测，非文献推断）**：

| 证据 | 数据 |
|---|---|
| IsaacLab 3.0.0 源码对两套 core 的引用 | 新 core **24** 个文件 vs 旧 core **1** 个（且是 CHANGELOG 里的历史引用） |
| Isaac Sim 原生 `standalone_examples` | 新 core **119** vs 旧 core **70** |
| NVIDIA 官方 | 《Core API to Core Experimental API》明确 `isaacsim.core.api/prims/utils` 在 6.0 已废弃 |

**结论**：IsaacLab（我们 P3 训练侧要依赖的工具）**已完成迁移**。继续使用旧 core 会立刻与依赖工具链错位。
我此前"先用旧 core 降低首周风险"的建议**作废**——那个判断建立在"新 core 生态不成熟"的假设上，实测不成立。

**遗留提示**：`experimental.*` 被官方标记为实验性，签名不保证跨版本稳定。因此 S1.4 的签名快照是
**本项目的 API 契约记录**，未来升级版本时用于差异比对。

---

## A-002 · 碰撞保真度扫描的实验条件
**状态**：`OPEN` · **日期**：2026-09-18 · **2026-09-18 补充：新 Core 复跑结果已出，见 `docs/P1.0-core-probe.md` §4**

下表结论所用的测试条件由我自行设定，**不是引用自任何文献**，因此若写入论文必须完整交代这些条件：

- 零重力自由空间（未铺地面，通过 `physxRigidBody:disableGravity` 关闭重力）
- 物体：两个 0.2 m 立方体，`scale=0.2`，默认材质
- 初始间距 2.0 m，仅沿 x 轴给 `box_b` 初速度
- 时间步 `dt = 1/60 s`（Isaac Sim 默认）
- 判定：`min |x_a − x_b|` 是否小于半宽 0.1 m

| 速度 m/s | 旧 Core 最小间距 m | 判定 |
|---|---|---|
| 1 / 2 / 4 | 0.200 / 0.236 / 0.199 | 正确碰撞 |
| 8 / 16 | 0.217 / 0.206 | 正确碰撞 |
| 25 | 0.037 | 穿透 |

**新 Core 复跑结果（2026-09-18，同条件）**：1/2/4 → 0.200（与旧一致）；8/16 → **0.133**（旧为 0.217/0.206，
**存在偏差**，新 Core 重叠更深）；25 → 0.083（旧 0.037，均穿透）。详见 `docs/P1.0-core-probe.md` §4。

**注意**：
- 真实 AGV 并非在无重力自由空间中运动。地面上存在摩擦与滚动阻力，实际碰撞行为需另行验证。
  此表只回答"离散碰撞检测在何速度下失效"，不能直接当作 AGV 碰撞行为的证据。
- **新旧 Core 在 ≥8 m/s 处数值不一致**，印证了 NVIDIA 迁移指南"并非所有旧 API 都有一对一替代"的提醒。
  论文引用时只能声明**低速区间（0.5–3 m/s，最小间距恒为 0.200）**的结论。

---

## A-003 · AGV 工作速度区间取 0.5–3 m/s
**状态**：`OPEN` · **日期**：2026-09-18

据此得出"无需开启 CCD"的结论。该速度区间取自仓储 AMR 的一般工程认知，**尚未引用具体文献或产品规格书**。
**待办**：P1 选型机器人时，用实际 URDF / 厂商规格替换此假设。

---

## A-004 · 部分卸载比例 ρ 离散化为 5 档
**状态**：`OPEN` · **日期**：2026-09-18

计划把 DAOMAN 的三档离散动作（本地 / BS / 卫星）扩展为 ρ ∈ {0, 0.25, 0.5, 0.75, 1}。选择 5 档而非连续值是为了保持动作头仍是分类问题、兼容交叉熵训练。
**依据**：无文献。DAOMAN 论文自身在局限中承认未做部分卸载（精读笔记 §16），但未给出离散化粒度建议。

---

## A-005 · "覆盖感知 cost-to-go"（C-C2G）的定义
**状态**：`OPEN` · **日期**：2026-09-18

`plan.md` §4.1 给出的定义为：

```
U(x,t)   = min over 可见卸载节点 k  [ D_i/R(x,k,t) + D_i/F(k,t) + 回传项 ]
C-C2G(x) = 沿最短路到「U 低于阈值处」的最小步数
```

**这是本方案提出的新表示，没有任何文献先例**（MAPF-GPT 的 cost-to-go 是几何距离，本式是通信代价场）。它是待验证的核心假设 H1，不是已知结论。

---

## A-006 · 场景取「室内仓库 + 室外堆场」混合
**状态**：`OPEN` · **等用户拍板` · **日期**：2026-09-18

`plan.md` §12 第 1 问尚未答复。当前计划按混合场景编写（室外约占 1/3），理由是机器人穿越室内外边界时卸载选项发生真实切换，"移动改变覆盖"的耦合最强。
**风险**：若老师要求纯室内或纯室外，P1 的场景搭建需要返工。

---

## A-007 · 复现 DAOMAN 时缺失的实现细节
**状态**：`OPEN` · **日期**：2026-09-18

DAOMAN 原文未交代、复现时必须自行补全的项（来源：精读笔记 §17）：

- 网络层数、隐藏维度、激活函数
- attention 特征维度、探索噪声标准差、TD3 target smoothing 系数
- PPO 的 clip range / GAE λ / epochs / entropy 系数
- 随机种子、训练重复次数
- 式(5)–(6) 在 `a_t = 0` 时**除零**，实现需补分支（原文未给）
- PPO buffer 用单独卸载奖励还是加权总奖励（Algorithm 1 文字与式(47) 不一致）

上述每一项在动手时都要追加子条目，不得凭默认参数默默实现。

---

## A-008 · 操作步骤：本地目录名与远程仓库名不一致
**状态**：`RESOLVED`（可接受） · **日期**：2026-09-18

本地目录为 `多智能体强化学习`，远程 GitHub 仓库为 `multi_agents_nav_offload`。二者无需一致，git 不要求同名，不影响推送与克隆。保持现状以避免改动你的个人目录结构。

---

## A-009 · S1 合同测试的分层与产物归属
**状态**：`OPEN` · **日期**：2026-09-18

由用户提出、我方补充后确定的 S1 结构。其中"探针脚本只放 `/tmp`、不进仓库"与"S1.2 扫描数据要留作基线"存在冲突；
我方建议分层处理（脚本暂存 `/tmp`，**S1.4 基线报告进仓库** `docs/P1.0-core-probe.md`，稳定后脚本提升到 `tools/probes/`）。
**依据**：部分有 NVIDIA 迁移验收清单支撑（new stage / existing stage 首次 step 必须验证），分层与归属为我方判断。
**待办**：用户确认产物归属方案。

---

## A-010 · S1 阶段不引入 IsaacLab
**状态**：`OPEN` → 倾向确认 · **日期**：2026-09-18

S1 只用 Isaac Sim standalone + `isaacsim.core.experimental.*`，不引入 IsaacLab 包装层。
理由：避免把「Isaac Sim API 问题」与「IsaacLab 抽象问题」混在一个实验里，保证失败可精确定位。
**影响**：P3 若切到 IsaacLab 训练，生命周期管理方式会换成 `PhysxManager` / `NewtonManager`，需另立 contract。
**待办**：P3 前重新评估。

---

## A-011 · S1 阶段不引入 DifferentialController
**状态**：`OPEN` → 倾向确认 · **日期**：2026-09-18

`DifferentialController`（`isaacsim.robot.experimental.wheeled_robots.controllers`）属于 S4 的 robot-control contract，不放进 S1。
**依据**：接口已实测确认存在，签名为 `wheel_radius / wheel_base / max_linear_speed / max_angular_speed / max_wheel_speed`，
`(v, ω) → [left, right]` 轮速。提前引入只会增加变量。

---

## A-012 · AGV 选型（S2）
**状态**：`RESOLVED` —— **已拍板：全项目统一用 Carter v1** · **日期**：2026-09-18

> **决议（2026-09-18 傍晚）**：用户在 `tools/view_carter.py` 中实际看过 Carter v1 后拍板
> 「就用这个机器人」。**S2–S6 全部锁定 Carter v1，不再评估切换。**
> 原「P1.2 按需切 iw.hub」的建议**作废** —— 避免中途换模型引入不可比的变量。
> 代价：iw.hub 的「工业 AMR」叙事放弃（Carter 是通用科研移动平台，叙事上稍弱但完全成立）。
> 影响：S5 的 ROS 2 action graph **需自行搭建**（Nova Carter 的官方已验证资产不可直接复用）。

**原始建议（存档）：S2 先用 Isaac Sim 自带的 Carter，P1.2 建仓库场景时按需切 iw.hub。**

依据（NVIDIA 官方资产文档查得，非推测）：

| 机器人 | 资产路径（6.0 实际） | 驱动 | 轮半径 / 轴距 |
|---|---|---|---|
| **Carter v1** | `Robots/NVIDIA/Carter/carter_v1.usd` | **差速**（2 驱动轮 + 后被动轮） | **0.24 / 0.54** |
| Nova Carter | `Robots/NVIDIA/NovaCarter/nova_carter.usd` | 差速 | 0.14 / 0.413 |
| JetBot | `Robots/Jetbot/jetbot.usd` | 差速 | 0.0325 / 0.118 |
| iRobot Create 3 | `Robots/IRobot/create_3.usd` | 差速 | 0.03575 / 0.233 |
| **iw.hub**（Idealworks） | `Robots/Idealworks/iw_hub{,_sensors,_static}.usd` | 移动底盘 | 0.08 / 0.58 |
| Clearpath Dingo / Jackal | `Robots/Clearpath/...` | — | — |
| Kaya | `Robots/Kaya` | 全向（三轮 holonomic） | — |

- 这些轮半径/轴距是**官方给出的测量参考值**，正好是 `DifferentialController(wheel_radius, wheel_base, ...)` 需要的两个构造参数。
- **iw.hub 是工业规格 AMR**：载荷 1000 kg、最高 2.2 m/s，另有 `iw_hub_sensors.usd`（带 LiDAR / 相机 API），更贴合"仓库 AGV"叙事。
- **Nova Carter 有官方已验证的 ROS 2 资产** `/Isaac/Samples/ROS2/Robots/Nova_Carter_ROS.usd`（带 action graph，官方标注 tested and verified）→ S6 桥接可直接借鉴。

**为什么不先用外部开源 URDF**（MiR100 / Clearpath Jackal / TurtleBot3 都能用）：
导入要自行调 joint target type、collision geometry、惯性参数，会拖慢 S2–S6 的垂直切片。
按"先打通、再换模型"的原则，第一版用官方资产零风险。

**URDF 导入时的关键配置**（官方教程明确，未来若导入外部 URDF 必看）：
- 移动机器人**必须取消勾选 Fix Base Link**，否则底座被钉死
- 驱动轮 target type 设为 **Velocity**（不是 Position）
- 被动轮（caster / pivot）target type 设为 **None**

### A-012 补充：Carter v1 实测参数（2026-09-18 已实际加载验证）

- **资产根 URL**：`https://omniverse-content-production.s3-us-west-2.amazonaws.com/Assets/Isaac/6.0`
- **⚠️ 6.0 真实路径是 `Isaac/Robots/NVIDIA/Carter/carter_v1.usd`** ——
  4.5 文档写的是 `Isaac/Robots/Carter/...`，**照抄旧文档会 404**。
- **关节名（USD prim 路径）**（实测）：

| 关节 prim 路径 | 类型 | 用途 |
|---|---|---|
| `chassis_link/left_wheel` | PhysicsRevoluteJoint | **驱动轮** |
| `chassis_link/right_wheel` | PhysicsRevoluteJoint | **驱动轮** |
| `chassis_link/rear_pivot` | PhysicsRevoluteJoint | 被动 |
| `rear_pivot_link/rear_axle` | PhysicsRevoluteJoint | 被动 |
| `chassis_link/com_joint`、`imu_joint` | PhysicsFixedJoint | 固定 |

> ⚠️ **上面是 prim 路径，不是 DOF 名。** 传给 `get_dof_indices()` / `wheel_dof_names=`
> 必须用 **DOF 名**，实测为 `['left_wheel', 'right_wheel', 'rear_pivot', 'rear_axle']`。
> 传 `'chassis_link/left_wheel'` 会 `AssertionError: Invalid DOF name`。详见 `A-016`。

- **整体尺寸**：`0.672 × 0.626 × 0.663 m`（包围盒，默认姿态）
- **link 名与路径**（实测）：`chassis_link`、`left_wheel_link`、`right_wheel_link`、
  `rear_pivot_link`、`com_offset`、`imu`、`rear_wheel_link`；
  路径形如 `/World/Carter/left_wheel_link`（**不在 `chassis_link` 之下**）
- **差速参数**（2026-09-18 修正）：
  - 轮半径 `0.24` ✅ 文档值正确，已由 C2 独立验证（误差 0.06%）
  - 轴距 ⚠️ **文档值 `0.54` 是错的**。实测 `left_wheel_link.y=+0.314213`、
    `right_wheel_link.y=-0.314198` → **真实间距 `0.628411 m`**。
    用 0.54 会让转向系统性偏小 **13.85%**。详见 `docs/P1.3-s4-drive-contract.md` §4.1。
  - 正确用法：`DifferentialController(wheel_radius=0.24, wheel_base=0.628411, ...)`
- 加载后 prim 数 = 92

**教训（项目级）**：NVIDIA 资产文档的「测量参考值」**必须逐个实测核对** ——
本次 `wheel_radius` 对、`wheel_base` 错。不能整体信任，也不能整体怀疑。

---

## A-013 · Isaac Sim GUI 打开后"没有画面"的根因
**状态**：`SUPERSEDED` → 见 **A-014**（真正根因是驱动版本不匹配，不是空场景）· **日期**：2026-09-18

NVIDIA 官方安装文档原话：*"Then the Isaac Sim GUI window opens with nothing displayed in it."*
**GUI 启动后默认就是空 stage；不加载任何内容当然没有画面 —— 这不是故障。**

排查顺序（按可能性从高到低）：
1. **空场景** → 用 Content Browser 拖入资产，或跑 `tools/view_carter.py`
2. **首次启动 shader 预热 5–10 分钟** → 先跑 `/home/gsh/isaacsim/warmup.sh` 预热
3. **混合显卡**（本机是 AMD Radeon 610M 核显 + RTX 4060 独显）→
   试 `__NV_PRIME_RENDER_OFFLOAD=1 __GLX_VENDOR_LIBRARY_NAME=nvidia ./isaac-sim.sh`
4. **配置损坏** → `./isaac-sim.sh --reset-user`

**⚠️ `--viz` 是 Isaac Lab 3.0 的参数，不是 Isaac Sim 的。**
取值：`kit` / `newton_gl` / `viser` / `rerun` / `newton_rtx` / `none`；
用法 `./isaaclab.sh -p <script> --viz kit`；且 **`--headless` 会覆盖 `--viz` 并禁用可视化**。
Isaac Sim 自身的 `isaac-sim.sh` 只接受 `--no-ros-env` 与透传给 kit 的参数
（实际执行：`kit/kit apps/isaacsim.exp.full.kit "$@"`）。

**待办**：用户确认；确认后需联网首次拉取资产（本机 `data/` 下无内置资产，按需下载）。

---

## A-014 · "没有画面"的真正根因：NVIDIA 驱动版本不匹配 ⭐
**状态**：`RESOLVED`（修复 = 重启系统） · **日期**：2026-09-18

### 现象
Isaac Sim GUI 启动后满屏刷：
```
[Error] [omni.kit.renderer.plugin] advanceCurrentFrame: backbuffers are not initialized!
```

### 根因（已实测确认）
`apt` 操作（装 ROS 2 期间）把 NVIDIA 驱动从 **595.84 升级到 595.91.07**，
但**内核模块仍是旧的 595.84**，用户态库已是 595.91 → 版本错配，导致
NVML / Vulkan 全部初始化失败，交换链建不出来，于是 backbuffer 永远没准备好。

实测证据：

| 检查项 | 值 |
|---|---|
| 已加载内核模块 `/proc/driver/nvidia/version` | **595.84** |
| 用户态库 `nvidia-smi` 报告 | **595.91** |
| `nvidia-smi` 直接报错 | `Failed to initialize NVML: Driver/library version mismatch` |
| 已安装包 | `nvidia-driver-595-open 595.91.07-0ubuntu0.24.04.1` |
| Isaac Sim 日志 | `NVML_ERROR_LIB_RM_VERSION_MISMATCH` → `VkResult: ERROR_INITIALIZATION_FAILED` → `vkEnumeratePhysicalDevices failed` |

### 修复
**重启系统**（让新的内核模块加载）。重启安全性已验证：
新模块已就位 `/lib/modules/7.0.0-31-generic/kernel/nvidia-595-open/nvidia.ko`（内嵌版本 595.91.07）。

### 附带确认的第二项改进
系统存在 **9 个 Vulkan ICD**（含 AMD / Intel / nouveau / lavapipe 软件渲染器），
Kit 可能选错设备。实测强制 NVIDIA ICD 后 backbuffers 报错归零：
```
VK_ICD_FILENAMES=/usr/share/vulkan/icd.d/nvidia_icd.json ./isaac-sim.sh
```
建议重启后仍带上此变量（本机是 AMD 核显 + RTX 独显的混合显卡，且会话为 Wayland）。

### 项目级教训（写给未来）
**在本机执行 `apt install` / `apt upgrade` 可能顺带升级 NVIDIA 驱动，导致 GUI 在重启前失效。**
这类故障表现是"Isaac Sim 打不开/没画面"，但根因在驱动层，与 Isaac Sim 无关。
排查顺序应为：`/proc/driver/nvidia/version` ↔ `nvidia-smi` 版本是否一致 → 不一致就重启。

---

## A-015 · 驱动力依赖 Carter 资产自带的默认增益（API 无法覆盖）
**状态**：`OPEN`（已知风险，暂接受）· **日期**：2026-09-18

Carter v1 的两个驱动轮关节在 USD 侧**自带**一套速度驱动：
`type=force`、`stiffness=0`、`damping=17453.29`、`maxForce=inf`。
它开箱即可用，且表现极好（C2 误差 0.06%，C4 收指令后 1 s 内 0.00024 m/s）。

但实测 **`set_dof_gains()` / `set_dof_max_efforts()` 对该资产完全无效** ——
调用前后 USD 读回**逐字相同**（`tools/drive_carter.py` 会打印 `drive_before` / `drive_after`）。

**依据**：本机实测（`docs/P1.3-s4-drive-contract.md` §4.2）。属 C 类假设。
**影响**：项目**依赖资产未文档化的默认增益**。若未来换资产、换版本或 NVIDIA 改了默认值，
控制表现会静默变化，且我们无法用 API 纠正。论文引用本项目代码必须注明此依赖。
**待办**：
1. 查明 setter 失效的真正原因（写入更弱的层？被 PhysX 缓存？需停止仿真后写？）
2. 找替代路径：直接操作 USD `UsdPhysics.DriveAPI` 属性、或走 PhysX 侧 articulation 增益接口
3. S5 接 ROS 2 前必须复核 —— 闭环控制对增益更敏感

---

## A-016 · DOF 名与 USD prim 路径是两套命名，不可混用
**状态**：`RESOLVED`（已实测确定）· **日期**：2026-09-18

| 用途 | 用什么 | 实例 |
|---|---|---|
| `get_dof_indices()` / `WheeledRobot(wheel_dof_names=)` | **DOF 名** | `left_wheel` |
| 查 drive 属性 / 操作关节 | **关节 prim 路径** | `/World/Carter/chassis_link/left_wheel` |
| 量几何 / 取 link 位姿 | **link 路径** | `/World/Carter/left_wheel_link` |

三者互不相同：DOF 名没有前缀；关节 prim 在 `chassis_link/` 下；
**link prim 不在 `chassis_link` 下**。

**依据**：本机实测。`Articulation.dof_names` / `.link_names` / `.link_paths` 是权威来源。
**影响**：混用通常直接 `AssertionError`（尚可），但
**对关节 prim 求世界变换会静默返回 identity**，量几何时会得到全同坐标或 float 溢出（危险）。
**待办**：无。已写入 `agents.md` §9.1。

---

## A-017 · 纯旋转时车体原点会绕偏移 3.35 cm 的 ICR 画圆
**状态**：`OPEN` · **日期**：2026-09-18

实测（`docs/P1.3-s4-drive-contract.md` §4.3、§7.3）：
- 理想旋转中心（驱动轴中点）与 chassis 原点几乎重合（相距 0.001 cm）
- **实际旋转中心偏 3.351 cm**（ω=0.5 工况），实测 ICR = `(0.02648, -0.02771)`
- 原因：Carter 是「2 驱动轮 + 后被动轮」构型，原地转时后被动轮必须侧向刮擦
- 佐证：车体原点在 1.5387 rad 旋转中移动 4.662 cm，与几何预测 4.663 cm 吻合到 3 位有效数字

⚠️ **偏移量不是常数**（2026-09-18 补充）：固定转角 90° 扫 ω 实测
ICR 偏移在 **2.529 cm（ω=2.0）～ 6.021 cm（ω=0.2, warm=240）** 之间变化。
即 ICR 随工况漂移，不是平台几何常量。上文的 3.351 cm 只是一个工况点。

**依据**：本机实测（由运动反解 ICR，不依赖模型假设）。
**影响**：纯旋转时车体原点**画一个半径 = ICR 偏移量的小圆**（实测该半径 2.5–6.0 cm）。

⚠️ **更正（2026-09-18）**：先前写的"每 90° 转向**累积**约 4.7 cm"是错的。
按刚体绕定轴转动，原点的位移是 `2R·sin(Δψ/2)`，**有界且周期性**：转满 360° 会回到起点
（连续 4 圈实测：离出发点峰值 6.668 cm ≈ 2R，转满一圈回落到 0.465 cm）。
所以它**不会随转向次数累积**。真正的影响是：

1. **单次转向期间的瞬时偏差有界但可达 2R**（R 取 6 cm 时约 12 cm）——
   这对**碰撞裕度**和**观测构造**是实打实的影响，不是可以忽略的噪声。
2. **R 本身随工况漂移**（ω=2.0 时 2.5 cm，ω=0.2 时 6.0 cm），所以这个偏差不严格可重复。
3. 模型上正确的做法是**以驱动轴中点（≈ ICR）为状态量**，而不是以 chassis 原点；这样描述是干净的。

**待办**：P2 定稿运动学模型前，决定是①把 ICR 偏移写进模型，还是②改用驱动轴中点为状态量。

---

## 追加新假设的模板

```
## A-0NN · 一句话标题
**状态**：`OPEN` · **日期**：YYYY-MM-DD

决策内容。

**依据**：无文献 —— 本条目即 C 类假设，待验证。
**影响**：若该假设错误，会导致什么。
**待办**：如何消解（补文献 / 做实验 / 询问用户）。
```
