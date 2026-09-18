# PROGRESS.md — 进度看板

> 每个小任务完成后更新本文件。**最近一次同步**：2026-09-18

---

## 当前状态

**阶段**：P1 物理仿真底座 · **垂直切片进行中**
**已完成**：立项、文献精读、环境可行性验证、仓库搭建、S1 合同测试、ROS 2 Jazzy、Carter 选型与加载、**S4 差速控制合同**
**下一步**：**S5 ROS 2 桥接**（`/cmd_vel` → 差速控制）—— 见文末「下一步」

```
P0 立项与基线      ▓▓▓░░░░░░░  文献精读完成，DAOMAN 代码复现未开始
P1 物理仿真底座    ▓▓▓▓▓▓▓░░░  S1–S4 完成，S5 桥接待做
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

## 已完成（S2 / S3 + 外部依赖，2026-09-18 傍晚）

| # | 日期 | 内容 | 结果 |
|---|---|---|---|
| — | 2026-09-18 | **ROS 2 Jazzy 安装**（用户手动执行） | ✅ `/opt/ros/jazzy`，296 个包；DDS 自发自收自测通过 |
| **S2** | 2026-09-18 | **Carter v1 导入与加载** | ✅ `tools/view_carter.py`；92 prim，尺寸 0.672×0.626×0.663 m |
| **S3** | 2026-09-18 | **最小场景**（地面 + 光照 + 物理场景 + 重力） | ✅ 已并入 `tools/view_carter.py`，GUI 实机看到画面 |
| — | 2026-09-18 | **AGV 选型定案** | ✅ 用户拍板 Carter v1（`A-012` 已 RESOLVED） |
| — | 2026-09-18 | 驱动失配故障定位（NVML 库/模块版本不一致） | ✅ 根因确认，重启后自愈（`A-014`） |
| — | 2026-09-18 | "GUI 未响应"二次定位（RTX PSO 缓存重建阻塞主线程） | ✅ 已定位，非崩溃；二次启动 11.3 s（首次 80.5 s） |
| **S4** | 2026-09-18 | **差速控制合同 C1–C4（含 C3b 绕固定轴自转）** | ✅ **全部 PASS**；报告 `docs/P1.3-s4-drive-contract.md` |

**S2/S3 实测参数**（S4 直接消费）：驱动轮 DOF 名 `left_wheel` / `right_wheel`
（关节 prim 路径是 `chassis_link/left_wheel`，**两者不可混用**）；
`wheel_radius=0.24` ✅、`wheel_base=0.628411` ⚠️（**不是文档里的 0.54**）。

### S4 的验收数值（脚本 `tools/drive_carter.py`）

| 项目 | 结果 |
|---|---|
| C1 零指令静止（5 s） | 位移 0.0000 cm、yaw 漂移 0.00000° |
| C2 直行 `[v=0.5]` = v·t | Δx = 1.50087 m（期望 1.50000），误差 **0.06%** |
| C3a 原地转 `[ω=0.5]` = ω·t | Δyaw = 1.53868 rad（期望 1.50000），误差 **2.58%** |
| C3b 绕固定轴自转 | 各采样点到 ICR 距离极差 **0.0174 cm** |
| C4 收指令后衰减 | 1 s 后 0.50003 → 0.00024 m/s |

### S4 的三个发现（都已进 `ASSUMPTIONS.md`）
1. **`wheel_base` 文档值是错的** —— 照抄 0.54 会让转向偏小 13.85%（`A-012` 已更正）
2. **`set_dof_gains()` / `set_dof_max_efforts()` 对 Carter 无效** —— 项目依赖资产默认增益（`A-015`）
3. **实际旋转中心偏离驱动轴 3.351 cm** —— 后被动轮侧向刮擦所致（`A-017`）

### S4 可用的速度驱动配方（实测）
```python
from isaacsim.robot.experimental.wheeled_robots.robots.wheeled_robot import WheeledRobot
from isaacsim.robot.experimental.wheeled_robots.controllers.differential_controller import DifferentialController

