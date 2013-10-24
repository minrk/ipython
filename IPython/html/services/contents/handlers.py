"""Tornado handlers for the contents web service.
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

import json

from tornado import web

from IPython.html.utils import url_path_join, url_escape
from IPython.utils.jsonutil import date_default

from IPython.html.base.handlers import IPythonHandler, json_errors

#-----------------------------------------------------------------------------
# Notebook web service handlers
#-----------------------------------------------------------------------------

class ContentsHandler(IPythonHandler):

    SUPPORTED_METHODS = (u'GET', u'PUT', u'PATCH', u'POST', u'DELETE')

    def _finish_model(self, model, location=True):
        """Finish a JSON request with a model, setting relevant headers, etc."""
        if location:
            location = self.notebook_location(model['name'], model['path'])
            self.set_header('Location', location)
        self.set_header('Last-Modified', model['last_modified'])
        self.finish(json.dumps(model, default=date_default))
    
    @web.authenticated
    @json_errors
    def get(self, path=''):
        """Get the contents of a file or directory
        """
        fm = self.file_manager
        contents = fm.get_contents(path)
        self.finish(json.dumps(contents, default=date_default, indent=1))

    @web.authenticated
    @json_errors
    def patch(self, path=''):
        """PATCH renames a notebook without re-uploading content."""
        fm = self.file_manager
        model = self.get_json_body()
        if model is None:
            raise web.HTTPError(400, u'JSON body missing')
        model = fm.rename_file(path, model['path'])
        self._finish_model(model)
    
    def _copy_notebook(self, copy_from, path, copy_to=None):
        """Copy a notebook in path, optionally specifying the new name.
        
        Only support copying within the same directory.
        """
        self.log.info(u"Copying notebook from %s/%s to %s/%s",
            path, copy_from,
            path, copy_to or '',
        )
        model = self.notebook_manager.copy_notebook(copy_from, copy_to, path)
        self.set_status(201)
        self._finish_model(model)
    
    def _upload_notebook(self, model, path, name=None):
        """Upload a notebook
        
        If name specified, create it in path/name.
        """
        self.log.info(u"Uploading notebook to %s/%s", path, name or '')
        if name:
            model['name'] = name
        
        model = self.notebook_manager.create_notebook_model(model, path)
        self.set_status(201)
        self._finish_model(model)
    
    def _create_empty_notebook(self, path, name=None):
        """Create an empty notebook in path
        
        If name specified, create it in path/name.
        """
        self.log.info(u"Creating new notebook in %s/%s", path, name or '')
        model = {}
        if name:
            model['name'] = name
        model = self.notebook_manager.create_notebook_model(model, path=path)
        self.set_status(201)
        self._finish_model(model)
    
    def _save_notebook(self, model, path, name):
        """Save an existing notebook."""
        self.log.info(u"Saving notebook at %s/%s", path, name)
        model = self.notebook_manager.save_notebook_model(model, name, path)
        if model['path'] != path.strip('/') or model['name'] != name:
            # a rename happened, set Location header
            location = True
        else:
            location = False
        self._finish_model(model, location)
    
    @web.authenticated
    @json_errors
    def post(self, path='', name=None):
        """Create a new notebook in the specified path.
        
        POST creates new notebooks. The server always decides on the notebook name.
        
        POST /api/notebooks/path : new untitled notebook in path
            If content specified, upload a notebook, otherwise start empty.
        POST /api/notebooks/path?copy=OtherNotebook.ipynb : new copy of OtherNotebook in path
        """
        
        if name is not None:
            raise web.HTTPError(400, "Only POST to directories. Use PUT for full names.")
        
        model = self.get_json_body()
        
        if model is not None:
            copy_from = model.get('copy_from')
            if copy_from:
                if model.get('content'):
                    raise web.HTTPError(400, "Can't upload and copy at the same time.")
                self._copy_notebook(copy_from, path)
            else:
                self._upload_notebook(model, path)
        else:
            self._create_empty_notebook(path)

    @web.authenticated
    @json_errors
    def put(self, path='', name=None):
        """Saves the notebook in the location specified by name and path.
        
        PUT /api/notebooks/path/Name.ipynb : Save notebook at path/Name.ipynb
            Notebook structure is specified in `content` key of JSON request body.
            If content is not specified, create a new empty notebook.
        PUT /api/notebooks/path/Name.ipynb?copy=OtherNotebook.ipynb : copy OtherNotebook to Name
        
        POST and PUT are basically the same. The only difference:
        
        - with POST, server always picks the name, with PUT the requester does
        """
        if name is None:
            raise web.HTTPError(400, "Only PUT to full names. Use POST for directories.")
        
        model = self.get_json_body()
        if model:
            copy_from = model.get('copy_from')
            if copy_from:
                if model.get('content'):
                    raise web.HTTPError(400, "Can't upload and copy at the same time.")
                self._copy_notebook(copy_from, path, name)
            elif self.notebook_manager.notebook_exists(name, path):
                self._save_notebook(model, path, name)
            else:
                self._upload_notebook(model, path, name)
        else:
            self._create_empty_notebook(path, name)

    @web.authenticated
    @json_errors
    def delete(self, path=''):
        """delete the notebook in the given notebook path"""
        fm = self.file_manager
        nbm.delete_file(path)
        self.set_status(204)
        self.finish()

#-----------------------------------------------------------------------------
# URL to handler mappings
#-----------------------------------------------------------------------------


_path_regex = r"(?P<path>(?:/.*)*)"

default_handlers = [
    (r"/api/contents%s" % _path_regex, ContentsHandler),
]



