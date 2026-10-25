"""Builds the 3D mission environments (sky dome, lit planet in the sky, horizon hills with aerial haze,
craters, boulders, drifting dust and the composed mission props).  Presentation only - no game rules."""
import math
import random

from ursina import *  # noqa: F401,F403
from ursina.prefabs.first_person_controller import FirstPersonController
from ursina.shaders import basic_lighting_shader as LIT
from panda3d.core import TransparencyAttrib

from . import ui

# mission -> (texture, position, scale, halo colour)   texture 'sun' = glowing disc
SKY_BODY = {
    "moon": ("earth.png", (-55, 38, 120), 24, (0.35, 0.6, 1.0)),
    "mars": ("sun", (70, 45, 110), 16, (1.0, 0.9, 0.7)),
    "orbital": ("earth.png", (0, 10, 215), 160, (0.3, 0.6, 1.0)),
    "europa": ("jupiter.png", (-45, 42, 130), 70, (1.0, 0.75, 0.5)),
}
SUN_DIR = {"moon": (1, -0.7, 0.5), "mars": (-0.6, -0.9, 0.7), "orbital": (0.3, -1, 0.4), "europa": (0.8, -0.6, 0.8)}
SUN_COL = {"moon": (1.0, 0.97, 0.9), "mars": (1.0, 0.85, 0.7), "orbital": (1.0, 1.0, 1.0), "europa": (0.85, 0.9, 1.0)}
AMBIENT = {"moon": (0.30, 0.32, 0.42), "mars": (0.45, 0.33, 0.28), "orbital": (0.38, 0.4, 0.5), "europa": (0.34, 0.38, 0.5)}
HAZE = {"moon": (0.07, 0.09, 0.2), "mars": (0.9, 0.55, 0.38), "orbital": (0.05, 0.1, 0.28), "europa": (0.22, 0.27, 0.5)}


def C(rgb, a=1.0):
    return Color(rgb[0], rgb[1], rgb[2], a)


def shade(rgb, f):
    return tuple(max(0.0, min(1.0, c * f)) for c in rgb)


def mixc(a, b, t):
    return tuple(a[i] * (1 - t) + b[i] * t for i in range(3))


