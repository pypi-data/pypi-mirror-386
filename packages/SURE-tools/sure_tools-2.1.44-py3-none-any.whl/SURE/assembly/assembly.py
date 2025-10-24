import scanpy as sc
import pandas as pd
import numpy as np
import scipy as sp
from scipy.sparse import csr_matrix
from sklearn.preprocessing import OneHotEncoder, LabelBinarizer

import os 
import shutil
import tempfile
import subprocess 
import pkg_resources
import datatable as dt

from ..SURE import SURE 
from ..codebook import codebook_generate, codebook_summarize, codebook_aggregate, codebook_sketch, codebook_bootstrap_sketch
from ..utils import convert_to_tensor, tensor_to_numpy
from ..utils import pretty_print
from ..utils import find_partitions_greedy

from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm


def assembly(adata_list_, batch_key, preprocessing=True, hvgs=None,
             n_top_genes=5000, hvg_method='cell_ranger', layer='counts', cuda_id=0, use_jax=False,
             codebook_size=800, codebook_size_per_adata=500, min_gamma=20, learning_rate=0.0001,
             batch_size=200, batch_size_per_adata=100, n_epochs=200, latent_dist='studentt',
             use_dirichlet=False, use_dirichlet_per_adata=False,
             zero_inflation=False, zero_inflation_per_adata=False,
             likelihood='multinomial', likelihood_per_adata='multinomial', 
             #n_samples_per_adata=10000, total_samples=1000000, summarize=False,
             sketch_func='sum', n_bootstrap_neighbors=8,
             #sketching=True, even_sketch=True, bootstrap_sketch=False, n_sketch_neighbors=10,
             n_workers=1, mute=True):
    adata_list = [ad.copy() for ad in adata_list_]
    n_adatas = len(adata_list)
    
    jit=''
    if use_jax:
        jit='--jit'

    # get common hvgs
    if hvgs is None:
        preprocessing = False if (hvg_method=='seurat_v3') else preprocessing
        
        # preprocess
        if preprocessing:
            with tqdm(total=n_adatas, desc='Preprocessing', unit='adata') as pbar:
                for i in np.arange(n_adatas):
                    #print(f'Adata {i+1} / {n_adatas}: Preprocessing')
                    adata_list[i] = preprocess(adata_list[i], layer)
                    pbar.update(1)

        #for i in np.arange(n_adatas):
        #    print(f'Adata {i+1} / {n_adatas}: Find {n_top_genes} HVGs')
        #    hvgs_ = highly_variable_genes(adata_list[i], n_top_genes, hvg_method)
        #    if hvgs is None:
        #        hvgs = set(hvgs_)
        #    else:
        #        hvgs = hvgs & set(hvgs_)
        #hvgs = list(hvgs)
        
        # test
        hvgs = highly_variable_genes_for_adatas(adata_list, n_top_genes, hvg_method)
        print(f'{len(hvgs)} common HVGs are found')
        
    adata_size_list = []
    for i in np.arange(n_adatas):
        adata_size_list.append(adata_list[i].shape[0])

    for i in np.arange(n_adatas):
        mask = [x in adata_list[i].var_names.tolist() for x in hvgs]
        if all(mask):
            adata_list[i] = adata_list[i][:,hvgs]    
        else:
            adata_i_X = get_subdata(adata_list[i], hvgs, 'X')
            adata_i_counts = get_subdata(adata_list[i], hvgs, 'counts')
            adata_i_obs = adata_list[i].obs
            adata_i_new = sc.AnnData(adata_i_X, obs=adata_i_obs)
            adata_i_new.var_names = hvgs
            adata_i_new.layers['counts'] = adata_i_counts
            adata_list[i] = adata_i_new

    models_list = []
    models_file_list = []
    model = None
    # process
    #with tempfile.TemporaryDirectory() as temp_dir:
    try:
        if not os.path.exists('./SURE_temp_dir'):
            os.mkdir('./SURE_temp_dir')
        else:
            pass
        temp_dir = tempfile.mkdtemp(dir='./SURE_temp_dir')
        
        if latent_dist == 'lapacian':
            latent_dist_param='--z-dist laplacian'
        elif latent_dist == 'studentt':
            latent_dist_param='--z-dist studentt'
        elif latent_dist == 'cauchy':
            latent_dist_param='--z-dist cauchy'
        else:
            latent_dist_param=''

        dirichlet = '-dirichlet' if use_dirichlet else ''
        dirichlet_per_adata = '-dirichlet' if use_dirichlet_per_adata else ''

        zi = '-zi exact' if zero_inflation else ''
        zi_per_adata = '-zi exact' if zero_inflation_per_adata else ''

        def run_sure(ad, i):
            X = get_data(ad, layer=layer)
            if batch_key is not None:
                U = batch_encoding(ad, batch_key=batch_key)
            else:
                U = pd.DataFrame(np.zeros((X.shape[0])), columns=['batch'])

            temp_count_file = os.path.join(temp_dir, f'temp_counts_{i}.txt.gz')
            temp_uwv_file = os.path.join(temp_dir, f'temp_uwv_{i}.txt.gz')
            temp_model_file = os.path.join(temp_dir, f'temp_{i}.pth')
            temp_log_file = os.path.join(temp_dir, f'temp_log_{i}.txt.gz')

            dt.Frame(X.round()).to_csv(temp_count_file)
            dt.Frame(U).to_csv(temp_uwv_file)
            
            codebook_size_per_adata_ = np.int32(X.shape[0] / min_gamma)
            codebook_size_per_adata_ = codebook_size_per_adata_ if codebook_size_per_adata > codebook_size_per_adata_ else codebook_size_per_adata
            
            mute_cmd = ''
            if mute:
                mute_cmd = f'2>&1 | gzip > {temp_log_file}'
            
            cmd = f'CUDA_VISIBLE_DEVICES={cuda_id}  SURE --data-file "{temp_count_file}" \
                        --undesired-factor-file "{temp_uwv_file}" \
                        --seed 0 \
                        --cuda {jit} \
                        -lr {learning_rate} \
                        -n {n_epochs} \
                        -bs {batch_size_per_adata} \
                        -cs {codebook_size_per_adata_} \
                        -likeli {likelihood_per_adata} {latent_dist_param} {dirichlet_per_adata} {zi_per_adata} \
                        --save-model "{temp_model_file}" {mute_cmd}'
            subprocess.call(f'{cmd}', shell=True)
            return {i:temp_model_file}
            
        with ThreadPoolExecutor(max_workers=n_workers) as executor:
            #models_file_list = list(tqdm(executor.map(run_sure, adata_list, np.arange(len(adata_list))), total=len(adata_list), desc="Metacell calling"))
            futures = [executor.submit(run_sure, ad, i) for i,ad in enumerate(adata_list)]
            results_ = {}
            for f in tqdm(as_completed(futures), total=len(adata_list), unit='adata', desc="Metacell calling"):
                results_.update(f.result())
            models_file_list = [results_[k] for k in sorted(results_)]
            
        # get the distribution structure for each adata
        for i in np.arange(n_adatas):
            '''
            X = get_data(adata_list[i], layer=layer)
            if batch_key is not None:
                U = batch_encoding(adata_list[i], batch_key=batch_key)
            else:
                U = pd.DataFrame(np.zeros((X.shape[0])), columns=['batch'])

            temp_count_file = os.path.join(temp_dir, f'temp_counts_{i}.txt.gz')
            temp_uwv_file = os.path.join(temp_dir, f'temp_uwv_{i}.txt.gz')
            temp_model_file = os.path.join(temp_dir, f'temp_{i}.pth')

            dt.Frame(X.round()).to_csv(temp_count_file)
            dt.Frame(U).to_csv(temp_uwv_file)
            
            codebook_size_per_adata_ = np.int32(X.shape[0] / min_gamma)
            codebook_size_per_adata_ = codebook_size_per_adata_ if codebook_size_per_adata > codebook_size_per_adata_ else codebook_size_per_adata
            
            print(f'Adata {i+1} / {n_adatas}: Compute distribution-preserved sketching with {codebook_size_per_adata_} metacells from {X.shape[0]} cells')

            cmd = f'CUDA_VISIBLE_DEVICES={cuda_id}  SURE --data-file "{temp_count_file}" \
                        --undesired-factor-file "{temp_uwv_file}" \
                        --seed 0 \
                        --cuda {jit} \
                        -lr {learning_rate} \
                        -n {n_epochs} \
                        -bs {batch_size_per_adata} \
                        -cs {codebook_size_per_adata_} \
                        -likeli {likelihood_per_adata} {latent_dist_param} {dirichlet_per_adata} {zi_per_adata} \
                        --save-model "{temp_model_file}" '
            pretty_print(cmd)
            subprocess.call(f'{cmd}', shell=True)
            model_i = SURE.load_model(temp_model_file)
            '''
            model_i = SURE.load_model(models_file_list[i])
            models_list.append(model_i)

        # generate samples from the learned distributions for assembly
        if n_adatas > 1:
            '''
            n_samples = n_samples_per_adata * n_adatas
            n_samples = n_samples if n_samples<total_samples else total_samples
            adata_freq = adata_size_list / np.sum(adata_size_list)
            #n_samples_list = generate_equal_list(n_samples, n_adatas)
            n_samples_list = n_samples * adata_freq
            n_samples_list = [np.int32(x) for x in n_samples_list]
            
            for i in np.arange(n_adatas):
                n_samples_list[i] = n_samples_list[i] if n_samples_list[i] < adata_size_list[i] else adata_size_list[i]
                n_samples_list[i] = n_samples_list[i] if n_samples_list[i] > min_gamma * models_list[i].code_size else min_gamma * models_list[i].code_size
            '''

            adatas_to_assembly=[]
            with tqdm(total=n_adatas, desc='Sampling', unit='adata') as pbar:
                for i in np.arange(n_adatas):
                #    print(f'Generate {n_samples_list[i]} samples from sketched atlas {i+1} / {n_adatas} ')
            
                    model_i = models_list[i]
                    if sketch_func=='sum':
                        xs_i_ = get_data(adata_list[i], layer=layer).values
                        ns = models_list[i].hard_assignments(xs_i_)
                        xs_i = codebook_aggregate(ns, xs_i_)
                    elif sketch_func=='mean':
                        xs_i_ = get_data(adata_list[i], layer=layer).values
                        ns = models_list[i].hard_assignments(xs_i_)
                        xs_i = codebook_summarize(ns, xs_i_)
                    elif sketch_func=='simulate':
                        zs_i,_ = codebook_generate(model_i, min_gamma * models_list[i].code_size)
                        xs_i = model_i.generate_count_data(zs_i)
                    elif sketch_func=='sample':
                        data_i = get_subdata(adata_list[i], hvgs=hvgs, layer=layer).values
                        xs_i,_,_ = codebook_sketch(model_i, data_i, min_gamma * models_list[i].code_size, even_sample=True)
                    elif sketch_func=='bootstrap_sample':
                        data_i = get_subdata(adata_list[i], hvgs=hvgs, layer=layer).values
                        xs_i,_,_ = codebook_bootstrap_sketch(model_i, data_i, min_gamma * models_list[i].code_size, n_bootstrap_neighbors, even_sample=True)
                    '''
                    if summarize:
                        xs_i_ = get_data(adata_list[i], layer=layer).values
                        ns = models_list[i].hard_assignments(xs_i_)
                        #xs_i = codebook_summarize(ns, xs_i_)
                        xs_i = codebook_aggregate(ns, xs_i_)
                    elif sketching:
                        data_i = get_subdata(adata_list[i], hvgs=hvgs, layer=layer).values
                        if not bootstrap_sketch:
                            xs_i,_,_ = codebook_sketch(model_i, data_i, n_samples_list[i], even_sample=even_sketch)
                        else:
                            xs_i,_,_ = codebook_bootstrap_sketch(model_i, data_i, n_samples_list[i], n_sketch_neighbors, even_sample=even_sketch)
                    else:
                        zs_i,_ = codebook_generate(model_i, n_samples_list[i])
                        xs_i = model_i.generate_count_data(zs_i)
                    '''

                    adata_i = sc.AnnData(xs_i)
                    adata_i.obs['adata_id'] = i

                    adatas_to_assembly.append(adata_i)
                    pbar.update(1)

            # assembly
            adata_to_assembly = sc.concat(adatas_to_assembly)
            temp_count_file = os.path.join(temp_dir, f'temp_counts.txt.gz')
            temp_uwv_file = os.path.join(temp_dir, f'temp_uwv.txt.gz')
            temp_model_file = os.path.join(temp_dir, f'temp_model.pth')

            X = get_data(adata_to_assembly, layer='X')
            U = batch_encoding(adata_to_assembly, batch_key='adata_id')
            dt.Frame(X.round()).to_csv(temp_count_file)
            dt.Frame(U).to_csv(temp_uwv_file)
            
            codebook_size_ = np.int32(X.shape[0] / min_gamma)
            codebook_size_ = codebook_size_ if codebook_size > codebook_size_ else codebook_size

            print(f'Create distribution-preserved atlas with {codebook_size_} metacells from {X.shape[0]} samples')
            cmd = f'CUDA_VISIBLE_DEVICES={cuda_id}  SURE --data-file "{temp_count_file}" \
                            --undesired-factor-file "{temp_uwv_file}" \
                            --seed 0 \
                            --cuda {jit}  \
                            -lr {learning_rate} \
                            -n {n_epochs} \
                            -bs {batch_size} \
                            -cs {codebook_size_} \
                            -likeli {likelihood} {latent_dist_param} {dirichlet} {zi} \
                            --save-model "{temp_model_file}" '
            pretty_print(cmd)
            subprocess.call(f'{cmd}', shell=True)
            model = SURE.load_model(temp_model_file)
        else:
            model = models_list[0]
    finally:
        shutil.rmtree('./SURE_temp_dir', ignore_errors=True)

    return model, models_list, hvgs

