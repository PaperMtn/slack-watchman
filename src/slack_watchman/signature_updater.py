import io
import os
import zipfile
import shutil
import sys
from datetime import datetime
from pathlib import Path
from urllib.request import urlopen

from . import sw_logger

SIGNATURE_URL = 'https://github.com/PaperMtn/watchman-signatures/archive/main.zip'


class SignatureUpdater(object):
    def __init__(self, logger: sw_logger.JSONLogger):
        self.application_path = str((Path(__file__).parents[2]).resolve())
        self.logger = logger

    def update_signatures(self):

        response = urlopen(SIGNATURE_URL)

        try:
            sig_dir = os.path.join(self.application_path, 'watchman-signatures/')
            for sub_directory in [
                '',
                'config_files',
                'competitive',
                'compliance',
                'tokens_and_credentials'
            ]:
                full_path = os.path.join(sig_dir, sub_directory)
                if not os.path.exists(full_path):
                    os.makedirs(full_path)
        except Exception as e:
            self.logger.log('CRITICAL', 'Error while creating the signature-base directories')
            sys.exit(1)

        try:
            signatures_zip_file = zipfile.ZipFile(io.BytesIO(response.read()))
            for file_path in signatures_zip_file.namelist():
                signature_name = os.path.basename(file_path)
                if file_path.endswith('/'):
                    continue

                self.logger.log('DEBUG', f'Extracting {file_path} ...')
                if '/competitive/' in file_path and file_path.endswith('.yaml'):
                    target_file = os.path.join(sig_dir, 'competitive', signature_name)
                elif '/compliance/' in file_path and file_path.endswith('.yaml'):
                    target_file = os.path.join(sig_dir, 'compliance', signature_name)
                elif '/config_files/' in file_path and file_path.endswith('.yaml'):
                    target_file = os.path.join(sig_dir, 'config_files', signature_name)
                elif file_path.endswith('.yaml'):
                    target_file = os.path.join(sig_dir, 'tokens_and_credentials', signature_name)
                elif file_path.endswith('.yaml'):
                    target_file = os.path.join(sig_dir, 'misc', signature_name)
                else:
                    continue

                if os.path.exists(target_file):
                    existing_modified_date = datetime.utcfromtimestamp(os.path.getmtime(target_file))
                    if datetime(*signatures_zip_file.getinfo(file_path).date_time) > existing_modified_date:
                        self.logger.log('SUCCESS', f'Signature updated to newest version: {signature_name}')
                        source = signatures_zip_file.open(file_path)
                        target = open(target_file, 'wb')
                        with source, target:
                            shutil.copyfileobj(source, target)
                        target.close()
                        source.close()
                else:
                    self.logger.log('SUCCESS', f'New signature file: {signature_name}')
                    source = signatures_zip_file.open(file_path)
                    target = open(target_file, 'wb')
                    with source, target:
                        shutil.copyfileobj(source, target)
                    target.close()
                    source.close()

        except Exception as e:
            self.logger.log('CRITICAL', f'Error while extracting the signature files from the download package {e}')
            sys.exit(1)
