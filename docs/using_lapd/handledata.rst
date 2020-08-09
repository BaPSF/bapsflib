:orphan:

With a :class:`numpy.recarray`, accessing a data field can be done via
a dictionary lookup or as an access to a member of the array.  For
example, accessing the shot number array can be like

    >>> data['shotnum']
    Out[0]: array([   1,    2,    3, ...], dtype=uint32)

or

    >>> data.shotnum
    Out[0]: Out[0]: array([   1,    2,    3, ...], dtype=uint32)

Fields :code:`'signal'` and :code:`'xyz'` can be accessed the same way.


    >>> import numpy as np
    >>> sn = 10
    >>> sni = np.where(data['shotnum'] == sn)
    >>> sni
    Out: (array([9]),)
    >>> data['signal'][sni].shape
    Out: (1, 12288)

    >>> sni = np.where(data['shotnum'] == sn)[0].squeeze()
    >>> sni
    Out: array(9)
    >>> data['signal'][sni].shape
    Out: (12288,)