def preprocess(adata, layer='counts'):
    adata.X = get_data(adata, layer).values.copy()
    sc.pp.normalize_total(adata, target_sum=1e4)
    sc.pp.log1p(adata)
    return adata

def highly_variable_genes(adata, n_top_genes, hvg_method):
    sc.pp.highly_variable_genes(adata, n_top_genes=n_top_genes, flavor=hvg_method)
    hvgs = adata.var_names[adata.var.highly_variable]
    return hvgs

def highly_variable_genes_for_adatas__(adata_list, n_top_genes, hvg_method):
    n_adatas = len(adata_list)

    for i in np.arange(n_adatas):
        adata_list[i].obs['adata_id'] = i 

    adata = sc.concat(adata_list)
    sc.pp.highly_variable_genes(adata, n_top_genes=n_top_genes, flavor=hvg_method, batch_key='adata_id')
    hvgs = adata.var_names[adata.var.highly_variable].tolist()
    return hvgs

def highly_variable_genes_for_adatas(adata_list, n_top_genes, hvg_method):
    n_adatas = len(adata_list)

    dfs = []
    for i in np.arange(n_adatas):
        #print(f'Adata {i+1} / {n_adatas}: Find {n_top_genes} HVGs')
        adata = adata_list[i]
        sc.pp.highly_variable_genes(adata, n_top_genes=n_top_genes, flavor=hvg_method)
        hvgs_i = adata.var_names[adata.var.highly_variable].tolist()
        df_i = adata.var.loc[hvgs_i,:]
        df_i.reset_index(drop=False, inplace=True, names=["gene"])
        dfs.append(df_i)
        
    df = pd.concat(dfs, axis=0)
    df["highly_variable"] = df["highly_variable"].astype(int)
    df = df.groupby("gene", observed=True).agg(
        dict(
            means="mean",
            dispersions="mean",
            dispersions_norm="mean",
            highly_variable="sum",
        )
    )
    df["highly_variable_nbatches"] = df["highly_variable"]
    df["dispersions_norm"] = df["dispersions_norm"].fillna(0)

    df.sort_values(
            ["highly_variable_nbatches", "dispersions_norm"],
            ascending=False,
            na_position="last",
            inplace=True,
        )
    df["highly_variable"] = np.arange(df.shape[0]) < n_top_genes

    #df["highly_variable"] = (df["means"]>0.0125) & (df["means"]<3) & (df["dispersions_norm"]>0.5) & ((df["dispersions_norm"]<np.inf))

    df = df[df['highly_variable']]
    hvgs = df.index.tolist()
    #hvgs = hvgs[:n_top_genes]
    return hvgs

