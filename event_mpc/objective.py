"""Literal manuscript (13): timing indices 0..N-1, terminal timing omitted."""
from dataclasses import dataclass
import numpy as np
from .mechanics import MechanicalParameters


@dataclass(frozen=True)
class Objective:
    period: float=.05
    amplitude: float=np.deg2rad(5.)
    gamma: float=1.

    def array(self):
        E0=.5*MechanicalParameters().stiffness*self.amplitude**2
        return np.array([self.period,self.amplitude,self.period**2/self.amplitude**2,
                         .05*self.period**2/E0,self.gamma])

    def evaluate(self,prediction,event_index):
        if prediction.status!='completed':return float('inf')
        N=len(prediction.amplitudes);w=self.array();indices=event_index+np.arange(N)
        terms=(indices*self.period-np.asarray(prediction.times[:N]))**2
        terms+=w[2]*(((-1.)**indices)*self.amplitude-np.asarray(prediction.amplitudes))**2
        terms+=w[3]*np.asarray(prediction.work)
        return float(np.sum(self.gamma**np.arange(N)*terms))