class World:
    """Holds everything created for one mission so it can be updated and destroyed together."""

    def __init__(self, mission):
        self.mission = mission
        self.entities = []
        self.lights = []
        self.markers = {}
        self.dust = []
        self.planet = None
        self.player = None
        self._rng = random.Random(mission.id)
        self._build()

    # -- helpers
    def ent(self, **k):
        k.setdefault("shader", LIT)
        e = Entity(**k)
        self.entities.append(e)
        return e

    def _build(self):
        m, rng = self.mission, self._rng
        gcol = C(m.ground_color)
        haze = HAZE[m.id]
        # -- sky dome with painted stars / milky way
        sky = Sky(texture=ui.tex(f"sky/sky_{m.id}.png"))
        self.entities.append(sky)
        # -- lights
        sun = DirectionalLight(shadows=False, color=C(SUN_COL[m.id]))
        sun.look_at(Vec3(*SUN_DIR[m.id]))
        amb = AmbientLight(color=Color(*AMBIENT[m.id], 1))
        self.lights = [sun, amb]
        # -- ground
        self.ent(model="plane", scale=(140, 1, 140), texture=ui.tex("ground.png"), texture_scale=(30, 30),
                 color=gcol, collider="box")
        self._craters(rng, m)
        # -- sky body with halo and terminator shading
        tname, spos, ssc, halo = SKY_BODY[m.id]
        if tname == "sun":
            h = self.ent(model="quad", shader=None, billboard=True, texture=ui.tex("sky/sun.png"), position=spos,
                         scale=ssc * 3.2, color=C((1, 1, 1), 1))
            h.setTransparency(TransparencyAttrib.MAlpha)
        else:
            self.planet = self.ent(model="sphere", shader=None, unlit=True, texture=ui.tex(f"sky/{tname}"),
                                   position=spos, scale=ssc, rotation_y=rng.uniform(0, 360))
            h = self.ent(model="quad", shader=None, billboard=True, texture=ui.tex("glow.png"), position=spos,
                         scale=ssc * 2.3, color=C(halo, 0.40))
            h.setTransparency(TransparencyAttrib.MAlpha)
            sh = self.ent(model="quad", shader=None, billboard=True, texture=ui.tex("planet_shade.png"),
                          position=(spos[0] * 0.995, spos[1], spos[2] * 0.995 - 0.5), scale=ssc * 1.02,
                          color=color.white)
            sh.setTransparency(TransparencyAttrib.MAlpha)
        # -- horizon hills fade toward the haze colour with distance (aerial perspective)
        for i in range(34):
            a = i / 34 * 6.283 + rng.uniform(-0.1, 0.1)
            d, hh, w = rng.uniform(78, 98), rng.uniform(9, 28), rng.uniform(22, 40)
            base = shade(m.ground_color, rng.uniform(0.45, 0.7))
            self.ent(model="sphere", position=(d * math.cos(a), -2, d * math.sin(a)), scale=(w, hh * 1.5, w),
                     color=C(mixc(base, haze, 0.45)))
        # -- boulders and small rocks
        for _ in range(55):
            sz = rng.uniform(0.5, 2.4)
            x, z = rng.uniform(-55, 55), rng.uniform(-55, 55)
            if abs(x) < 17 and abs(z) < 17:
                continue
            self.ent(model="sphere", scale=(sz * 1.3, sz * 0.8, sz), position=(x, sz * 0.25, z), collider="box",
                     rotation_y=rng.uniform(0, 360), color=C(shade(m.ground_color, rng.uniform(0.6, 0.95))))
        for _ in range(90):
            sz = rng.uniform(0.12, 0.4)
            x, z = rng.uniform(-30, 30), rng.uniform(-30, 30)
            self.ent(model="sphere", scale=(sz * 1.4, sz * 0.7, sz), position=(x, sz * 0.15, z),
                     color=C(shade(m.ground_color, rng.uniform(0.5, 1.0))))
        # -- lander + props
        self._lander()
        for o in m.objects:
            self._prop(o)
            mk = self.ent(model="diamond", shader=None, unlit=True, scale=(0.5, 0.8, 0.5), color=C(ui.GOLD),
                          position=(o.pos[0], o.size[1] + 1.6, o.pos[1]), enabled=False)
            self.markers[o.id] = mk
        # -- floating dust motes near the player
        for _ in range(70):
            e = self.ent(model="quad", shader=None, billboard=True, texture=ui.tex("speck.png"),
                         position=(rng.uniform(-22, 22), rng.uniform(0.4, 7), rng.uniform(-30, 14)),
                         scale=rng.uniform(0.05, 0.14), color=C(mixc(haze, (1, 1, 1), 0.6), rng.uniform(0.25, 0.6)))
            e.setTransparency(TransparencyAttrib.MAlpha)
            e._ph = rng.uniform(0, 6.28)
            e._sp = rng.uniform(0.15, 0.5)
            self.dust.append(e)
        self.player = FirstPersonController(position=(0, 2, -18), speed=7)
        self.player.cursor.enabled = False
        self.entities.append(self.player)

    def _craters(self, rng, m):
        for _ in range(26):
            r = rng.uniform(2.0, 7.5)
            x, z = rng.uniform(-60, 60), rng.uniform(-60, 60)
            if abs(x) < 15 and abs(z) < 20:
                continue
            col = shade(m.ground_color, 0.62)
            self.ent(model="circle", shader=None, rotation_x=90, position=(x, 0.03, z), scale=r * 2,
                     color=C(col, 0.9))
            self.ent(model="circle", shader=None, rotation_x=90, position=(x + r * 0.07, 0.035, z + r * 0.07),
                     scale=r * 1.62, color=C(shade(m.ground_color, 0.88), 0.9))
            self.ent(model="circle", shader=None, rotation_x=90, position=(x, 0.04, z), scale=r * 1.5,
                     color=C(shade(m.ground_color, 0.72), 0.95))

    def _lander(self):
        ent = self.ent
        w = (0.86, 0.88, 0.92)
        ent(model="cube", scale=(4, 2.4, 4), position=(0, 3.0, -25), color=C(w), collider="box")
        ent(model="cube", scale=(4.4, 0.4, 4.4), position=(0, 1.7, -25), color=C(shade(w, 0.7)))
        for sx in (-1, 1):
            for sz in (-1, 1):
                ent(model="cube", scale=(0.25, 2.6, 0.25), position=(sx * 2.4, 1.0, -25 + sz * 2.4),
                    rotation=(sz * 14, 0, -sx * 14), color=C(shade(w, 0.55)))
                ent(model="cube", scale=(1, 0.18, 1), position=(sx * 2.8, 0.1, -25 + sz * 2.8), color=C(shade(w, 0.5)))
        ent(model="cube", scale=(1.2, 1.4, 0.1), position=(0, 2.7, -22.97), color=C((0.1, 0.15, 0.3)))
        ent(model="sphere", shader=None, unlit=True, scale=0.35, position=(0, 5.6, -25), color=C(ui.CYAN))
        ent(model="cube", scale=(0.1, 1.6, 0.1), position=(0, 4.9, -25), color=C(shade(w, 0.6)))

    def _prop(self, o):
        ent, rng = self.ent, self._rng
        x, z = o.pos
        w, h, d = o.size
        base = o.color
        ent(model="cube", shader=None, color=Color(0, 0, 0, 0), position=(x, h / 2, z), scale=(w, h, d),
            collider="box", obj_id=o.id)                              # invisible hit-box
        light = lambda col, y, sx=0.0, sz=0.0: ent(model="sphere", shader=None, unlit=True, scale=0.3,
                                                   position=(x + sx, y, z + sz), color=C(col))
        if o.id == "solar_array":
            for dx in (-w * 0.25, w * 0.25):
                ent(model="cube", scale=(0.18, h * 0.6, 0.18), position=(x + dx * 1.6, h * 0.3, z), color=C((0.5, 0.5, 0.55)))
            ent(model="cube", scale=(w, h * 0.7, 0.14), position=(x, h * 0.62, z), rotation_x=-14,
                texture="white_cube", texture_scale=(8, 3), color=C((0.12, 0.25, 0.7)))
            ent(model="cube", scale=(w + 0.2, h * 0.75, 0.1), position=(x, h * 0.62, z + 0.08), rotation_x=-14,
                color=C((0.7, 0.72, 0.78)))
        elif o.id in ("regolith", "clay_rock", "salt_ice"):
            for _ in range(6):
                s = rng.uniform(0.5, 1.0) * w * 0.55
                ent(model="sphere", scale=(s, s * rng.uniform(0.6, 0.9), s),
                    position=(x + rng.uniform(-w * 0.4, w * 0.4), s * 0.3, z + rng.uniform(-d * 0.4, d * 0.4)),
                    color=C(shade(base, rng.uniform(0.8, 1.15))))
            if o.id == "clay_rock":
                for k in range(3):
                    ent(model="cube", scale=(w * (0.9 - k * 0.2), 0.18, d * (0.9 - k * 0.2)),
                        position=(x, 0.4 + k * 0.5, z), color=C(shade(base, 1.2 - k * 0.15)))
            if o.id == "salt_ice":
                for k in range(4):
                    ent(model="cube", scale=(0.12, 0.9, 0.4), position=(x - 1 + k * 0.7, 0.9, z + 0.6),
                        rotation_z=rng.uniform(-15, 15), color=C((0.6, 0.35, 0.25)))
        elif o.id in ("riverbed", "ice_ridge"):
            n = 9 if o.id == "riverbed" else 6
            for k in range(n):
                t = (k / (n - 1) - 0.5) * w * 0.9
                s = rng.uniform(0.7, 1.2)
                if o.id == "riverbed":
                    ent(model="sphere", scale=(s * 1.2, s * 0.55, s), position=(x + t, 0.25, z + rng.uniform(-d * 0.3, d * 0.3)),
                        color=C(shade(base, rng.uniform(0.7, 1.2))))
                else:
                    ent(model="cube", scale=(0.9, h * rng.uniform(0.7, 1.3), 0.7), position=(x + t, h * 0.4, z),
                        rotation=(0, rng.uniform(-20, 20), rng.uniform(-18, 18)), color=C(shade(base, rng.uniform(0.85, 1.1))))
        elif o.id == "rover":
            ent(model="cube", scale=(w, 0.8, d * 0.85), position=(x, 1.0, z), color=C((0.85, 0.85, 0.88)))
            ent(model="cube", scale=(w * 0.8, 0.12, d * 0.8), position=(x, 1.5, z), color=C((0.25, 0.3, 0.45)))
            for sx in (-1, 0, 1):
                for sz in (-1, 1):
                    ent(model="cube", scale=(0.55, 0.55, 0.28), position=(x + sx * w * 0.38, 0.32, z + sz * d * 0.5),
                        color=C((0.12, 0.12, 0.14)))
            ent(model="cube", scale=(0.1, 1.1, 0.1), position=(x + w * 0.3, 1.9, z), color=C((0.6, 0.6, 0.65)))
            ent(model="cube", scale=(0.4, 0.25, 0.25), position=(x + w * 0.3, 2.5, z), color=C((0.2, 0.2, 0.25)))
            light(ui.RED, 1.65, w * 0.4, 0)
        elif o.id == "plant_rack":
            for k in range(3):
                ent(model="cube", scale=(w, 0.12, d), position=(x, 0.6 + k * 1.0, z), color=C((0.75, 0.78, 0.85)))
                for j in range(4):
                    ent(model="sphere", scale=0.5, position=(x - w * 0.35 + j * w * 0.23, 0.95 + k * 1.0, z),
                        color=C(shade(base, rng.uniform(0.8, 1.2))))
            for sx in (-1, 1):
                ent(model="cube", scale=(0.1, h, 0.1), position=(x + sx * w * 0.48, h / 2, z - d * 0.4), color=C((0.5, 0.5, 0.55)))
        elif o.id == "earth_window":
            ent(model="cube", scale=(w, h, d), position=(x, h / 2, z), color=C((0.3, 0.32, 0.38)))
            ent(model="cube", shader=None, unlit=True, scale=(0.06, h * 0.7, d * 0.8), position=(x - w / 2 - 0.02, h / 2, z),
                color=C((0.2, 0.5, 0.95)))
            ent(model="cube", shader=None, unlit=True, scale=(0.07, h * 0.15, d * 0.4), position=(x - w / 2 - 0.03, h * 0.6, z + 0.5),
                color=C((0.95, 0.97, 1.0)))
        else:                                                         # machines: relay, scrubber, drill
            ent(model="cube", scale=(w * 1.3, 0.3, d * 1.3), position=(x, 0.15, z), color=C((0.25, 0.27, 0.33)))
            ent(model="cube", scale=(w * 0.8, h * 0.8, d * 0.8), position=(x, h * 0.5, z), color=C(base))
            for k in range(4):
                ent(model="cube", scale=(w * 0.82, 0.07, d * 0.82), position=(x, h * 0.25 + k * 0.4, z), color=C(shade(base, 0.6)))
            ent(model="cube", scale=(0.08, 1.4, 0.08), position=(x, h + 0.7, z), color=C((0.7, 0.7, 0.75)))
            light(ui.RED, h + 1.5)
            if o.id == "drill":
                ent(model="diamond", scale=(0.5, 1.4, 0.5), position=(x, 0.9, z + d * 0.8), rotation_x=180, color=C((0.7, 0.7, 0.75)))

    # -- per-frame ambience
    def update(self, t, dt):
        if self.planet is not None and not self.planet.is_empty():
            self.planet.rotation_y += 1.2 * dt
        for e in self.dust:
            if e.is_empty():
                continue
            e.y += math.sin(t * e._sp + e._ph) * 0.15 * dt
            e.x += math.cos(t * e._sp * 0.7 + e._ph) * 0.2 * dt

    def destroy(self):
        for e in self.entities + self.lights:
            try:
                destroy(e)
            except Exception:
                pass
        self.entities, self.lights, self.markers, self.dust, self.planet, self.player = [], [], {}, [], None, None
