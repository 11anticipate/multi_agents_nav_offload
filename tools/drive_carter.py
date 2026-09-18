"""S4 差速控制合同测试（C1–C4）

验证：Carter v1 收到 [v, ω] 指令后，底盘是否按差速运动学预期移动。
全部用数值断言，不靠肉眼 —— 沿用 S1 的风格。

用法：
    /home/gsh/isaacsim/python.sh tools/drive_carter.py                    # headless 跑断言
    /home/gsh/isaacsim/python.sh tools/drive_carter.py --gui              # GUI 看原地转（带旋转轴标记）
    /home/gsh/isaacsim/python.sh tools/drive_carter.py --gui --spin       # 只看原地转，跳过直行断言
    /home/gsh/isaacsim/python.sh tools/drive_carter.py --gui --cycle      # GUI 加反向转 / 直行演示
    /home/gsh/isaacsim/python.sh tools/drive_carter.py --wheel-base 0.54  # 强制官方值以作对照
    /home/gsh/isaacsim/python.sh tools/drive_carter.py --dump /tmp/s4.json

可调参数（都在这一步改；不需要改下面的代码）：

| 开关 | 默认 | 作用 | 改了会看到什么 |
|---|---|---|---|
| `--v` | 0.5 | C2 直行速度 m/s | 调大→误差通常变大（轮子打滑/驱动跟不上） |
| `--omega` | 0.5 | C3 原地转与 `--spin` 的角速度 rad/s | **最值得试**：扫 0.2 / 0.5 / 1.0，看 C3a 残余误差是否随 ω 单调变化 |
| `--wheel-base` | 实测 0.628411 | 差速轴距 m | 用 0.54 会看到 C3a 误差从 2.6% 跳到 13.9% |
| `--wheel-radius` | 0.24 | 轮半径 m | 直接线性影响 C2 的 Δx |
| `--damping` / `--max-effort` | 20 / 50 | 尝试写入的驱动增益 | ⚠️ **看不到任何变化** —— 对 Carter 实测无效，可用来复现这个事实 |
| `--laps` | 0 | `--spin` 转几圈后退出 | 0 = 一直转到关窗 |

想扫参数看趋势，直接用 shell 循环，例如：

    for w in 0.2 0.5 1.0; do
      /home/gsh/isaacsim/python.sh tools/drive_carter.py --omega $w --dump /tmp/c3_$w.json \
        | grep -E "C3a|C3b"
    done

前置结论（S1，见 docs/P1.0-core-probe.md §5）：
  - 必须先 `app_utils.play()`，否则单独 step() 不驱动物理（静默失效）
  - 必须 set_default_physics_scene + 显式 set_gravity
  - 返回的是 Warp 数组，需 .numpy()

S4 实测事实（探针 /tmp/s4_probe.py、/tmp/s4_probe3.py）：
  1. robot.dof_names = ['left_wheel', 'right_wheel', 'rear_pivot', 'rear_axle']
     **DOF 名是关节自己的名字，不是 USD prim 路径** ——
     传 'chassis_link/left_wheel' 会 AssertionError（最容易踩的坑）
  2. link 名形如 left_wheel_link，路径是 /World/Carter/left_wheel_link（**不在 chassis_link 下**）
  3. 两个驱动轮关节在 USD 侧**已有** UsdPhysics.DriveAPI(type='angular')，
     资产自带 stiffness=0 / damping=17453.29 / maxForce=inf —— 开箱即可用速度控制
  4. ⚠️ `set_dof_gains()` / `set_dof_max_efforts()` 对该资产**实测无效**（配置前后逐字相同），
     因此本项目**依赖资产自带增益**。见 --dump 里的 drive_before / drive_after。
  5. ⚠️ NVIDIA 文档给的 wheel_base=0.54 **不是本资产的驱动轮间距**：
     实测 left_wheel_link.y=+0.314213、right_wheel_link.y=-0.314198 → 间距 0.628411 m。
     用 0.54 → C3 误差 13.85%；用实测值 → 误差 ~2.2%。
"""
import argparse
import json
import math
import sys

parser = argparse.ArgumentParser()
parser.add_argument("--gui", action="store_true", help="开 GUI 看画面（默认 headless）")
parser.add_argument("--spin", action="store_true",
                    help="只演示原地转：跳过 C1–C4 断言，直接做绕旋转中心的自转演示（配 --gui 看画面）")
