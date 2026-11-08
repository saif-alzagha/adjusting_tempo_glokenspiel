"""
TempoPlayer: adjustable tempo for the Robot Glockenspiel.

Notes are stored in BEATS instead of seconds. A beat clock advances at the
current BPM, so changing the BPM while playing stretches or shrinks every
remaining gap between notes automatically.

How to use it with the existing code:
  1. Write the song as (beat, key) pairs instead of fixed delays,
     e.g. [(0, "E"), (1, "D"), (2, "C"), ...]   (1 = quarter note, 0.5 = eighth)
  2. Pass in the existing function that hits a key as `strike`.
  3. Replace the sleep()-based loop with a loop that calls update() every ~1 ms:

        player = TempoPlayer(song, bpm=100, strike=hit_key, ramp=0.5)
        while player.update(time.monotonic()):
            # whenever the tempo should change (keys, conductor, ...):
            # player.set_tempo(new_bpm)
            time.sleep(0.001)
"""


class TempoPlayer:
    def __init__(self, song, bpm, strike, lead_s=0.0, ramp=None):
        self.song = song        # list of (beat, key)
        self.bpm = bpm          # tempo actually being played
        self.target = bpm       # tempo asked for (by keys / the conductor)
        self.strike = strike    # function(key): the existing code that hits a key
        self.lead_s = lead_s    # optional: fire this many seconds early (e.g. relay delay)
        self.ramp = ramp        # None = jump to a new tempo instantly
                                # 0.5  = move halfway to the new tempo each beat
        self.beat = 0.0         # beat clock
        self.last_t = None
        self.i = 0              # index of the next note

    def set_tempo(self, bpm):
        """Change the tempo while playing."""
        if bpm:
            self.target = bpm
            if self.ramp is None:
                self.bpm = bpm

    def update(self, now):
        """Call every ~1 ms with time.monotonic(). Hits every note whose beat
        has been reached. Returns False when the song is finished."""
        if self.last_t is not None:
            passed = (now - self.last_t) * self.bpm / 60      # beats since last call
            self.beat += passed
            if self.ramp is not None:                         # ease toward the target
                self.bpm += (self.target - self.bpm) * min(1.0, self.ramp * passed)
        self.last_t = now
        lead_beats = self.lead_s * self.bpm / 60
        while self.i < len(self.song) and self.beat + lead_beats >= self.song[self.i][0]:
            self.strike(self.song[self.i][1])
            self.i += 1
        return self.i < len(self.song)
