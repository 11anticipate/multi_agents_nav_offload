"""Carter v1 查看器

默认开 GUI：加载 Carter + 地面 + 光照，直接看。
加 --headless 则只打印结构信息（关节名、尺寸），不渲染。

用法（Isaac Sim 独立 Python）：
    /home/gsh/isaacsim/python.sh tools/view_carter.py
    /home/gsh/isaacsim/python.sh tools/view_carter.py --headless

注意：Isaac Sim GUI 默认打开的是**空场景**，不加载任何东西就没有画面。
本脚本会主动创建地面/光照/相机并加载 Carter。
"""
import argparse
import sys

parser = argparse.ArgumentParser()
parser.add_argument("--headless", action="store_true", help="只打印结构，不渲染")
args, _ = parser.parse_known_args()

from isaacsim import SimulationApp  # noqa: E402

simulation_app = SimulationApp({
    "headless": args.headless,
    "width": 1280,
    "height": 800,
})

import isaacsim.core.experimental.utils.app as app_utils  # noqa: E402
import isaacsim.core.experimental.utils.stage as stage_utils  # noqa: E402
from isaacsim.core.experimental.objects import DistantLight, GroundPlane  # noqa: E402
from isaacsim.core.simulation_manager import PhysicsScene, SimulationManager  # noqa: E402
import omni.usd  # noqa: E402
from pxr import Usd, UsdGeom  # noqa: E402

ROOT = "https://omniverse-content-production.s3-us-west-2.amazonaws.com/Assets/Isaac/6.0"
CARTER_URL = f"{ROOT}/Isaac/Robots/NVIDIA/Carter/carter_v1.usd"

stage_utils.create_new_stage()

# 物理与光照（缺一不可，否则场景全黑 / 物理不动）
pscene = PhysicsScene("/World/PhysicsScene")
SimulationManager.set_default_physics_scene("/World/PhysicsScene")
pscene.set_gravity((0.0, 0.0, -9.81))
GroundPlane("/World/GroundPlane", positions=[0, 0, 0])
light = DistantLight("/World/DistantLight")
light.set_intensities(1000)

# 加载 Carter 到 /World/Carter
stage = omni.usd.get_context().get_stage()
stage.DefinePrim("/World/Carter", "Xform")
omni.usd.get_context().get_stage().GetPrimAtPath("/World/Carter").GetReferences().AddReference(CARTER_URL)

for _ in range(60):
    simulation_app.update()

n = len([p for p in stage.Traverse()])
print(f"\n[场景] prim 总数 = {n}")

print("\n[关节]（S4 配 DifferentialController 要用这些名字）")
for p in stage.Traverse():
    if "Joint" in p.GetTypeName():
        print(f"  {p.GetPath().pathString:<60} {p.GetTypeName()}")

print("\n[Carter 整体尺寸]")
cache = UsdGeom.BBoxCache(Usd.TimeCode.Default(), ["default", "render"])
prim = stage.GetPrimAtPath("/World/Carter")
if prim.IsValid():
    size = cache.ComputeWorldBound(prim).GetRange().GetSize()
    print(f"  X={size[0]:.3f}  Y={size[1]:.3f}  Z={size[2]:.3f}  (m)")

if args.headless:
    print("\n[headless 模式] 结束。要看画面请去掉 --headless。")
    simulation_app.close()
    sys.exit(0)

# GUI：把相机对准机器人
app_utils.play()
simulation_app.update()
print("\n[GUI] 场景已就绪，可在视口中查看 Carter。按 Ctrl+C 或关闭窗口退出。")
while simulation_app.is_running():
    simulation_app.update()
simulation_app.close()