parser.add_argument("--cycle", action="store_true", help="GUI 模式下额外演示反向转与直行")
parser.add_argument("--wheel-base", type=float, default=None,
                    help="强制指定 wheel_base；默认用从 USD 实测的驱动轮间距")
parser.add_argument("--wheel-radius", type=float, default=0.24,
                    help="轮半径 (m)，默认 0.24（官方值，已被 C2 验证）")
parser.add_argument("--v", type=float, default=0.5,
                    help="C2 直行线速度 (m/s)，默认 0.5")
parser.add_argument("--omega", type=float, default=0.5,
                    help="C3 原地转 / --spin 演示的角速度 (rad/s)，默认 0.5")
parser.add_argument("--damping", type=float, default=20.0,
                    help="尝试写入的速度驱动阻尼；⚠️ 对 Carter 实测无效，仅用于复现'写入无效'")
parser.add_argument("--max-effort", type=float, default=50.0,
                    help="尝试写入的最大力矩；⚠️ 同上，实测无效")
parser.add_argument("--max-linear", type=float, default=1.5,
                    help="DifferentialController 线速度上限 (m/s)，默认 1.5；--v 超过会被静默截断")
parser.add_argument("--max-angular", type=float, default=2.0,
                    help="DifferentialController 角速度上限 (rad/s)，默认 2.0；--omega 超过会被静默截断")
parser.add_argument("--angle", type=float, default=0.0,
                    help="C3 的测量窗口改为『正好转过该角度（度）』，而不是固定 180 步。"
                         "用于把转速与转角解耦（0 = 用固定 180 步）")
parser.add_argument("--warm", type=int, default=60,
                    help="丢弃的起动瞬态步数，默认 60；低速指令可能需要更长")
parser.add_argument("--laps", type=int, default=0,
                    help="--spin 模式下转几圈后自动退出；0 = 一直转到手动关闭")
parser.add_argument("--dump", default="", help="把结果 JSON 写到该路径")
args, unknown = parser.parse_known_args()

# Isaac Sim 的 python.sh 会往 argv 里塞 --/app/... 这类 Kit 参数，不算错。
# 但本项目自己的参数一律用**连字符**（--wheel-base），写成下划线（--wheel_base）
# 会被 argparse 判为未知参数。因为用的是 parse_known_args，它**不会报错**，
# 所以必须在这里显式提醒 —— 否则改参数会静默不生效（已踩）。
_leaked = [a for a in unknown if not a.startswith("--/")]
if _leaked:
    print("\n" + "!" * 72)
    print(f"⚠️  无法识别的参数，已忽略：{_leaked}")
    print("    本项目参数用『连字符』，不是下划线：  --wheel-base  （不是 --wheel_base）")
    print("    运行 --help 查看全部可用参数。")
    print("!" * 72 + "\n")

from isaacsim import SimulationApp  # noqa: E402

simulation_app = SimulationApp({"headless": not args.gui, "width": 1280, "height": 800})

import numpy as np  # noqa: E402
import omni.usd  # noqa: E402
from pxr import Usd, UsdGeom, UsdPhysics  # noqa: E402

import isaacsim.core.experimental.utils.app as app_utils  # noqa: E402
import isaacsim.core.experimental.utils.stage as stage_utils  # noqa: E402
from isaacsim.core.experimental.objects import Cylinder, DistantLight, GroundPlane  # noqa: E402
from isaacsim.core.simulation_manager import PhysicsScene, SimulationManager  # noqa: E402
from isaacsim.robot.experimental.wheeled_robots.controllers.differential_controller import DifferentialController  # noqa: E402
from isaacsim.robot.experimental.wheeled_robots.robots.wheeled_robot import WheeledRobot  # noqa: E402

# ---------------------------------------------------------------- 常量

ROOT = "https://omniverse-content-production.s3-us-west-2.amazonaws.com/Assets/Isaac/6.0"
CARTER_URL = f"{ROOT}/Isaac/Robots/NVIDIA/Carter/carter_v1.usd"

# DOF 名 = 关节自身名字（实测，勿写成 chassis_link/left_wheel）
WHEEL_DOF_NAMES = ["left_wheel", "right_wheel"]
WHEEL_LINK_NAMES = ["left_wheel_link", "right_wheel_link"]

WHEEL_RADIUS = args.wheel_radius  # 官方测量参考值 0.24，已被 C2 验证（误差 0.06%）
WHEEL_BASE_DOC = 0.54  # NVIDIA 文档值 —— 实测证明它不是本资产的驱动轮间距

