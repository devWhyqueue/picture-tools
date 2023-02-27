import os
import glob
from PIL import Image
import imagehash
import argparse
from tqdm import tqdm
import multiprocessing
from pathlib import Path
from pillow_heif import register_heif_opener

register_heif_opener()


def hash_images(dir):
    file_paths = []
    hashes = []
    all_files = list(Path(dir).rglob('*'))
    for file in tqdm(all_files, total=len(all_files), desc=f'Hashing {dir}'):
        if file.suffix.lower() in ('.jpg', '.jpeg', '.png', '.gif', ".heic"):
            file_paths.append(file)
            hash = imagehash.phash(Image.open(file))
            hashes.append(hash)
    print(hashes[0])
    return file_paths, hashes


def compare_images(hashes_a, paths_a, hashes_b, paths_b, cutoff, delete):
    similar = set()
    for idx_b, hash_b in enumerate(tqdm(hashes_b, total=len(hashes_b), desc='Comparing')):
        for idx_a, hash_a in enumerate(hashes_a):
            if paths_a[idx_a] != paths_b[idx_b] and hash_b - hash_a < cutoff:
                os.remove(paths_b[idx_b]) if delete else None
                similar.add(frozenset([paths_a[idx_a], paths_b[idx_b]]))
    return similar


def delete_similar_images(dir_a, dir_b, cutoff, delete):
    images_a, images_a_hashes = hash_images(dir_a)
    images_b, images_b_hashes = (images_a, images_a_hashes) if dir_a == dir_b else hash_images(dir_b)
    similar = compare_images(images_a_hashes, images_a, images_b_hashes, images_b, cutoff, delete)
    similar = [list(pair) for pair in similar]
    [print(f'Similar("{pair[0]}", "{pair[1]}")') for pair in similar]
    print(f"\n{len(similar)} similar images in {dir_b} found.")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Find/delete similar images in dir_b which exist in dir_a')
    parser.add_argument('dir_a', type=str, help='Directory A')
    parser.add_argument('dir_b', type=str, help='Directory B')
    parser.add_argument('--cutoff', type=int, default=1, help='Cutoff')
    parser.add_argument('--delete', action='store_true')
    args = parser.parse_args()
    delete_similar_images(args.dir_a, args.dir_b, args.cutoff, args.delete)
