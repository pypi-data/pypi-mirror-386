# %%
import numpy as np
import time
import pandas as pd
import sys
import os
import gc
import bisect
from scipy.sparse import csr_matrix
from ast import literal_eval

from concurrent.futures import ProcessPoolExecutor
from functools import partial

import psutil
from contextlib import contextmanager

try:
    # prefer direct function import for simple call style
    from pympler.asizeof import asizeof  # type: ignore
except Exception:  # pragma: no cover - optional dependency

    def asizeof(_obj):  # fallback stub
        return -1


sys.path.append("./")
# from VariantsProportionCoOcc import VariantsProportionCoOcc
from varaps2.util import VariantsProportionCoOcc
from varaps2.util import VariantsProportionFreyjaSparse
from varaps2.util import VariantsProportionFreyja1Sparse
from varaps2.util import VariantsProportionLCS
import warnings

warnings.filterwarnings("ignore")


# %%
def _proc_mem_mb():
    return psutil.Process(os.getpid()).memory_info().rss / 1024 / 1024


@contextmanager
def timer(label: str):
    # debug timer disabled
    yield


def print_mem(label: str, **objs):
    # debug memory prints disabled
    return


def get_files(fpath):
    # checks if path is a file
    isFile = os.path.isfile(fpath)

    # checks if path is a directory
    isDirectory = os.path.isdir(fpath)

    files_to_analyse = []
    if isFile and fpath.endswith(".csv"):
        files_to_analyse.append(fpath)
    elif isDirectory:
        for file in os.listdir(fpath):
            if file.startswith("Xsparse_") and file.endswith(".csv"):
                files_to_analyse.append(os.path.join(fpath, file))
                # files_to_analyse.append(fpath + "/" + file)
    else:
        print("The path is not a file or a directory")

    if len(files_to_analyse) == 0:
        print("No files to analyse")
        # return
    # print("Files to analyse: ", *files_to_analyse, sep="\n")
    files_to_analyse.sort()

    files_to_analyse = np.array(files_to_analyse)
    # reverse the order of the files
    files_to_analyse = files_to_analyse[::-1]
    return files_to_analyse


# %%
def get_sample_bootstrap_weight(weights):
    positions = np.random.choice(
        np.arange(len(weights)),
        size=np.sum(weights),
        replace=True,
        p=weights / np.sum(weights),
    )
    return np.bincount(positions, minlength=len(weights))


def extract_positions(mut_str):
    """
    returns the position (extract digits from a string) in a mutation string
    """
    return int("".join([i for i in mut_str if i.isdigit()]))


# PATH_X_MATRIXs = "../../EauDeParis/X_sparse"
# PATH_RESULT = "../../EauDeParis/X_sparse_result"
# PATH_M_MATRIX = "../../Arnaud/proposed_lineages_list4SUMMIT.stringent.freyja0001.csv"
# NbBootstraps = 10
# alphaInit = 0.01
# freezeAlpha = False
# files_to_analyze = get_files(PATH_X_MATRIXs)


def parse_tuple(s):
    try:
        return literal_eval(s)
    except:
        return s


def process_single_index(x, all_positions, muts_to_analyse):
    return min(len(muts_to_analyse) - 1, bisect.bisect_left(all_positions, x + 1))


def process_tuple(t, all_positions, muts_to_analyse):
    return [process_single_index(x, all_positions, muts_to_analyse) for x in t]


def process_single_end_index(x, all_positions):
    return bisect.bisect_right(all_positions, x + 1)


def process_end_tuple(t, all_positions):
    return [process_single_end_index(x, all_positions) for x in t]


def create_X_matrix(starts_idx_new, ends_idx_new, muts_data_new, nb_mutations):

    X = np.full((len(starts_idx_new), nb_mutations), False, dtype=bool)
    for i in range(len(muts_data_new)):
        for mut in muts_data_new[i]:
            X[i, list(mut)] = True
    return X


