#!/usr/bin/env python
import os

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

readme_file = 'README.md'
readme_file_full_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), readme_file)
with open(readme_file_full_path, 'r') as f:
    readme_contents = f.read()
if not readme_contents:
    readme_contents = ''

setup(name='server-status',
      version='0.0.1',
      author='David Beall',
      author_email='david@beallio.com',
      url='http://ww.beallio.com',
      description='Server Status',
      long_description='{}'.format(readme_contents),
      packages=['serverstatus'],
      package_dir={'serverstatus': 'serverstatus'},
      classifiers=[
          'Development Status :: 4 - Beta',
          'Intended Audience :: System Administrators',
          'Intended Audience :: Information Technology',
          'License :: OSI Approved :: GNU General Public License (GPL)',
          'Natural Language :: English',
          'Operating System :: POSIX',
          'Programming Language :: Python',
          'Topic :: Software Development :: Libraries :: Python Modules',
          'Topic :: Software Development :: Libraries',
          'Topic :: System',
      ])