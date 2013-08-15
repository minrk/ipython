"""
build [and upload] Windows IPython releases

usage:

python tools/release_windows.py [--github] [--pypi]

Meant to be run on Windows

Requires that you have python and python3 on your PATH
"""

import glob
import os
import shutil
import sys

from toollib import sh
try:
    import gh_api
except ImportError:
    gh_api = None

github = '--github' in sys.argv

cmd_t = "{py} setup.py bdist_msi"

pypi = '--pypi' in sys.argv
pypi_cmd_t = "python setup.py upload_msi -f {fname}"

# Windows Python cannot normally cross-compile,
# so you must have 4 Pythons to make 4 installers:
# http://docs.python.org/2/distutils/builtdist.html#cross-compiling-on-windows

pythons = {
    2: {
        'win32' : r'C:\\Python27\Python.exe',
        'win-amd64': r'C:\\Python27_64\Python.exe',
    },
    3: {
        'win32' : r'C:\\Python33\Python.exe',
        'win-amd64': r'C:\\Python33_64\Python.exe',
    },
}

for v,plat_py in pythons.items():
    try:
        shutil.rmtree('build')
    except OSError:
        pass
    for plat,py in plat_py.items():
        cmd = cmd_t.format(**locals())
        sh(cmd)
        fname = glob.glob(os.path.join('dist', 'ipython-*.{plat}.msi'.format(**locals())))[0]
        if pypi:
            sh(pypi_cmd_t.format(fname=fname))
        if github and gh_api:
            print ("Uploading %s to GitHub" % mangled)
            desc = "IPython Installer for Python {v}.x on {plat}".format(**locals())
            gh_api.post_download('ipython/ipython', fname, description=desc)
