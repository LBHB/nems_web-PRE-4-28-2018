import numpy as np
import scipy.io
import scipy.signal
import copy

empty_data={}

class nems_data:
    """nems_data

    NOT USED CURRENTLY!  JUST USING LIST OF DICTIONARIES FOR DATA STACK!
    
    Generic NEMS data bucket

    provides input and output of each nems_module

    structure containing a set of matrices, corresponding to input(s)
    and output(s). eg, resp, stim, stim2, state, etc.

    """
    est_files=[]
    val_files=[]
    data=[]
    
    def __init__(self):
        self.data=[]

    def d(self,n=None):
        if n is None:
            return self.data
        else:
            return self.data[n]

    def copy_keys(self,d_in=None):
        if d_in != None:
            self.est_files=d_in.est_files
            self.val_files=d_in.val_files
            self.data=d_in.data.copy()

# end nems_data

        
        
class nems_module:
    """nems_module

    Generic NEMS module

    """
    
    # common properties for all modules
    name='pass-through'
    input_name='stim'  # name of input matrix in d_in
    output_name='stim' # name of output matrix in d_out
    phi=None # vector of parameter values that can be fit
    d_in=None
    d_out=None
    fit_params=[]
    meta={}

    def __init__(self,d_in=None):
        self.data_setup(d_in)
        
    def data_setup(self,d_in=None):
        if d_in is None:
            self.d_in=[] # list of data buckets fed into module
        else:
            self.d_in=d_in
        self.d_out=[] # list of outputs, same size as data in

    def prep_eval(self):
        del self.d_out[:]
        for i, val in enumerate(self.d_in):
            self.d_out.append(val)
        
    def eval(self):
        # default: pass-through pointers to data from input to output,
        # need to deepcopy individual dict entries if they are changed
        self.prep_eval()
        
    def parms2phi(self):
        phi=np.empty(shape=[0,1])
        for k in self.fit_params:
            phi=np.append(phi,getattr(self, k).flatten())
        return phi
        
    def phi2parms(self,phi=[]):
        os=0;
        for k in self.fit_params:
            s=getattr(self, k).shape
            setattr(self,k,phi[os:(os+np.prod(s))].reshape(s))
            os+=np.prod(s)
            
    def auto_plot(self):
        print("dummy auto_plot")
        
# end nems_module

class load_mat(nems_module):

    name='load_mat'
    est_files=[]
    val_files=[]
    fs=100
    
    def __init__(self,d_in=None,est_files=[],val_files=[],fs=100):
        self.data_setup(d_in)
        self.est_files=est_files.copy()
        self.val_files=val_files.copy()
        self.fs=fs

    def eval(self):
        self.prep_eval()
        self.meta['est_files']=self.est_files
        self.meta['val_files']=self.val_files
        
        # new list object for dat
        del self.d_out[:]
        
        # load contents of Matlab data file
        for f in self.est_files:
            #f='tor_data_por073b-b1.mat'
            matdata = scipy.io.loadmat(f,chars_as_strings=True)
            try:
                s=matdata['data'][0][0]
                data={}
                data['resp']=s['resp_raster']
                data['stim']=s['stim']
                data['respFs']=s['respfs']
                data['stimFs']=s['stimfs']
                data['stimparam']=[str(''.join(letter)) for letter in s['fn_param']]
                data['isolation']=s['isolation']
            except:
                data = scipy.io.loadmat(f,chars_as_strings=True)
                data['raw_stim']=data['stim'].copy()
                data['raw_resp']=data['resp'].copy()
#            data = scipy.io.loadmat(f,chars_as_strings=True)
#            data['raw_stim']=data['stim'].copy()
#            data['raw_resp']=data['resp'].copy()
                
            data['fs']=self.fs
            stim_resamp_factor=self.fs/data['stimFs']
            resp_resamp_factor=self.fs/data['respFs']
                                
            # reshape stimulus to be channel X time
            data['stim']=np.transpose(data['stim'],(0,2,1))
            if stim_resamp_factor != 1:
                s=data['stim'].shape
                new_stim_size=np.round(s[2]*stim_resamp_factor)
                print('resampling stim from {0} to {1}'.format(s[2],new_stim_size))
                data['stim']=scipy.signal.resample(data['stim'],new_stim_size,axis=2)
                
            # resp time (axis 0) should be resampled to match stim time (axis 1)
            if resp_resamp_factor != 1:
                s=data['resp'].shape
                new_resp_size=np.round(s[0]*resp_resamp_factor)
                print('resampling response from {0} to {1}'.format(s[0],new_resp_size))
                # why warning here??
                data['resp']=scipy.signal.resample(data['resp'],new_resp_size,axis=0)
                
            # average across trials
            data['resp']=np.nanmean(data['resp'],axis=1)
            data['resp']=np.transpose(data['resp'],(1,0))
            
            # append contents of file to data, assuming data is a dictionary
            # with entries stim, resp, etc...
            print('load_mat: appending {0} to d_out stack'.format(f))
            self.d_out.append(data)

            # spectrogram of TORC stimuli. 15 frequency bins X 300 time samples X 30 different TORCs
            #stim=data['stim']
            #FrequencyBins=data['FrequencyBins'][0,:]
            #stimFs=data['stimFs'][0,0]
            #StimCyclesPerSec=data['StimCyclesPerSec'][0,0]
            #StimCyclesPerSec=np.float(StimCyclesPerSec)
            
            # response matrix. sampled at 1kHz. value of 1 means a spike occured
            # in a particular time bin. 0 means no spike. shape: [3000 time bins X 2
            # repetitions X 30 different TORCs]
                                                                  
            #resp=data['resp']
            #respFs=data['respFs'][0,0]
            
            # each trial is (PreStimSilence + Duration + PostStimSilence) sec long
            #Duration=data['Duration'][0,0] # Duration of TORC sounds
            #PreStimSilence=data['PreStimSilence'][0,0]
            #PostStimSilence=data['PostStimSilence'][0,0]
        