robot = WheeledRobot("/World/Carter", wheel_dof_names=["left_wheel", "right_wheel"],
                     usd_path=CARTER_URL, positions=[0, 0, 0.3])       # usd_path 自动引用到 stage
ctrl  = DifferentialController(wheel_radius=0.24, wheel_base=0.628411)  # 参数全 keyword-only
robot.apply_wheel_actions(ctrl.forward(np.array([v, w])))               # [v,ω] → [左, 右] 角速度
```

## 进行中

无。（S4 已完成，**等 S5 放行**）

---

## 待办（按推荐顺序）

| 优先级 | 任务 | 前置 |
|---|---|---|
| 1 | **S5 ROS 2 桥接** —— `/cmd_vel` → `DifferentialController`（**需自建 action graph**，Nova Carter 的官方资产不可复用） | **用户放行** |
| 2 | S6 闭环验收 —— 外部 `ros2 topic pub /cmd_vel` 驱车，回读位姿 | S5 |
| 3 | S4 遗留：扫 ω ∈ {0.2, 0.5, 1.0} 确认 C3a 残余 2.58% 是否来自轮子滑移 | 无 |
| 4 | P0.2–P0.4 DAOMAN 复现（**可并行**，纯 PyTorch，不依赖 Isaac Sim） | 无 |
| 5 | 精读 Nagai & Okumura 2026《From Gridworlds to Warehouses》—— P2 栅格桥接的核心参照 | 无 |
| 6 | P1.2 场景搭建（室内仓库 + 室外堆场） | `A-006` 拍板 |
| 7 | S1 探针脚本从 `/tmp` 提升到 `tools/probes/` 作回归测试 | `A-009` 拍板 |
| ~~—~~ | ~~装 ROS 2 Jazzy~~ / ~~S2 Carter 导入~~ / ~~S3 最小场景~~ | ✅ **已完成** |

> ⚠️ **ROS 2 + zsh 的坑（已踩）**：`/opt/ros/jazzy/setup.bash` 是 bash 语法，当前 shell 是 **zsh**，
> 直接 `source` 会**静默失败**。必须写成 `bash -c 'source /opt/ros/jazzy/setup.bash && ...'`。

---

## 待用户拍板的决策（`plan.md` §12）

| # | 问题 | 状态 |
|---|---|---|
| 1 | 场景：室内仓库+室外堆场混合 vs 纯室外 | ⏳ 未答（`A-006`） |
| 2 | ~~Isaac Sim core API：新 vs 旧~~ | ✅ **已定：新 core**（`A-001` 已 RESOLVED） |
| 3 | ROS 2 Jazzy 还是 Humble | ✅ **已定：Jazzy**。依据：①`setup_ros_env.sh` 在 Ubuntu 24.04 默认 `ROS_DISTRO=jazzy`；②桥接同时打包 `jazzy/` 与 `humble/` 两套 lib；③装 Humble 有"发现正常但数据面静默全丢"的风险 |
| 4 | 目标机器人数（建议先 8 台） | ⏳ 未答 |
| 5 | 是否要求实机验证 | ⏳ 未答 |
| 6 | P5 进阶技术做几项 | ⏳ 未答 |
| 7 | 目标 venue / deadline | ⏳ 未答 |
| 8 | S1 产物归属：`/tmp` 还是进仓库（建议分层） | ⏳ 未答（`A-009`） |
| 9 | ~~AGV 平台选 Carter / Nova Carter / iw.hub / 外部 URDF~~ | ✅ **已定：Carter v1**（`A-012` 已 RESOLVED，全项目锁定不切换） |

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
驱动  595.91.07（open 内核模块，与用户态库已对齐）
ROS 2 Jazzy          已装（/opt/ros/jazzy，296 包）
AGV                   Carter v1（已定案）
磁盘                  65 GB 可用
```

---

## ROS 2 Jazzy 安装命令（✅ 已于 2026-09-18 完成，以下留档备重装）

