from pathlib import Path
from unittest.mock import patch

from dupfind.hashing import PicklingFileHasher


def test_hash_files_on_empty_folder(tmp_path):
    # Given
    hasher = PicklingFileHasher(tmp_path)
    # When
    file_hashes = hasher.hash_files()
    # Then
    assert file_hashes == {}


def test_hash_files_on_non_empty_folder(tmp_path):
    # Given
    (tmp_path / 'file1.txt').touch()
    (tmp_path / 'file2.txt').touch()
    hasher = PicklingFileHasher(tmp_path)

    with patch('pickle.load', return_value={}):
        with patch('pickle.dump'):
            with patch('dupfind.hashing.Pool') as mock_pool:
                mock_pool.return_value.__enter__.return_value \
                    .imap.return_value = [(tmp_path / 'file1.txt', 'hash1'), (tmp_path / 'file2.txt', 'hash2')]
                # When
                file_hashes = hasher.hash_files()

    # Then
    assert file_hashes == {tmp_path / 'file1.txt': 'hash1', tmp_path / 'file2.txt': 'hash2'}


def test_hash_files_with_none_hashes(tmp_path):
    # Given
    (tmp_path / 'file1.txt').touch()
    (tmp_path / 'problematic_image.jpg').touch()
    hasher = PicklingFileHasher(tmp_path)

    with patch('pickle.load', return_value={}):
        with patch('pickle.dump'):
            with patch('dupfind.hashing.Pool') as mock_pool:
                mock_pool.return_value.__enter__.return_value \
                    .imap.return_value = [(tmp_path / 'file1.txt', 'hash1'), (tmp_path / 'file1.txt', None)]
                # When
                file_hashes = hasher.hash_files()

    # Then
    assert file_hashes == {tmp_path / 'file1.txt': 'hash1'}


def test_hash_files_on_adding_new_files(tmp_path):
    # Given
    (tmp_path / 'file1.txt').touch()
    (tmp_path / 'file2.txt').touch()
    hasher = PicklingFileHasher(tmp_path)

    with patch('dupfind.hashing.PicklingFileHasher._load_existing_hashes',
               return_value={tmp_path / 'file1.txt': 'hash1'}):
        with patch('dupfind.hashing.Pool') as mock_pool:
            mock_pool.return_value.__enter__.return_value.imap.return_value = [(tmp_path / 'file2.txt', 'hash2')]
            # When
            file_hashes = hasher.hash_files()

    # Then
    assert file_hashes == {tmp_path / 'file1.txt': 'hash1', tmp_path / 'file2.txt': 'hash2'}


def test_hash_files_on_removing_files(tmp_path):
    # Given
    (tmp_path / 'file1.txt').touch()
    hasher = PicklingFileHasher(tmp_path)

    with patch('dupfind.hashing.PicklingFileHasher._load_existing_hashes') as mock_load_existing_hashes:
        mock_load_existing_hashes.return_value = {tmp_path / 'file1.txt': 'hash1', tmp_path / 'file2.txt': 'hash2'}
        # When
        file_hashes = hasher.hash_files()

    # Then
    assert file_hashes == {tmp_path / 'file1.txt': 'hash1'}


def test_hash_files_with_existing_pickle_file(tmp_path):
    # Given
    (tmp_path / 'file1.txt').touch()
    hasher = PicklingFileHasher(tmp_path)

    with patch('dupfind.hashing.PicklingFileHasher._load_existing_hashes') as mock_load_existing_hashes:
        mock_load_existing_hashes.return_value = {tmp_path / 'file1.txt': 'existing_hash1'}
        # When
        file_hashes = hasher.hash_files()

    # Then
    assert file_hashes == {tmp_path / 'file1.txt': 'existing_hash1'}


def test_hash_files_respects_exclusions(tmp_path):
    # Given: Create excluded and non-excluded files and directories
    excluded_file = tmp_path / '.hashes.pkl'
    excluded_file.touch()
    non_excluded_file = tmp_path / 'file3.txt'
    non_excluded_file.touch()

    # Create excluded and non-excluded folders
    (tmp_path / '$RECYCLE.BIN').mkdir()
    (tmp_path / 'normal_folder').mkdir()
    (tmp_path / 'normal_folder' / 'file4.txt').touch()

    hasher = PicklingFileHasher(tmp_path)

    # Mocking the load and save methods
    with patch('dupfind.hashing.PicklingFileHasher._load_existing_hashes', return_value={}):
        with patch('dupfind.hashing.PicklingFileHasher._save_hashes'):
            with patch('dupfind.hashing.Pool') as mock_pool:
                # Mock the pool to return hashes for non-excluded files
                mock_pool.return_value.__enter__.return_value.imap.return_value = [
                    (tmp_path / 'normal_folder' / 'file4.txt', 'hash4')
                ]
                # When: Call the hash_files method
                file_hashes = hasher.hash_files()

    # Then: Assert only non-excluded files are hashed
    assert file_hashes == {tmp_path / 'normal_folder' / 'file4.txt': 'hash4'}
    assert excluded_file not in file_hashes
    assert Path(tmp_path / '$RECYCLE.BIN').is_dir() and not any(
        file for file in file_hashes if file.parent == tmp_path / '$RECYCLE.BIN')