DRIVE_DAMPING = args.damping  # ⚠️ 实测写入无效（见文件头第 4 条），保留以示记录
DRIVE_MAX_EFFORT = args.max_effort

# 断言阈值（先定死，避免事后挑选）
TOL_LINEAR = 0.05  # C2 位移误差 5%
TOL_ANGULAR = 0.05  # C3a 偏航率误差 5%
TOL_STATIC_POS = 0.01  # C1 静止位移 1 cm
TOL_STATIC_YAW = math.radians(0.5)  # C1 静止 yaw 漂移 0.5°
TOL_ICR_RADIUS = 0.01  # C3b 旋转半径恒定度 1 cm
TOL_STOP_SPEED = 0.01  # C4 收指令后线速度 1 cm/s

# ---------------------------------------------------------------- 场景

stage_utils.create_new_stage()

pscene = PhysicsScene("/World/PhysicsScene")
SimulationManager.set_default_physics_scene("/World/PhysicsScene")
pscene.set_gravity((0.0, 0.0, -9.81))
GroundPlane("/World/GroundPlane", positions=[0, 0, 0])
DistantLight("/World/DistantLight").set_intensities(1000)

DT = pscene.get_dt()
USD_STAGE = omni.usd.get_context().get_stage()

robot = WheeledRobot(
    "/World/Carter",
    wheel_dof_names=WHEEL_DOF_NAMES,
    usd_path=CARTER_URL,
    positions=[0.0, 0.0, 0.3],
)


def run_steps(n: int) -> None:
    for _ in range(n):
        simulation_app.update()


def link_xy(name: str) -> np.ndarray:
    idx = robot.link_names.index(name)
    prim = USD_STAGE.GetPrimAtPath(robot.link_paths[0][idx])
    t = UsdGeom.Xformable(prim).ComputeLocalToWorldTransform(Usd.TimeCode.Default()).ExtractTranslation()
    return np.array([t[0], t[1]])


def pose():
    """返回 (xy ndarray, yaw float)。四元数顺序为 (w, x, y, z)。"""
    positions, orientations = robot.get_world_poses()
    p = positions.numpy()[0]
    q = orientations.numpy()[0]
    w, x, y, z = (float(q[i]) for i in range(4))
    return np.array([p[0], p[1]]), math.atan2(2.0 * (w * z + x * y), 1.0 - 2.0 * (y * y + z * z))


def rotate(vec: np.ndarray, yaw: float) -> np.ndarray:
    c, s = math.cos(yaw), math.sin(yaw)
    return np.array([c * vec[0] - s * vec[1], s * vec[0] + c * vec[1]])


def yaw_diff(a: float, b: float) -> float:
    return math.atan2(math.sin(b - a), math.cos(b - a))


def drive_attrs() -> dict:
    """读回驱动轮在 USD 上的 drive 配置。"""
    out = {}
    for name in WHEEL_DOF_NAMES:
        prim = USD_STAGE.GetPrimAtPath(f"/World/Carter/chassis_link/{name}")
        api = UsdPhysics.DriveAPI(prim, "angular")
        out[name] = {
            "type": api.GetTypeAttr().Get(),
            "stiffness": api.GetStiffnessAttr().Get(),
            "damping": api.GetDampingAttr().Get(),
            "maxForce": api.GetMaxForceAttr().Get(),
        }
    return out


def icr_from_pair(p0: np.ndarray, y0: float, p1: np.ndarray, y1: float):
    """由两点位姿反解刚体绕固定轴的旋转中心 ICR。

    纯旋转满足 p1 - C = R(Δψ)(p0 - C)，故 p0 - C = (I - R(Δψ))^-1 (p1 - p0)。
    返回 (C, Δψ)；Δψ≈0 时无法定解，返回 (None, Δψ)。
    """
    dyaw = yaw_diff(y0, y1)
    c, s = math.cos(dyaw), math.sin(dyaw)
    a = np.array([[1.0 - c, s], [-s, 1.0 - c]])
    if abs(np.linalg.det(a)) < 1e-9:
        return None, dyaw
    return p0 + np.linalg.solve(a, p1 - p0), dyaw


# ---------------------------------------------------------------- 启动

for _ in range(120):  # 落地并静稳
    simulation_app.update()

app_utils.play()  # ← S1 铁律：不 play 则物理静默不跑
run_steps(60)

wheel_indices = robot.get_dof_indices(WHEEL_DOF_NAMES).numpy().tolist()

