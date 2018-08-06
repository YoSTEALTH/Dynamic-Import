from setuptools import setup, find_packages

with open('README.rst', 'r') as file:
    long_description = file.read()

setup(
    name='noname',
    version='0.9.0',
    author='STEALTH',
    author_email='ritesh@stealthcentral.com',
    description="Dynamic run-time importer & easy to use module import path.",
    long_description=long_description,
    long_description_content_type="text/x-rst",
    python_requires='>=3.5',
    packages=find_packages(),
    url='https://github.com/YoSTEALTH/noname',
    classifiers=[
        # Info: https://pypi.python.org/pypi?%3Aaction=list_classifiers
        'License :: Public Domain',
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Topic :: Software Development :: Libraries :: Python Modules'
    ]
)

# http https://pypi.python.org/simple/ | grep \'noname\'
