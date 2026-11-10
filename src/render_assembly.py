"""Rough assembly render: the designed frame with the off-the-shelf parts as
plain stand-ins, and the bumpers as their envelope. python render_assembly.py frame.stl out.png"""
import sys, math
import numpy as np
import trimesh
sys.path.insert(0, "/home/user/loadpath/docs")
from render3d import Scene
import spec as S
import frame as F

frame = trimesh.load(sys.argv[1])


def ring_sector(c, r0, r1, z0, z1, a0, a1, n=96):
    a = np.linspace(a0, a1, n)
    pts = []
    for r in (r0, r1):
        for z in (z0, z1):
            pts.append(np.stack([c[0] + r * np.cos(a), c[1] + r * np.sin(a), np.full(n, z)], 1))
    P = np.concatenate(pts)              # 4 rows of n: (r0,z0),(r0,z1),(r1,z0),(r1,z1)
    idx = lambda k, i: k * n + i
    faces = []
    loop = [0, 2, 3, 1]                   # around the section
    for i in range(n - 1):
        for j in range(4):
            a_, b_ = loop[j], loop[(j + 1) % 4]
            faces += [[idx(a_, i), idx(b_, i), idx(b_, i + 1)], [idx(a_, i), idx(b_, i + 1), idx(a_, i + 1)]]
    for i in (0, n - 1):
        faces += [[idx(0, i), idx(2, i), idx(3, i)], [idx(0, i), idx(3, i), idx(1, i)]]
    m = trimesh.Trimesh(P, faces, process=True)
    m.fix_normals()
    return m


def box(c, size):
    m = trimesh.creation.box(size)
    m.apply_translation(c)
    return m


def cyl(c, r, h, z0):
    m = trimesh.creation.cylinder(radius=r, height=h, sections=64)
    m.apply_translation([c[0], c[1], z0 + h / 2])
    return m


parts = {"motors": [], "props": [], "bumpers": []}
for (x, y) in F.MOTORS:
    parts["motors"].append(cyl((x, y), S.MOTOR["bellDiameter"] / 2, S.MOTOR["height"], 0.0))
    parts["props"].append(cyl((x, y), S.PROP["diameter"] / 2, 0.6, S.PROP_Z))
    ang = math.atan2(y, x)
    parts["bumpers"].append(ring_sector((x, y), F.R_SEAT, F.R_SEAT + F.BUMPER, F.BUMPER_Z, F.Z1,
                                        ang - math.radians(114), ang + math.radians(114)))
stack = box((0, 0, 8.5), (27, 27, 14))
battery = box((-9, 0, 47), S.BATTERY["size"])
vtx = box((0, 0, 25), S.VTX["board"])
cam = box((36, 0, 41), [26, 19, 19])

TPU = (0.15, 0.16, 0.18)
METAL = (0.35, 0.36, 0.40)
PCB = (0.10, 0.45, 0.25)
BAT = (0.85, 0.55, 0.15)
s = Scene(f"hum: frame {frame.volume * 1.01 / 1000:.0f} g PA12 (designed), the rest stand-ins", panel_size=(820, 620))
for label, view in (("three-quarter", (28, -50)), ("top", (89, -90)), ("side", (4, -90))):
    p = s.panel(label, view=view)
    p.mesh(frame)
    for m in parts["bumpers"]:
        p.mesh(m, color=TPU, opacity=0.55)
    for m in parts["motors"]:
        p.mesh(m, color=METAL)
    for m in parts["props"]:
        p.mesh(m, color=(0.2, 0.5, 0.9), opacity=0.18)
    p.mesh(stack, color=PCB)
    p.mesh(vtx, color=PCB, opacity=0.8)
    p.mesh(cam, color=(0.1, 0.1, 0.1))
    p.mesh(battery, color=BAT, opacity=0.85)
s.render(sys.argv[2])
print("ok")
