import gzip, os, tarfile, subprocess, gc, json, numpy as np, pandas as pd
BGEE="https://www.bgee.org/ftp/current/download/processed_expr_values/rna_seq"
G="/tmp/gtex"

Xh_full=pd.read_pickle(f"{G}/wgcna_input.pkl")
hs_mod_full=pd.read_csv(f"{G}/stage1_gene_modules_local.csv").set_index('ensembl_gene')['module'].reindex(Xh_full.index)
mods=[m for m in hs_mod_full.unique() if m!='grey']

def download_bgee(sp):
    dst=f"{G}/bgee_{sp}.tar.gz"
    if os.path.exists(dst) and os.path.getsize(dst)>1e5: return dst
    subprocess.run(["curl","-sL","-m","900",f"{BGEE}/{sp}/{sp}_RNA-Seq_read_counts_TPM.tar.gz","-o",dst],capture_output=True)
    return dst

def load_bgee(sp,minlib=3):
    dst=download_bgee(sp); tpm={}; ltd={}
    with tarfile.open(dst,"r:gz") as tar:
        for mem in tar.getmembers():
            if not mem.name.endswith(".gz"): continue
            f=tar.extractfile(mem)
            if f is None: continue
            gz=gzip.GzipFile(fileobj=f)
            head=gz.readline().decode().rstrip("\n").split("\t")
            ci={c:i for i,c in enumerate(head)}
            gi,li,ti,ai=ci["Gene ID"],ci["Library ID"],ci["TPM"],ci["Anatomical entity name"]
            for line in gz:
                p=line.decode().rstrip("\n").split("\t")
                if len(p)<=ti: continue
                tpm.setdefault(p[li],{})[p[gi]]=float(p[ti]); ltd[p[li]]=p[ai].strip('"')
    M=np.log2(pd.DataFrame(tpm).fillna(0)+1); lt=pd.Series(ltd)
    good=lt.value_counts(); keept=good[good>=minlib].index
    keep=[l for l in lt[lt.isin(keept)].index if l in M.columns]
    return M[keep], lt.loc[keep]

def adjc(X,beta=8):
    A=X.to_numpy(dtype=np.float32); Az=A-A.mean(1,keepdims=True); Az/=np.linalg.norm(Az,axis=1,keepdims=True)+1e-12
    c=Az@Az.T; np.clip(c,-1,1,out=c); a=np.maximum(c,0)**beta; np.fill_diagonal(a,0)
    return a.astype(np.float32), c.astype(np.float32)

def preservation(sp,nperm=150,seed=0):
    o=pd.read_csv(f"{G}/orth/{sp}.tsv",sep="\t",header=None,names=["hs","tg","type","conf"])
    o2o=o[(o.type=="ortholog_one2one")&(o.tg.notna())].drop_duplicates('hs').drop_duplicates('tg')
    m=o2o.set_index('hs')['tg']
    Xsp,lt=load_bgee(sp)
    common=[g for g in Xh_full.index if g in m.index and m[g] in Xsp.index]
    if len(common)<500: return None
    Xh=Xh_full.loc[common]; Xs=Xsp.loc[[m[g] for g in common]].copy(); Xs.index=common
    hs=hs_mod_full.loc[common].to_numpy()
    adjH,corrH=adjc(Xh); adjS,corrS=adjc(Xs)
    gi={mm:np.where(hs==mm)[0] for mm in mods}; allidx=np.arange(len(common)); rng=np.random.default_rng(seed)
    def st(idx):
        n=len(idx)
        if n<3: return None
        iu=np.triu_indices(n,1)
        aH=adjH[np.ix_(idx,idx)];aS=adjS[np.ix_(idx,idx)];cH=corrH[np.ix_(idx,idx)];cS=corrS[np.ix_(idx,idx)]
        return dict(meanAdj=aS[iu].mean(),meanCor=cS[iu].mean(),
                    cor_kIM=np.corrcoef(aH.sum(0),aS.sum(0))[0,1],
                    cor_cor=np.corrcoef(cH[iu],cS[iu])[0,1],cor_adj=np.corrcoef(aH[iu],aS[iu])[0,1])
    obs={mm:st(gi[mm]) for mm in mods if len(gi[mm])>=3}
    null={mm:{k:[] for k in ['meanAdj','meanCor','cor_kIM','cor_cor','cor_adj']} for mm in obs}
    for _ in range(nperm):
        perm=rng.permutation(allidx)
        for mm in obs:
            s=st(perm[:len(gi[mm])])
            for k in s: null[mm][k].append(s[k])
    def Z(o,nl): a=np.array(nl); return (o-a.mean())/(a.std()+1e-9)
    rows=[]
    for mm in obs:
        zden=np.median([Z(obs[mm][k],null[mm][k]) for k in ['meanAdj','meanCor']])
        zcon=np.median([Z(obs[mm][k],null[mm][k]) for k in ['cor_kIM','cor_cor','cor_adj']])
        rows.append(dict(module=mm,n_genes=len(gi[mm]),Zdensity=round(zden,2),Zconnectivity=round(zcon,2),Zsummary=round((zden+zcon)/2,2)))
    del adjH,adjS,corrH,corrS; gc.collect()
    pres=pd.DataFrame(rows); pres['species']=sp; pres['n_common']=len(common); pres['n_tissues']=int(lt.nunique()); pres['n_libs']=len(lt)
    return pres

work=pd.read_csv(f"{G}/work_species.csv",header=None)[0].tolist()
done=set()
outp=f"{G}/allsp_preservation.csv"
if os.path.exists(outp): done=set(pd.read_csv(outp).species.unique())
for i,sp in enumerate(work):
    if sp in done: print(f"[{i+1}/{len(work)}] skip {sp}",flush=True); continue
    try:
        pr=preservation(sp)
        if pr is None: print(f"[{i+1}/{len(work)}] {sp} SKIP <500 genes",flush=True); continue
        hdr=not os.path.exists(outp)
        pr.to_csv(outp,mode='a',header=hdr,index=False)
        print(f"[{i+1}/{len(work)}] {sp}: ncommon={pr.n_common.iloc[0]} tissues={pr.n_tissues.iloc[0]} median_Zsum={pr.Zsummary.median():.1f}",flush=True)
    except Exception as e:
        print(f"[{i+1}/{len(work)}] {sp} ERR {str(e)[:80]}",flush=True)
    # cleanup tar to save disk
    t=f"{G}/bgee_{sp}.tar.gz"
    if os.path.exists(t): os.remove(t)
print("SWEEP DONE",flush=True)
