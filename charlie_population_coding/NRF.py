import sys
print(sys.path)

import matplotlib.pyplot as plt
import numpy as np
import pop_utils as pu
import numpy.linalg as la
from tqdm import tqdm
import sys
sys.path.append('/auto/users/hellerc/nems/nems/charlie_population_coding')
from baphy_charlie import load_baphy_file2
import scipy.signal as ss
import NRF_tools as NRF
import os
#=============================================================================
#                              Loading data
#=============================================================================

bytrial=1
bystim=0

#---------------------------- SET UP DB QUERY --------------------------------
user = 'david'
passwd = 'nine1997'
host = 'neuralprediction.org'
database = 'cell'
from sqlalchemy import create_engine
db_uri = 'mysql+pymysql://{0}:{1}@{2}/{3}'.format(user, passwd, host, database)
engine = create_engine(db_uri)
if bystim:
    f = '/auto/data/code/nems_in_cache/batch299/BOL005c-04-1_b299_none_fs100.mat'
if bytrial:
    f = '/auto/data/code/nems_in_cache/batch299/BOL005c-04-1_b299_pertrial_ozgf_c18_fs100.mat'
    #f = '/auto/data/code/nems_in_cache/batch299/BOL006b-02-1_b299_pertrial_ozgf_c18_fs100.mat'
#f = '/auto/data/code/nems_in_cache/batch299/BOL006b-02-1_b299_none_fs100.mat'

data = load_baphy_file2(f)
# ----------- pull units with given iso criteria matching filename f ----------
cid = data['id'][0]
respfile = os.path.basename(data['resp_fn'][0])
# get rawid
rid = engine.execute('SELECT rawid FROM sCellFile WHERE respfile = "'+respfile+'" AND cellid = %s', (cid,))
for obj in rid:
    rawid = str(obj[0])
isolation = 84
chan_unit_cellid = engine.execute('SELECT channum, unit, cellid FROM gSingleRaw WHERE isolation  > %s AND rawid = %s', (isolation,rawid)).fetchall()
chan_unit_cellid = sorted(chan_unit_cellid, key=lambda x: x[-1])

keep_ind = []
for i in range(0, len(chan_unit_cellid)):
    keep_ind.append(np.argwhere(data['cellids'] == np.array(chan_unit_cellid)[:,2][i]))

keep_ind = [int(s) for s in keep_ind]

trialen = int(data['respFs']*(data['prestim']+data['duration']+data['poststim'])) #remove nans
r = data['resp'][0:trialen,:,:,keep_ind]
p = data['pupil'][0:trialen,:,:]
cellids = data['cellids'][keep_ind]


# ----------------------------- pre-process data -----------------------------
# choose which data to keep (spont, stim1, stim2 etc)
spontonly = 0

if spontonly:
    r, p = pu.get_spont_data(r, data['pupil'], data['prestim'], data['respFs'])

#use scipy's resample which uses fft and low pass FIR filtering (faster))
fs = 10

samps = int(round(fs*(r.shape[0]/100.0)))
r = ss.resample(r, samps)
p = ss.resample(p, samps)

# z-score spikes and pupil
r = pu.whiten(r)
p = pu.whiten(p)

if bytrial:
    # Must reorder into stimid oriented for NRF fitting
    p, r = NRF.sort_bytrial_voc(r,p,data)
elif bystim:
    pass
bincount = r.shape[0]
repcount = r.shape[1]
stimcount = r.shape[2]
cellcount = r.shape[3]
# --------- sanity check on data processing - visualize the psth's -----------
plt.figure()
for i in range(0,cellcount):
    plt.plot(np.squeeze(np.mean(r[:,:, 1,i],1)))
plt.title('psth for binned, z-scored, stim2')
print('data pre-processing and visualization complete')

# ============================================================================
#                                   NRF
# ============================================================================
print('NRF...')

# ========================= Compare r0 vs. NRF (rN) ===========================
print('Comparing different models...')
def onpick3(event):
    ind = event.ind
    print('onpick3 scatter:', cellids[ind][0])

# fit model
n_cvs = 10
rN = NRF.NRF_fit(r, cv_count=n_cvs, model='NRF_PSTH', spontonly=spontonly, shuffle=True)
r0 = NRF.NRF_fit(r, cv_count=n_cvs, model='PSTH_only', spontonly=spontonly, shuffle=True)

#evaluate model performance
#re-sort r and p into by trial (in time) and compute performance across trials ind of stim
if bytrial:
    rbytrial = np.empty((bincount, stimcount*repcount, cellcount))
    rNbytrial = np.empty((bincount, stimcount*repcount, cellcount))
    r0bytrial = np.empty((bincount, stimcount*repcount, cellcount))
    pbytrial = np.empty((bincount, stimcount*repcount))
    
    for stim in range(0, stimcount):
        inds = [t[0] for t in np.argwhere(data['stimids']==(stim+1))]
        for i, idx in enumerate(inds):
            rbytrial[:,idx,:] = r[:,i,stim,:]
            rNbytrial[:,idx,:]=rN[:,i,stim,:]
            r0bytrial[:,idx,:]=r0[:,i,stim,:]
            pbytrial[:,idx]=p[:,i,stim]
    r = rbytrial[:,:,np.newaxis,:]
    rN = rNbytrial[:,:,np.newaxis,:]
    r0 = r0bytrial[:,:,np.newaxis,:]
    p = pbytrial[:,:,np.newaxis]
    rN_perf = NRF.eval_fit(r, rN)
    r0_perf = NRF.eval_fit(r, r0)
    stimcount = 1
    repcount = r.shape[1]
