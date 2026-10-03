import sys,glob,json,numpy as np,scipy.io as sio
sys.path.insert(0,'/tmp/PCIst')
from PCIst import pci_st
from scipy.stats import wilcoxon
F={}
for f in sorted(glob.glob('/tmp/f/Farnes*/evoked/*.mat')):
    n=f.split('/')[-1]; s,r=n.split('_')[:2]
    d=sio.loadmat(f); F[(s,int(r))]=(d['Y'],d['times'][0])
subs=sorted({s for s,_ in F}); disc=subs[0::2]; held=subs[1::2]
base=dict(baseline_window=(-400,-50),response_window=(0,300),k=1.2,min_snr=1.1,max_var=99,embed=False,n_steps=100)
rng=np.random.default_rng(0)
def pci(s,r,ch=None,ntr=None,**o):
    Y,t=F[(s,r)]
    if ntr: Y=Y[:,:,rng.choice(Y.shape[2],ntr,replace=False)]
    e=Y.mean(2)
    if ch is not None: e=e[ch]
    return pci_st.calc_PCIst(e,t,**{**base,**o})
def summ(group,**kw):
    w=np.array([pci(s,31,**kw) for s in group]);k=np.array([pci(s,32,**kw) for s in group]);d=k-w
    p=wilcoxon(d).pvalue if len(d)>4 and np.any(d!=0) else np.nan
    return dict(wake=w.round(1).tolist(),ket=k.round(1).tolist(),mean_delta=round(d.mean(),2),sd=round(d.std(ddof=1),2),n_up=int((d>0).sum()),n=len(d),p=round(float(p),3))
out={'split':{'disc':disc,'held':held}}
out['default_held']=summ(held); out['default_disc']=summ(disc); out['default_all']=summ(subs)
out['LOSO_mean_delta']={s:round(summ([x for x in subs if x!=s])['mean_delta'],2) for s in subs}
st={}
for name,o in {'resp_0-200':dict(response_window=(0,200)),'resp_0-400':dict(response_window=(0,400)),'base_-300_-50':dict(baseline_window=(-300,-50)),'base_-400_-100':dict(baseline_window=(-400,-100)),'snr1.0':dict(min_snr=1.0),'snr1.5':dict(min_snr=1.5),'snr2.0':dict(min_snr=2.0),'maxvar95':dict(max_var=95),'k1.0':dict(k=1.0),'k1.5':dict(k=1.5),'k2.0':dict(k=2.0)}.items():
    try: st[name]=summ(subs,**o)
    except Exception as e: st[name]=str(e)
for i in range(5):
    ch=np.sort(rng.choice(60,30,replace=False)); st[f'ch50_{i}']=summ(subs,ch=ch)
for i in range(3): st[f'trials200_{i}']=summ(subs,ntr=200)
out['stress_all']=st
json.dump(out,open('results.json','w'),indent=1)
print(json.dumps({k:out[k] for k in ['split','default_held','default_disc','default_all','LOSO_mean_delta']},indent=0))
for k,v in st.items(): print(k,v if isinstance(v,str) else (v['mean_delta'],v['n_up'],v['p']))
