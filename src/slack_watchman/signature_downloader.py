import io
import os
import sys
import traceback
import zipfile
from typing import List
from urllib.request import urlopen

import yaml

from slack_watchman.loggers import JSONLogger, StdoutLogger
from slack_watchman.models.signature import Signature, create_from_dict

SIGNATURE_URL = 'https://github.com/PaperMtn/watchman-signatures/archive/main.zip'


class SignatureDownloader:
    """A class for downloading and processing signature files from a GitHub repository."""

    def __init__(self, logger: JSONLogger | StdoutLogger):
        """
        Initializes a SignatureDownloader object.

        Args:
            logger (Union[JSONLogger, StdoutLogger]): The logger object to use for logging.
        """
        self.logger = logger

    def download_signatures(self) -> List[Signature]:
        """
        Downloads and processes signature files from a GitHub repository.

        Returns:
            List[Signature]: A list of processed Signature objects.
        """
        try:
            with urlopen(SIGNATURE_URL) as response:
                with zipfile.ZipFile(io.BytesIO(response.read())) as signatures_zip_file:
                    signature_objects = []

                    for file_path in signatures_zip_file.namelist():
                        if file_path.endswith('/'):  # Skip directories
                            continue

                        signature_name = os.path.basename(file_path)
                        self.logger.log('DEBUG', f'Processing {file_path}...')

                        with signatures_zip_file.open(file_path) as source:
                            file_content = source.read()

                        if file_path.endswith('.yaml'):
                            processed_signatures = self._process_signature(file_content)
                            signature_objects.extend(processed_signatures)
                            self.logger.log('INFO', f'Downloaded and processed signature file: {signature_name}')
                        else:
                            self.logger.log('DEBUG', f'Skipping unrecognized file: {file_path}')

                    return signature_objects

        except Exception as e:
            self.logger.log('CRITICAL', f"Error processing signature files: {e}")
            self.logger.log('DEBUG', traceback.format_exc())
            sys.exit(1)

    @staticmethod
    def _process_signature(signature_data: bytes) -> List[Signature]:
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
                output.append(create_from_dict(sig))
        return output
