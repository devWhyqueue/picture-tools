import hashlib
from pathlib import Path
from unittest.mock import patch, mock_open

import pytest
from PIL import UnidentifiedImageError

import dupfind.hashing as hashing


@pytest.fixture
def mock_files():
    files = [Path(f'test_file_{i}.txt') for i in range(3)]
    with patch('pathlib.Path.rglob', return_value=files):
        yield files


@pytest.fixture
def mock_cpu_count():
    with patch('dupfind.hashing.cpu_count', return_value=4):
        yield


@pytest.fixture
def mock_pool():
    with patch('dupfind.hashing.Pool') as mock_pool:
        mock_pool.return_value.__enter__.return_value.imap = map
        yield mock_pool


def test_hash_file_image_file():
    with patch('dupfind.hashing.Image.open'):
        with patch('dupfind.hashing.imagehash.phash', return_value='image_hash'):
            result = hashing.hash_file(Path('image.jpg'))
    assert result == (Path('image.jpg'), 'image_hash')


def test_hash_file_non_image_file():
    with patch('dupfind.hashing._hash_file', return_value='file_hash'):
        result = hashing.hash_file(Path('file.txt'))
    assert result == (Path('file.txt'), 'file_hash')


def test_hash_file_unidentified_image_error():
    with patch('dupfind.hashing.Image.open', side_effect=UnidentifiedImageError):
        result = hashing.hash_file(Path('bad_image.jpg'))
    assert result == (Path('bad_image.jpg'), None)


def test_hash_file_permission_error():
    with patch('dupfind.hashing.Image.open', side_effect=PermissionError):
        result = hashing.hash_file(Path('restricted.jpg'))
    assert result == (Path('restricted.jpg'), None)


def test__hash_file():
    m = mock_open(read_data=b'data')
    with patch('builtins.open', m):
        result = hashing._hash_file(Path('file.txt'))
    sha256 = hashlib.sha256()
    sha256.update(b'data')
    assert result == sha256.hexdigest()


@patch('dupfind.hashing.os')
@patch('dupfind.hashing.win32con')
@patch('dupfind.hashing.win32api')
def test_hidden_or_system_windows(mock_win32api, mock_win32con, mock_os):
    mock_os.name = 'nt'
    mock_win32api.GetFileAttributes.return_value = 2
    mock_win32con.FILE_ATTRIBUTE_HIDDEN = 2
    mock_win32con.FILE_ATTRIBUTE_SYSTEM = 4

    assert hashing._hidden_or_system("C:\\hidden_file") == 2


def test_hidden_or_system_non_windows():
    with patch('dupfind.hashing.os') as mock_os:
        mock_os.name = 'posix'
        assert hashing._hidden_or_system(".hidden_file") is True
        assert hashing._hidden_or_system("visible_file") is False