print("\n" + "=" * 72)
print("S4 差速控制合同测试")
print("=" * 72)
print(f"物理         dt = {DT:.6f} s   gravity = {pscene.get_gravity()}")
print(f"DOF          names={robot.dof_names}")
print(f"驱动轮下标    {dict(zip(WHEEL_DOF_NAMES, wheel_indices))}")

# wheel_base：从驱动轮 link 的世界坐标实测
lx = link_xy(WHEEL_LINK_NAMES[0])[1]
rx = link_xy(WHEEL_LINK_NAMES[1])[1]
track = float(abs(lx - rx))
WHEEL_BASE = args.wheel_base if args.wheel_base is not None else track

print(f"\n驱动轮 y 坐标  {WHEEL_LINK_NAMES[0]}={lx:+.6f}   {WHEEL_LINK_NAMES[1]}={rx:+.6f}")
print(f"wheel_base   实测 {track:.6f} m   官方文档 {WHEEL_BASE_DOC} m   "
      f"偏差 {abs(track - WHEEL_BASE_DOC) / WHEEL_BASE_DOC * 100:.2f}%")
print(f"             本脚本采用 {WHEEL_BASE:.6f} m"
      f"{'  (--wheel-base 强制)' if args.wheel_base is not None else '  (实测值)'}")
print(f"wheel_radius {WHEEL_RADIUS} m（官方测量参考值）")

controller = DifferentialController(
    wheel_radius=WHEEL_RADIUS,
    wheel_base=WHEEL_BASE,
    max_linear_speed=args.max_linear,
    max_angular_speed=args.max_angular,
    max_wheel_speed=20.0,
)

# DifferentialController.forward() 会把指令 **静默 clip** 到 max_*_speed。
# 所以 --v 1.0 配 max_linear 0.5 只会得到 0.5 —— 不报错、不提示。
_clip = []
if abs(args.v) > args.max_linear:
    _clip.append(f"--v={args.v} > max_linear_speed={args.max_linear}")
if abs(args.omega) > args.max_angular:
    _clip.append(f"--omega={args.omega} > max_angular_speed={args.max_angular}")
if _clip:
    print("\n" + "!" * 72)
    print("⚠️  下列指令会被 DifferentialController 静默截断（不是 bug，是它的 clip 行为）：")
    for _c in _clip:
        print(f"     - {_c}")
    print("    实际生效值会被压到上限。要真用这个值，请同时调高 --max-linear / --max-angular。")
    print("!" * 72)

# 本脚本的转角是「逐段累加」得出的，每段 0.25 s（C3）或 1 s（--spin）。
# 若单段转角超过 π，累加本身也会绕回，测量就不再可信。
_SEG = 1.0 if args.spin else 15 * (1.0 / 60.0)
if abs(args.omega) * _SEG > math.pi:
    print("\n" + "!" * 72)
    print(f"⚠️  |ω| = {abs(args.omega)} rad/s 超过本脚本的测量能力上限 "
          f"({math.pi / _SEG:.2f} rad/s)：")
    print(f"    采样间隔 {_SEG:.2f} s，单段转角会超过 π，逐段累加也会绕回。")
    print("    C3 / --spin 的转角将不可信。请把 ω 控制在 ±2 以内（也是控制器的默认上限）。")
    print("!" * 72)

print(f"\n-- 本次运行的指令与参数 --")
print(f"   v = {args.v} m/s      (上限 {args.max_linear})")
print(f"   ω = {args.omega} rad/s  (上限 {args.max_angular})")
print(f"   wheel_base = {WHEEL_BASE:.6f} m"
      f"{'  [--wheel-base 强制]' if args.wheel_base is not None else '  [USD 实测]'}")
print(f"   wheel_radius = {WHEEL_RADIUS} m")
print(f"   模式 = {'GUI' if args.gui else 'headless'}"
      f"{' + spin-only' if args.spin else ''}{' + cycle' if args.cycle else ''}")

before = drive_attrs()
robot.set_dof_gains(stiffnesses=0.0, dampings=DRIVE_DAMPING, dof_indices=wheel_indices)
robot.set_dof_max_efforts(DRIVE_MAX_EFFORT, dof_indices=wheel_indices)
robot.set_dof_drive_types("force", dof_indices=wheel_indices)
after = drive_attrs()

print("\n-- 驱动轮 drive 配置（USD 读回）--")
for name in WHEEL_DOF_NAMES:
    print(f"   配置前 {name:<12} {before[name]}")
    print(f"   配置后 {name:<12} {after[name]}")
