import os
from collections import defaultdict
from pathlib import Path

from tqdm import tqdm


def remove_files_in_a_which_exist_in_b(file_hashes_folder_a, file_hashes_folder_b, dry_run=False):
    groups_folder_b = _group_by_hash(file_hashes_folder_b)
    removed = 0
    for path_a, hash_str_a in tqdm(file_hashes_folder_a.items(), total=len(file_hashes_folder_a), desc='Removing'):
        if hash_str_a in groups_folder_b:
            os.remove(path_a) if not dry_run else print(f'Would remove {path_a}.')
            removed += 1
    return removed


def remove_duplicates(file_hashes: dict[Path, str], dry_run=False):
    groups = _group_by_hash(file_hashes)
    removed = 0
    for f_hashes in tqdm(groups.values(), total=len(groups), desc='Removing'):
        if len(f_hashes) > 1:
            for f_hash in f_hashes[1:]:
                if not dry_run:
                    os.remove(f_hash[0])
                else:
                    paths = [path.resolve().as_posix() for path, _hash in f_hashes]
                    print(f'Would remove {f_hash[0].resolve().as_posix()} from group {paths}.')
                removed += 1
    return removed


def _group_by_hash(items: dict[Path, str]) -> defaultdict:
    groups = defaultdict(list)
    for path, hash_str in tqdm(items.items(), total=len(items), desc='Grouping'):
        groups[hash_str].append((path, hash_str))
    return groups
