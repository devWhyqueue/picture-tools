import argparse
import copy
import multiprocessing
import os
from pathlib import Path

import imagehash
from PIL import Image, ImageFile
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
        groups = {}
        for item in items:
            if item not in groups:
                groups[item] = [item]
            else:
                groups[item].append(item)
        return list(groups.values())

    def __eq__(self, other):
        if isinstance(other, PhotoHash):
            return self.hash == other.hash
        return False

    def __hash__(self):
        return hash(self.hash)


def hash_photo(file):
    if file.suffix.lower() in ('.jpg', '.jpeg', '.png', '.gif', '.heic'):
        img_hash = imagehash.phash(Image.open(file))
        return PhotoHash(file, img_hash)


def hash_photos(folder):
    with multiprocessing.Pool(multiprocessing.cpu_count() - 1) as pool:
        all_files = list(Path(folder).rglob('*'))
        photos_hashes = list(tqdm(pool.imap(hash_photo, all_files), total=len(all_files), desc=f'Hashing {folder}'))
    return [photo_hash for photo_hash in photos_hashes if photo_hash is not None]


def find_similar_photos(photo_hashes_a, photo_hashes_comp, delete):
    if not photo_hashes_comp:
        similar = PhotoHash.group(photo_hashes_a)
        purge_groups(similar) if delete else None
        return similar
    similar = []
    for idx_a, hash_a in enumerate(tqdm(photo_hashes_a, total=len(photo_hashes_a), desc='Comparing')):
        for idx_comp, hash_comp in enumerate(photo_hashes_comp):
            if hash_comp.file_path != hash_a.file_path:
                os.remove(hash_a.file_path) if delete else None
                similar.append(hash_a)
                similar.append(hash_comp) if hash_comp.file_path not in \
                                             [img_hash.file_path for img_hash in similar] else None
    return PhotoHash.group(similar)


def purge_groups(similar):
    similar = copy.deepcopy(similar)
    while any(len(group) > 1 for group in similar):
        for group in similar:
            if len(group) > 1:
                item = group.pop()
                os.remove(item.file_path)


def delete_similar_photos(dir_a, dir_comp, delete):
    photo_hashes_a = hash_photos(dir_a)
    photo_hashes_comp = hash_photos(dir_comp) if dir_comp else None
    similar = find_similar_photos(photo_hashes_a, photo_hashes_comp, delete)
    group_count = 0
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
    args = parser.parse_args()
    delete_similar_photos(args.dir_a, args.dir_comp, args.delete)
