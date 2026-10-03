import mne,json,sys,numpy as np
sys.argv=['x'];exec(open('/tmp/w/lz.py').read().split("D='/tmp/f")[0].replace('cache=True',''))
from scipy.stats import wilcoxon
mne.set_log_level('ERROR')
D='/tmp/w/bajwa/'
subs=['1010','1017','1024','1036','1046','1055','1060','1062','1067','1071']
disc=['1010','1024','1046','1060','1067'];held=['1017','1036','1055','1062','1071']
def meas(s,t):
    p=f'{D}sub-{s}/sub-{s}_{t}_eeg.vhdr'
    r=mne.io.read_raw_brainvision(p,preload=False)
    r.pick('eeg');d=r.times[-1];t1=d-60 if d>260 else d;r.crop(max(0,t1-200),t1);print('dur',round(d),flush=True);r.load_data();r.filter(0.5,40,verbose=False);r.resample(250)
    X=r.get_data();T=X.shape[1]//2000
    X=X[:,:T*2000].reshape(X.shape[0],T,2000).transpose(1,0,2)[:20]
    ch=list(range(0,X.shape[1],3))
    return float(np.mean([lzn(X[e,c],'med') for e in range(X.shape[0]) for c in ch])),X.shape[1],T
out={}
for s in subs:
    try:
        a=meas(s,'task-awake_acq-EC');b=meas(s,'task-sed_acq-rest_run-1')
        out[s]={'awake':a,'sed':b};print(s,a,b,flush=True)
    except Exception as e: print('FAIL',s,str(e)[:150],flush=True)
json.dump(out,open('/tmp/w/bajwa_attempt2_results.json','w'),indent=1)
for name,G in [('all',subs),('disc',disc),('held',held)]:
    d=np.array([out[s]['sed'][0]-out[s]['awake'][0] for s in G if s in out]);
    if len(d)>1:
        r=np.random.default_rng(1);bs=[r.choice(d,len(d)).mean() for _ in range(4000)]
        print(name,len(d),'meanΔ %.4f'%d.mean(),np.percentile(bs,[2.5,97.5]).round(4),'down',int((d<0).sum()),'p',wilcoxon(d).pvalue if len(d)>4 else None)
