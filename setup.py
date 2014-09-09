#!/usr/bin/env python

from distutils.core import setup

setup(name='server-status',
      version='0.0.1',
      author='David Beall',
      author_email='david@beallio.com',
      url='http://ww.beallio.com',
      description='Server Status',
      long_description='Server Status',
      packages=['app'],
      package_dir={'app': 'app'},
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
      ]
)
