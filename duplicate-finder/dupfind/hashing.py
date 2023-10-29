import hashlib
import os
import pickle
from multiprocessing import Pool, cpu_count
from pathlib import Path

import imagehash
from PIL import Image, UnidentifiedImageError, ImageFile
from tqdm import tqdm

if os.name == 'nt':
    import win32api, win32con

ImageFile.LOAD_TRUNCATED_IMAGES = True


class PicklingFileHasher:
    def __init__(self, folder: Path):
        self.folder = folder
        self.pickle_file = self.folder / '.hashes.pkl'

    def hash_files(self) -> dict[Path, str]:
        file_hashes = self._load_existing_hashes()
        all_files = set(filter(lambda p: not _hidden_or_system_parents(p), Path(self.folder).rglob('*')))
        new_files = [f for f in all_files if f not in file_hashes]

        with Pool(cpu_count() - 1) as pool:
            new_hashes = list(
                tqdm(pool.imap(hash_file, new_files), total=len(new_files), desc=f'Hashing {self.folder}'))

        file_hashes.update({file: hash_value for file, hash_value in new_hashes if hash_value is not None})
        # Remove hashes of files that no longer exist
        for file in list(file_hashes.keys()):
            if file not in all_files:
                del file_hashes[file]

        self._save_hashes(file_hashes)
        return file_hashes

    def _load_existing_hashes(self) -> dict[Path, str]:
        if self.pickle_file.exists():
            with open(self.pickle_file, 'rb') as f:
                return pickle.load(f)
        return {}

    def _save_hashes(self, file_hashes: dict[Path, str]):
        with open(self.pickle_file, 'wb') as f:
            pickle.dump(file_hashes, f)


def hash_file(file):
    try:
        if file.suffix.lower() in ('.jpg', '.jpeg', '.png', '.gif', '.heic'):
            file_hash = imagehash.phash(Image.open(file))
        else:
            file_hash = _hash_file(file)
        return file, str(file_hash)
    except (UnidentifiedImageError, PermissionError):
        return file, None


def _hash_file(file):
    sha256 = hashlib.sha256()
    with open(file, 'rb') as f:
        while chunk := f.read(4096):
            sha256.update(chunk)
    return sha256.hexdigest()


def _hidden_or_system_parents(path: Path):
    for parent in path.parents:
        if _hidden_or_system(str(parent)):
            return True
    return False


def _hidden_or_system(path: str):
    if os.name == 'nt':
        attribute = win32api.GetFileAttributes(path)
        return attribute & (win32con.FILE_ATTRIBUTE_HIDDEN | win32con.FILE_ATTRIBUTE_SYSTEM)
    else:
        return path.startswith('.')  # linux-osx
