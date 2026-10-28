"""Languages (English / Arabic), Arabic text shaping and right-to-left helpers.

Panda3D draws text left-to-right with no shaping, so Arabic must be *reshaped* (letters joined) and
*reordered* (bidi) before it is drawn.  Every string shown on screen goes through :func:`shape` exactly once
(the UI helpers in ``astro/game/ui.py`` do this); never shape text twice.

Logic modules (missions, assistant) only deal with *logical* text and accept an explicit ``lang``.
"""
import re
import textwrap
from typing import Dict

LANGS = ("en", "ar")
LANG_NAMES = {"en": "English", "ar": "\u0627\u0644\u0639\u0631\u0628\u064a\u0629"}

_current = "en"

try:  # optional at import time so logic and tests still work without the Arabic packages
    import arabic_reshaper
    from bidi.algorithm import get_display
    _reshaper = arabic_reshaper.ArabicReshaper(configuration={"use_unshaped_instead_of_isolated": True,
                                                              "delete_harakat": True})
except Exception:  # pragma: no cover
    _reshaper = None
    get_display = None

_ARABIC = re.compile("[\u0600-\u06FF\u0750-\u077F]")


def set_lang(code: str):
    global _current
    _current = code if code in LANGS else "en"


def get_lang() -> str:
    return _current


def is_rtl(lang: str = None) -> bool:
    return (lang or _current) == "ar"


def has_arabic(text: str) -> bool:
    return bool(_ARABIC.search(text or ""))


def shape(text: str, force: bool = None) -> str:
    """Return text ready to draw.  Arabic is reshaped + bidi-reordered; everything else is untouched.
    ``force`` overrides auto-detection (default: shape if the text contains Arabic letters)."""
    if text is None:
        return ""
    text = str(text)
    do = has_arabic(text) if force is None else force
    if not do or _reshaper is None or get_display is None:
        return text
    lines = []
    for line in text.split("\n"):
        lines.append(get_display(_reshaper.reshape(line), base_dir="R") if has_arabic(line) else line)
    return "\n".join(lines)


def wrap(text: str, width: int = 60) -> str:
    """Word-wrap *logical* text (call before shape)."""
    return "\n".join(textwrap.fill(p, width) if p.strip() else "" for p in str(text).split("\n"))


def font(kind: str = "body", lang: str = None, text: str = None) -> str:
    """Font file name (looked up in assets/fonts).  kind: 'display' (titles) or 'body'.
    If ``text`` contains Arabic letters the Arabic-capable font is used whatever the UI language is."""
    if (lang or _current) == "ar" or (text is not None and has_arabic(text)):
        return "Cairo-Black.ttf" if kind == "display" else "Cairo-Bold.ttf"
    return "Orbitron-Bold.ttf" if kind == "display" else "Rajdhani-Bold.ttf"


def t(key: str, lang: str = None, **kw) -> str:
    code = lang or _current
    table = STRINGS.get(code, STRINGS["en"])
    s = table.get(key)
    if s is None:
        s = STRINGS["en"].get(key, key)
    try:
        return s.format(**kw) if kw else s
    except (KeyError, IndexError):
        return s


def has_key(key: str, lang: str) -> bool:
    return key in STRINGS[lang]


