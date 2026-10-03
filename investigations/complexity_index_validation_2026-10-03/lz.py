import mne,glob,re,json,numpy as np
from scipy.signal import hilbert
from scipy.stats import wilcoxon
mne.set_log_level('ERROR')
import numba
@numba.njit(cache=True)
def lz76(s):
    # Kaspar-Schuster
    n=len(s);i,k,l=0,1,1;k_max=1;c=1
    while True:
        if s[i+k-1]==s[l+k-1]:
            k+=1
            if l+k>n: c+=1;break
        else:
            if k>k_max:k_max=k
            i+=1
            if i==l:
                c+=1;l+=k_max
                if l+1>n:break
                i=0;k=1;k_max=1
            else:k=1
    return c
rng=np.random.default_rng(0)
def lzn(x,mode):
    if mode=='amp': x=np.abs(hilbert(x))
    b=(x>np.median(x)).astype(np.uint8) if mode=='med' else (x>x.mean()).astype(np.uint8)
    c=lz76(b);sh=b.copy();rng.shuffle(sh)
    return c/max(lz76(sh),1)
D='/tmp/f/Farnes_et_al_PLOS_ONE_Dryad/spontaneous/'
files={}
for f in sorted(glob.glob(D+'*.set')):
    n=f.split('/')[-1];s=n[:3];rec=int(re.search(r'_(\d{4})',n).group(1))
    files.setdefault(s,[]).append((rec,f,'open' if re.search('open|pen',n,re.I) else 'closed'))
res={}
for s,L in files.items():
    L.sort()
    for idx,(rec,f,eye) in enumerate(L):
        cond='wake' if idx<2 else 'ket'
        try: ep=mne.io.read_epochs_eeglab(f);X=ep.get_data()
        except Exception as e:
            print('FAIL',s,idx,f.split('/')[-1],str(e)[:80],flush=True);continue
        # 8 ch-subsample not applied; all channels, 12 epochs max for speed
        out={}
        for mode in ['med','amp']:
            out[mode]=float(np.mean([lzn(X[e,c],mode) for e in range(X.shape[0]) for c in range(0,X.shape[1],2)]))
        res[(s,cond,eye)]=out|{'shape':list(X.shape),'sfreq':ep.info['sfreq']}
        print(s,cond,eye,X.shape,ep.info['sfreq'],out,flush=True)
json.dump({'|'.join(k):v for k,v in res.items()},open('lz_results.json','w'),indent=1)
