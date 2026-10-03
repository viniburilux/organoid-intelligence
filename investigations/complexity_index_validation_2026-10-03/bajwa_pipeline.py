import mne,sys,json,numpy as np,time
sys.path.insert(0,'/tmp/pyc')
import pyconscious as pc
import mne_icalabel as il
from autoreject import AutoReject
mne.set_log_level('ERROR')
def run(s,task,w0,w1):
    t0=time.time()
    r=mne.io.read_raw_brainvision(f'/tmp/w/bajwa/sub-{s}/sub-{s}_{task}_eeg.vhdr')
    d=r.times[-1]
    a,b=(0,120) if w0 is None else (d-60-120,d-60)
    r.crop(a,b);r.load_data()
    if r.ch_names[-1]=='EMG': r.set_channel_types({'VEOG':'eog','HEOG':'eog','EMG':'emg'});r.drop_channels(['EMG'])
    else: r.set_channel_types({'VEOG':'eog','HEOG':'eog'})
    r.set_montage('standard_1005')
    r.resample(250);r.filter(0.5,40,method='fir',picks=['eeg','eog'])
    e=mne.add_reference_channels(r,['ref'],copy=True);e,_=mne.set_eeg_reference(e,['ref'])
    w=mne.preprocessing.EOGRegression(picks='eeg',picks_artifact='eog').fit(e);c=w.apply(e,copy=True);c.drop_channels(['ref'])
    n=int(c.times[-1]//5);ev=np.array([[c.first_samp+i*5*250,0,1] for i in range(n)])
    ep=mne.Epochs(c,ev,tmin=0,tmax=5-1/250,baseline=None,preload=True,reject=None)
    d=ep.get_data();p2p=np.ptp(d,axis=2);thr=np.median(p2p,axis=0)+4*1.4826*np.median(np.abs(p2p-np.median(p2p,axis=0)),axis=0)
    bad=(p2p>thr).mean(axis=1)>0.2;ep2=ep[~bad];print('rejected',int(bad.sum()),'of',len(bad),flush=True)
    ep2.set_eeg_reference('average')
    ica=mne.preprocessing.ICA(n_components=20,random_state=100,method='infomax',fit_params=dict(extended=True));ica.fit(ep2)
    lab=il.label_components(ep2,ica,method='iclabel')
    ex=[i for i,(l,p) in enumerate(zip(lab['labels'],lab['y_pred_proba'])) if l in('eye blink','muscle artifact','channel noise') and p>0.75]
    rec=ep2.copy();ica.apply(rec,exclude=ex)
    rec.apply_baseline((None,None));csd=mne.preprocessing.compute_current_source_density(rec)
    X=csd.get_data(picks='csd')
    v=pc.LZc(X)
    return dict(lzc=float(v),n_epochs=int(X.shape[0]),n_ch=int(X.shape[1]),ic_removed=len(ex),bad_epochs=int(bad.sum()),sec=round(time.time()-t0))
out={}
for s in sys.argv[1:]:
    try:
        out[s]={'awake':run(s,'task-awake_acq-EC',None,None),'sed':run(s,'task-sed_acq-rest_run-1',1,1)};print(s,out[s],flush=True)
    except Exception as ex:
        import traceback;traceback.print_exc();print('FAIL',s,flush=True)
    json.dump(out,open('/tmp/w/bajwa_pipeline_results.json','w'),indent=1)