def highly_variable_genes_for_adatas_(adata_list, n_top_genes, hvg_method):
    n_adatas = len(adata_list)
    hvgs,hvgs_ = None,None

    for i in np.arange(n_adatas):
        print(f'Adata {i+1} / {n_adatas}: Find {n_top_genes} HVGs')
        adata = adata_list[i]
        sc.pp.highly_variable_genes(adata, n_top_genes=n_top_genes, flavor=hvg_method)
        if hvgs_:
            hvgs_ &= set(adata.var_names[adata.var.highly_variable].tolist())
        else:
            hvgs_ = set(adata.var_names[adata.var.highly_variable].tolist())
        
    if len(hvgs_) == n_top_genes:
        hvgs = list(hvgs_)
    else:
        hvgs = list(hvgs_)

        n_average = (n_top_genes - len(hvgs)) // n_adatas
        for i in np.arange(n_adatas):
            if i==n_adatas-1:
                n_average = n_top_genes - len(hvgs)

            adata = adata_list[i]
            hvgs_i = list(set(adata.var_names[adata.var.highly_variable].tolist()) - set(hvgs))
            df_i = adata.var.loc[hvgs_i,:].copy()
            #df_i.sort_values(by='highly_variable_rank', inplace=True)
            df_i.sort_values(by='dispersions_norm', ascending=False, inplace=True)
            hvgs_i = df_i.index.tolist()
            hvgs.extend(hvgs_i[:n_average])

    return hvgs

