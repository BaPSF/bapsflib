# This file is part of the bapsflib package, a Python toolkit for the
# BaPSF group at UCLA.
#
# http://plasma.physics.ucla.edu/
#
# Copyright 2017-2019 Erik T. Everson and contributors
#
# License: Standard 3-clause BSD; see "LICENSES/LICENSE.txt" for full
#   license terms and contributor agreement.
#
"""
Decorators for the :mod:`bapsflib` package.
"""
__all__ = ["with_bf", "with_lapdf"]

import functools
import inspect

from typing import Union


def with_bf(
    wfunc=None,
    *,
    filename: Union[str, None] = None,
    control_path: Union[str, None] = None,
    digitizer_path: Union[str, None] = None,
    msi_path: Union[str, None] = None
):
    """
    Context decorator for managing the opening and closing BaPSF HDF5
    Files (:class:`bapsflib._hdf.utils.file.File`).  An instance of the
    BaPSF HDF5 file is injected into the decorated function at the end of
    the positional arguments.  The decorator is primarily designed for use
    on test methods, but can also be used as a function decorator.

    :param wfunc: function or method to be wrapped
    :param filename: name of the BaPSF HDF5 file
    :param control_path: internal HDF5 path for control devices
    :param digitizer_path: internal HDF5 path for digitizers
    :param msi_path: internal HDF5 path for MSI devices

    :example:
        The HDF5 file parameters (:data:`filename`, :data:`control_path`,
        :data:`digitizer_path`, and :data:`msi_path`) can be passed to the
        decorator in three ways (listed by predominance):

        #. The wrapped function arguments.
        #. If the wrapped function is a method, then through appropriately
           named :data:`self` attributes.
        #. The decorator keywords.

        **Defined with wrapped function arguments**::

            >>> # as function keywords
            >>> @with_bf
            ... def foo(bf, **kwargs):
            ...     # * bf will be the HDF5 file object
            ...     # * do whatever is needed with bf and @with_bf will close
            ...     #   the file at the end
            ...     return bf.filename
            >>> foo(filename='test.hdf5', control_path='Raw data + config',
            ...     digitizer_path='Raw data + config', msi_path='MSI')
            'test.hdf5'
            >>>
            >>> # as a function argument
            >>> @with_bf
            ... def foo(filename, bf, **kwargs):
            ...     # use bf
            ...     return bf.filename
            ... foo('test.hdf5')
            'test.hdf5'

        **Defined with wrapped method attributes**::

            >>> # use `self` to pass file settings
            >>> class BehaveOnFile:
            ...     def __init__(self):
            ...         super().__init__()
            ...         self.filename = 'test.hdf5'
            ...         self.control_path = 'Raw data + config'
            ...         self.digitizer_path = 'Raw data + config'
            ...         self.msi_path = 'MSI'
            ...
            ...     @with_bf
            ...     def foo(self, bf, **kwargs):
            ...         return bf.filename
            >>> a = BehaveOnFile()
            >>> a.foo()
            'test.hdf5'
            >>>
            >>> # but keywords will still take precedence
            >>> a.foo(filename='test_2.hdf5')
            'test_2.hdf5'

        **Defined with decorator keywords**:

            >>> # as function keywords
            >>> @with_bf(filename='test.hdf5',
            ...          control_path='Raw data + config',
            ...          digitizer_path='Raw data +config',
            ...          msi_path='MSI')
            ... def foo(bf, **kwargs):
            ...     return bf.filename
            >>> foo()
            'test.hdf5'
            >>>
            >>> # function keywords will still take precedence
            >>> foo(filename='test_2.hdf5')
            'test_2.hdf5'
    """
    # How to pass in file settings (listed in priority):
    # 1. function keywords
    # 2. self attributes
    # 3. decorator keywords
    #
    # define decorator set file settings
    settings = {
        "filename": filename,
        "control_path": control_path,
        "digitizer_path": digitizer_path,
        "msi_path": msi_path,
    }

    def decorator(func):
        # to avoid cyclical imports
        from bapsflib._hdf.utils.file import File

        @functools.wraps(func)
        def wrapper(*args, **kwargs):

            # is decorated function a method
            # - this relies on the convention that a method's first argument
            #   is self
            # - inspect.ismethod only works on bound methods, so it does
            #   not work at time of decorating in class
            #
            func_sig = inspect.signature(func)
            bound_args = func_sig.bind_partial(*args, **kwargs)
            self = None  # type: Union[None, object]
            if "self" in func_sig.parameters:
                try:
                    if hasattr(args[0], func.__name__):  # pragma: no branch
                        # arg[0] is an object with method of the same name
                        # as the decorated function
                        self = args[0]
                except IndexError:  # pragma: no cover
                    pass

            # update settings
            fsettings = settings.copy()
            for name in fsettings.keys():
                if name in bound_args.arguments:
                    # look for setting in passed arguments
                    if bound_args.arguments[name] is None:
                        continue
                    fsettings[name] = bound_args.arguments[name]
                elif name in bound_args.kwargs:
                    # look for setting in passed kwargs (if not in arguments)
                    if bound_args.kwargs[name] is None:
                        continue
                    fsettings[name] = bound_args.kwargs[name]
                elif self is not None:
                    # if wrapped function is a method, and setting not passed
                    # as function argument then look to self
                    try:
                        if self.__getattribute__(name) is None:
                            continue
                        fsettings[name] = self.__getattribute__(name)
                    except KeyError:  # pragma: no cover
                        pass
            for name in list(fsettings.keys()):
                if fsettings[name] is None:
                    if name == "filename":
                        raise ValueError("No valid file name specified.")
                    else:
                        del fsettings[name]
            fname = fsettings.pop("filename")

            # run function with in if statement
            with File(fname, **fsettings) as bf:
                args += (bf,)
                return func(*args, **kwargs)

        return wrapper

    if wfunc is not None:
        # This is a decorator call without arguments, e.g. @with_bf
        return decorator(wfunc)
    else:
        # This is a factory call, e.g. @with_bf()
        return decorator


