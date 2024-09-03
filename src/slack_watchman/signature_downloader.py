import io
import os
import sys
import traceback
import zipfile
from urllib.request import urlopen
from typing import List

import yaml

from slack_watchman.sw_logger import JSONLogger, StdoutLogger
from slack_watchman.models.signature import Signature, TestCases

SIGNATURE_URL = 'https://github.com/PaperMtn/watchman-signatures/archive/main.zip'


class SignatureDownloader:
    def __init__(self, logger: JSONLogger or StdoutLogger):
        """ Initializes a SignatureDownloader object.

        Args:
            logger (JSONLogger or StdoutLogger): The logger object to use for logging.
        Returns:
            None
        """
        self.logger = logger

    def download_signatures(self) -> List[Signature]:
        """ Download signatures from GitHub repository

        Returns:
            List of downloaded Signature objects
        """

        try:
            response = urlopen(SIGNATURE_URL)
            signatures_zip_file = zipfile.ZipFile(io.BytesIO(response.read()))
            signature_files = {}
            signature_objects = []
            for file_path in signatures_zip_file.namelist():
                if file_path.endswith('/'):
                    continue

                signature_name = os.path.basename(file_path)
                self.logger.log('DEBUG', f'Processing {file_path} ...')

                with signatures_zip_file.open(file_path) as source:
                    signature_files[signature_name] = source.read()

                if file_path.endswith('.yaml'):
                    signature_objects.append(self._process_signature(signature_files[signature_name]))
                    self.logger.log('SUCCESS', f'Downloaded signature file: {signature_name}')
                else:
                    self.logger.log('DEBUG', f'Skipping unrecognized file: {file_path}')

            return [item for sublist in signature_objects for item in sublist]

        except Exception as e:
            self.logger.log('CRITICAL', f'Error while processing the signature'
                                        f' files from the download package: {e}')
            self.logger.log('DEBUG', traceback.format_exc())
            sys.exit(1)

    def _process_signature(self, signature_data: bytes) -> List[Signature]:
        """ Process a signature data bytes object into a list of Signature objects.

        This function takes a bytes object containing signature data, parses it into a dictionary,
        and then creates a list of Signature objects based on the parsed data.

        Args:
            signature_data (bytes): A bytes object containing signature data.
        Returns:
            List[Signature]: A list of Signature objects created from the parsed signature data.
        """

        signature_dict = yaml.safe_load(io.StringIO(signature_data.decode('utf-8')))
        output = []
        for sig in signature_dict.get('signatures'):
            if 'slack_std' in sig.get('watchman_apps') and sig.get('status') == 'enabled':
                output.append(Signature(
                    name=sig.get('name'),
                    status=sig.get('status'),
                    author=sig.get('author'),
                    date=sig.get('date'),
                    version=sig.get('version'),
                    description=sig.get('description'),
                    severity=sig.get('severity'),
                    watchman_apps=sig.get('watchman_apps'),
                    category=sig.get('watchman_apps').get('slack_std').get('category'),
                    scope=sig.get('watchman_apps').get('slack_std').get('scope'),
                    file_types=sig.get('watchman_apps').get('slack_std').get('file_types'),
                    test_cases=TestCases(
                        match_cases=sig.get('test_cases').get('match_cases'),
                        fail_cases=sig.get('test_cases').get('fail_cases')
                    ),
                    search_strings=sig.get('watchman_apps').get('slack_std').get('search_strings'),
                    patterns=sig.get('patterns')))
        return output
