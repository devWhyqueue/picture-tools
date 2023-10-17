import argparse
import copy
import multiprocessing
import os
import pickle
from pathlib import Path
from collections import defaultdict

import imagehash
from PIL import Image, ImageFile, UnidentifiedImageError
from pillow_heif import register_heif_opener
from tqdm import tqdm

ImageFile.LOAD_TRUNCATED_IMAGES = True
register_heif_opener()


class PhotoHash:
    def __init__(self, file_path: Path, img_hash: imagehash.ImageHash):
        self.file_path = file_path
        self.hash = img_hash

    @staticmethod
    def group(items):
        groups = defaultdict(list)
        for item in tqdm(items, total=len(items), desc='Grouping'):
            groups[hash(item)].append(item)
        return list(groups.values())

    def __eq__(self, other):
        if isinstance(other, PhotoHash):
            return self.hash == other.hash
        return False

    def __hash__(self):
        return hash(self.hash)


def hash_photo(file):
    try:
        if file.suffix.lower() in ('.jpg', '.jpeg', '.png', '.gif', '.heic'):
            img_hash = imagehash.phash(Image.open(file))
            return PhotoHash(file, img_hash)
    except (UnidentifiedImageError, PermissionError):
        return None


def hash_photos(folder):
    hash_file = f"{folder}/.photo_hashes.pkl"
    existing_hashes = pickle.load(open(hash_file, "rb")) if os.path.exists(hash_file) else {}

    all_files = list(Path(folder).rglob('*'))
    new_files = [f for f in all_files if str(f) not in existing_hashes]

    with multiprocessing.Pool(multiprocessing.cpu_count() - 1) as pool:
        new_hashes = list(
            filter(None, tqdm(pool.imap(hash_photo, new_files), total=len(new_files), desc=f'Hashing {folder}')))

    existing_hashes.update({str(ph.file_path): ph.hash for ph in new_hashes})
    deleted_files = set(existing_hashes) - set(map(str, all_files))

    for f in deleted_files:
        del existing_hashes[f]

    pickle.dump(existing_hashes, open(hash_file, "wb"))
    return [PhotoHash(file_path, img_hash) for file_path, img_hash in existing_hashes.items()]


def handle_file_removal_and_append(hash_obj, delete, similar_list, file_paths_set):
    if delete:
        os.remove(hash_obj.file_path)
    similar_list.append(hash_obj)
    file_paths_set.add(hash_obj.file_path)


def process_hashes(hash_a, hash_comp, delete, similar, file_paths_in_similar):
    if hash_comp.file_path == hash_a.file_path:
        return

    handle_file_removal_and_append(hash_a, delete, similar, file_paths_in_similar)

    if hash_comp.file_path not in file_paths_in_similar:
        handle_file_removal_and_append(hash_comp, delete, similar, file_paths_in_similar)


def find_similar_photos(photo_hashes_a, photo_hashes_comp, delete):
    if not photo_hashes_comp:
        similar = PhotoHash.group(photo_hashes_a)
        if delete:
            purge_groups(similar)
        return similar

    similar = []
    file_paths_in_similar = set()

    for hash_a in tqdm(photo_hashes_a, total=len(photo_hashes_a), desc='Comparing'):
        for hash_comp in photo_hashes_comp:
            process_hashes(hash_a, hash_comp, delete, similar, file_paths_in_similar)

    return PhotoHash.group(similar)


def purge_groups(similar):
    similar = copy.deepcopy(similar)
    while any(len(group) > 1 for group in similar):
        for group in similar:
            if len(group) > 1:
                item = group.pop()
                os.remove(item.file_path)


def delete_similar_photos(dir_a, dir_comp, delete, debug):
    photo_hashes_a = hash_photos(dir_a)
    photo_hashes_comp = hash_photos(dir_comp) if dir_comp else None
    similar = find_similar_photos(photo_hashes_a, photo_hashes_comp, delete)
    group_count = 0
    if debug:
        for group in similar:
            if len(group) > 1:
                print(f'Similar({", ".join([str(item.file_path) for item in group])})')
                group_count += 1
    print(f"\nFound {group_count} similarity groups.")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Find/delete similar images in dir_b which exist in dir_a')
    parser.add_argument('dir_a', type=str, help='Directory to delete from')
    parser.add_argument('--dir_comp', type=str, help='Directory to compare to', required=False)
    parser.add_argument('--delete', action='store_true')
    parser.add_argument('--debug', action='store_true')
    args = parser.parse_args()
    delete_similar_photos(args.dir_a, args.dir_comp, args.delete, args.debug)
