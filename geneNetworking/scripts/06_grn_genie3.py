
import pandas as pd, numpy as np, pickle, time
from sklearn.ensemble import ExtraTreesRegressor
from joblib import Parallel, delayed
t0=time.time()
wg=pickle.load(open("/tmp/gtex/wgcna_input.pkl","rb"))          # genes x samples
gm=pd.read_csv("/tmp/gtex/phaseB_gene_TF_module.csv")
tf_ids=gm[gm.is_TF].ensembl_gene.tolist()
targets=gm[gm.module!='grey'].ensembl_gene.tolist()             # 7034
X=wg.T                                                          # samples x genes
# standardize each gene to unit variance (GENIE3 normalizes target; z-score features too)
Xz=(X-X.mean(0))/(X.std(0)+1e-9)
TFmat=Xz[tf_ids].values.astype(np.float32)                     # samples x 793
tf_arr=np.array(tf_ids)
NEST=100; TOPK=30
def one(target):
    y=Xz[target].values.astype(np.float32)
    # exclude self if target is a TF
    if target in tf_set:
        keep=tf_arr!=target; Xt=TFmat[:,keep]; names=tf_arr[keep]
    else:
        Xt=TFmat; names=tf_arr
    m=ExtraTreesRegressor(n_estimators=NEST,max_features="sqrt",n_jobs=1,random_state=0)
    m.fit(Xt,y)
    imp=m.feature_importances_
    if imp.sum()>0: imp=imp/imp.sum()
    idx=np.argsort(imp)[::-1][:TOPK]
    return [(names[i],target,float(imp[i])) for i in idx if imp[i]>0]
tf_set=set(tf_ids)
res=Parallel(n_jobs=14,backend="threading",verbose=0)(delayed(one)(t) for t in targets)
edges=[e for sub in res for e in sub]
E=pd.DataFrame(edges,columns=["TF","target","weight"])
E.to_parquet("/tmp/gtex/genie3_edges.parquet"); E.to_csv("/tmp/gtex/genie3_edges.csv.gz",index=False,compression="gzip")
print("edges:",len(E),"| targets:",E.target.nunique(),"| elapsed min:",round((time.time()-t0)/60,1))
