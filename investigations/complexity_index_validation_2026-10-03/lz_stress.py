import mne,glob,re,json,numpy as np
exec(open('/tmp/w/lz.py').read().split("D='/tmp/f")[0].replace('cache=True',''))
from scipy.stats import wilcoxon
mne.set_log_level('ERROR')
def lzv(x,mode,norm=True):
    if mode=='mean': b=(x>x.mean()).astype(np.uint8)
    else: b=(x>np.median(x)).astype(np.uint8)
    c=lz76(b)
    if not norm: return c/len(b)
    sh=b.copy();rng.shuffle(sh);return c/max(lz76(sh),1)
D='/tmp/f/Farnes_et_al_PLOS_ONE_Dryad/spontaneous/'
files={}
for f in sorted(glob.glob(D+'*.set')):
    n=f.split('/')[-1];s=n[:3];rec=int(re.search(r'_(\d{4})',n).group(1))
    files.setdefault(s,[]).append((rec,f,'open' if re.search('open|pen',n,re.I) else 'closed'))
V={'mean_bin':dict(mode='mean',chs=0,ne=99,norm=True),'odd_ch':dict(mode='med',chs=1,ne=99,norm=True),'first8ep':dict(mode='med',chs=0,ne=8,norm=True),'unnorm':dict(mode='med',chs=0,ne=99,norm=False)}
res={}
for s,L in files.items():
    L.sort()
    for idx,(rec,f,eye) in enumerate(L):
        cond='wake' if idx<2 else 'ket'
        try: X=mne.io.read_epochs_eeglab(f).get_data()
        except Exception as e: continue
        for v,p in V.items():
            res[f'{v}|{s}|{cond}|{eye}']=float(np.mean([lzv(X[e,c],p['mode'],p['norm']) for e in range(min(p['ne'],X.shape[0])) for c in range(p['chs'],X.shape[1],2)]))
json.dump(res,open('/tmp/w/lz_stress_results.json','w'),separators=(',',':'))
subs=sorted({k.split('|')[1] for k in res});held=subs[1::2]
for v in V:
  for eye in ['open','closed']:
    for name,G in [('all',subs),('held',held)]:
      d=np.array([res[f'{v}|{s}|ket|{eye}']-res[f'{v}|{s}|wake|{eye}'] for s in G if f'{v}|{s}|ket|{eye}' in res and f'{v}|{s}|wake|{eye}' in res])
      r=np.random.default_rng(1);bs=[r.choice(d,len(d)).mean() for _ in range(4000)]
      print(v,eye,name,'n',len(d),'Δ %.4f'%d.mean(),np.percentile(bs,[2.5,97.5]).round(4),'up',int((d>0).sum()),'p',round(wilcoxon(d).pvalue,3) if len(d)>4 else None)
