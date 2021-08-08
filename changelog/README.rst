=========
Changelog
=========

.. note::

    This README was adapted from the SunPy changelog readme under the terms of
    the BSD 2-Clause licence.

This directory contains "news fragments" which are short files that contain a
small **ReST**-formatted text that will be added to the next ``CHANGELOG``.

The ``CHANGELOG`` will be read by users, so this description should be aimed at
`bapsflib` users instead of describing internal changes which are only relevant
to the developers.

Make sure to use full sentences with correct case and punctuation, for example:

    Added new HDF5 group mapping class for control device "MyDevice", see
    `~bapsflib._hdf.maps.controls.my_device`.

Please try to use the `cross-referencing mechanisms provided by Sphinx
<https://www.sphinx-doc.org/en/master/usage/restructuredtext/roles.html>`_ .

Each file should be named like ``<PULL REQUEST>.<TYPE>.<ID>.rst``, where ``<PULL
REQUEST>`` is a pull request number and ``<TYPE>`` is one of the types listed
below, and ``<ID>`` is an optional, sequential identifier if there is more
than one entry for a given ``<TYPE>>``.

* ``breaking``: A change which requires users to change code and is not
  backwards compatible. (Not to be used for removal of deprecated features.)
* ``feature``: New user facing features and any new behavior.
* ``bugfix``: Fixes a reported bug.
* ``doc``: Documentation addition or improvement, like rewording an entire
  session or adding missing docs.
* ``removal``: Feature deprecation and/or feature removal.
* ``trivial``: A change which has no user facing effect or is tiny change.
* ``pkg_management``:  A change related to package management, like updates
  to continuous integration (CI).  A change should only be placed in this
  category if it does not fit in any of the other categories.

So for example: ``123.feature.rst``, ``456.bugfix.rst``, ``111.feature.1.rst``,
``111.feature.2.rst``, etc.

**Do NOT try to list all changes into a single changelog.  PRs can have multiple
changes corresponding to multiple types and multiple changes for a single type,
so it's best to place each unique change into its own changelog.**

If you are unsure what pull request type to use, don't hesitate to ask in your
PR.

Note that the ``towncrier`` tool will automatically reflow your text, so it
will work best if you stick to a single paragraph, but multiple sentences and
links are OK and encouraged.  You can install ``towncrier`` and then run
``towncrier --draft`` if you want to get a preview of how your change will look
in the final release notes.
