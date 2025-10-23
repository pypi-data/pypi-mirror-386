from setuptools import setup

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name='lsoc',
    packages=['lsoc'],
    version='0.1.4',
    description='Lite Python package that lets you view file and directory access rights with octal',
    long_description=long_description,
    long_description_content_type="text/markdown",
    author='Alper Sakarya',
    author_email='alpersakarya@gmail.com',
    url='https://github.com/AlperSakarya/lsoc',
    download_url='https://github.com/AlperSakarya/lsoc/tarball/0.1',
    keywords=['ls', 'octal'],
    classifiers=[],
    entry_points={'console_scripts': ['lsoc = lsoc.lsoc:lsoccmd']}
)
