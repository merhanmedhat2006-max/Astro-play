"""Music + sound effects for Astro Play (Panda3D audio).  Never raises: if no audio device exists
or a file is missing, the game simply runs silent.

* music tracks loop and crossfade (menu <-> mission)
* ``set_music(False)`` fades the music out and stops it; ``set_music(True)`` brings it back
* ``sfx(name)`` plays assets/audio/sfx_<name>.wav (honours the sound-effects toggle)
"""
import logging

from . import config

log = logging.getLogger("astro.audio")

MUSIC = {"menu": "music_menu.wav", "mission": "music_mission.wav"}
MUSIC_GAIN = {"menu": 0.8, "mission": 0.65}          # per-track balance (the files are mastered loud)


class AudioManager:
    def __init__(self, settings, loader=None):
        self.settings = settings
        self._loader = loader
        self._music = {}              # name -> AudioSound
        self._vol = {}                # name -> current fade volume 0..1
        self._target = {}             # name -> target fade volume 0..1
        self._sfx = {}
        self.current = None           # name of the track that should be audible
        self.available = loader is not None

    # ---- loading
    def _load(self, kind, filename):
        if not self._loader:
            return None
        path = config.ASSETS_DIR / "audio" / filename
        if not path.exists():
            return None
        try:
            from panda3d.core import Filename
            fn = Filename.from_os_specific(str(path))
            return self._loader.loadMusic(fn) if kind == "music" else self._loader.loadSfx(fn)
        except Exception as e:  # pragma: no cover
            log.warning("could not load %s (%s)", filename, e)
            return None

    # ---- music
    def play_music(self, name):
        """Switch to a track (crossfade). Safe to call repeatedly with the same name."""
        if name not in MUSIC:
            return
        self.current = name
        if name not in self._music:
            snd = self._load("music", MUSIC[name])
            if snd is None:
                return
            snd.setLoop(True)
            self._music[name] = snd
            self._vol[name] = 0.0
        for n in self._music:
            self._target[n] = 1.0 if (n == name and self.settings.music) else 0.0
        snd = self._music[name]
        if self.settings.music and snd.status() != snd.PLAYING:
            snd.setVolume(0.0)
            snd.play()

    def set_music(self, on: bool):
        self.settings.music = bool(on)
        self.settings.save()
        if self.current:
            self.play_music(self.current)

    def toggle_music(self) -> bool:
        self.set_music(not self.settings.music)
        return self.settings.music

    def update(self, dt: float):
        """Call every frame: moves fade volumes toward their targets."""
        for name, snd in self._music.items():
            tgt = self._target.get(name, 0.0)
            cur = self._vol.get(name, 0.0)
            if cur != tgt:
                step = dt * (1.2 if tgt > cur else 1.8)
                cur = min(tgt, cur + step) if tgt > cur else max(tgt, cur - step)
                self._vol[name] = cur
            snd.setVolume(cur * self.settings.music_volume * MUSIC_GAIN.get(name, 1.0))
            if cur <= 0.0 and tgt <= 0.0 and snd.status() == snd.PLAYING:
                snd.stop()

    def music_is_audible(self) -> bool:
        return bool(self.settings.music and self.current)

    # ---- effects
    def set_sfx(self, on: bool):
        self.settings.sfx = bool(on)
        self.settings.save()

    def toggle_sfx(self) -> bool:
        self.set_sfx(not self.settings.sfx)
        return self.settings.sfx

    def sfx(self, name: str, volume: float = 1.0, rate: float = 1.0):
        if not self.settings.sfx:
            return
        if name not in self._sfx:
            self._sfx[name] = self._load("sfx", f"sfx_{name}.wav")
        snd = self._sfx[name]
        if snd is None:
            return
        try:
            snd.setVolume(max(0.0, min(1.0, volume * self.settings.sfx_volume)))
            snd.setPlayRate(rate)
            snd.play()
        except Exception:  # pragma: no cover
            pass
