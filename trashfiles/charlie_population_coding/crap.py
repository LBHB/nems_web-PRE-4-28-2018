import matplotlib.pyplot as plt
import numpy as np
import pop_utils as pu
import numpy.linalg as la
from tqdm import tqdm
import scipy.io as si
import sys
sys.path.insert(0, '/auto/users/hellerc/nems/nems/utilities')
from baphy_utils import load_baphy_file

f = '/auto/data/code/nems_in_cache/batch299/BOL005c-04-1_b299_none_fs100.mat'

data = load_baphy_file(f)
data2 = si.loadmat(f)
print(data2['cellid'])
print(data2['__globals__'])


plt.figure()
plt.imshow(data['resp'].reshape(550*40*2, 57).T, aspect='auto')
plt.title('response raster')

r_spont, p_spont, fs = pu.get_spont_data(data)
r_spont = pu.z_score(r_spont)
plt.figure()
plt.title('spont activity')
plt.imshow(r_spont.reshape(200*40*2, 57).T, aspect='auto')


replen = r_spont.shape[0]
stimcount = r_spont.shape[2]
repcount = r_spont.shape[1]
cellcount = r_spont.shape[3]
r_spont = r_spont.reshape(replen, repcount*stimcount, cellcount)
test = r_spont[:,74:80,:]
r_spont = r_spont[:,0:74,:]
r_spont = r_spont.reshape((int(replen*74), cellcount))

h = np.empty((cellcount,cellcount))
# ------------------ filter at one time point -------------------------------

for i in tqdm(range(0, cellcount)):
    n = i
    neuron = r_spont[:,n]
    r_spont_temp = np.delete(r_spont, n, 1)
    Css = np.matmul(r_spont_temp.T, r_spont_temp)/len(r_spont_temp)
    Csr = np.matmul(r_spont_temp.T, neuron)/len(r_spont_temp)
    h_temp = np.matmul(la.inv(Css).T, Csr)
    h[i,:] = np.concatenate((h_temp[0:i], np.zeros(1), h_temp[i:len(h_temp)]))
plt.figure()
plt.title('Auto-correlation matrix')
plt.imshow(Css)

plt.figure()
plt.title('ex. population-neuron correlation')
plt.plot(Csr)

plt.figure()
plt.title("Filters")
plt.xlabel('neurons')
plt.ylabel('neurons')
plt.imshow(h)
plt.colorbar()


# ----------------------- Use "filters" to model responses -------------------

trial = r_spont.reshape((replen, 74, cellcount))
cov = np.empty(cellcount)
pred = np.empty((cellcount, 1200))
for i in range(0, cellcount):
    sample_act = np.delete(trial, i, 1)
    sample_resp = trial[:,:,i]
    stim = np.delete(test,i,2)
    stim = stim.reshape(replen*6, cellcount-1)
    hnew = np.delete(h[i,:],i)
    pred[i, :] = np.matmul(np.squeeze(hnew.T),stim.T)
    cov[i] = np.corrcoef(pred[i,:], np.squeeze(test[:,:,i].reshape(1200,1)))[0][1]

plt.figure()
plt.plot(cov)
plt.title('prediction ability for each neuron')
plt.ylabel('correlation coefficient')
plt.xlabel('neuron')

plt.figure()
plt.plot(pred[1,:])
plt.plot(test[:,:,1].reshape(1200,1))
plt.title('example prediction')
plt.xlabel('time')

plt.show()

# ----------------------------- filter with lags -----------------------------
'''
seconds = .1
lags = int(seconds*fs)
h = np.empty((cellcount, lags, cellcount))
for i in tqdm(range(0,cellcount)):
    n = i
    neuron = r_spont[:,n]
    r_spont_temp = np.delete(r_spont, n, 1)
    Css = np.matmul(r_spont_temp.T, r_spont_temp)/len(r_spont_temp)
    for j in range(0, lags):
        Csr = np.matmul(r_spont_temp.T, np.roll(neuron, j))/len(r_spont_temp)
        h_temp = np.matmul(la.inv(Css).T, Csr)
        h[i,j,:] = np.concatenate((h_temp[0:i], np.zeros(1), h_temp[i:len(h_temp)]))

fig, axes = plt.subplots(ncols = 8, nrows =8)
for i, ax in enumerate(axes.flat):
    if i >= cellcount:
        break
    im = ax.imshow(h[i].T, aspect='auto')
fig.colorbar(im, ax=axes.ravel().tolist())
'''