gains_unchanged = before == after
print(f"   => set_dof_gains/set_dof_max_efforts 是否生效: "
      f"{'否（逐字相同，写入无效 → 依赖资产自带增益）' if gains_unchanged else '是'}")


# ---------------------------------------------------------------- 工具

def chassis_speed() -> float:
    linear, _ = robot.get_velocities()
    return float(np.linalg.norm(linear.numpy()[0]))


def command(v: float, w: float) -> None:
    robot.apply_wheel_actions(controller.forward(np.array([v, w])))


def reset() -> None:
    robot.reset_to_default_state()
    run_steps(15)


p_settle, y_settle = pose()
robot.set_default_state(
    positions=[float(p_settle[0]), float(p_settle[1]), 0.24],
    orientations=[1.0, 0.0, 0.0, 0.0],
    dof_positions=0.0,
    dof_velocities=0.0,
)

axis_mid = (link_xy(WHEEL_LINK_NAMES[0]) + link_xy(WHEEL_LINK_NAMES[1])) / 2.0
axis_offset_body = rotate(axis_mid - p_settle, -y_settle)

print(f"\n复位基准      xy={np.round(p_settle, 5)}  yaw={math.degrees(y_settle):.3f}°")
print(f"理想旋转轴    驱动轴中点，体坐标 {np.round(axis_offset_body, 5)} m  "
      f"(|d|={np.linalg.norm(axis_offset_body):.5f} m)")
print("              注意：这只是运动学理想值。实际 ICR 受后被动轮侧向刮擦影响，"
      "由 C3b 实测。")

# ---------------------------------------------------------------- --spin 纯原地转演示

if args.spin:
    SPIN_OMEGA = args.omega
    print("\n" + "=" * 72)
    print(f"--spin：纯原地转演示（ω = {SPIN_OMEGA} rad/s，不跑任何直行指令）")
    print("=" * 72)

    # 标定实测旋转中心。两个必须做对的地方（都踩过）：
    #  ① 窗口要够长：icr_from_pair 的系数矩阵行列式 = 4·sin²(Δψ/2)，
    #     Δψ 太小会严重放大噪声。90 步（42°）标出的 ICR 偏离真值 3.3 cm
    #     —— 恰好一个半径，会让演示时「到旋转中心的距离」在 0.4~6.7 cm 间摆动。
    #  ② 必须丢弃起动瞬态：从静止开始给 ω 的头 ~1 s 里，车体并非绕固定点转动，
    #     把这段算进标定窗口同样会污染结果（实测 180 步含瞬态 → 仍偏 1.6 cm）。
    #     口径与 C3 完全一致：60 步 warm + 180 步测量。
    reset()
    command(0.0, SPIN_OMEGA)
    run_steps(60)  # ← 丢弃起动瞬态
    p_cal0, y_cal0 = pose()
    run_steps(180)
    p_cal1, y_cal1 = pose()
    icr_est, cal_dyaw = icr_from_pair(p_cal0, y_cal0, p_cal1, y_cal1)
    command(0.0, 0.0)
    run_steps(30)
    reset()

    if icr_est is None:
        print("  标定失败（转角过小），改用车体原点作标记。")
        icr_est = p_settle
    print(f"  标定：转了 {math.degrees(cal_dyaw):.2f}°，反解出旋转中心 "
          f"({icr_est[0]: .5f}, {icr_est[1]: .5f})")

    Cylinder(
        "/World/ICR_Marker",
        radii=0.012,
        heights=0.9,
        colors=[1.0, 0.2, 0.2],
        positions=[float(icr_est[0]), float(icr_est[1]), 0.45],
    )
    print(f"  已在旋转中心竖起红色细杆。车应当绕着它自转。")
    print("  下表每秒打印一次：yaw / 车体原点 / 到旋转中心的距离。")
    print("  判据：①「到旋转中心」应恒为 ~3.35 cm（= 车体原点到 ICR 的距离）；")
    print("        ② 该距离若持续增大，就是一边转一边往外走，不是原地转。")
    print("        ③「离出发点」最大不超过 2×3.35 ≈ 6.7 cm（沿 3.35 cm 半径的小圆走）。")
    print("  按 Ctrl+C 或关窗退出。\n")

    # 起动瞬态同样丢弃，否则开头几秒的数据不可比
    command(0.0, SPIN_OMEGA)
    run_steps(60)
    p_start, y_ref = pose()
    y_accum = 0.0   # 逐秒累加转角，避免超过半圈后 yaw_diff 绕回（同 C3）
    y_prev = y_ref
    lap = 0
    while simulation_app.is_running():
        for sec in range(3):
            run_steps(60)
            p, y = pose()
            y_accum += yaw_diff(y_prev, y)
            y_prev = y
            d_icr = float(np.linalg.norm(p - icr_est))
            d_start = float(np.linalg.norm(p - p_start))
            print(f"  [第 {lap + 1} 圈 t={sec + 1}s] yaw={math.degrees(y_accum):8.2f}°  "
                  f"原点=({p[0]: .4f},{p[1]: .4f})  到旋转中心 {d_icr * 100:6.3f} cm  "
                  f"离出发点 {d_start * 100:6.3f} cm")
        lap += 1
        if args.laps and lap >= args.laps:
            break
    command(0.0, 0.0)

    simulation_app.close()
    sys.exit(0)

