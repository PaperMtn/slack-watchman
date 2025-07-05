import io
from unittest.mock import patch, MagicMock

import pytest

from slack_watchman.models.signature import Signature, TestCases
from slack_watchman.signature_downloader import SignatureDownloader


@pytest.fixture
def mock_logger():
    """Mock logger for testing."""
    return MagicMock()


@pytest.fixture
def downloader(mock_logger):
    """Fixture for initializing the SignatureDownloader."""
    return SignatureDownloader(logger=mock_logger)


@patch('slack_watchman.signature_downloader.requests.get')
@patch('slack_watchman.signature_downloader.zipfile.ZipFile')
def test_download_signatures(mock_zipfile, mock_get, downloader, mock_logger):
    """Test the download_signatures method."""
    # Set up mock response
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.content = b'zipfile-bytes'
    mock_get.return_value = mock_response

    # Mock a zip file structure
    mock_zip = MagicMock()
    mock_zip.namelist.return_value = ['file1.yaml', 'file2.txt']
    mock_zip.open.side_effect = [
        io.BytesIO(b'signatures:\n  - watchman_apps: ["slack_std"]\n    status: "enabled"'),
        io.BytesIO(b'not a yaml file content')
    ]
    mock_zipfile.return_value.__enter__.return_value = mock_zip

    # Mock _process_signature
    mock_signature = Signature(
        id='123',
        name='mock_name',
        status='enabled',
        author='author',
        date='2024-01-01',
        version='1.0',
        description='desc',
        severity='high',
        watchman_apps={
            'slack_std': {
                'category': 'category',
                'scope': ['scope'],
                'file_types': ['file_types'],
                'search_strings': []
            }
        },
        category='category',
        scope=['scope'],
        file_types=['file_types'],
        test_cases=TestCases(match_cases=[], fail_cases=[]),
        search_strings=[],
        patterns=[]
    )
    with patch.object(downloader, '_process_signature', return_value=[mock_signature]) as mock_process:
        result = downloader.download_signatures()

    # Verify
    assert len(result) == 1
    mock_logger.log.assert_any_call('DEBUG', 'Processing file1.yaml...')
    mock_logger.log.assert_any_call('INFO', 'Downloaded and processed signature file: file1.yaml')
    mock_logger.log.assert_any_call('DEBUG', 'Skipping unrecognized file: file2.txt')
    mock_process.assert_called_once()


def test_process_signature():
    """Test the _process_signature method."""
    signature_data = (b'signatures:\n  - watchman_apps: ["slack_std"]\n    status: "enabled"\n    id: "123"\n    name: '
                      b'"mock_name"')

    # Mock create_from_dict
    mock_signature = Signature(
        id='123',
        name='mock_name',
        status='enabled',
        author='author',
        date='2024-01-01',
        version='1.0',
        description='desc',
        severity='high',
        watchman_apps={
            'slack_std': {
                'category': 'category',
                'scope': ['scope'],
                'file_types': ['file_types'],
                'search_strings': []
            }
        },
        category='category',
        scope=['scope'],
        file_types=['file_types'],
        test_cases=TestCases(match_cases=[], fail_cases=[]),
        search_strings=[],
        patterns=[]
    )
    with patch('slack_watchman.signature_downloader.create_from_dict', return_value=mock_signature) as mock_create:
        result = SignatureDownloader._process_signature(signature_data)

    assert len(result) == 1
    assert isinstance(result[0], Signature)
    mock_create.assert_called_once_with({
        'watchman_apps': ['slack_std'],
        'status': 'enabled',
        'id': '123',
        'name': 'mock_name'
    })


@patch('slack_watchman.signature_downloader.requests.get', side_effect=Exception('Mocked Exception'))
def test_download_signatures_exception(mock_get, downloader, mock_logger):
    """Test that download_signatures handles exceptions correctly."""
    with pytest.raises(SystemExit):  # sys.exit(1) triggers SystemExit
        downloader.download_signatures()

    mock_logger.log.assert_any_call('CRITICAL', 'Error processing signature files: Mocked Exception')
    assert any(call[0][0] == 'DEBUG' for call in mock_logger.log.call_args_list)  # Verify traceback logging


def test_init(downloader, mock_logger):
    """Test the __init__ method."""
    assert downloader.logger == mock_logger