def batch_encoding_bk(adata, batch_key):
    sklearn_version = pkg_resources.get_distribution("scikit-learn").version
    if pkg_resources.parse_version(sklearn_version) < pkg_resources.parse_version("1.2"):
        enc = OneHotEncoder(sparse=False).fit(adata.obs[batch_key].to_numpy().reshape(-1,1))
    else:
        enc = OneHotEncoder(sparse_output=False).fit(adata.obs[batch_key].to_numpy().reshape(-1,1))
    return pd.DataFrame(enc.transform(adata.obs[batch_key].to_numpy().reshape(-1,1)), columns=enc.categories_[0])

def batch_encoding(adata, batch_key):
    enc = LabelBinarizer().fit(adata.obs[batch_key].to_numpy())
    return pd.DataFrame(enc.transform(adata.obs[batch_key].to_numpy()), columns=enc.classes_)
    
def get_data(adata, layer='counts'):
    if layer.lower()!='x':
        data = adata.layers[layer]
    else:
        data = adata.X

    if sp.sparse.issparse(data):
        data = data.toarray()

    data[np.isnan(data)] = 0

    return pd.DataFrame(data.astype('float32'), columns=adata.var_names) 

def get_subdata(adata, hvgs, layer='counts'):
    #mask = [hvg in X for hvg in hvgs]
    hvgs_df = pd.DataFrame({'hvgs':hvgs})
    mask = hvgs_df['hvgs'].isin(adata.var_names.tolist())
    if all(mask):
        X = get_data(adata[:,hvgs], layer)
        return X[hvgs]
    else:
        #X2 = np.zeros((X.shape[0], len(hvgs)))
        #X2 = pd.DataFrame(X2, columns=hvgs)

        #columns = [c for c in X.columns.tolist() if c in hvgs]
        #X2[columns] = X[columns].copy()

        # inspired by SCimilarity
        shell = sc.AnnData(
            X=csr_matrix((0, len(hvgs))),
            var=pd.DataFrame(index=hvgs),
        )
        if layer.lower() != 'x':
            shell.layers[layer] = shell.X.copy()
        shell = sc.concat(
            (shell, adata[:, adata.var.index.isin(shell.var.index)]), join="outer"
        )
        X2 = get_data(shell, layer)
        return X2[hvgs]
    
