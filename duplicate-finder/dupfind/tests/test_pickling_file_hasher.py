from unittest.mock import patch

from dupfind.hashing import PicklingFileHasher


def test_hash_files_on_empty_folder(tmp_path):
    # Given
    hasher = PicklingFileHasher(tmp_path)
    # When
    file_hashes = hasher.hash_files()
    # Then
    assert file_hashes == {}


def test_hash_files_on_non_empty_folder_first_run(tmp_path):
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
