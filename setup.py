from setuptools import setup, find_packages
from datestamp import stamp


with open('README.rst', 'r') as file:
    long_description = file.read()

project = 'dynamic_import'

setup(url='https://github.com/YoSTEALTH/Dynamic-Import',
      name=project,
      author='STEALTH',
      version=stamp(project),
      packages=find_packages(),
      description=('Dynamically/Lazily import python module on run-time. '
                   'Also enables easy to use import path name.'),
      python_requires='>=3.6',
      long_description=long_description,
      long_description_content_type="text/x-rst",
      # Info: https://pypi.python.org/pypi?%3Aaction=list_classifiers
      classifiers=['License :: Public Domain',
                   # 'Development Status :: 4 - Beta',
                   # note: had 0 issues reported over the year, should be ready for production.
                   'Development Status :: 5 - Production/Stable',
                   'Intended Audience :: Developers',
                   'Programming Language :: Python :: 3.6',
                   'Programming Language :: Python :: 3.7',
                   'Programming Language :: Python :: 3.8',
                   'Topic :: Software Development :: Libraries :: Python Modules'])
