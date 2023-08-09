from setuptools import setup, find_packages

setup(
    name='patronigence',
    version='1.0',
    packages=find_packages(),
    url='https://github.com/taylorhickem/sqlite-gsheet.git',
    description='generative AI with personalized data using Notion API',
    author='@taylorhickem',
    long_description=open('README.md').read(),
    install_requires=open("requirements.txt", "r").read().splitlines(),
    include_package_data=True
)