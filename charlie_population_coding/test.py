# Test script
import matplotlib.pyplot as plt
import numpy as np
import pop_utils as pu
import numpy.linalg as la
from sklearn.model_selection import train_test_split
import sys
sys.path.append('/auto/users/hellerc/nems/nems/utilities')
from utils import crossval_set
x = np.linspace(0,10,1000)
y = np.sin(x)

train, test = crossval_set(40, interleave_valtrials=False)
for t in test:
    print(t)
print(len(train))
print(test)

plt.figure()
plt.plot(y)

r_train, r_test = train_test_split(np.roll(y, 1000, 0), test_size=1.0, shuffle=False)

plt.plot(r_test, '--k', lw=2)
plt.show()