前置已满足：`LANG=en_US.UTF-8`、amd64、Ubuntu 24.04（noble）、无旧 ROS 源。

```bash
# 1. 启用 Universe 仓库
sudo apt install -y software-properties-common
sudo add-apt-repository -y universe

# 2. 导入 ROS 官方 GPG key
sudo apt update && sudo apt install -y curl
sudo curl -sSL https://raw.githubusercontent.com/ros/rosdistro/master/ros.key \
  -o /usr/share/keyrings/ros-archive-keyring.gpg

# 3. 添加 ROS 2 源
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/ros-archive-keyring.gpg] \
http://packages.ros.org/ros2/ubuntu $(. /etc/os-release && echo $UBUNTU_CODENAME) main" | \
  sudo tee /etc/apt/sources.list.d/ros2.list > /dev/null

# 4. 安装（desktop 含 RViz2，调试必需）
sudo apt update
sudo apt install -y ros-jazzy-desktop ros-dev-tools

# 5. 验证
source /opt/ros/jazzy/setup.bash
ros2 --version && ros2 topic list
```

装完后把 `source /opt/ros/jazzy/setup.bash` 加进 `~/.zshrc` 便于日常使用。

**S6 注意事项**：若出现 `ros2 topic list` 看得到话题但 `echo` 收不到数据，
说明 Isaac 桥接（自带 FastDDS）与系统 ROS 2 的共享内存布局不兼容 ——
在 ROS 2 侧挂 UDP-only 的 `FASTRTPS_DEFAULT_PROFILES_FILE` 即可，Isaac 侧零改动。

---

## 下一步

**S5 · ROS 2 桥接** —— 把 S4 已确立的差速控制接到 `/cmd_vel` 上。

### 现状

S4 已经证明：给 `DifferentialController` 传 `[v, ω]`，Carter 会按运动学预期移动
（直行误差 0.06%、原地转误差 2.58%，且是干净的绕固定轴自转）。
**缺的只是"让 `/cmd_vel` 话题变成那个 `[v, ω]`"。**

### S5 要建的东西

`/cmd_vel`（`geometry_msgs/Twist`）→ **OmniGraph action graph** → `DifferentialController` → `apply_wheel_actions`
→ 反向再发 `odom` / `tf`（这是 S6 回读位姿的前提）。

| 步骤 | 内容 |
|---|---|
| S5.1 | 用 `isaacsim.ros2.bridge` 的 OmniGraph 节点建 action graph：`ROS2SubscribeTwist` → 差速换算 → `ArticulationController` |
| S5.2 | 发布 `/odom` 与 `/tf`（`ROS2PublishOdometry` / `ROS2PublishTransformTree`） |
| S5.3 | 命名空间按多机设计：`/robot_{i}/cmd_vel`、`/robot_{i}/odom` |
| S6 | 外部 `ros2 topic pub` 驱车 → 回读位姿，与 S4 的数值断言对照 |

### S5 的三个已知拦路点（都不是盲区）

1. **⚠️ `DifferentialController` 是 Python 类，不是 OmniGraph 节点。**
   action graph 里没有现成的"差速换算"节点 —— 要么用 OmniGraph 的 `DifferentialController` C++ 节点
   （需查 `isaacsim.robot.wheeled_robots.nodes` 是否提供），要么走 Python 脚本节点回调。
   **这是 S5 第一件要查清的事。**
2. **`wheel_base` 必须用 0.628411**（`A-012` 已更正）；用文档值 0.54 会让转向偏小 13.85%。
   action graph 里若硬编码参数，务必核对。
3. **zsh 下 source ROS 会静默失败** —— 必须 `bash -c 'source /opt/ros/jazzy/setup.bash && ...'`。
   另：若出现"话题可见但收不到数据"，按下方 S6 注意事项挂 UDP-only 的 FastDDS profile。

> 备选并行轨：**P0.2–P0.4 DAOMAN 复现**（纯 PyTorch，不依赖 Isaac Sim，产出 H2 批判性基线）。
