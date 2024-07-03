from dataclasses import dataclass

@dataclass
class DurationFix:
    """Contains info about converting frame durations to timestamp durations.
    The expected out frame won't be known at first.
    We recommend you run the tool first to fill in the expected frame and the correct fix.
    """

    expectedFrames: int     # expected out frame
    fix: str                # timestamp fix
    comment: str = ""       # optional field to leave comment


@dataclass
class Threshold:
    """Contains info about mapping count to duration
    """

    count: int
    seconds: float