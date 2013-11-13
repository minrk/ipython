"""Abstract base classes for kernel manager and channels."""

#-----------------------------------------------------------------------------
#  Copyright (C) 2013  The IPython Development Team
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------

import abc

from IPython.utils.py3compat import with_metaclass


#-----------------------------------------------------------------------------
# Main kernel manager class
#-----------------------------------------------------------------------------

class KernelManagerABC(with_metaclass(abc.ABCMeta, object)):
    """KernelManager ABC.

    The docstrings for this class can be found in the base implementation:

    `IPython.kernel.kernelmanager.KernelManager`
    """

    @abc.abstractproperty
    def kernel(self):
        pass

    #--------------------------------------------------------------------------
    # Kernel management
    #--------------------------------------------------------------------------

    @abc.abstractmethod
    def start_kernel(self, **kw):
        pass

    @abc.abstractmethod
    def shutdown_kernel(self, now=False, restart=False):
        pass

    @abc.abstractmethod
    def restart_kernel(self, now=False, **kw):
        pass

    @abc.abstractproperty
    def has_kernel(self):
        pass

    @abc.abstractmethod
    def interrupt_kernel(self):
        pass

    @abc.abstractmethod
    def signal_kernel(self, signum):
        pass

    @abc.abstractmethod
    def is_alive(self):
        pass