def get_uns(adata, key):
    data = None 

    if key in adata.uns:
        data = adata.uns[key]
        columns = adata.uns[f'{key}_columns']
        if sp.sparse.issparse(data):
            data = data.toarray()
        data = pd.DataFrame(data.astype('float32'), 
                            columns=columns) 
        
    return data
    
def split_by(adata, by:str, copy:bool=False):
    adata_list = []
    for id in adata.obs[by].unique():
        if copy:
            adata_list.append(adata[adata.obs[by].isin([id])].copy())
        else:
            adata_list.append(adata[adata.obs[by].isin([id])])
    return adata_list

def split_batch_by_bk(adata, by, batch_size=30000, copy=False):
    df = adata.obs[by].value_counts().reset_index()
    df.columns = [by,'Value']

    n = int(np.round(adata.shape[0] / batch_size))
    n = n if n > 0 else 1

    adata_list = []
    parts = find_partitions_greedy(df['Value'].tolist(), n)
    for _,by_ids in parts:
        ids = df.iloc[by_ids,:][by].tolist()
        if copy:
            adata_list.append(adata[adata.obs[by].isin(ids)].copy())
        else:
            adata_list.append(adata[adata.obs[by].isin(ids)])

    return adata_list

def split_batch_by(adata, 
                   by:str, 
                   batch_size: int = 30000, 
                   copy: bool = False):
    groups = adata.obs[by].unique()
    adata_list = []
    for grp in groups:
        adata_list.extend(split_batch(adata[adata.obs[by]==grp], batch_size=batch_size, copy=copy))

    return adata_list

def split_batch(adata, batch_size: int=30000, copy: bool=False):
    n = int(np.round(adata.shape[0] / batch_size))
    n = n if n > 0 else 1
    
    cells = adata.obs_names.tolist()
    chunks = np.array_split(cells, n)
    
    adata_list = []
    for chunk in chunks:
        chunk = list(chunk)
        
        if copy:
            adata_list.append(adata[chunk].copy())
        else:
            adata_list.append(adata[chunk])

    return adata_list


def generate_equal_list(total, n):
    base_value = total // n
    remainder = total - (base_value * n)
    result = [base_value] * (n - 1) + [base_value + remainder]
    return result