from setuptools import setup, find_packages

with open('README.rst', 'r') as file:
    long_description = file.read()

setup(
    name='dynamic_import',
    author='STEALTH',
    version='0.9.6',
    author_email='ritesh@stealthcentral.com',
    description="Dynamically/Lazily import python module on run-time. \
    Also enables easy to use import path name.",
    long_description=long_description,
    long_description_content_type="text/x-rst",
    python_requires='>=3.6',
    packages=find_packages(),
    url='https://github.com/YoSTEALTH/Dynamic-Import',
    classifiers=[
        # Info: https://pypi.python.org/pypi?%3Aaction=list_classifiers
        'License :: Public Domain',
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Topic :: Software Development :: Libraries :: Python Modules'
    ]
)
