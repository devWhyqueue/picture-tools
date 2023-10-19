from collections import defaultdict
from pathlib import Path
from unittest.mock import patch

from dupfind import purge


@patch('dupfind.purge.tqdm')
def test_group_by_hash(mock_tqdm):
    items = {
        Path('file1.txt'): 'hash1',
        Path('file2.txt'): 'hash2',
        Path('file3.txt'): 'hash1'
    }
    mock_tqdm.return_value = iter(items.items())
    expected_result = defaultdict(
        list,
        {
            'hash1': [(Path('file1.txt'), 'hash1'), (Path('file3.txt'), 'hash1')],
            'hash2': [(Path('file2.txt'), 'hash2')]
        }
    )
    result = purge._group_by_hash(items)
    assert result == expected_result


@patch('dupfind.purge._group_by_hash')
@patch('dupfind.purge.os.remove')
@patch('dupfind.purge.tqdm')
def test_remove_files_in_a_which_exist_in_b(mock_tqdm, mock_remove, mock_group_b):
    folder_a = {
        Path('a/file1.txt'): 'hash1',
        Path('a/file2.txt'): 'hash2'
    }
    folder_b = {
        Path('b/file3.txt'): 'hash1',
        Path('b/file4.txt'): 'hash3'
    }
    mock_group_b.return_value = defaultdict(
        list,
        {
            'hash1': [(Path('file3.txt'), 'hash1')],
            'hash3': [(Path('file4.txt'), 'hash3')]
        }
    )
    mock_tqdm.return_value = iter(folder_a.items())
    purge.remove_files_in_a_which_exist_in_b(folder_a, folder_b)
    mock_remove.assert_called_once_with(Path('a/file1.txt'))


@patch('dupfind.purge._group_by_hash')
@patch('dupfind.purge.os.remove')
@patch('dupfind.purge.tqdm')
def test_remove_duplicates(mock_tqdm, mock_remove, mock_group):
    mock_group.return_value = defaultdict(
        list,
        {
            'hash1': [(Path('file1.txt'), 'hash1'), (Path('file3.txt'), 'hash1')],
            'hash2': [(Path('file2.txt'), 'hash2')]
        }
    )
    mock_tqdm.return_value = mock_group.return_value.values()
    purge.remove_duplicates([
        (Path('file1.txt'), 'hash1'),
        (Path('file2.txt'), 'hash2'),
        (Path('file3.txt'), 'hash1')
    ])
    mock_remove.assert_called_once_with(Path('file3.txt'))
