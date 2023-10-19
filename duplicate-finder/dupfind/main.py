from argparse import ArgumentParser
from pathlib import Path

from dupfind import purge
from dupfind.hashing import PicklingFileHasher

if __name__ == '__main__':
    parser = ArgumentParser(description='Delete duplicates in dir_a or files in dir_a which exist in dir_b')
    parser.add_argument('--dir_a', type=str, help='Directory to delete from', required=True)
    parser.add_argument('--dir_b', type=str, help='Directory to compare to', required=False)
    parser.add_argument('--dry_run', action='store_true')
    args = parser.parse_args()
    if args.dir_b:
        file_hashes_a = PicklingFileHasher(Path(args.dir_a)).hash_files()
        file_hashes_b = PicklingFileHasher(Path(args.dir_b)).hash_files()
        removed = purge.remove_files_in_a_which_exist_in_b(file_hashes_a, file_hashes_b, args.dry_run)
    else:
        file_hashes = PicklingFileHasher(Path(args.dir_a)).hash_files()
        removed = purge.remove_duplicates(file_hashes, args.dry_run)
    print(f'Removed {removed} files.')
