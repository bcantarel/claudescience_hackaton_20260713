
import pandas as pd, numpy as np, pickle, time
from lightgbm import LGBMRegressor
from joblib import Parallel, delayed
t0=time.time()
wg=pickle.load(open("/tmp/gtex/wgcna_input.pkl","rb"))
gm=pd.read_csv("/tmp/gtex/phaseB_gene_TF_module.csv")
tf_ids=gm[gm.is_TF].ensembl_gene.tolist()
targets=gm[gm.module!='grey'].ensembl_gene.tolist()
X=wg.T; Xz=((X-X.mean(0))/(X.std(0)+1e-9))
TFmat=Xz[tf_ids].values.astype(np.float32); tf_arr=np.array(tf_ids); tf_set=set(tf_ids)
TOPK=30

# ---- METHOD 1: GRNBoost2 (LightGBM gradient boosting, arboreto algorithm) ----
def gb_one(target):
    y=Xz[target].values.astype(np.float32)
    if target in tf_set:
        keep=tf_arr!=target; Xt=TFmat[:,keep]; names=tf_arr[keep]
    else: Xt=TFmat; names=tf_arr
    m=LGBMRegressor(n_estimators=200,learning_rate=0.01,max_depth=3,num_leaves=7,
                    subsample=0.9,colsample_bytree=0.1,n_jobs=1,verbosity=-1,random_state=0)
    m.fit(Xt,y)
    imp=m.feature_importances_.astype(float)
    if imp.sum()>0: imp=imp/imp.sum()
    idx=np.argsort(imp)[::-1][:TOPK]
    return [(names[i],target,float(imp[i])) for i in idx if imp[i]>0]
resGB=Parallel(n_jobs=14,backend="threading")(delayed(gb_one)(t) for t in targets)
EGB=pd.DataFrame([e for s in resGB for e in s],columns=["TF","target","gb_weight"])
EGB.to_parquet("/tmp/gtex/grnboost2_edges.parquet")
print("GRNBoost2 edges:",len(EGB),"elapsed",round((time.time()-t0)/60,1),"min")
