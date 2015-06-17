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
    parser.add_argument('--port', '-p', type=int, default=5545)
    options = parser.parse_args()

    runner.start(basedir, options.port)