def create_X_mask_matrix(starts_idx_new, ends_idx_new, muts_data_new, nb_mutations):

    t0 = time.time()
    mask_pair_end = [len(muts_data_new[i]) >= 2 for i in range(len(muts_data_new))]
    first_starts_ids = [starts_idx_new[i][0] for i in range(len(starts_idx_new))]
    first_starts_ids = np.array(first_starts_ids)
    first_ends_ids = [ends_idx_new[i][0] for i in range(len(ends_idx_new))]
    first_ends_ids = np.array(first_ends_ids)
    second_starts_ids = [starts_idx_new[i][1] if mask_pair_end[i] else 0 for i in range(len(starts_idx_new))]
    second_starts_ids = np.array(second_starts_ids)
    second_ends_ids = [ends_idx_new[i][1] if mask_pair_end[i] else 0 for i in range(len(ends_idx_new))]
    second_ends_ids = np.array(second_ends_ids)
    X_first = np.full((len(starts_idx_new), nb_mutations), False, dtype=bool)
    X_second = np.full((len(starts_idx_new), nb_mutations), False, dtype=bool)
    cols = np.arange(X_first.shape[1])
    mask_first = (cols >= first_starts_ids[:, None]) & (cols < first_ends_ids[:, None])
    mask_second = (cols >= second_starts_ids[:, None]) & (cols < second_ends_ids[:, None])
    X_first[mask_first] = True
    X_second[mask_second] = True
    # sum X_first and X_second by or operation
    X_first |= X_second
    del X_second

    return X_first