STRINGS: Dict[str, Dict[str, str]] = {
    "en": {
        # ---- common
        "tagline": "EXPLORE  \u2022  DISCOVER  \u2022  LEARN",
        "loading": "Loading mission control...",
        "press_start": "Press any key",
        "new_game": "New Game", "continue": "Continue", "quit": "Quit", "back": "Back", "next": "Next",
        "music": "Music", "sound": "Sound", "language": "Language", "on": "ON", "off": "OFF",
        "music_hint": "Music (M)", "sfx_hint": "Sound effects", "lang_hint": "Language",
        "assistant_backend": "AI assistant retrieval: {backend}",
        "assistant_llm": "AI: {llm}",
        # ---- profile
        "create_profile": "Create your profile", "astro_name": "Astronaut name",
        "age_hint": "Age group  (changes how science is explained)",
        "age_young": "Ages 6-9", "age_mid": "Ages 10-13", "age_teen": "Ages 14+",
        "default_name": "Astro", "type_name": "Type your name",
        "suit_up": "Suit up, {name}!", "visor_color": "Visor color", "suit_color": "Suit color",
        "launch_map": "Launch to Galaxy Map", "choose_astronaut": "Choose your astronaut",
        # ---- map
        "galaxy_map": "G A L A X Y   M A P", "level": "LEVEL {n}", "xp_line": "{xp} / {hi} XP",
        "easy": "EASY", "normal": "NORMAL", "hard": "HARD",
        "achievements_count": "Achievements  {a}/{b}", "main_menu": "Main Menu", "locked": "LOCKED",
        "aborted": "Mission aborted. Progress in that attempt wasn't saved.",
        # ---- briefing
        "science_focus": "Science focus:  {x}", "objectives": "OBJECTIVES", "controls": "CONTROLS",
        "key_move": "Move", "key_look": "Look", "key_tools": "Tools", "key_use": "Use", "key_hint": "Hint",
        "key_ask": "Ask AI", "key_log": "Log", "key_leave": "Leave", "key_mouse": "Mouse",
        "difficulty": "Difficulty: {t}", "adapts": "adapts to how you play", "launch": "LAUNCH!",
        # ---- HUD / tools
        "tool_scanner": "Scanner", "tool_sampler": "Sample Collector", "tool_analyzer": "Spectrometer",
        "tool_wrench": "Repair Kit",
        "glyph_scanner": "SCAN", "glyph_sampler": "COLLECT", "glyph_analyzer": "ANALYZE", "glyph_wrench": "REPAIR",
        "start_tip": "Select the Scanner (1) and press E on equipment.  H = hint.",
        "hud_info": "Difficulty: {t}\nMistakes {m}   Hints {h}",
        "hud_keys": "H Hint   Q Ask AI   Tab Log   M Music   Esc Leave",
        # ---- panels
        "repair_title": "REPAIR  \u2022  {name}", "diagnosis": "Diagnosis: {d}",
        "fix_question": "Which fix will work in this environment?",
        "fix_question_young": "Which fix is the best one here?",
        "esc_cancel": "Esc to cancel", "esc_close": "Esc to close",
        "log_title": "EVIDENCE LOG", "log_empty": "Nothing yet. Scan objects to gather evidence.",
        "ask_title": "AI SPACE ASSISTANT",
        "ask_hint": "Ask a science question about this mission, then press Enter.",
        "ask_placeholder": "Type your question here...", "try_asking": "Or tap a question:",
        "thinking": "Thinking...", "comms_down": "My comms are down. Try again!",
        "ask_empty": "Ask me anything about the mission or the science!", "ask_btn": "Ask",
        "no_data": "I don't have data on that yet. Try scanning nearby objects, or ask about the environment you're exploring.",
        "from_notes": "From my notes:",
        # ---- completion & quiz
        "complete": "MISSION COMPLETE", "xp_total": "+{xp} XP      total {total}      Level {lvl}",
        "level_up": "LEVEL UP!",
        "stats": "Mistakes {m}    Hints {h}    Time {s}s    Next difficulty: {t}",
        "unlocked": "UNLOCKED: {names}", "achievement": "Achievement: {text}",
        "learned": "WHAT YOU LEARNED", "deep_dive": "DEEP DIVE",
        "back_to_map": "Back to Galaxy Map", "take_quiz": "Take the Quiz  (+XP)",
        "quiz_title": "MISSION QUIZ", "quiz_q": "Question {i} of {n}",
        "quiz_correct": "Correct!  +{xp} XP", "quiz_wrong": "Not quite.", "quiz_next": "Next question",
        "quiz_finish": "Finish", "quiz_result": "You got {c} of {n} right!  +{xp} XP",
        "quiz_great": "Amazing work, astronaut!", "quiz_ok": "Good try. Every explorer learns by trying!",
        # ---- achievements
        "ach_first_mission": "First Landing: complete your first mission",
        "ach_flawless": "Flawless: finish a mission with no mistakes or hints",
        "ach_scientist": "Field Scientist: analyze 5 samples in total",
        "ach_problem_solver": "Problem Solver: complete 3 missions",
        "ach_explorer": "Galaxy Explorer: complete every mission",
        "ach_level_5": "Veteran Astronaut: reach level 5",
        # ---- mission engine messages
        "aim_at": "Aim at an object to use the tool.", "unknown_tool": "Unknown tool.", "nothing_happened": "Nothing happened.",
        "nothing_collect": "Nothing to collect from the {name}.", "sample_done": "Sample already collected.",
        "sample_ok": "Sample collected from {name}. Analyze it with the Spectrometer.",
        "nothing_analyze": "The {name} has nothing to analyze.", "collect_first": "Collect a sample first.",
        "already_analyzed": "Already analyzed.", "analysis_msg": "Analysis: {text}",
        "no_repair": "The {name} doesn't need repairs.", "already_repaired": "Already repaired.",
        "diagnose_first": "Diagnose first! Scan it to find out what's wrong.",
        "scanned_msg": "Scanned {name}. {fact}", "already_scanned": "{name}: already scanned.",
        "repair_impossible": "Repair not possible right now.", "repaired": "Repaired! {expl}",
        "wont_work": "That won't work. {expl}", "wont_work_young": "Oops, not that one! {expl}",
        "ev_fact": "{name}: {fact}", "ev_diag": "{name} diagnosis: {fault}",
        "ev_analysis": "{name} analysis: {text}", "ev_fix": "{name} fix: {expl}",
        "hint_prefix": "Hint: ", "hint_done": "Everything is done. Return to the shuttle!",
        "hint_easy": "Go to the {obj} and use the {tool} (look for the glowing marker).",
        "hint_easy_young": "Walk to the {obj} and press E with the {tool}. Look for the shiny diamond!",
        "hint_normal": "Try your {tool}. Which object hasn't been investigated yet?",
        "hint_normal_young": "Try your {tool}! Is there something you haven't looked at yet?",
        "hint_hard": "Check your evidence log. What is still unexplained?",
        "hint_hard_young": "Peek at your evidence log. What do you still wonder about?",
        "obj_scan": "Scan the {name}", "obj_collect": "Collect a sample from the {name}",
        "obj_analyze": "Analyze the {name} sample", "obj_diagnose": "Diagnose the {name} with the Scanner",
        "obj_repair": "Repair the {name}",
    },
    "ar": {
        # ---- common
        "tagline": "\u0627\u0633\u062a\u0643\u0634\u0641  \u2022  \u0627\u0643\u062a\u0634\u0641  \u2022  \u062a\u0639\u0644\u0651\u0645",
        "loading": "\u062c\u0627\u0631\u064d \u062a\u062c\u0647\u064a\u0632 \u0645\u0631\u0643\u0632 \u0627\u0644\u062a\u062d\u0643\u0645...",
        "press_start": "\u0627\u0636\u063a\u0637 \u0623\u064a \u0632\u0631 \u0644\u0644\u0628\u062f\u0621",
        "new_game": "\u0644\u0639\u0628\u0629 \u062c\u062f\u064a\u062f\u0629", "continue": "\u0645\u062a\u0627\u0628\u0639\u0629",
        "quit": "\u062e\u0631\u0648\u062c", "back": "\u0631\u062c\u0648\u0639", "next": "\u0627\u0644\u062a\u0627\u0644\u064a",
        "music": "\u0627\u0644\u0645\u0648\u0633\u064a\u0642\u0649", "sound": "\u0627\u0644\u0635\u0648\u062a",
        "language": "\u0627\u0644\u0644\u063a\u0629", "on": "\u062a\u0634\u063a\u064a\u0644", "off": "\u0625\u064a\u0642\u0627\u0641",
        "music_hint": "\u0627\u0644\u0645\u0648\u0633\u064a\u0642\u0649 (M)", "sfx_hint": "\u0627\u0644\u0645\u0624\u062b\u0631\u0627\u062a \u0627\u0644\u0635\u0648\u062a\u064a\u0629",
        "lang_hint": "\u0627\u0644\u0644\u063a\u0629",
        "assistant_backend": "\u0627\u0644\u0628\u062d\u062b \u0641\u064a \u0627\u0644\u0645\u0639\u0644\u0648\u0645\u0627\u062a: {backend}",
        "assistant_llm": "\u0627\u0644\u0630\u0643\u0627\u0621 \u0627\u0644\u0627\u0635\u0637\u0646\u0627\u0639\u064a: {llm}",
        # ---- profile
        "create_profile": "\u0623\u0646\u0634\u0626 \u0645\u0644\u0641\u0643 \u0627\u0644\u0634\u062e\u0635\u064a",
        "astro_name": "\u0627\u0633\u0645 \u0631\u0627\u0626\u062f \u0627\u0644\u0641\u0636\u0627\u0621",
        "age_hint": "\u0627\u0644\u0641\u0626\u0629 \u0627\u0644\u0639\u0645\u0631\u064a\u0629  (\u062a\u063a\u064a\u0651\u0631 \u0637\u0631\u064a\u0642\u0629 \u0634\u0631\u062d \u0627\u0644\u0639\u0644\u0648\u0645)",
        "age_young": "\u0645\u0646 6 \u0625\u0644\u0649 9 \u0633\u0646\u0648\u0627\u062a", "age_mid": "\u0645\u0646 10 \u0625\u0644\u0649 13 \u0633\u0646\u0629",
        "age_teen": "14 \u0633\u0646\u0629 \u0641\u0623\u0643\u062b\u0631",
        "default_name": "\u0631\u0627\u0626\u062f", "type_name": "\u0627\u0643\u062a\u0628 \u0627\u0633\u0645\u0643",
        "suit_up": "\u062c\u0647\u0651\u0632 \u0628\u062f\u0644\u062a\u0643 \u064a\u0627 {name}!",
        "visor_color": "\u0644\u0648\u0646 \u0627\u0644\u062e\u0648\u0630\u0629", "suit_color": "\u0644\u0648\u0646 \u0627\u0644\u0628\u062f\u0644\u0629",
        "launch_map": "\u0627\u0646\u0637\u0644\u0642 \u0625\u0644\u0649 \u062e\u0631\u064a\u0637\u0629 \u0627\u0644\u0645\u062c\u0631\u0629",
        "choose_astronaut": "\u0627\u062e\u062a\u0631 \u0631\u0627\u0626\u062f \u0627\u0644\u0641\u0636\u0627\u0621",
        # ---- map
        "galaxy_map": "\u062e\u0631\u064a\u0637\u0629 \u0627\u0644\u0645\u062c\u0631\u0629", "level": "\u0627\u0644\u0645\u0633\u062a\u0648\u0649 {n}",
        "xp_line": "{xp} / {hi} XP",
        "easy": "\u0633\u0647\u0644", "normal": "\u0639\u0627\u062f\u064a", "hard": "\u0635\u0639\u0628",
        "achievements_count": "\u0627\u0644\u0625\u0646\u062c\u0627\u0632\u0627\u062a  {a}/{b}",
        "main_menu": "\u0627\u0644\u0642\u0627\u0626\u0645\u0629 \u0627\u0644\u0631\u0626\u064a\u0633\u064a\u0629", "locked": "\u0645\u0642\u0641\u0644\u0629",
        "aborted": "\u062a\u0645 \u0625\u0646\u0647\u0627\u0621 \u0627\u0644\u0645\u0647\u0645\u0629. \u0644\u0645 \u064a\u064f\u062d\u0641\u0638 \u062a\u0642\u062f\u0651\u0645 \u0647\u0630\u0647 \u0627\u0644\u0645\u062d\u0627\u0648\u0644\u0629.",
        # ---- briefing
        "science_focus": "\u0627\u0644\u062a\u0631\u0643\u064a\u0632 \u0627\u0644\u0639\u0644\u0645\u064a:  {x}",
        "objectives": "\u0627\u0644\u0623\u0647\u062f\u0627\u0641", "controls": "\u0627\u0644\u062a\u062d\u0643\u0651\u0645",
        "key_move": "\u062d\u0631\u0643\u0629", "key_look": "\u0646\u0638\u0631", "key_tools": "\u0623\u062f\u0648\u0627\u062a",
        "key_use": "\u0627\u0633\u062a\u062e\u062f\u0627\u0645", "key_hint": "\u062a\u0644\u0645\u064a\u062d",
        "key_ask": "\u0627\u0633\u0623\u0644 AI", "key_log": "\u0627\u0644\u0633\u062c\u0644", "key_leave": "\u062e\u0631\u0648\u062c",
        "key_mouse": "\u0627\u0644\u0645\u0627\u0648\u0633",
        "difficulty": "\u0627\u0644\u0635\u0639\u0648\u0628\u0629: {t}",
        "adapts": "\u062a\u062a\u0643\u064a\u0651\u0641 \u0645\u0639 \u0623\u0633\u0644\u0648\u0628 \u0644\u0639\u0628\u0643",
        "launch": "\u0627\u0646\u0637\u0644\u0642!",
        # ---- HUD / tools
        "tool_scanner": "\u0627\u0644\u0645\u0627\u0633\u062d", "tool_sampler": "\u062c\u0627\u0645\u0639 \u0627\u0644\u0639\u064a\u0651\u0646\u0627\u062a",
        "tool_analyzer": "\u0627\u0644\u0645\u0637\u064a\u0627\u0641", "tool_wrench": "\u0639\u062f\u0651\u0629 \u0627\u0644\u0625\u0635\u0644\u0627\u062d",
        "glyph_scanner": "\u0641\u062d\u0635", "glyph_sampler": "\u062c\u0645\u0639", "glyph_analyzer": "\u062a\u062d\u0644\u064a\u0644",
        "glyph_wrench": "\u0625\u0635\u0644\u0627\u062d",
        "start_tip": "\u0627\u062e\u062a\u0631 \u0627\u0644\u0645\u0627\u0633\u062d (1) \u0648\u0627\u0636\u063a\u0637 E \u0639\u0644\u0649 \u0627\u0644\u0645\u0639\u062f\u0627\u062a.  H = \u062a\u0644\u0645\u064a\u062d.",
        "hud_info": "\u0627\u0644\u0635\u0639\u0648\u0628\u0629: {t}\n\u0623\u062e\u0637\u0627\u0621 {m}   \u062a\u0644\u0645\u064a\u062d\u0627\u062a {h}",
        "hud_keys": "H \u062a\u0644\u0645\u064a\u062d   Q \u0627\u0633\u0623\u0644 AI   Tab \u0627\u0644\u0633\u062c\u0644   M \u0645\u0648\u0633\u064a\u0642\u0649   Esc \u062e\u0631\u0648\u062c",
        # ---- panels
        "repair_title": "\u0625\u0635\u0644\u0627\u062d  \u2022  {name}", "diagnosis": "\u0627\u0644\u062a\u0634\u062e\u064a\u0635: {d}",
        "fix_question": "\u0623\u064a \u062d\u0644\u0651 \u0633\u064a\u0646\u062c\u062d \u0641\u064a \u0647\u0630\u0647 \u0627\u0644\u0628\u064a\u0626\u0629\u061f",
        "fix_question_young": "\u0623\u064a \u062d\u0644\u0651 \u0647\u0648 \u0627\u0644\u0623\u0646\u0633\u0628 \u0647\u0646\u0627\u061f",
        "esc_cancel": "Esc \u0644\u0644\u0625\u0644\u063a\u0627\u0621", "esc_close": "Esc \u0644\u0644\u0625\u063a\u0644\u0627\u0642",
        "log_title": "\u0633\u062c\u0644 \u0627\u0644\u0623\u062f\u0644\u0629",
        "log_empty": "\u0644\u0627 \u0634\u064a\u0621 \u0628\u0639\u062f. \u0627\u0641\u062d\u0635 \u0627\u0644\u0623\u0634\u064a\u0627\u0621 \u0644\u062a\u062c\u0645\u0639 \u0627\u0644\u0623\u062f\u0644\u0629.",
        "ask_title": "\u0645\u0633\u0627\u0639\u062f \u0627\u0644\u0641\u0636\u0627\u0621 \u0627\u0644\u0630\u0643\u064a",
        "ask_hint": "\u0627\u0633\u0623\u0644 \u0633\u0624\u0627\u0644\u064b\u0627 \u0639\u0644\u0645\u064a\u064b\u0627 \u0639\u0646 \u0647\u0630\u0647 \u0627\u0644\u0645\u0647\u0645\u0629 \u062b\u0645 \u0627\u0636\u063a\u0637 Enter.",
        "ask_placeholder": "\u0627\u0643\u062a\u0628 \u0633\u0624\u0627\u0644\u0643 \u0647\u0646\u0627...",
        "try_asking": "\u0623\u0648 \u0627\u0636\u063a\u0637 \u0639\u0644\u0649 \u0633\u0624\u0627\u0644:",
        "thinking": "\u0623\u0641\u0643\u0651\u0631...", "comms_down": "\u0627\u0646\u0642\u0637\u0639 \u0627\u0644\u0627\u062a\u0635\u0627\u0644. \u062d\u0627\u0648\u0644 \u0645\u0631\u0629 \u0623\u062e\u0631\u0649!",
        "ask_btn": "\u0627\u0633\u0623\u0644", "ask_empty": "\u0627\u0633\u0623\u0644\u0646\u064a \u0623\u064a \u0634\u064a\u0621 \u0639\u0646 \u0627\u0644\u0645\u0647\u0645\u0629 \u0623\u0648 \u0627\u0644\u0639\u0644\u0645!",
        "no_data": "\u0644\u064a\u0633 \u0639\u0646\u062f\u064a \u0645\u0639\u0644\u0648\u0645\u0627\u062a \u0639\u0646 \u0647\u0630\u0627 \u0628\u0639\u062f. \u062c\u0631\u0651\u0628 \u0641\u062d\u0635 \u0627\u0644\u0623\u0634\u064a\u0627\u0621 \u0627\u0644\u0642\u0631\u064a\u0628\u0629\u060c \u0623\u0648 \u0627\u0633\u0623\u0644 \u0639\u0646 \u0627\u0644\u0628\u064a\u0626\u0629 \u0627\u0644\u062a\u064a \u062a\u0633\u062a\u0643\u0634\u0641\u0647\u0627.",
        "from_notes": "\u0645\u0646 \u0645\u0644\u0627\u062d\u0638\u0627\u062a\u064a:",
        # ---- completion & quiz
        "complete": "\u0627\u0643\u062a\u0645\u0644\u062a \u0627\u0644\u0645\u0647\u0645\u0629!",
        "xp_total": "+{xp} XP      \u0627\u0644\u0645\u062c\u0645\u0648\u0639 {total}      \u0627\u0644\u0645\u0633\u062a\u0648\u0649 {lvl}",
        "level_up": "\u062a\u0631\u0642\u064a\u0629 \u0645\u0633\u062a\u0648\u0649!",
        "stats": "\u0623\u062e\u0637\u0627\u0621 {m}    \u062a\u0644\u0645\u064a\u062d\u0627\u062a {h}    \u0627\u0644\u0648\u0642\u062a {s} \u062b    \u0627\u0644\u0635\u0639\u0648\u0628\u0629 \u0627\u0644\u0642\u0627\u062f\u0645\u0629: {t}",
        "unlocked": "\u0641\u064f\u062a\u062d\u062a: {names}", "achievement": "\u0625\u0646\u062c\u0627\u0632: {text}",
        "learned": "\u0645\u0627\u0630\u0627 \u062a\u0639\u0644\u0651\u0645\u062a", "deep_dive": "\u0644\u0644\u0645\u062a\u0639\u0645\u0651\u0642\u064a\u0646",
        "back_to_map": "\u0627\u0644\u0639\u0648\u062f\u0629 \u0644\u062e\u0631\u064a\u0637\u0629 \u0627\u0644\u0645\u062c\u0631\u0629",
        "take_quiz": "\u0627\u0628\u062f\u0623 \u0627\u0644\u0627\u062e\u062a\u0628\u0627\u0631  (+XP)",
        "quiz_title": "\u0627\u062e\u062a\u0628\u0627\u0631 \u0627\u0644\u0645\u0647\u0645\u0629", "quiz_q": "\u0627\u0644\u0633\u0624\u0627\u0644 {i} \u0645\u0646 {n}",
        "quiz_correct": "\u0625\u062c\u0627\u0628\u0629 \u0635\u062d\u064a\u062d\u0629!  +{xp} XP",
        "quiz_wrong": "\u0644\u064a\u0633\u062a \u0635\u062d\u064a\u062d\u0629 \u062a\u0645\u0627\u0645\u064b\u0627.",
        "quiz_next": "\u0627\u0644\u0633\u0624\u0627\u0644 \u0627\u0644\u062a\u0627\u0644\u064a", "quiz_finish": "\u0625\u0646\u0647\u0627\u0621",
        "quiz_result": "\u0623\u062c\u0628\u062a \u0635\u062d \u0639\u0644\u0649 {c} \u0645\u0646 {n}!  +{xp} XP",
        "quiz_great": "\u0639\u0645\u0644 \u0631\u0627\u0626\u0639 \u064a\u0627 \u0631\u0627\u0626\u062f \u0627\u0644\u0641\u0636\u0627\u0621!",
        "quiz_ok": "\u0645\u062d\u0627\u0648\u0644\u0629 \u062c\u0645\u064a\u0644\u0629. \u0643\u0644 \u0645\u0633\u062a\u0643\u0634\u0641 \u064a\u062a\u0639\u0644\u0651\u0645 \u0645\u0646 \u0627\u0644\u062a\u062c\u0631\u0628\u0629!",
        # ---- achievements
        "ach_first_mission": "\u0623\u0648\u0644 \u0647\u0628\u0648\u0637: \u0623\u0643\u0645\u0644 \u0645\u0647\u0645\u062a\u0643 \u0627\u0644\u0623\u0648\u0644\u0649",
        "ach_flawless": "\u0628\u0644\u0627 \u0623\u062e\u0637\u0627\u0621: \u0623\u0646\u0647\u0650 \u0645\u0647\u0645\u0629 \u0628\u062f\u0648\u0646 \u0623\u062e\u0637\u0627\u0621 \u0623\u0648 \u062a\u0644\u0645\u064a\u062d\u0627\u062a",
        "ach_scientist": "\u0639\u0627\u0644\u0645 \u0645\u064a\u062f\u0627\u0646\u064a: \u062d\u0644\u0651\u0644 5 \u0639\u064a\u0651\u0646\u0627\u062a",
        "ach_problem_solver": "\u062d\u0627\u0644\u0651 \u0627\u0644\u0645\u0634\u0643\u0644\u0627\u062a: \u0623\u0643\u0645\u0644 3 \u0645\u0647\u0645\u0627\u062a",
        "ach_explorer": "\u0645\u0633\u062a\u0643\u0634\u0641 \u0627\u0644\u0645\u062c\u0631\u0629: \u0623\u0643\u0645\u0644 \u0643\u0644 \u0627\u0644\u0645\u0647\u0645\u0627\u062a",
        "ach_level_5": "\u0631\u0627\u0626\u062f \u0645\u062d\u0646\u0651\u0643: \u0627\u0628\u0644\u063a \u0627\u0644\u0645\u0633\u062a\u0648\u0649 5",
        # ---- mission engine messages
        "aim_at": "\u0648\u062c\u0651\u0647 \u0627\u0644\u0645\u0624\u0634\u0651\u0631 \u0646\u062d\u0648 \u0634\u064a\u0621 \u0644\u062a\u0633\u062a\u062e\u062f\u0645 \u0627\u0644\u0623\u062f\u0627\u0629.",
        "unknown_tool": "\u0623\u062f\u0627\u0629 \u063a\u064a\u0631 \u0645\u0639\u0631\u0648\u0641\u0629.", "nothing_happened": "\u0644\u0645 \u064a\u062d\u062f\u062b \u0634\u064a\u0621.",
        "nothing_collect": "\u0644\u0627 \u0634\u064a\u0621 \u0644\u062c\u0645\u0639\u0647 \u0645\u0646 {name}.",
        "sample_done": "\u062a\u0645 \u062c\u0645\u0639 \u0627\u0644\u0639\u064a\u0651\u0646\u0629 \u0645\u0646 \u0642\u0628\u0644.",
        "sample_ok": "\u062c\u0645\u0639\u062a \u0639\u064a\u0651\u0646\u0629 \u0645\u0646 {name}. \u062d\u0644\u0651\u0644\u0647\u0627 \u0628\u0627\u0644\u0645\u0637\u064a\u0627\u0641.",
        "nothing_analyze": "{name} \u0644\u064a\u0633 \u0641\u064a\u0647 \u0645\u0627 \u064a\u064f\u062d\u0644\u0651\u0644.",
        "collect_first": "\u0627\u062c\u0645\u0639 \u0639\u064a\u0651\u0646\u0629 \u0623\u0648\u0644\u064b\u0627.",
        "already_analyzed": "\u062a\u0645 \u0627\u0644\u062a\u062d\u0644\u064a\u0644 \u0645\u0646 \u0642\u0628\u0644.", "analysis_msg": "\u0627\u0644\u062a\u062d\u0644\u064a\u0644: {text}",
        "no_repair": "{name} \u0644\u0627 \u064a\u062d\u062a\u0627\u062c \u0625\u0635\u0644\u0627\u062d\u064b\u0627.",
        "already_repaired": "\u062a\u0645 \u0627\u0644\u0625\u0635\u0644\u0627\u062d \u0645\u0646 \u0642\u0628\u0644.",
        "diagnose_first": "\u0634\u062e\u0651\u0635 \u0623\u0648\u0644\u064b\u0627! \u0627\u0641\u062d\u0635\u0647 \u0644\u062a\u0639\u0631\u0641 \u0645\u0627 \u0627\u0644\u0645\u0634\u0643\u0644\u0629.",
        "scanned_msg": "\u0641\u062d\u0635\u062a {name}. {fact}", "already_scanned": "{name}: \u062a\u0645 \u0641\u062d\u0635\u0647 \u0645\u0646 \u0642\u0628\u0644.",
        "repair_impossible": "\u0627\u0644\u0625\u0635\u0644\u0627\u062d \u063a\u064a\u0631 \u0645\u0645\u0643\u0646 \u0627\u0644\u0622\u0646.",
        "repaired": "\u062a\u0645 \u0627\u0644\u0625\u0635\u0644\u0627\u062d! {expl}",
        "wont_work": "\u0647\u0630\u0627 \u0644\u0646 \u064a\u0646\u062c\u062d. {expl}", "wont_work_young": "\u0623\u0648\u0647! \u0644\u064a\u0633 \u0647\u0630\u0627. {expl}",
        "ev_fact": "{name}: {fact}", "ev_diag": "\u062a\u0634\u062e\u064a\u0635 {name}: {fault}",
        "ev_analysis": "\u062a\u062d\u0644\u064a\u0644 {name}: {text}", "ev_fix": "\u0625\u0635\u0644\u0627\u062d {name}: {expl}",
        "hint_prefix": "\u062a\u0644\u0645\u064a\u062d: ", "hint_done": "\u0643\u0644 \u0634\u064a\u0621 \u062a\u0645. \u0639\u064f\u062f \u0625\u0644\u0649 \u0627\u0644\u0645\u0631\u0643\u0628\u0629!",
        "hint_easy": "\u0627\u0630\u0647\u0628 \u0625\u0644\u0649 {obj} \u0648\u0627\u0633\u062a\u062e\u062f\u0645 {tool} (\u0627\u0628\u062d\u062b \u0639\u0646 \u0627\u0644\u0639\u0644\u0627\u0645\u0629 \u0627\u0644\u0645\u062a\u0648\u0647\u062c\u0629).",
        "hint_easy_young": "\u0627\u0645\u0634\u0650 \u0625\u0644\u0649 {obj} \u0648\u0627\u0636\u063a\u0637 E \u0645\u0639 {tool}. \u0627\u0628\u062d\u062b \u0639\u0646 \u0627\u0644\u0645\u0627\u0633\u0629 \u0627\u0644\u0644\u0627\u0645\u0639\u0629!",
        "hint_normal": "\u062c\u0631\u0651\u0628 {tool}. \u0623\u064a \u0634\u064a\u0621 \u0644\u0645 \u062a\u062f\u0631\u0633\u0647 \u0628\u0639\u062f\u061f",
        "hint_normal_young": "\u062c\u0631\u0651\u0628 {tool}! \u0647\u0644 \u0647\u0646\u0627\u0643 \u0634\u064a\u0621 \u0644\u0645 \u062a\u0646\u0638\u0631 \u0625\u0644\u064a\u0647 \u0628\u0639\u062f\u061f",
        "hint_hard": "\u0631\u0627\u062c\u0639 \u0633\u062c\u0644 \u0627\u0644\u0623\u062f\u0644\u0629. \u0645\u0627 \u0627\u0644\u0630\u064a \u0644\u0627 \u064a\u0632\u0627\u0644 \u063a\u064a\u0631 \u0645\u0641\u0647\u0648\u0645\u061f",
        "hint_hard_young": "\u0623\u0644\u0642\u0650 \u0646\u0638\u0631\u0629 \u0639\u0644\u0649 \u0633\u062c\u0644 \u0627\u0644\u0623\u062f\u0644\u0629. \u0645\u0627\u0630\u0627 \u0644\u0627 \u062a\u0632\u0627\u0644 \u062a\u062a\u0633\u0627\u0621\u0644 \u0639\u0646\u0647\u061f",
        "obj_scan": "\u0627\u0641\u062d\u0635 {name}", "obj_collect": "\u0627\u062c\u0645\u0639 \u0639\u064a\u0651\u0646\u0629 \u0645\u0646 {name}",
        "obj_analyze": "\u062d\u0644\u0651\u0644 \u0639\u064a\u0651\u0646\u0629 {name}",
        "obj_diagnose": "\u0634\u062e\u0651\u0635 \u0639\u0637\u0644 {name} \u0628\u0627\u0644\u0645\u0627\u0633\u062d",
        "obj_repair": "\u0623\u0635\u0644\u062d {name}",
    },
}


