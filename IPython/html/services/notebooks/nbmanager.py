"""A base class notebook manager.

Authors:

* Brian Granger
* Zach Sailer
"""

#-----------------------------------------------------------------------------
#  Copyright (C) 2011  The IPython Development Team
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------

import os
import uuid
from urllib import quote, unquote

from tornado import web

from IPython.config.configurable import LoggingConfigurable
from IPython.nbformat import current
from IPython.utils.traitlets import List, Dict, Unicode, TraitError

#-----------------------------------------------------------------------------
# Classes
#-----------------------------------------------------------------------------

class NotebookManager(LoggingConfigurable):

    # Todo:
    # The notebook_dir attribute is used to mean a couple of different things:
    # 1. Where the notebooks are stored if FileNotebookManager is used.
    # 2. The cwd of the kernel for a project.
    # Right now we use this attribute in a number of different places and
    # we are going to have to disentangle all of this.
    notebook_dir = Unicode(os.getcwdu(), config=True, help="""
            The directory to use for notebooks.
            """)

    def named_notebook_path(self, notebook_path):
        """Given a notebook_path (a URL path to notebook), returns a 
        (name, path) tuple, where name is a .ipynb file, and path is the 
        URL path that describes the file system path for the file. 
        It *always* starts *and* ends with a '/' character.

        Parameters
        ----------
        notebook_path : string
            A path that may be a .ipynb name or a directory

        Returns
        -------
        name : string or None
            the filename of the notebook, or None if not a .ipynb extension
        path : string
            the path to the directory which contains the notebook
        """
        names = notebook_path.split('/')
        names = [n for n in names if n != ''] # remove duplicate splits

        names = [''] + names

        if names and names[-1].endswith(".ipynb"):
            name = names[-1]
            path = "/".join(names[:-1]) + '/'
        else:
            name = None
            path = "/".join(names) + '/'
        return name, path
        
    def get_os_path(self, fname=None, path='/'):
        """Given a notebook name and a server URL path, return its file system
        path.

        Parameters
        ----------
        fname : string
            The name of a notebook file with the .ipynb extension
        path : string
            The relative URL path (with '/' as separator) to the named
            notebook.

        Returns
        -------
        path : string
            A file system path that combines notebook_dir (location where
            server started), the relative path, and the filename with the
            current operating system's url.
        """
        parts = path.split('/')
        parts = [p for p in parts if p != ''] # remove duplicate splits
        if fname is not None:
            parts += [fname]
        path = os.path.join(self.notebook_dir, *parts)
        return path

    def url_encode(self, path):
        """Returns the path with all special characters URL encoded"""
        parts = os.path.split(path)
        return os.path.join(*[quote(p) for p in parts])

    def url_decode(self, path):
        """Returns the URL with special characters decoded"""
        parts = os.path.split(path)
        return os.path.join(*[unquote(p) for p in parts])

    def _notebook_dir_changed(self, name, old, new):
        """do a bit of validation of the notebook dir"""
        if not os.path.isabs(new):
            # If we receive a non-absolute path, make it absolute.
            abs_new = os.path.abspath(new)
            self.notebook_dir = os.path.dirname(abs_new)
            return
        if os.path.exists(new) and not os.path.isdir(new):
            raise TraitError("notebook dir %r is not a directory" % new)
        if not os.path.exists(new):
            self.log.info("Creating notebook dir %s", new)
            try:
                os.mkdir(new)
            except:
                raise TraitError("Couldn't create notebook dir %r" % new)

    def increment_filename(self, name, path='/'):
        """Increment a filename to make it unique.

        This exists for notebook stores that must have unique names. When a notebook
        is created or copied this method constructs a unique filename, typically
        by appending an integer to the name.
        """
        return name

    # Main notebook API

    def list_notebooks(self):
        """Return a list of notebook dicts without content.

        This returns a list of dicts, each of the form::

            dict(notebook_id=notebook,name=name)

        This list of dicts should be sorted by name::

            data = sorted(data, key=lambda item: item['name'])
        """
        raise NotImplementedError('must be implemented in a subclass')

    def get_notebook_model(self, name, path='/', content=True):
        """Get the notebook model with or without content."""
        raise NotImplementedError('must be implemented in a subclass')

    def save_notebook_model(self, model, name, path='/'):
        """Save the notebook model and return the model with no content."""
        raise NotImplementedError('must be implemented in a subclass')

    def update_notebook_model(self, model, name, path='/'):
        """Update the notebook model and return the model with no content."""
        raise NotImplementedError('must be implemented in a subclass')

    def delete_notebook_model(self, name, path):
        """Delete notebook by name and path."""
        raise NotImplementedError('must be implemented in a subclass')

    def create_notebook_model(self, model=None, path='/'):
        """Create a new untitled notebook and return its model with no content."""
        name = self.increment_filename('Untitled', path)
        if model is None:
            model = {}
            metadata = current.new_metadata(name=u'')
            nb = current.new_notebook(metadata=metadata)
            model['content'] = nb
            model['name'] = name
            model['path'] = path
            #model['last_modified'] = ???
        model = self.save_notebook_model(model, name, path)
        return model

    def copy_notebook(self, name, path='/'):
        """Copy an existing notebook and return its new notebook_name."""
        last_mod, nb = self.read_notebook_object(name, path)
        name = name + '-Copy'
        name = self.increment_filename(name, path)
        nb.metadata.name = name
        name = self.write_notebook_object(nb, path = path)
        return name  
    
    # Checkpoint-related
    
    def create_checkpoint(self, name, path='/'):
        """Create a checkpoint of the current state of a notebook
        
        Returns a checkpoint_id for the new checkpoint.
        """
        raise NotImplementedError("must be implemented in a subclass")
    
    def list_checkpoints(self, name, path='/'):
        """Return a list of checkpoints for a given notebook"""
        return []
    
    def restore_checkpoint(self, name, checkpoint_id, path='/'):
        """Restore a notebook from one of its checkpoints"""
        raise NotImplementedError("must be implemented in a subclass")

    def delete_checkpoint(self, name, checkpoint_id, path='/'):
        """delete a checkpoint for a notebook"""
        raise NotImplementedError("must be implemented in a subclass")
    
    def log_info(self):
        self.log.info(self.info_string())
    
    def info_string(self):
        return "Serving notebooks"