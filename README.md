# Astro Play

A 3D educational space-exploration game. You are an astronaut: scan, sample, analyze, diagnose and repair across
four worlds while an AI Space Assistant (powered by **Google Gemini**) helps you reason about real science.
Fully **bilingual: English / العربية**, with music, sound effects and questions that adapt to the player's age.
Built with Python, Ursina, SQLite and (optionally) ChromaDB.

## Install and run
```bash
python -m venv .venv && source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env                                   # then put your Gemini key in .env (optional)
python main.py
```
Python 3.10+ (developed on 3.12). Get a free Gemini API key at https://aistudio.google.com/apikey and set
`GEMINI_API_KEY` in `.env`. Without a key the assistant still works offline from its built-in notes.

## What's new in this version
- **Redesigned look:** drifting nebulae, parallax star layers and shooting stars, a glowing planet horizon,
  neon glass panels with sci-fi corner brackets, glowing buttons, an animated HUD, painted sky domes with a real
  Earth / Jupiter / Sun, craters, haze and floating dust in the 3D worlds. Your logo is kept as-is.
- **Music + sound:** two original looping tracks (menu / mission) and 15 sound effects, all synthesized from scratch.
  Top-right buttons (and the **M** key) switch music on/off; another button switches sound effects. Settings are remembered.
- **Arabic + English:** switch any time with the language button (top-right). Arabic is properly joined and
  right-to-left, the whole layout mirrors, and you can type Arabic questions and names with an Arabic keyboard.
- **Gemini assistant:** streams its answer, tuned per age and language. Easy, playful and short for kids; more
  precise for teens. No markdown or emoji (the fonts don't have them).
- **Questions that really adapt to age (6-9 / 10-13 / 14+):** the mission text, the repair question and
  explanations, the "tap a question" suggestions, the offline answers and a new **Mission Quiz** (+XP) all change
  wording and difficulty by age group.

## Astronaut, habitat and survival update
- **First-person hands, tools and watch:** suited arms and gloves, the selected tool in your right hand (scanner,
  sample collector, spectrometer, repair wrench) with its own equip and use animations, and a digital wristwatch on
  your left wrist showing your real oxygen percentage (turns amber below 30%, flashes red below 15%).
- **Oxygen:** drains while you are outside (faster when walking), not inside the habitat. Warnings and alarm sounds at
  30% and 15%. At 0% the suit's emergency system returns you to your last checkpoint (+1 mistake). Difficulty
  changes the drain rate. Rules live in `astro/suit.py`.
- **Tool batteries:** every successful tool use costs charge (bars under the tool slots). They trickle back slowly
  and are fully recharged at the tool locker. A flat battery blocks that tool.
- **Space habitat** on every map (west of the lander, airlock facing the centre), with real window openings and a sliding
  airlock door. Press **E** while looking at a station (any tool):
  airlock panel (open/close), **science analyzer** (analyzes your collected sample - completes the analysis objective, and once
  everything is analyzed gives a one-time +10 XP detailed report), **bunk** (rest + save a checkpoint),
  **tool locker** (recharge batteries), **oxygen station** outside beside the door (refills your tank).
- **Sounds that follow what you do:** footsteps (dust / gravel / ice / metal, depending on the world and on whether you
  are inside), landing thuds, breathing that speeds up as oxygen drops, tool and wrench sounds, door, bunk, locker, lab,
  oxygen-fill hiss and low-oxygen alarms. All procedural (`scripts/make_audio_extra.py`).
- **Richer surface:** per-world rocky ground textures with a close-range pebble layer, large-scale patches, craters
  with raised rims, textured boulders, footprint trails from the lander, ice shards on Europa, dunes on Mars, hull
  debris at the orbital lab, and soft contact shadows. Real-time sun shadows are available but experimental:
  set `ASTRO_SHADOWS=1` (off by default).

## Controls
| Key | Action |
|---|---|
| WASD / mouse | Move / look |
| 1-4 or scroll | Select tool: Scanner, Sample Collector, Spectrometer, Repair Kit |
| E or left click | Use selected tool on the object under the crosshair, or use the habitat station you are looking at |
| H | Hint (detail adapts to difficulty) |
| Q | Ask the AI Space Assistant (type, press Enter, or tap a suggested question) |
| Tab | Evidence log |
| M | Music on/off |
| Esc | Close panel / leave mission (unsaved) |

## How it plays
Each mission: **scan** the site, **collect** a sample, **analyze** it, **diagnose** a broken system with the Scanner,
then **repair** it by choosing the fix that works in that environment. Finishing awards XP and stars, unlocks the next
world, may grant achievements, and offers a short quiz for bonus XP. Progress saves to SQLite.
Difficulty adapts to how you play (Easy / Normal / Hard).
Missions: Moon -> Mars -> Orbital Lab -> Europa.

## Settings and the LLM
`.env` options: `ASTRO_LLM_PROVIDER` (`gemini` or `none`), `GEMINI_API_KEY`, `ASTRO_LLM_MODEL`
(default `gemini-flash-latest`, the newest Flash model), `ASTRO_LLM_FALLBACKS` (tried in order if the model isn't
available for your key). If anything fails the player simply gets the offline answer.
Player settings (language, music, sound) are stored in `data/settings.json`.

## Files that matter
`main.py` · `astro/game/app.py` screens/HUD/panels · `astro/game/world.py` 3D worlds · `astro/game/ui.py` widgets
(incl. Arabic-capable text box) · `astro/i18n.py` strings + Arabic shaping · `astro/content.py` mission text (EN/AR,
young/standard) · `astro/quiz.py` quizzes + suggested questions · `astro/knowledge.py` offline notes (EN/AR, 3 levels) ·
`astro/assistant.py` Gemini + retrieval · `astro/audio.py` music/SFX · `astro/missions.py` rules · `astro/progression.py`.

## Adding or editing text
Add a string to **both** languages in `astro/i18n.py` (a test fails if one is missing or placeholders differ).
Mission text lives in `astro/content.py`, quiz questions in `astro/quiz.py`. Fonts are bundled
(Cairo for Arabic, Orbitron/Rajdhani for English; all OFL licensed); a test checks every on-screen character exists in the fonts.

## Regenerating art and audio (optional, files are included)
```bash
pip install numpy scipy pillow fonttools
python scripts/make_art.py        # nebulae, stars, horizon, skies, planets, icons
python scripts/make_audio.py      # music + sound effects
python scripts/make_audio_extra.py  # footsteps, breathing, doors, alarms (separate seed: never changes the files above)
python scripts/make_terrain.py    # ground, detail, crater, rock and footprint textures
```

## Tests
```bash
python -m pytest                                        # 73 tests: logic, DB, assistant, Gemini (mocked), Arabic, audio, oxygen, batteries, lab, footsteps
xvfb-run -a python scripts/smoke_test.py shots/         # plays the real game in English and Arabic (106 checks incl. oxygen, habitat stations, sounds), saves screenshots
```

## Troubleshooting
- **No sound:** check the music/sound buttons (top-right). The game runs silently if no audio device exists.
- **Arabic letters look separated/reversed:** install `arabic-reshaper` and `python-bidi` (they're in requirements.txt).
- **Assistant says "AI: offline":** no valid `GEMINI_API_KEY` in `.env`. If a key is set but answers are offline, the
  model name may not be available to your key: set `ASTRO_LLM_MODEL` to one listed in Google AI Studio.
- **"retrieval: keyword":** ChromaDB missing or its embedding model couldn't download. Keyword search works fine.
- **Reset all progress:** delete `data/astro_play.db`.
