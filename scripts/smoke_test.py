"""Headless end-to-end smoke test of the real Ursina game (needs a display or xvfb).

    xvfb-run -a python scripts/smoke_test.py [screenshot_dir]

Plays through menu -> profile -> map -> mission -> completion -> quiz in English, then switches to Arabic
and checks the main screens, the music/sound toggles and the language switch.
"""
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from ursina import Ursina, Text, application, camera, Vec3  # noqa: E402

from astro import config, i18n  # noqa: E402
from astro.assistant import SpaceAssistant  # noqa: E402
from astro.db import Database  # noqa: E402
from astro.game import ui  # noqa: E402
from astro.game.app import Game  # noqa: E402
from astro.settings import Settings  # noqa: E402

shots = Path(sys.argv[1]) if len(sys.argv) > 1 else None
if shots:
    shots.mkdir(parents=True, exist_ok=True)

Text.default_resolution = 1080 * Text.size
app = Ursina(title="Astro Play smoke", borderless=False, development_mode=False, size=(1280, 720))
tmp = Path(tempfile.mkdtemp())
db = Database(tmp / "smoke.db")
settings = Settings.load(tmp / "settings.json")
config.SETTINGS_PATH = tmp / "settings.json"
game = Game(db, SpaceAssistant(use_chroma=False), settings)


def step(n=3):
    for _ in range(n):
        app.step()


def shot(name):
    step(3)
    if shots:
        from panda3d.core import Filename
        application.base.win.save_screenshot(Filename.from_os_specific(str(shots / (name + ".png"))))


def check(cond, msg):
    print(("PASS " if cond else "FAIL ") + msg)
    if not cond:
        sys.exit(1)


def play_mission(mid, tag):
    game.show_briefing(mid); step(); check(game.mode == "briefing", f"[{tag}] briefing"); shot(f"{tag}_briefing")
    m = game.briefing_mission
    game.start_mission(m); step(5)
    check(game.mode == "mission" and game.world.player is not None, f"[{tag}] 3D mission world built")
    first = m.objects[0]
    game.world.player.position = Vec3(first.pos[0], 2, first.pos[1] - 6)
    game.world.player.rotation_y = 0
    game.world.player.camera_pivot.rotation_x = 12
    step(3)
    shot(f"{tag}_mission")
    check(game._target == first.id, f"[{tag}] crosshair targets {first.id}")
    game.tool_index = 0
    game.use_equipment(); step()
    check("scan_site" in game.state.done, f"[{tag}] raycast + scanner completes an objective")
    game.open_log(); step(); check(game.panel_kind == "log" and not game.world.player.enabled, f"[{tag}] log freezes player"); shot(f"{tag}_log")
    game.close_panel(); check(game.world.player.enabled, f"[{tag}] panel closes, player restored")
    game.open_ask(); step()
    game.ask_box.set_value("Why do astronauts float?" if tag.startswith("en") else "\u0644\u0645\u0627\u0630\u0627 \u064a\u0637\u0641\u0648 \u0631\u0627\u0626\u062f \u0627\u0644\u0641\u0636\u0627\u0621\u061f")
    game._submit_ask()
    for _ in range(60):
        step(2)
        if game._answer and game._answer != game.T("thinking") and not game._asking:
            break
    step(3)
    check(game._answer and game._answer != game.T("thinking"), f"[{tag}] assistant answered")
    shot(f"{tag}_ask")
    game.close_panel()
    fix = m.objects[2]
    game.open_repair(fix.id); step(); check(game.panel_kind == "repair", f"[{tag}] repair panel"); shot(f"{tag}_repair"); game.close_panel()
    st = game.state
    st.use_tool("sampler", m.objects[1].id); st.use_tool("analyzer", m.objects[1].id); st.use_tool("scanner", fix.id)
    idx = next(i for i, o in st.repair_options(fix.id) if o.correct)
    game.choose_fix(fix.id, idx); step()
    check(st.complete, f"[{tag}] mission objectives complete")
    game.finish_mission(); step(3)
    check(game.mode == "complete", f"[{tag}] completion screen"); shot(f"{tag}_complete")
    game.start_quiz(m); step(); check(game.mode == "quiz", f"[{tag}] quiz screen"); shot(f"{tag}_quiz")
    q, opts, correct, expl = game._quiz["qs"][0]
    game.answer_quiz(correct); step(); shot(f"{tag}_quiz_answer")
    game.next_quiz(); step()
    game.answer_quiz((game._quiz["qs"][1][2] + 1) % 3); step()
    game.next_quiz(); step(); check(game.mode == "quiz_result", f"[{tag}] quiz result"); shot(f"{tag}_quiz_result")


check(game.mode == "splash", "splash screen shows")
step(); shot("1_splash")
game.show_menu(); step(); check(game.mode == "menu", "main menu"); shot("2_menu")
game.show_profile_creation(); step(); shot("3_profile")
game.name_box.set_value("Nova"); game._pick_age("young"); game._profile_next(); step()
check(game.mode == "customize", "customization screen"); shot("4_customize")
game._pick_suit(1); game._pick_visor(2); game._create_profile(); step()
check(game.mode == "map" and game.profile, "profile created -> galaxy map")
p = db.get_profile(game.profile["id"])
check((p["name"], p["age_group"], p["suit_color"], p["visor_color"]) == ("Nova", "young", "Orbit", "Rose"), "profile saved correctly")
shot("5_map")

# music / sound toggles persist
on = game.audio.toggle_music(); check(on is False and not game.settings.music, "music can be switched off")
game.toggle_music(); check(game.settings.music, "music can be switched back on")
game.audio.toggle_sfx(); check(not game.settings.sfx, "sound effects can be switched off"); game.audio.toggle_sfx()
check(Settings.load(tmp / "settings.json").music is True, "settings persisted to disk")

play_mission("moon", "en_moon")
game.show_galaxy_map(); step(); shot("en_map_after")

# ---- Arabic
game.set_language("ar"); step()
check(game.lang == "ar" and game.rtl, "language switched to Arabic")
shot("ar_map")
game.show_menu(); step(); shot("ar_menu")
game.start_new_game(); step()
game.name_box.set_value("\u0623\u062d\u0645\u062f"); shot("ar_profile")
game.show_customization(); step(); shot("ar_customize")
game.show_galaxy_map(); step()
play_mission("mars", "ar_mars")
game.show_galaxy_map(); step(); shot("ar_map_after")
game.set_language("en"); step(); check(game.lang == "en" and not game.rtl, "switched back to English")
game.show_continue(); step(); shot("en_continue")
print("ALL SMOKE CHECKS PASSED")