def with_lapdf(wfunc=None, *, filename: Union[str, None] = None):
    """
    Context decorator for managing the opening and closing LaPD HDF5
    Files (:class:`bapsflib.lapd._hdf.file.File`).  An instance of the
    LaPD HDF5 file is injected into the decorated function at the end of
    the positional arguments.  The decorator is primarily designed for use
    on test methods, but can also be used as a function decorator.

    :param wfunc: function or method to be wrapped
    :param filename: name of the BaPSF HDF5 file

    :example:
        The HDF5 :data:`filename` can be passed to the decorator in three
        ways (listed by predominance):

        #. The wrapped function arguments.
        #. If the wrapped function is a method, then through the
           appropriately named :data:`self` attributes.
        #. The decorator keywords.

        **Defined with wrapped function arguments**::

            >>> # as function keywords
            >>> @with_lapdf
            ... def foo(lapdf, **kwargs):
            ...     # * bf will be the HDF5 file object
            ...     # * do whatever is needed with bf and @with_bf will close
            ...     #   the file at the end
            ...     return lapdf.filename
            >>> foo(filename='test.hdf5')
            'test.hdf5'
            >>>
            >>> # as a function argument
            >>> @with_lapdf
            ... def foo(filename, lapdf, **kwargs):
            ...     # use bf
            ...     return lapdf.filename
            ... foo('test.hdf5')
            'test.hdf5'

        **Defined with wrapped method attributes**::

            >>> # use `self` to pass file settings
            >>> class BehaveOnFile:
            ...     def __init__(self):
            ...         super().__init__()
            ...         self.filename = 'test.hdf5'
            ...
            ...     @with_bf
            ...     def foo(self, lapdf, **kwargs):
            ...         return lapdf.filename
            >>> a = BehaveOnFile()
            >>> a.foo()
            'test.hdf5'
            >>>
            >>> # but keywords will still take precedence
            >>> a.foo(filename='test_2.hdf5')
            'test_2.hdf5'

        **Defined with decorator keywords**:

            >>> # as function keywords
            >>> @with_bf(filename='test.hdf5')
            ... def foo(lapdf, **kwargs):
            ...     return lapdf.filename
            >>> foo()
            'test.hdf5'
            >>>
            >>> # function keywords will still take precedence
            >>> foo(filename='test_2.hdf5')
            'test_2.hdf5'
    """
    # How to pass in file settings (listed in priority):
    # 1. function keywords
    # 2. self attributes
    # 3. decorator keywords
    #
    # define decorator set file settings
    settings = {"filename": filename}

    def decorator(func):
        # to avoid cyclical imports
        from bapsflib.lapd._hdf.file import File

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # is decorated function a method
            # - this relies on the convention that a method's first argument
            #   is self
            # - inspect.ismethod only works on bound methods, so it does
            #   not work at time of decorating in class
            #
            func_sig = inspect.signature(func)
            bound_args = func_sig.bind_partial(*args, **kwargs)
            self = None  # type: Union[None, object]
            if "self" in func_sig.parameters:
                try:
                    if hasattr(args[0], func.__name__):  # pragma: no branch
                        self = args[0]
                except IndexError:  # pragma: no cover
                    pass

            # update settings
            fsettings = settings.copy()
            for name in fsettings.keys():
                if name in bound_args.arguments:
                    # look for setting in passed arguments
                    if bound_args.arguments[name] is None:
                        continue
                    fsettings[name] = bound_args.arguments[name]
                elif name in bound_args.kwargs:
                    # look for setting in passed kwargs (if not in arguments)
                    if bound_args.kwargs[name] is None:  # pragma: no cover
                        # currently with_lapdf only takes filename as an
                        # argument, this need to be tested if that changes
                        continue
                    fsettings[name] = bound_args.kwargs[name]
                elif self is not None:
                    # if wrapped function is a method, and setting not passed
                    # as function argument then look to self
                    try:
                        if self.__getattribute__(name) is None:  # pragma: no cover
                            # currently with_lapdf only takes filename as an
                            # argument, this need to be tested if that changes
                            continue
                        fsettings[name] = self.__getattribute__(name)
                    except KeyError:  # pragma: no cover
                        pass
            for name in list(fsettings.keys()):
                if fsettings[name] is None:
                    if name == "filename":
                        raise ValueError("No valid file name specified.")
                    else:  # pragma: no cover
                        del fsettings[name]
            fname = fsettings.pop("filename")

            # run function with in if statement
            with File(fname) as lapdf:
                args += (lapdf,)
                return func(*args, **kwargs)

        return wrapper

    if wfunc is not None:
        # This is a decorator call without arguments, e.g. @with_lapdf
        return decorator(wfunc)
    else:
        # This is a factory call, e.g. @with_lapdf()
        return decorator
