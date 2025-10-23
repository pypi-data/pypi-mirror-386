#!/usr/bin/python
import os
import sys

def lsoccmd():
    if len(sys.argv) > 1:
        myFile = str(sys.argv[1])
        lsoc = 'stat -c "%a %n" {0}'.format(myFile)
    else:
        lsoc = 'stat -c "%a %n" *'

    os.system(lsoc)

if __name__ == "__main__":
    lsoccmd()