# ---------------------------------------------------------------- C1 零指令静止

print("\n" + "=" * 72)
print("C1 · 零指令静止（5 s）")
print("=" * 72)
reset()
command(0.0, 0.0)
run_steps(30)
p0, y0 = pose()
run_steps(300)
p1, y1 = pose()
d_pos = float(np.linalg.norm(p1 - p0))
d_yaw = abs(yaw_diff(y0, y1))
c1 = d_pos < TOL_STATIC_POS and d_yaw < TOL_STATIC_YAW
print(f"  位移 {d_pos * 100:.4f} cm   (限 {TOL_STATIC_POS * 100:.1f} cm)")
print(f"  yaw 漂移 {math.degrees(d_yaw):.5f}°  (限 {math.degrees(TOL_STATIC_YAW):.1f}°)")
print(f"  -> {'PASS' if c1 else 'FAIL'}")

# ---------------------------------------------------------------- C2 直行

V = args.v
# 期望值必须用**剪断后**的指令算 —— 否则 --v/--omega 超过上限时，
# 期望值会按原始值算，误差恒为巨值，看着像物理错了（其实是参数被 clip）。
V_EFF = max(-args.max_linear, min(args.max_linear, V))
WARM, MEAS = args.warm, 180
print("\n" + "=" * 72)
print(f"C2 · 直行 [v={V_EFF}, ω=0]，稳态后 {MEAS} 步（{MEAS * DT:.2f} s）测量")
print("=" * 72)
reset()
command(V, 0.0)
run_steps(WARM)
p0, y0 = pose()
run_steps(MEAS)
p1, y1 = pose()
dx = float(p1[0] - p0[0])
dy = float(p1[1] - p0[1])
dyaw = abs(yaw_diff(y0, y1))
exp_dx = V_EFF * MEAS * DT
err_dx = abs(dx - exp_dx) / exp_dx
c2 = err_dx < TOL_LINEAR and abs(dy) < 0.02
print(f"  Δx = {dx:.5f} m   期望 {exp_dx:.5f} m   误差 {err_dx * 100:.2f}%  (限 {TOL_LINEAR * 100:.0f}%)")
print(f"  Δy = {dy:.5f} m  (应≈0)   Δyaw = {math.degrees(dyaw):.4f}°  (应≈0)")
print(f"  -> {'PASS' if c2 else 'FAIL'}")

# ---------------------------------------------------------------- C3 原地转

OMEGA = args.omega
OMEGA_EFF = max(-args.max_angular, min(args.max_angular, OMEGA))
SAMPLE_EVERY = 15
# --angle：把测量窗口换算成「正好转过该角度」，用来把**转速**与**转角**解耦。
# 不指定时用固定的 180 步 —— 那样不同 ω 测的转角不同（ω=0.2 只转 34°），
# 短窗口既噪声大又可能没脱离起动瞬态，会把转速效应和窗口伪影混在一起。
if args.angle > 0.0 and abs(OMEGA_EFF) > 1e-9:
    MEAS_C3 = max(SAMPLE_EVERY, int(round(math.radians(args.angle) / (abs(OMEGA_EFF) * DT))))
else:
    MEAS_C3 = MEAS
print("\n" + "=" * 72)
print(f"C3 · 原地转 [v=0, ω={OMEGA_EFF}]，稳态后 {MEAS_C3} 步（{MEAS_C3 * DT:.2f} s）测量"
      f" → 目标转角 {math.degrees(abs(OMEGA_EFF) * MEAS_C3 * DT):.1f}°")
print("=" * 72)
reset()
command(0.0, OMEGA)
run_steps(WARM)
p0, y0 = pose()
samples = [pose()]
for k in range(MEAS_C3):
    run_steps(1)
    if (k + 1) % SAMPLE_EVERY == 0:
        samples.append(pose())
