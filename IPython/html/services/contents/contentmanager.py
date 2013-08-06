"""A base class contents manager.

Authors:

* Zach Sailer
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

import datetime
import io
import os
import glob
import shutil
import ast
import base64

from tornado import web

from IPython.config.configurable import LoggingConfigurable
from IPython.nbformat import current
from IPython.utils.traitlets import List, Dict, Unicode, TraitError
from IPython.utils import tz

#-----------------------------------------------------------------------------
# Classes
#-----------------------------------------------------------------------------

class ContentManager(LoggingConfigurable):
    
    content_dir = Unicode(os.getcwdu(), config=True, help="""
            The directory to use for contents.
            """)
            
    contents = List()
    
    def get_content_names(self, content_path=None):
        """List of dicts of files in content_path"""
        names = glob.glob(os.path.join(self.content_dir, content_path,'*'))
        contents = list()
        dirs = list()
        notebooks = list()
        for name in names:
            if os.path.isdir(name) == True:
                dirs.append(os.path.split(name)[1])
            elif os.path.splitext(name)[1] == '.ipynb':
                notebooks.append(os.path.split(name)[1])        
            else:
                contents.append(os.path.split(name)[1])        
        return dirs, notebooks, contents

    def list_contents(self, content_path=None):
        """List all contents in the named path."""
        dir_names, notebook_names, content_names = self.get_content_names(content_path)
        content_mapping = []
        for name in dir_names:
            model = self.content_model(name, content_path, type='dir')
            content_mapping.append(model)
        for name in content_names:
            model = self.content_model(name, content_path, type='file')
            content_mapping.append(model)
        for name in notebook_names:
            model = self.content_model(name, content_path, type='notebook')
            content_mapping.append(model)
        return content_mapping

    def get_path_by_name(self, name, content_path=None):
        """Return a full path to content"""
        if content_path==None:
            path = os.path.join(self.content_dir, name)
        else:
            path = os.path.join(self.content_dir, content_path, name)
        return path

    def content_info(self, name, content_path=None):
        """Read the content of a named file"""
        file_type = os.path.splitext(os.path.basename(name))[1]
        full_path = self.get_path_by_name(name, content_path)
        info = os.stat(full_path)
        size = info.st_size
        last_modified = tz.utcfromtimestamp(info.st_mtime)
        return last_modified, file_type, size

    def content_model(self, name, content_path=None, type=None):
        """Create a dict standard model for any file (other than notebooks)"""
        last_modified, file_type, size = self.content_info(name, content_path)
        model = {"name": name,
                    "path": content_path,
                    "type": type,
                    "MIME-type": "",
                    "last_modified (UTC)": last_modified.ctime(),
                    "size": size}
        return model
    
    def new_folder(self, name=None, path=None):
        """Create a new folder in the path location"""
        if name==None:
            name = self.increment_filename("new_folder", path)
        if path==None:
            new_path = os.path.join(self.content_dir, name)
        else:
            new_path = os.path.join(self.content_dir, path, name)
        if not os.path.exists(new_path):
            os.makedirs(new_path)
        else:
            raise web.HTTPError(409, u'Directory already exists or creation permission not allowed.')
        return name

    def increment_filename(self, basename, content_path=None):
        """Return a non-used filename of the form basename<int>.

        This searches through the filenames (basename0, basename1, ...)
        until is find one that is not already being used. It is used to
        create Untitled and Copy names that are unique.
        """
        i = 0
        while True:
            name = u'%s%i' % (basename,i)
            path = self.get_path_by_name(name, content_path)
            if not os.path.isdir(path):
                break
            else:
                i = i+1
        return name

    def delete_content(self, content_path):
        """Delete a file"""
        os.unlink(os.path.join(self.content_dir, content_path))
        