#evaluate model performance
if bystim:
    rN_perf = NRF.eval_fit(r, rN)
    r0_perf = NRF.eval_fit(r, r0)




plt.figure()
plt.plot((rN_perf['mean']), '.', alpha=0.7)
plt.xticks(np.arange(0,cellcount),cellids, rotation=90, fontsize=6)
plt.title('Corr coef over all trials/stims')

x = np.linspace(-1,1,3)
ncols = np.ceil(repcount/7)
nrows = 7
color = np.arange(cellcount)
for stim in range(0, stimcount):
    fig = plt.figure()
    for rep in range(0, repcount):
        ax = fig.add_subplot(nrows,ncols,rep+1)
        ax.scatter(r0_perf['bytrial'][rep,stim,:], rN_perf['bytrial'][rep,stim,:], c=color,s=10,picker=True)
        ax.plot(x, x, '-k',lw=2)
        ax.axis([-.1,1,-.1,1])
        ax.set_title(rep+1, fontsize=7)
        fig.canvas.mpl_connect('pick_event',onpick3)
        if rep != (ncols*nrows - ncols):
                ax.set_xticks([])
                ax.set_yticks([])
        else:
            ax.set_ylabel('rN')
            ax.set_xlabel('r0')
    fig.suptitle('r0 vs. rN for each cell \n stim: %s, rawid: %s, spontonly: %s, fs: %s' %(stim+1, rawid, spontonly, fs))

# ======= Evaluate r0 and rN performance over trials (av over neuron) ==========
rN_av_over_cells = (np.nanmean(rN_perf['bytrial'],2))
r0_av_over_cells = (np.nanmean(r0_perf['bytrial'],2))

for stim in range(0, stimcount):
    diff =rN_av_over_cells[:,stim]-r0_av_over_cells[:,stim]
    pup = np.squeeze(np.nanmean(p[:,:,stim],0))/10
    plt.figure()
    if bystim ==0:
        plt.title('stim: all, rawid: %s, fs: %s, \n pupil vs. diff: %s' %(
    rawid, fs, np.corrcoef(pup, diff)[0][1]))
    else:
        plt.title('stim: %s, rawid: %s, fs: %s, \n pupil vs. diff: %s' %(stim+1,
    rawid, fs, np.corrcoef(pup, diff)[0][1]))
    plt.plot(rN_av_over_cells[:,stim], '-o', color='r')
    plt.plot(r0_av_over_cells[:,stim], '-o', color='b')
    plt.plot(diff, '-o', color='g')
    plt.plot(pup, '-o', color='k')
    plt.xlabel('Trial')
    plt.ylabel('Corr coef')
    plt.legend(['rN', 'r0', 'diff', 'pupil'])


plt.show()

sys.exit('Finished NRF model fitting')
# ------------------- Weight matrix for single time point --------------------

r = r.reshape(bincount*stimcount*repcount, cellcount)
h = np.empty((cellcount,cellcount))
for i in tqdm(range(0, cellcount)):
    n = i
    neuron = r[:,n]
    r_temp = np.delete(r, n, 1)
    Css = np.matmul(r_temp.T, r_temp)/len(r_temp)
    Csr = np.matmul(r_temp.T, neuron)/len(r_temp)
    h_temp = np.matmul(la.inv(Css).T, Csr)
    h[i,:] = np.concatenate((h_temp[0:i], np.zeros(1), h_temp[i:len(h_temp)]))
plt.figure()
plt.title('Auto-correlation matrix')
plt.imshow(Css)

plt.figure()
plt.title("Filters")
plt.xlabel('neurons')
plt.ylabel('neurons')
plt.imshow(h)
plt.colorbar()

import seaborn as sn
plt.figure()
sn.heatmap(h, yticklabels=cellids) #, xticklabels=cellids, cmap='jet')
plt.yticks(rotation=0)
#plt.xticks(rotation=90)

# ------------------------- weight matri(ces) with lags ---------------------
# get matrix
seconds = 1
r = r.reshape(bincount, repcount, stimcount, cellcount)
h = NRF.get_weight_mat(r, seconds, fs)

# plot results
cols = 5
rows = 6
fig, axes = plt.subplots(ncols = cols, nrows = rows)
ma = np.max(np.max(np.max(h)))
mi = np.min(np.min(np.min(h)))
for i, ax in enumerate(axes.flat):
    if i >= cellcount:
        break
    im = ax.imshow(h[i].T, aspect='auto', vmin=mi, vmax=ma)
    ax.set_title(cellids[i], fontsize=7)
    if i != (cols*rows - cols):
        ax.set_xticks([])
        ax.set_yticks([])
    else:
        ax.set_ylabel('neurons')
        ax.set_xlabel('bins')
        ax.grid(False)
fig.suptitle(('fs: %s  rawid: %s'%(fs,rawid)))
fig.colorbar(im, ax=axes.ravel().tolist())





plt.show()
