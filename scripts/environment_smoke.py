from pathlib import Path
import sys
import numpy as np
import scipy
from scipy.integrate import solve_ivp
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
r = solve_ivp(lambda t,y: -y, (0,2), [1.], events=lambda t,y:y[0]-0.5, rtol=1e-9, atol=1e-12)
assert r.success and abs(r.y[0,-1]-np.exp(-2)) < 1e-8
assert len(r.t_events[0]) == 1 and abs(r.t_events[0][0]-np.log(2)) < 1e-7
p=Path(__file__).resolve().parents[1] / 'outputs' / 'environment' / 'import-smoke.png'
p.parent.mkdir(parents=True, exist_ok=True)
plt.plot(r.t,r.y[0]); plt.savefig(p); plt.close()
assert p.stat().st_size > 1000
print('PASS: imports, adaptive ODE integration, event detection, headless PNG')
print(sys.version.split()[0], 'numpy',np.__version__,'scipy',scipy.__version__,'matplotlib',matplotlib.__version__)
