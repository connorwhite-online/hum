"""The designed rotors, side by side. python render_props.py ../out/props out.png"""
import json, sys
from pathlib import Path
import trimesh
sys.path.insert(0, "/home/user/lp-push/docs")
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
closes = []
for name in sorted(best, key=lambda k: rows[(k, best[k])]["hoverWatts"]):
    r = rows[(name, best[name])]
    m = trimesh.load(d / f"{name}-ccw.stl")
    zc = 0.5 * (m.bounds[0][2] + m.bounds[1][2])
    fl = r.get("fillet", {}).get("radius", 0)
    p = s.panel(f"{name} root: {fl:.1f} mm fillet, hub {r.get('hubHeight', 0):.1f} mm", view=(30, -35),
                center=(9.0, 0.0, zc), span=22)
    p.mesh(m, color=(0.92, 0.92, 0.9))
# one row each: whole rotors, then their roots (a single row this wide tiles badly)
from PIL import Image
out = Path(sys.argv[2])
n = len(best)
top, bot = Scene(s.title, panel_size=s.panel_size), Scene(None, panel_size=s.panel_size)
top.panels, bot.panels = s.panels[:n], s.panels[n:]
top.render(str(out.with_suffix(".top.png")))
bot.render(str(out.with_suffix(".bot.png")))
a, b = Image.open(out.with_suffix(".top.png")), Image.open(out.with_suffix(".bot.png"))
im = Image.new("RGB", (max(a.width, b.width), a.height + b.height), "white")
im.paste(a, (0, 0)); im.paste(b, (0, a.height)); im.save(out)
out.with_suffix(".top.png").unlink(); out.with_suffix(".bot.png").unlink()
print("ok")
