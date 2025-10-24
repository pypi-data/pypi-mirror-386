# *****************************************************************************
# Copyright (c) 2024 IBM Corporation and other Contributors.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
# *****************************************************************************

from setuptools import setup, find_namespace_packages
import codecs
import sys
import os
sys.path.insert(0, 'src')


if not os.path.exists('README.rst'):
    import pypandoc
    pypandoc.download_pandoc(targetfolder='~/bin/')
    pypandoc.convert_file('README.md', 'rst', outputfile='README.rst')

here = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(here, 'README.rst'), encoding='utf-8') as f:
    long_description = f.read()

# Maintain a single source of versioning
# https://packaging.python.org/en/latest/guides/single-sourcing-package-version/


def read(rel_path):
    here = os.path.abspath(os.path.dirname(__file__))
    with codecs.open(os.path.join(here, rel_path), 'r') as fp:
        return fp.read()


def get_version(rel_path):
    for line in read(rel_path).splitlines():
        if line.startswith('__version__'):
            delim = '"' if '"' in line else "'"
            return line.split(delim)[1]
    else:
        raise RuntimeError("Unable to find version string.")


setup(
    name='mas-devops',
    version=get_version("src/mas/devops/__init__.py"),
    author='David Parker',
    author_email='parkerda@uk.ibm.com',
    package_dir={'': 'src'},
    packages=find_namespace_packages(where='src'),
    include_package_data=True,
    url='https://github.com/ibm-mas/python-devops',
    license='Eclipse Public License - v1.0',
    description='Python for Maximo Application Suite Dev/Ops',
    long_description=long_description,
    install_requires=[
        'pyyaml',                  # MIT License
        'openshift',               # Apache Software License
        'kubernetes',              # Apache Software License
        'kubeconfig',              # BSD License
        'jinja2',                  # BSD License
        'jinja2-base64-filters',   # MIT License
        'semver',                  # BSD License
        'boto3'                    # Apache Software License
    ],
    extras_require={
        'dev': [
            'build',        # MIT License
            'flake8',       # MIT License
            'pytest',       # MIT License
            'pytest-mock',  # MIT License
            'requests-mock',  # Apache Software License
            'setuptools',    # MIT License
        ]
    },
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Operating System :: Microsoft :: Windows',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Topic :: Communications',
        'Topic :: Internet',
        'Topic :: Software Development :: Libraries :: Python Modules'
    ],
    scripts=[
        'bin/mas-devops-db2-validate-config',
        'bin/mas-devops-create-initial-users-for-saas',
        'bin/mas-devops-saas-job-cleaner'
    ]
)
