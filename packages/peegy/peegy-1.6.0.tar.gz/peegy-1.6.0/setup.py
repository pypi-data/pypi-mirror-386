#! /usr/bin/env python
# -*- coding: utf-8 -*-
from setuptools import setup, find_packages
import os
from importlib.metadata import version
__version__ = version(__package__)


def run_setup():
    _folder = os.path.dirname(os.path.realpath(__file__))
    requirement_path = _folder + os.path.sep + 'requirements.txt'
    install_requires = []
    if os.path.isfile(requirement_path):
        with open(requirement_path) as f:
            install_requires = f.read().splitlines()
    setup(name="peegy",
          install_requires=install_requires,
          setup_requires=['gitpython'],
          version=__version__,
          packages=find_packages(),
          author="Jaime A. Undurraga",
          author_email="jaime.undurraga@gmail.com",
          description="Tools to pipeline bulk analyses of EEG and other modalities.",
          long_description="""
          Set of tools for processing EEG data data using bdf/edf file format. These can be extended to other modalities
          too. The overall goal is to produce easy processing pipelines to perform batch data analyses in a systematic 
          and reproducible manner. 
          This package includes several statistical, visualization, and output tools to generate consistent SQLITE
          databases. 
          """,
          license="MIT",
          url="https://jundurraga.gitlab.io/peegy/",

          package_data={'': ['*.lay', '*.json']},
          include_package_data=True,
          classifiers=[
              'Development Status :: 3 - Alpha',
              'Environment :: Console',
              'Intended Audience :: Science/Research',
              'License :: OSI Approved :: MIT License',
              'Operating System :: MacOS :: MacOS X',
              'Operating System :: Microsoft :: Windows :: Windows 10',
              'Operating System :: POSIX :: Linux',
              'Programming Language :: Python :: 3',
              'Topic :: Scientific/Engineering :: Bio-Informatics'
              ]
          )
    # update_git_hash_version()


def update_git_hash_version():
    """Return version with local version identifier."""
    import git
    repo = git.Repo(search_parent_directories=True)
    sha = repo.head.object.hexsha
    with open('GITHEADHASH', mode='w+') as f:
        f.write(sha)


if __name__ == '__main__':
    run_setup()