p1, y1 = samples[-1]

# ⚠️ 转角必须**逐段累加**，不能用首尾 yaw_diff ——
# 后者会绕回到 (−π, π]，ω≥1.05 rad/s 时 3 s 就转超半圈，误差会被算错（已踩）。
# SAMPLE_EVERY=15 → 每段 0.25 s，即使 ω 取上限 2.0 rad/s 也只有 0.5 rad，累加安全。
dyaw_total = 0.0
_prev_y = y0
for _, _yy in samples[1:]:
    dyaw_total += yaw_diff(_prev_y, _yy)
    _prev_y = _yy
_yaw_endpoint = abs(yaw_diff(y0, y1))
if abs(abs(dyaw_total) - _yaw_endpoint) > 1e-6:
    print(f"  [注] 首尾直接相减会绕回（{_yaw_endpoint:.4f} rad），"
          f"已改用逐段累加（{dyaw_total:.4f} rad）")

exp_yaw = OMEGA_EFF * MEAS_C3 * DT
err_yaw = abs(abs(dyaw_total) - exp_yaw) / exp_yaw
c3a = err_yaw < TOL_ANGULAR

# C3b：由实测运动反解旋转中心，检验「是否绕固定轴自转」
icu, _ = icr_from_pair(p0, y0, p1, y1)
if icu is None:
    icr_radius_spread = float("inf")
    icr_offset_from_origin = float("nan")
    icr_split_diff = float("nan")
    mid = len(samples) // 2
    icr_a = icr_b = None
else:
    radii = [float(np.linalg.norm(p - icu)) for p, _ in samples]
    icr_radius_spread = max(radii) - min(radii)
    icr_offset_from_origin = float(np.linalg.norm(icu - p0))
    mid = len(samples) // 2
    icr_a, _ = icr_from_pair(*samples[0], *samples[mid])
    icr_b, _ = icr_from_pair(*samples[mid], *samples[-1])
    icr_split_diff = (float(np.linalg.norm(icr_a - icr_b))
                      if icr_a is not None and icr_b is not None else float("nan"))
c3b = icr_radius_spread < TOL_ICR_RADIUS

origin_shift = float(np.linalg.norm(p1 - p0))
print(f"  C3a 偏航率   Δyaw = {math.degrees(dyaw_total):.4f}° = {dyaw_total:.5f} rad   "
      f"期望 {exp_yaw:.5f} rad   误差 {err_yaw * 100:.2f}%  (限 {TOL_ANGULAR * 100:.0f}%)")
print(f"      -> {'PASS' if c3a else 'FAIL'}")
print(f"  C3b 旋转轴   实测 ICR = ({icu[0]: .5f}, {icu[1]: .5f})" if icu is not None
      else "  C3b 旋转轴   ICR 无法定解（转角过小）")
print(f"      车体原点到 ICR 距离 {icr_offset_from_origin * 100:.3f} cm   "
      f"（理想驱动轴中点距原点 {np.linalg.norm(axis_offset_body) * 100:.3f} cm）")
print(f"      各采样点到 ICR 的距离极差 = {icr_radius_spread * 100:.4f} cm  "
      f"(限 {TOL_ICR_RADIUS * 100:.0f} cm) → 旋转半径{'恒定，绕固定轴自转' if c3b else '不恒定，不是固定轴自转'}")
print(f"      前半段/后半段各自反解的 ICR 相差 {icr_split_diff * 100:.4f} cm  车体原点总位移 "
      f"{origin_shift * 100:.3f} cm")
print(f"      -> {'PASS' if c3b else 'FAIL'}")

# ---------------------------------------------------------------- C4 收指令衰减

print("\n" + "=" * 72)
print("C4 · 收指令后速度衰减（60 步 = 1 s）")
print("=" * 72)
reset()
command(V, 0.0)
run_steps(120)
v_before = chassis_speed()
command(0.0, 0.0)
run_steps(60)
v_after = chassis_speed()
dof_after = np.round(robot.get_dof_velocities().numpy(), 5).tolist()
c4 = v_after < TOL_STOP_SPEED
print(f"  收指令前线速度 {v_before:.5f} m/s")
print(f"  1 s 后线速度   {v_after:.5f} m/s  (限 {TOL_STOP_SPEED:.3f} m/s)")
print(f"  1 s 后全 DOF 角速度 {dof_after}")
print(f"  -> {'PASS' if c4 else 'FAIL'}")

