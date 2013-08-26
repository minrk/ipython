"""Tornado handlers for the notebooks web service.

Authors:

* Brian Granger
"""

#-----------------------------------------------------------------------------
#  Copyright (C) 2008-2011  The IPython Development Team
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------

from tornado import web

from zmq.utils import jsonapi

from IPython.utils.jsonutil import date_default

from ...base.handlers import IPythonHandler

#-----------------------------------------------------------------------------
# Notebook web service handlers
#-----------------------------------------------------------------------------


class NotebookHandler(IPythonHandler):

    SUPPORTED_METHODS = ('GET', 'PUT', 'PATCH', 'POST','DELETE')

    def get_json_body(self):
        if not self.request.body:
            return None
        # Do we need to call body.decode('utf-8') here?
        body = self.request.body.strip().decode('utf-8')
        try:
            json = jsonapi.loads(body)
        except:
            raise web.HTTPError(400, 'Invalid JSON in body of request')
        return json

    @web.authenticated
    def get(self, notebook_path):
        """get checks if a notebook is not named, an returns a list of notebooks
        in the notebook path given. If a name is given, return 
        the notebook representation"""
        nbm = self.notebook_manager
        # path will have leading and trailing slashes, such as '/foo/bar/'
        name, path = nbm.named_notebook_path(notebook_path)
        
        # Check to see if a notebook name was given
        if name is None:
            # List notebooks in 'notebook_path'
            notebooks = nbm.list_notebooks(path)
            self.finish(jsonapi.dumps(notebooks))
        else:
            # get and return notebook representation
            model = nbm.get_notebook_model(name, path)
            self.set_header('Last-Modified', model['last_modified'])
            self.finish(jsonapi.dumps(model))

    @web.authenticated
    def patch(self, notebook_path):
        """patch is currently used strictly for notebook renaming.
        Changes the notebook name to the name given in data."""
        nbm = self.notebook_manager
        # path will have leading and trailing slashes, such as '/foo/bar/'
        name, path = nbm.named_notebook_path(notebook_path)
        if name is None:
            raise web.HTTPError(400, 'Notebook name missing.')
        model = self.get_json_body()
        if model is None:
            raise web.HTTPError(400, 'JSON body missing')
        model = nbm.update_notebook_model(model, name, path)
        self.finish(jsonapi.dumps(model))

    @web.authenticated
    def post(self, notebook_path):
        """Create a new notebook in the location given by 'notebook_path'."""
        nbm = self.notebook_manager
        # path will have leading and trailing slashes, such as '/foo/bar/'
        name, path = nbm.named_notebook_path(notebook_path)
        model = self.get_json_body()
        if name is not None:
            raise web.HTTPError(400, 'No name can be provided when POSTing a new notebook.')
        model = nbm.create_notebook_model(model, path)
        location = nbm.notebook_dir + model['path'] + model['name']
        self.set_header('Location', location)
        self.finish(jsonapi.dumps(model))

    @web.authenticated
    def put(self, notebook_path):
        """saves the notebook in the location given by 'notebook_path'."""
        nbm = self.notebook_manager
        # path will have leading and trailing slashes, such as '/foo/bar/'
        name, path = nbm.named_notebook_path(notebook_path)
        model = self.get_json_body()
        if model is None:
            raise web.HTTPError(400, 'JSON data missing')
        nbm.save_notebook_model(model, name, path)
        self.finish(jsonapi.dumps(model))

    @web.authenticated
    def delete(self, notebook_path):
        """delete the notebook in the given notebook path"""
        nbm = self.notebook_manager
        # path will have leading and trailing slashes, such as '/foo/bar/'
        name, path = nbm.named_notebook_path(notebook_path)
        nbm.delete_notebook_model(name, path)
        self.set_status(204)
        self.finish()


class NotebookCheckpointsHandler(IPythonHandler):
    
    SUPPORTED_METHODS = ('GET', 'POST')
    
    @web.authenticated
    def get(self, notebook_path):
        """get lists checkpoints for a notebook"""
        nbm = self.notebook_manager
        # path will have leading and trailing slashes, such as '/foo/bar/'
        name, path = nbm.named_notebook_path(notebook_path)
        checkpoints = nbm.list_checkpoints(name, path)
        data = jsonapi.dumps(checkpoints, default=date_default)
        self.finish(data)
    
    @web.authenticated
    def post(self, notebook_path):
        """post creates a new checkpoint"""
        nbm = self.notebook_manager
        name, path = nbm.named_notebook_path(notebook_path)
        # path will have leading and trailing slashes, such as '/foo/bar/'
        checkpoint = nbm.create_checkpoint(name, path)
        data = jsonapi.dumps(checkpoint, default=date_default)
        if path == None:
            self.set_header('Location', '{0}notebooks/{1}/checkpoints/{2}'.format(
                self.base_project_url, name, checkpoint['checkpoint_id']
                ))
        else:
            self.set_header('Location', '{0}notebooks/{1}/{2}/checkpoints/{3}'.format(
                self.base_project_url, path, name, checkpoint['checkpoint_id']
                ))
        self.finish(data)


class ModifyNotebookCheckpointsHandler(IPythonHandler):
    
    SUPPORTED_METHODS = ('POST', 'DELETE')
    
    @web.authenticated
    def post(self, notebook_path, checkpoint_id):
        """post restores a notebook from a checkpoint"""
        nbm = self.notebook_manager
        # path will have leading and trailing slashes, such as '/foo/bar/'
        name, path = nbm.named_notebook_path(notebook_path)
        nbm.restore_checkpoint(name, checkpoint_id, path)
        self.set_status(204)
        self.finish()
    
    @web.authenticated
    def delete(self, notebook_path, checkpoint_id):
        """delete clears a checkpoint for a given notebook"""
        nbm = self.notebook_manager
        # path will have leading and trailing slashes, such as '/foo/bar/'
        name, path = nbm.named_notebook_path(notebook_path)
        nbm.delete_checkpoint(name, checkpoint_id, path)
        self.set_status(204)
        self.finish()
        
#-----------------------------------------------------------------------------
# URL to handler mappings
#-----------------------------------------------------------------------------


_notebook_path_regex = r"(?P<notebook_path>.*)"
_checkpoint_id_regex = r"(?P<checkpoint_id>[\w-]+)"

default_handlers = [
    (r"api/notebooks/%s/checkpoints" % _notebook_path_regex, NotebookCheckpointsHandler),
    (r"api/notebooks/%s/checkpoints/%s" % (_notebook_path_regex, _checkpoint_id_regex),
        ModifyNotebookCheckpointsHandler),
    (r"api/notebooks%s" % _notebook_path_regex, NotebookHandler),
]




