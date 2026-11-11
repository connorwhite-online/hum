"""The designed rotors, side by side. python render_props.py ../out/props out.png"""
import json, sys
from pathlib import Path
import trimesh
sys.path.insert(0, "/home/user/loadpath/docs")
from render3d import Scene

d = Path(sys.argv[1])
rep = json.loads((d / "props.json").read_text())
best = rep["best"]
rows = {(r["name"], r["blades"]): r for r in rep["designs"]}
s = Scene("hum rotors, PA12 SLS, each designed for the least watts at hover", panel_size=(620, 560))
for name in sorted(best, key=lambda k: rows[(k, best[k])]["hoverWatts"]):
    r = rows[(name, best[name])]
    m = trimesh.load(d / f"{name}-ccw.stl")
    p = s.panel(f"{name}: {r['blades']} blades, {r['hoverWatts']:.1f} W hover, {r['bladeMass']:.1f} g blades", view=(35, -60))
    p.mesh(m, color=(0.92, 0.92, 0.9))
s.render(sys.argv[2])
print("ok")