# ---- habitat, oxygen and tool-battery strings
STRINGS["en"].update({
    "hab_door": "Habitat Airlock", "hab_analyzer": "Science Analyzer", "hab_bed": "Astronaut Bunk",
    "hab_locker": "Tool Locker", "hab_o2": "Oxygen Station",
    "prompt_e": "E  -  {action}",
    "act_open": "Open airlock", "act_close": "Close airlock", "act_lab": "Analyze my samples",
    "act_rest": "Rest and save checkpoint", "act_locker": "Recharge my tools", "act_o2": "Refill oxygen",
    "door_opened": "Airlock open.", "door_closed": "Airlock closed.",
    "bed_rest": "You rest in the bunk. Checkpoint saved: if your oxygen runs out you will wake up here.",
    "bed_todo": "Still to do: {todo}", "bed_all_done": "Everything is done. Time to head back to the shuttle!",
    "o2_filling": "Refilling oxygen...", "o2_full": "Oxygen tank full.", "o2_already_full": "Your oxygen tank is already full.",
    "locker_charged": "All tool batteries recharged.", "locker_full": "Your tools are already fully charged.",
    "tool_low": "The {tool} battery is too low. Recharge it at the tool locker inside the habitat.",
    "lab_no_sample": "Collect a sample first, then bring it to the analyzer.",
    "lab_report": "Lab analysis: {text}", "lab_bonus": "Detailed lab report: {text}  (+{xp} XP)",
    "lab_done": "The analyzer has no new samples to study.", "ev_lab": "{name} lab report: {text}",
    "o2_low": "Oxygen low: {p}%. Return to the habitat oxygen station.",
    "o2_critical": "OXYGEN CRITICAL: {p}%! Get to the habitat now!",
    "o2_empty": "Out of oxygen! Emergency return to the habitat. (+1 mistake)",
    "watch_o2": "O2", "battery": "Battery",
})
STRINGS["ar"].update({
    "hab_door": "بوابة المسكن", "hab_analyzer": "المحلّل العلمي", "hab_bed": "سرير رائد الفضاء",
    "hab_locker": "خزانة الأدوات", "hab_o2": "محطة الأكسجين",
    "prompt_e": "E  -  {action}",
    "act_open": "افتح البوابة", "act_close": "أغلق البوابة", "act_lab": "حلّل عيّناتي",
    "act_rest": "استرح واحفظ نقطة العودة", "act_locker": "اشحن أدواتي", "act_o2": "املأ الأكسجين",
    "door_opened": "البوابة مفتوحة.", "door_closed": "البوابة مغلقة.",
    "bed_rest": "ارتحت على السرير. حُفظت نقطة العودة: إن نفد أكسجينك ستستيقظ هنا.",
    "bed_todo": "ما زال عليك: {todo}", "bed_all_done": "كل شيء تمّ. حان وقت العودة إلى المركبة!",
    "o2_filling": "جارٍ ملء الأكسجين...", "o2_full": "خزّان الأكسجين ممتلئ.", "o2_already_full": "خزّان الأكسجين ممتلئ بالفعل.",
    "locker_charged": "تم شحن بطاريات كل الأدوات.", "locker_full": "أدواتك مشحونة بالكامل بالفعل.",
    "tool_low": "بطارية {tool} ضعيفة جدًّا. اشحنها من خزانة الأدوات داخل المسكن.",
    "lab_no_sample": "اجمع عيّنة أولًا ثم أحضرها إلى المحلّل.",
    "lab_report": "تحليل المعمل: {text}", "lab_bonus": "تقرير المعمل المفصّل: {text}  (+{xp} XP)",
    "lab_done": "ليس عند المحلّل عيّنات جديدة ليدرسها.", "ev_lab": "تقرير معمل {name}: {text}",
    "o2_low": "الأكسجين منخفض: {p}%. عُد إلى محطة الأكسجين في المسكن.",
    "o2_critical": "الأكسجين في خطر: {p}%! اذهب إلى المسكن الآن!",
    "o2_empty": "نفد الأكسجين! عودة طارئة إلى المسكن. (+1 خطأ)",
    "watch_o2": "O2", "battery": "البطارية",
})

STRINGS["en"]["door_blocked"] = "Step away from the doorway first."
STRINGS["ar"]["door_blocked"] = "ابتعد عن مدخل البوابة أولًا."