class add_scalar(nems_module):
 
    name='add_scalar'
    
    def __init__(self, d_in=None, n=1, fit_params=['n']):
        self.fit_params=fit_params
        self.data_setup(d_in)
        self.n=n
       
    def eval(self):
        del self.d_out[:]
        for i, val in enumerate(self.d_in):
            self.d_out.append(copy.deepcopy(val))

        for f in self.d_out:
            f[self.output_name]=f[self.input_name]+self.n
        
class sum_dim(nems_module):
    name='sum_dim'
     
    def __init__(self, d_in=None, dim=1):
        self.data_setup(d_in)
        self.dim=dim
        
    def eval(self):
        del self.d_out[:]
        for i, val in enumerate(self.d_in):
            self.d_out.append(copy.deepcopy(val))

        for f in self.d_out:
            f[self.output_name]=f[self.input_name].sum(axis=self.dim)

            
class fir_filter(nems_module):
    name='fir_filter'
    coefs=None
    baseline=np.zeros([1,1])
    num_dims=0
    
    def __init__(self, d_in=None, num_dims=0, num_coefs=20, baseline=0, fit_params=['baseline','coefs']):
        if d_in and not(num_dims):
            num_dims=d_in[0]['stim'].shape[0]
        self.num_dims=num_dims
        self.num_coefs=num_coefs
        self.baseline[0]=baseline
        self.coefs=np.zeros([num_dims,num_coefs])
        
        self.fit_params=fit_params
        self.data_setup(d_in)
        
    def eval(self):
        #if not self.d_out:
        #    # only allocate memory once, the first time evaling. rish is that output_name could change
        del self.d_out[:]
        for i, val in enumerate(self.d_in):
            #self.d_out.append(copy.deepcopy(val))
            self.d_out.append(val.copy())
            self.d_out[-1][self.output_name]=copy.deepcopy(self.d_out[-1][self.output_name])
            
        for f_in,f_out in zip(self.d_in,self.d_out):
            X=copy.deepcopy(f_in[self.input_name])
            s=X.shape
            X=np.reshape(X,[s[0],-1])
            for i in range(0,s[0]):
                y=np.convolve(X[i,:],self.coefs[i,:])
                X[i,:]=y[0:X.shape[1]]
            X=X.sum(0)+self.baseline
            f_out[self.output_name]=np.reshape(X,s[1:])

class mean_square_error(nems_module):
 
    name='mean_square_error'
    input1='stim'
    input2='resp'
    output=np.ones([1,1])
    norm=True
    
    def __init__(self, d_in=None, input1='stim',input2='resp',norm=True):
        self.data_setup(d_in)
        self.input1=input1
        self.input2=input2
        self.norm=norm
        
    def eval(self):
        self.prep_eval()
        E=np.zeros([1,1])
        P=np.zeros([1,1])
        N=0
        for f in self.d_out:
            E+=np.sum(np.sum(np.sum(np.square(f[self.input1]-f[self.input2]))))
            P+=np.sum(np.sum(np.sum(np.square(f[self.input2]))))
            N+=f[self.input2].size
    
        if self.norm:
            mse=E/P
        else:
            mse=E/N
            
        self.meta['est_mse']=mse
        
        return mse

    def error(self, est_data=True):
        if est_data:
            return self.meta['est_mse']
        else:
            # placeholder for something that can distinguish between est and val
            return self.meta['val_mse']
            
class nems_stack:
    """nems_stack

    Properties:
     modules = list of nems_modules in sequence of execution

    """
    modules=[]  # stack of modules
    data=[]     # corresponding stack of data in/out for each module
    modelname=None
    meta={}
    
    def __init__(self):
        print("dummy")
        self.modules=[]
        self.data=[]
        self.meta={}
        self.modelname='Empty stack'
        self.error=self.default_error
        
    def eval(self,start=0):
        # evalute stack, starting at module # start
        for ii in range(start,len(self.modules)):
            #if ii>0:
            #    print("Propagating mod {0} d_out to mod{1} d_in".format(ii-1,ii))
            #    self.modules[ii].d_in=self.modules[ii-1].d_out
            self.modules[ii].eval()
            
    def append(self, mod=None):
        if mod is None:
            mod=nems_module()
        mod.meta=self.meta
        if len(self.modules):
            print("Propagating d_out from {0} into new d_in".format(self.modules[-1].name))
            mod.d_in=self.data[-1]
        self.modules.append(mod)
        self.data.append(mod.d_out)
        
    def popmodule(self, mod=nems_module()):
        del self.modules[-1]
        del self.data[-1]
        
    def output(self):
        return self.data[-1]
    
    def default_error(self):
        return np.zeros([1,1])
        
# end nems_stack



        
