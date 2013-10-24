"""A file manager.
"""

#-----------------------------------------------------------------------------
#  Copyright (C) 2013  The IPython Development Team
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------

import base64
import io
import itertools
import os
import glob
import posixpath
import shutil

from tornado import web

from IPython.config import Configurable
from IPython.utils.traitlets import Unicode, Dict, Bool, TraitError
from IPython.utils import tz

#-----------------------------------------------------------------------------
# Classes
#-----------------------------------------------------------------------------

class FileManager(Configurable):
    
    root = Unicode(os.getcwd())
    
    def get_os_path(self, path):
        """Get the real OS path for an API path"""
        parts = path.strip('/').split('/')
        parts = [p for p in parts if p != ''] # remove duplicate splits
        return os.path.join(self.root, *parts)
    
    def is_hidden(self, name, path):
        if name.startswith('.'):
            return True
        return False
    
    def get_directory_contents(self, path):
        os_path = self.get_os_path(path)
        files = os.listdir(os_path)
        model = []
        for name in files:
            if self.is_hidden(name, path):
                continue
            model.append(self.get_summary('/'.join((path, name))))
        return model
    
    def get_file_contents(self, path):
        model = self.get_summary(path)
        os_path = self.get_os_path(path)
        with open(os_path) as f:
            content = f.read()
        b64content = base64.encodestring(content).decode('ascii')
        model['encoding'] = 'base64'
        model['content'] = b64content
        return model
    
    def get_summary(self, path):
        os_path = self.get_os_path(path)
        stats = os.stat(os_path)
        if os.path.isdir(os_path):
            type = 'dir'
        else:
            if os_path.endswith('.ipynb'):
                type = 'notebook'
            else:
                type = 'file'
        path, name = posixpath.split(path)
        summary = dict(
            type = type,
            name = name,
            path = path.strip('/'),
            last_modified = tz.utcfromtimestamp(stats.st_mtime),
            created = tz.utcfromtimestamp(stats.st_ctime),
            size = stats.st_size if type != 'dir' else 0,
        )
        return summary
    
    def get_contents(self, path):
        path = path.strip('/')
        os_path = self.get_os_path(path)
        if not os.path.exists(os_path):
            raise web.HTTPError(404)
        
        if os.path.isdir(os_path):
            return self.get_directory_contents(path)
        else:
            return self.get_file_contents(path)
    
    def rename_file(self, src, dest):
        """Move the file `src` to `dest`"""
        self.log.info("Renaming %s to %s", src, dest)
        os_src = self.get_os_path(src)
        os_dest = self.get_os_path(dest)
        self.log.debug("OS Rename: %s to %s", os_src, os_dest)
        if not os.path.exists(os_src):
            raise web.HTTPError(404)
        parent, name = os.path.split(os_dest)
        if not os.path.exists(parent):
            raise web.HTTPError(400, "Destination not available: %s" % dest)
        if os.path.exists(os_dest):
            raise web.HTTPError(400, "Destination already exists: %s" % dest)
        
        os.rename(os_src, os_dest)
        return self.get_summary(dest)
    
    def create_file(self, model, path):
        """Create a file from 'model' in 'path'"""
        
        parts = path.split('/')[:-1]
        d = self.root
        for part in parts:
            d = os.path.join(d, part)
            if not os.path.exists(d):
                os.mkdir(d)
        
        os_path = self.get_os_path(path)
        data = base64.decodestring(model['content'].encode('ascii'))
        with open(os_path, 'w') as f:
            f.write(data)
        return self.get_summary(path)