def analyse_file(file, PATH_RESULT, PATH_M_MATRIX, NbBootstraps, alphaInit, optibyAlpha, decov_method=1):
    M = pd.read_csv(PATH_M_MATRIX, index_col=0)

    variants = M.index.values
    # M = pd.read_csv('data/MmatrixFreyjaOldDelsFULL.csv', index_col=0)
    # M = M.T
    # Read only necessary columns; avoid eager object conversion
    muts_data_df = pd.read_csv(
        file,
        sep=";",
        usecols=["muts", "startIdx_0Based", "endIdx_0Based"],
    )
    Weights_df = pd.read_csv(
        file.replace("Xsparse_", "Wsparse_"),
        usecols=["Counts"],
    )
    mut_idx_df = pd.read_csv(
        file.replace("Xsparse_", "mutations_index_"),
        usecols=["Mutations"],
    )

    # return

    Weights = Weights_df.Counts.values.astype(np.int32, copy=False)
    muts_idx = mut_idx_df.Mutations.values

    # print('Number of mutations in M matrix: ', M.shape[1])
    # print('Number of mutations in bam: ', len(muts_idx))
    # Build sorted mutation order by genomic position (no string use in remap loop)
    muts_to_analyse = set(M.columns)
    muts_to_analyse = {mut: extract_positions(mut) for mut in muts_to_analyse}
    muts_to_analyse = {k: v for k, v in sorted(muts_to_analyse.items(), key=lambda item: item[1])}
    all_positions = list(muts_to_analyse.values())

    # Update start and end index to be relative to mutations, not absolute to the reference
    # Lazily parse string tuples and convert to compact int32 Nx2 arrays
    starts_mapped_obj = muts_data_df["startIdx_0Based"].apply(lambda s: process_tuple([] if pd.isna(s) else parse_tuple(s), all_positions, muts_to_analyse)).to_numpy()
    ends_mapped_obj = muts_data_df["endIdx_0Based"].apply(lambda s: process_end_tuple([] if pd.isna(s) else parse_tuple(s), all_positions)).to_numpy()

    n_reads = len(starts_mapped_obj)
    starts_idx_new = np.zeros((n_reads, 2), dtype=np.int32)
    ends_idx_new = np.zeros((n_reads, 2), dtype=np.int32)
    for i in range(n_reads):
        sm = starts_mapped_obj[i]
        em = ends_mapped_obj[i]
        if len(sm) >= 1:
            starts_idx_new[i, 0] = sm[0]
        if len(sm) >= 2:
            starts_idx_new[i, 1] = sm[1]
        if len(em) >= 1:
            ends_idx_new[i, 0] = em[0]
        if len(em) >= 2:
            ends_idx_new[i, 1] = em[1]
    del starts_mapped_obj
    del ends_mapped_obj

    # Precompute integer mapping: old mutation ID (from bam) -> new index in M (or -1 if absent)
    mut_str_to_Midx = {mut: idx for idx, mut in enumerate(muts_to_analyse.keys())}
    id_map = np.full(len(muts_idx), -1, dtype=np.int32)
    for old_id, mut_str in enumerate(muts_idx):
        new_id = mut_str_to_Midx.get(mut_str, -1)
        id_map[old_id] = new_id

    # Build final structure directly from `muts` strings to avoid large intermediates
    muts_data_new_list = []
    for s in muts_data_df["muts"].values:
        raw_mut = [] if pd.isna(s) else parse_tuple(s)
        res_item = []
        for x in raw_mut:
            if x is None or (isinstance(x, float) and pd.isna(x)):
                mut_set = set()
            else:
                mut_set = set(x)
            remapped = {int(new_id) for mut in mut_set if (new_id := id_map[mut]) != -1}

            res_item.append(remapped)
        muts_data_new_list.append(res_item)
    muts_data_new = np.array(muts_data_new_list, dtype=object)

    # Free large intermediates ASAP
    del muts_data_df
    del mut_idx_df
    del muts_idx
    del id_map
    del mut_str_to_Midx
    gc.collect()

    M = M[list(muts_to_analyse.keys())].to_numpy().T
    # Now safe to drop mapping helpers derived from M's columns
    del muts_to_analyse
    del all_positions
    nM, nV = M.shape

    # generate X matrix
    # print memory usage before and after creating X matrix
    # print(f"Memory usage before creating X matrix: {_proc_mem_mb():.2f} MB")
    X = create_X_matrix(starts_idx_new, ends_idx_new, muts_data_new, nM)
    if decov_method != 1:
        start_time = time.time()
        X = csr_matrix(X)
        print(f"Time taken to convert X to csr_matrix: {time.time() - start_time:.4f} seconds")
    X_mask = create_X_mask_matrix(starts_idx_new, ends_idx_new, muts_data_new, nM)
    print(f"X_mask.shape: {X_mask.shape}")
    if decov_method != 1:
        start_time = time.time()
        X_mask = csr_matrix(X_mask)
        print(f"Time taken to convert X_mask to csr_matrix: {time.time() - start_time:.4f} seconds")
    # print(f"Memory usage after creating X matrix: {_proc_mem_mb():.2f} MB")
    # # calculat sum of each row of X_mask
    # X_mask_sum = X_mask.sum(axis=1)
    # # export X_mask_sum to csv each row in a new line
    # np.savetxt(os.path.join(PATH_RESULT, "X_mask_sum.csv"), X_mask_sum, delimiter="\n")
    # print(f"X_mask_sum.shape: {X_mask_sum.shape}")
    # print(f"path: {os.path.join(PATH_RESULT, 'X_mask_sum.csv')}")
    resCooc = np.zeros((NbBootstraps, 6 + nV), dtype=np.float32)

    top5_list = []
    start_time = time.time()
    pair_end_lens = [len(starts_idx_new[i]) for i in range(len(starts_idx_new))]
    nb_reads = np.array(pair_end_lens, dtype=np.int32).dot(Weights)
    print("Number of reads: ", nb_reads)
    # Decov method
    if decov_method == 1:
        decov_func = VariantsProportionCoOcc.VariantsProportionCoOcc
        decov_name = "CoOcc"
    elif decov_method == 2:
        decov_func = VariantsProportionLCS.VariantsProportionLCS
        decov_name = "LCS"
    elif decov_method == 4 or decov_method == 3:
        decov_func = VariantsProportionFreyja1Sparse.VariantsProportionFreyja1Sparse
        decov_name = "Freyja1Sparse"

    for i in range(NbBootstraps):
        print("Bootstrap: ", i + 1)
        weight = get_sample_bootstrap_weight(Weights)  # Do the bootstrap on the weights not on the X matrix to reduce the memory usage
        # print("starts_idx_new: ", muts_data_new[10])
        if decov_method == 1:
            res_decov = decov_func(
                starts_idx_new,
                ends_idx_new,
                muts_data_new,
                M,
                X_mask=X_mask,
                X=X,
                alphaInit=alphaInit,
                readsCount=weight,
            )
        else:
            res_decov = decov_func(
                X_mask,
                X,
                M,
                alphaInit=alphaInit,
                readsCount=weight,
            )
        res_decov()
        res_decov.fit(freezeAlpha=not optibyAlpha)
        # if np.abs(pi0 - pi000)<0.001:
        result = res_decov.params
        if decov_method == 3 or decov_method == 4:
            result = res_decov.solution
        # order result idx by decreasing order
        idxs = np.argsort(result)[::-1]

        # save result
        # get top 5 name variants with highest proportion of co-occurrence with their proportion on str

        top5 = [variants[i] + ": " + str(result[i]) + "|" for i in idxs[:5]]
        print("Top: ", top5[0])
        print(top5[1])
        # convert list to string
        top5 = "".join(top5)
        top5_list.append(top5[:-1])
        resCooc[i, :nV] = result
        resCooc[i, nV] = res_decov.alpha
        resCooc[i, nV + 1] = res_decov.nbIter_alpha_fixed
        resCooc[i, nV + 2] = res_decov.time_alpha_fixed
        resCooc[i, nV + 3] = res_decov.nbIter_alpha
        resCooc[i, nV + 4] = res_decov.time_alpha
        resCooc[i, nV + 5] = res_decov.time_used
        # print(top5)

    # save result df
    resCooc_df = pd.DataFrame(
        resCooc,
        columns=list(variants)
        + [
            "alpha",
            "nbIter_alpha_fixed",
            "time_alpha_fixed",
            "nbIter_alpha",
            "time_alpha",
            "time_used",
        ],
    )
    resCooc_df["top5"] = top5_list
    resCooc_df["file"] = file.replace("Xsparse_", "").split("/")[-1]
    # make file first column and top5 second column
    cols = resCooc_df.columns.tolist()
    cols = cols[-2:] + cols[:-2]
    resCooc_df = resCooc_df[cols]
    resCooc_df["nbReads"] = np.sum(Weights)
    resCooc_df["nbMutations"] = int(nM)

    # convert to int
    resCooc_df["nbReads"] = resCooc_df["nbReads"].astype(int)
    resCooc_df["nbMutations"] = resCooc_df["nbMutations"].astype(int)
    resCooc_df["nbIter_alpha_fixed"] = resCooc_df["nbIter_alpha_fixed"].astype(int)
    resCooc_df["nbIter_alpha"] = resCooc_df["nbIter_alpha"].astype(int)
    # save result on csv
    # creat result folder if it does not exist
    out_dir = os.path.join(PATH_RESULT, decov_name)
    if not os.path.exists(out_dir):
        abs_path = os.path.abspath(out_dir)
        print("creating directory: ", abs_path)
        os.makedirs(abs_path, exist_ok=True)
    save_path = os.path.join(out_dir, file.replace("Xsparse_", "").split("/")[-1])
    print("saving :", save_path)
    resCooc_df.to_csv(save_path, index=False)


def analyze_file_mode2(path_X, path_M, path_result, nb_bootstrap, alpha_init, optibyAlpha, decov_method=1, max_workers_=4):
    PATH_X_MATRIXs = path_X
    PATH_RESULT = path_result
    PATH_M_MATRIX = path_M
    NbBootstraps = nb_bootstrap
    alphaInit = alpha_init
    optibyAlpha = optibyAlpha
    files_to_analyze = get_files(PATH_X_MATRIXs)
    max_workers = min(max_workers_, len(files_to_analyze))
    # analyse_file(files_to_analyze[0], PATH_RESULT=PATH_RESULT, PATH_M_MATRIX=PATH_M_MATRIX, NbBootstraps=NbBootstraps, alphaInit=alphaInit, optibyAlpha=optibyAlpha, decov_method=decov_method)

    func = partial(analyse_file, PATH_RESULT=PATH_RESULT, PATH_M_MATRIX=PATH_M_MATRIX, NbBootstraps=NbBootstraps, alphaInit=alphaInit, optibyAlpha=optibyAlpha, decov_method=decov_method)
    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        # Force iteration over results so that worker exceptions are propagated
        list(executor.map(func, files_to_analyze))


# %%
