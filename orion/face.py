import math
import os
import sys
import threading
import time

CYAN = "\033[96m"
RESET = "\033[0m"
SHOW = "\033[?25h"

VIS_W = 49
FACE_HEIGHT = 5
INDENT = "    "


class State:
    IDLE = "idle"
    LISTENING = "listening"
    SPEAKING = "speaking"
    PROCESSING = "processing"


SCAN_LINE = f"{INDENT}╶{'─' * (VIS_W + 4)}╴"


def _visor(fill):
    return f"{INDENT}  ▐{fill}▌"


def _visor_solid(ch):
    return _visor(ch * VIS_W)


def _visor_scan(pos, width=5):
    chars = []
    for i in range(VIS_W):
        chars.append("▓" if pos <= i < pos + width else "░")
    return _visor("".join(chars))


def _visor_breathe(frame, phase_offset=0):
    mid = VIS_W // 2
    phase = frame * 0.12 + phase_offset
    blocks = " ░▒"
    chars = []
    for i in range(VIS_W):
        dist = abs(i - mid) / mid
        val = math.sin(phase - dist * 2.5) * 0.5 + 0.5
        idx = min(int(val * len(blocks)), len(blocks) - 1)
        chars.append(blocks[idx])
    return _visor("".join(chars))


def _visor_wave(frame, phase_offset=0):
    blocks = "░▒▓█▓▒"
    f = frame + phase_offset
    chars = []
    for i in range(VIS_W):
        phase = math.sin(i * 0.45 + f * 0.55) * 0.5 + 0.5
        noise = math.sin(i * 1.7 + f * 0.9) * 0.25
        val = max(0.0, min(1.0, phase + noise))
        idx = int(val * (len(blocks) - 1))
        chars.append(blocks[idx])
    return _visor("".join(chars))


class FaceAnimator:
    def __init__(self):
        self._state = State.IDLE
        self._running = False
        self._thread = None
        self._lock = threading.Lock()

    @property
    def state(self):
        with self._lock:
            return self._state

    def setup(self):
        rows, _ = os.get_terminal_size()
        sys.stdout.write("\033[2J\033[H")
        self._draw_full()
        sys.stdout.write(f"\033[{FACE_HEIGHT + 1};{rows}r")
        sys.stdout.write(f"\033[{FACE_HEIGHT + 1};1H")
        sys.stdout.flush()
        self._running = True
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

    def cleanup(self):
        self._running = False
        if self._thread:
            self._thread.join(timeout=1)
        sys.stdout.write("\033[r")
        sys.stdout.write(SHOW)
        sys.stdout.flush()

    def set_state(self, state):
        with self._lock:
            self._state = state

    def _draw_full(self):
        v = _visor_solid("░")
        for i, line in enumerate([SCAN_LINE, v, v, v, SCAN_LINE]):
            sys.stdout.write(f"\033[{i + 1};1H{CYAN}{line}{RESET}")
        sys.stdout.flush()

    def _update(self, nums, contents):
        sys.stdout.write("\033[s")
        for n, c in zip(nums, contents):
            sys.stdout.write(f"\033[{n + 1};1H\033[2K{CYAN}{c}{RESET}")
        sys.stdout.write("\033[u")
        sys.stdout.flush()

    def _loop(self):
        frame = 0

        while self._running:
            time.sleep(0.10)
            if not self._running:
                break

            with self._lock:
                state = self._state

            frame += 1
            nums = [1, 2, 3]

            if state == State.IDLE:
                if frame % 3 != 0:
                    continue
                contents = [
                    _visor_breathe(frame, 0),
                    _visor_breathe(frame, 0.5),
                    _visor_breathe(frame, 1.0),
                ]

            elif state == State.LISTENING:
                pos = frame % (VIS_W + 7) - 7
                v = _visor_scan(pos, 7)
                contents = [v, v, v]

            elif state == State.SPEAKING:
                contents = [
                    _visor_wave(frame, 0),
                    _visor_wave(frame, 3),
                    _visor_wave(frame, 6),
                ]

            elif state == State.PROCESSING:
                cycle = VIS_W + 5
                raw = (frame * 2) % (cycle * 2)
                pos = raw - 5 if raw < cycle else VIS_W - (raw - cycle)
                v = _visor_scan(pos, 5)
                contents = [v, v, v]

            else:
                continue

            self._update(nums, contents)
