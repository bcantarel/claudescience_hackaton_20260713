
import pandas as pd, numpy as np, pickle, json, time
import xgboost as xgb, shap
t0=time.time()
ME=pd.read_csv("/tmp/gtex/ME_local.csv",index_col=0)
wg=pickle.load(open("/tmp/gtex/wgcna_input.pkl","rb"))
gm=pd.read_csv("/tmp/gtex/phaseB_gene_TF_module.csv")
tf_ids=gm[gm.is_TF].ensembl_gene.tolist()
sym=gm.dropna(subset=['symbol']).set_index('ensembl_gene').symbol.to_dict()
TFX=wg.loc[wg.index.isin(tf_ids)].T
tf_cols=TFX.columns.tolist()

modules=[c for c in ME.columns]
singles=[]; pairs=[]
for m in modules:
    y=ME[m].values
    dtr=xgb.XGBRegressor(n_estimators=300,max_depth=4,learning_rate=0.05,
        subsample=0.8,colsample_bytree=0.5,n_jobs=14,random_state=0,verbosity=0)
    dtr.fit(TFX.values,y)
    gain=dtr.feature_importances_
    order=np.argsort(gain)[::-1]
    top=order[:15]  # top-15 candidate TFs for this module
    # singles
    for rnk,i in enumerate(order[:20]):
        if gain[i]<=0: break
        singles.append((m,sym.get(tf_cols[i],tf_cols[i]),tf_cols[i],float(gain[i]),rnk+1))
    # SHAP interaction among top-15 (restrict features for tractable interaction calc)
    sub=TFX.values[:,top]
    subnames=[sym.get(tf_cols[i],tf_cols[i]) for i in top]
    m2=xgb.XGBRegressor(n_estimators=200,max_depth=4,learning_rate=0.05,
        subsample=0.8,n_jobs=14,random_state=0,verbosity=0).fit(sub,y)
    expl=shap.TreeExplainer(m2)
    # sample 800 rows for interaction (O(n*T^2))
    idx=np.random.RandomState(0).choice(len(y),min(800,len(y)),replace=False)
    inter=expl.shap_interaction_values(sub[idx])  # n x T x T
    mean_abs=np.abs(inter).mean(0)                 # T x T
    np.fill_diagonal(mean_abs,0)
    T=len(subnames)
    for a in range(T):
        for b in range(a+1,T):
            pairs.append((m,subnames[a],subnames[b],float(mean_abs[a,b])))
    print(f"{m} done {round(time.time()-t0,1)}s")
S=pd.DataFrame(singles,columns=["module","TF","TF_ens","xgb_gain","gain_rank"])
P=pd.DataFrame(pairs,columns=["module","TF_a","TF_b","shap_interaction"])
S.to_csv("/tmp/gtex/cocktail_singles.csv",index=False)
P.to_csv("/tmp/gtex/cocktail_pairs.csv",index=False)
print("SINGLES",len(S),"PAIRS",len(P),"elapsed",round((time.time()-t0)/60,1),"min")
