from setuptools import setup
from dynamic_import.version import version


package = 'dynamic_import'

with open('README.rst', 'r') as file:
    long_description = file.read()

setup(url='https://github.com/YoSTEALTH/Dynamic-Import',
      name=package,
      author='Ritesh',
      version=version,
      packages=[package],
      description=('Let Dynamic Import handle your projects(package) import needs. '
                   'Enables you to dynamically(lazily) import module as needed on run-time.'),
      python_requires='>=3.8',
      long_description=long_description,
      long_description_content_type="text/x-rst",
      classifiers=['Topic :: Software Development',
                   'License :: Public Domain',
                   'Intended Audience :: Developers',
                   # 'Development Status :: 1 - Planning',
                   # 'Development Status :: 2 - Pre-Alpha',
                   # 'Development Status :: 3 - Alpha',
                   # 'Development Status :: 4 - Beta',
                   'Development Status :: 5 - Production/Stable',
                   # 'Development Status :: 6 - Mature',
                   # 'Development Status :: 7 - Inactive',
                   'Operating System :: POSIX :: Linux',
                   'Programming Language :: Python :: 3.8',
                   'Programming Language :: Python :: 3.9',
                   'Programming Language :: Python :: 3.10',
                   'Programming Language :: Python :: 3.11',
                   'Programming Language :: Python :: 3.12'],
      zip_safe=False)