# ---------------------------------------------------------------- 汇总

print("\n" + "=" * 72)
print("汇总")
print("=" * 72)
results = [
    ("C1", "零指令静止", c1, f"位移 {d_pos * 100:.4f} cm / yaw {math.degrees(d_yaw):.5f}°"),
    ("C2", "直行 v·t", c2, f"Δx={dx:.5f} m 误差 {err_dx * 100:.2f}%"),
    ("C3a", "偏航率 ω·t", c3a, f"Δyaw={dyaw_total:.5f} rad 误差 {err_yaw * 100:.2f}%"),
    ("C3b", "绕固定轴自转", c3b, f"半径极差 {icr_radius_spread * 100:.4f} cm"),
    ("C4", "收指令衰减", c4, f"1 s 后 {v_after:.5f} m/s"),
]
for tid, name, ok, detail in results:
    print(f"  {tid:<4} {name:<14} {'PASS' if ok else 'FAIL'}   {detail}")
all_pass = all(r[2] for r in results)
print(f"\n  === {'ALL PASS' if all_pass else '存在 FAIL'} ===")

if args.dump:
    with open(args.dump, "w") as fh:
        json.dump(
            {
                "dt": DT,
                "wheel_radius": WHEEL_RADIUS,
                "wheel_base_measured": track,
                "wheel_base_doc": WHEEL_BASE_DOC,
                "wheel_base_used": WHEEL_BASE,
                "dof_names": robot.dof_names,
                "link_names": robot.link_names,
                "axis_offset_body": axis_offset_body.tolist(),
                "drive_before": before,
                "drive_after": after,
                "drive_setters_effective": not gains_unchanged,
                "c1": {"d_pos_m": d_pos, "d_yaw_deg": math.degrees(d_yaw), "pass": c1},
                "c2": {"dx": dx, "dy": dy, "expected": exp_dx, "err_pct": err_dx * 100, "pass": c2},
                "c3a": {"dyaw": dyaw_total, "expected": exp_yaw, "err_pct": err_yaw * 100, "pass": c3a},
                "c3b": {"icr": icu.tolist() if icu is not None else None,
                        "icr_offset_from_origin_m": icr_offset_from_origin,
                        "radius_spread_m": icr_radius_spread,
                        "split_icr_diff_m": icr_split_diff,
                        "origin_shift_m": origin_shift, "pass": c3b},
                "c4": {"v_before": v_before, "v_after": v_after, "pass": c4},
                "all_pass": all_pass,
            },
            fh,
            indent=2,
        )
    print(f"  结果已写入 {args.dump}")

# ---------------------------------------------------------------- GUI 演示

if args.gui:
    icr_now = icu if icu is not None else p0
    Cylinder(
        "/World/ICR_Marker",
        radii=0.012,
        heights=0.9,
        colors=[1.0, 0.2, 0.2],
        positions=[float(icr_now[0]), float(icr_now[1]), 0.45],
    )
    print("\n" + "=" * 72)
    print("GUI 演示")
    print("=" * 72)
    print(f"  已在实测旋转中心竖起红色细杆：({icr_now[0]:.4f}, {icr_now[1]:.4f})")
    print("  判据：车体应绕着这根杆自转，杆始终停在原地不动。")
    print("        若车是「画着圈走开」而不是「绕杆自转」，说明旋转轴不固定。")
    print("  按 Ctrl+C 或关窗退出。\n")

    def report(tag):
        p, y = pose()
        print(f"  [{tag:<10}] yaw={math.degrees(y):8.2f}°  车体原点=({p[0]: .4f},{p[1]: .4f})  "
              f"离杆 {np.linalg.norm(p - icr_now) * 100:6.3f} cm")

    report("起始")
    phase = 0
    n_phase = 3 if args.cycle else 1
    while simulation_app.is_running():
        if phase == 0:
            print("  → 原地转 +ω")
            command(0.0, OMEGA)
            run_steps(180)
            command(0.0, 0.0)
            run_steps(30)
            report("正转 3 s")
        elif phase == 1:
            print("  → 原地反向转 −ω")
            command(0.0, -OMEGA)
            run_steps(180)
            command(0.0, 0.0)
            run_steps(30)
            report("反转 3 s")
        else:
            print("  → 直行 +v")
            command(V, 0.0)
            run_steps(120)
            command(0.0, 0.0)
            run_steps(30)
            report("直行 2 s")
        phase = (phase + 1) % n_phase

simulation_app.close()
sys.exit(0 if all_pass else 1)
