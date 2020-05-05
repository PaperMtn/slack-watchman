import os
from setuptools import setup

with open(os.path.join(os.path.abspath(os.path.dirname(__file__)), 'README.md')) as f:
    README = f.read()

setup(
    name='slack-watchman',
    version='1.0.0',
    url='https://github.com/PaperMtn/slack-watchman',
    license='GPL-3.0',
    classifiers=[
        'Intended Audience :: Information Technology',
        'Topic :: Security',
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
    ],
    author='PaperMtn',
    author_email='papermtn@protonmail.com',
    long_description=README,
    long_description_content_type='text/markdown',
    description='Monitoring your Slack instances for data leaks',
    install_requires=[
        'requests',
        'colorama',
        'termcolor'
    ],
    keywords='audit slack slack-watchman watchman blue-team red-team threat-hunting',
    packages=['watchman'],
    entry_points={
        'console_scripts': ['slack-watchman=watchman:main']
    }
)
