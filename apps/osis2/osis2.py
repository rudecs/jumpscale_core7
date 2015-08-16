
from JumpScale import j
from JumpScale.baselib import cmdutils

import os
import sys

if __name__ == "__main__":
    import sys
    basedir = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, basedir)
    from app import runner

    parser = cmdutils.ArgumentParser()
    parser.add_argument('--instance', '-i', default='main')
    options = parser.parse_args()
    hrd = j.application.getAppInstanceHRD('osis2', options.instance)

    runner.start(basedir, hrd)
