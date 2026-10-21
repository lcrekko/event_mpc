"""Only detector identities and timestamps enter the reconstruction (24)."""
from dataclasses import dataclass
from .coupled import GAMMA_S


@dataclass(frozen=True)
class Observation:
    crossing_time: float
    available_time: float
    omega: float
    first_detector: str
    second_detector: str


class DetectorPairing:
    def __init__(self,window=.0025):
        if window<=0:raise ValueError('Positive pairing window required')
        self.window=window;self.previous=None;self.rejected=[]

    def consume(self,detector,time):
        if detector not in ('L','R'):raise ValueError('Detector must be L or R')
        old=self.previous
        if old is not None and time<=old[1]:
            self.rejected.append('nonincreasing_timestamp');return None
        self.previous=(detector,time)
        if old is None:return None
        if old[0]==detector:
            self.rejected.append('same_detector');return None
        dt=time-old[1]
        if dt>self.window:
            self.rejected.append('pair_timeout');return None
        self.previous=None
        sigma=1 if old[0]=='R' else -1
        return Observation((time+old[1])/2,time,2*sigma*GAMMA_S/dt,old[0],detector)
