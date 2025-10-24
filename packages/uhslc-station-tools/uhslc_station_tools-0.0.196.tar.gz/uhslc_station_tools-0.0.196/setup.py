from setuptools import setup, find_packages
from setuptools.command.install import install
import os
import sys

# set the release candidate flag as appropriate.
RC=''
#RC=''
VERSION=f'0.0.{os.environ.get("CIRCLE_BUILD_NUM","DEVELOPMENT")}{RC}'

class VerifyVersionCommand(install):
    def run(self):

        print(f'version: {VERSION}')

setup(
    name='uhslc_station_tools',
    version=VERSION,
    python_requires='>=3.6',
    description='Set of tools for loading, processing and saving sea level data from tide gauges',
    url='https://github.com/uhsealevelcenter/station_tools',
    author='Nemanja Komar',
    author_email='komar@hawaii.edu',
    license='MIT',
    packages=find_packages(),
    install_requires=[
        'numpy==1.15.0',
        'pandas==0.24.1',
        'scipy==1.4.1',
        'utide==0.2.5'
      ],

    package_data={'': [
        '*.txt',
        '*.dat'
            ]},

    classifiers=[
        'Development Status :: 1 - Planning',
        'Intended Audience :: Science/Research',
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    cmdclass={
        'verify': VerifyVersionCommand,
    }
)
