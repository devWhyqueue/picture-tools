import os
from PIL import Image
import imagehash
import argparse
from tqdm import tqdm
from pillow_heif import register_heif_opener

register_heif_opener()


def compare_images(images_a, images_a_hashes, image_b, cutoff):
    hash_b = imagehash.average_hash(Image.open(image_b))
    for hash_a in images_a_hashes:
        dif = hash_b - hash_a
        if hash_b - hash_a < cutoff:
            os.remove(image_b)
            return 1
    return 0


def delete_similar_images(dir_a, dir_b, cutoff):
    # Get image file paths in dir_a
    images_a = []
    images_a_hashes = []
    for root, dirs, files in os.walk(dir_a):
        for file in tqdm(files, total=len(files), desc='Hashing dir_a'):
            if file.lower().endswith(('.jpg', '.jpeg', '.png', '.gif', ".heic")):
                images_a.append(os.path.join(root, file))
                hash = imagehash.average_hash(Image.open(images_a[-1]))
                images_a_hashes.append(hash)
    # Get image file paths in dir_b
    images_b = []
    for root, dirs, files in os.walk(dir_b):
        for file in files:
            if file.lower().endswith(('.jpg', '.jpeg', '.png', '.gif', ".heic")):
                images_b.append(os.path.join(root, file))

    # Compare images in dir_a with images in dir_b using multiprocessing
    num_deleted = 0
    for image_b in tqdm(images_b, total=len(images_b), desc='Comparing'):
        num_deleted = num_deleted + compare_images(images_a, images_a_hashes, image_b, cutoff)

    print(f"{num_deleted} images deleted.")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Delete similar images in dir_b which exist in dir_a')
    parser.add_argument('dir_a', type=str, help='Directory A')
    parser.add_argument('dir_b', type=str, help='Directory B')
    parser.add_argument('--cutoff', type=int, default=1, help='Cutoff')
    args = parser.parse_args()
    delete_similar_images(args.dir_a, args.dir_b, args.cutoff)
