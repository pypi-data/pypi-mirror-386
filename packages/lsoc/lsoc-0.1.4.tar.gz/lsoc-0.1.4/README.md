# lsoc - LS OCTAL

A lite Python package that lets you view file and directory access rights with octal.

Equivalent to typing: `stat -c "%a %n" *`

## Installation

### From PyPI
```bash
pip install lsoc
```

### On Ubuntu 24+ and modern Linux distros
```bash
pipx install lsoc
```

### From source
```bash
git clone https://github.com/AlperSakarya/lsoc.git
cd lsoc
pipx install -e .
```

## Usage

View all files in current directory:
```bash
lsoc
```

View specific file:
```bash
lsoc filename
```

## Example Output

```
$ lsoc
755 Desktop
755 Documents
755 Downloads
755 Music
600 myfile.tar.gz
755 Pictures
755 Public
400 Python.pem
775 Steam
```

```
$ lsoc /usr/bin/sudo
4755 /usr/bin/sudo
```

## Available on PyPI
https://pypi.org/project/lsoc/
