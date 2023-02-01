Magics
======
.. A ``.. contents::`` directive would be useful, sadly, it does not show the auto-generated magics
.. (see https://github.com/sphinx-doc/sphinx/issues/11162)

.. note:: You must be :ref:`authenticated <auth:Authentication>` towards the appropriate cloud
    provider for the magics to work.

.. note:: Most magics fall back to using configuration values in the ``tool.mindlab`` section of
    the ``pyproject.toml`` file or set via environment variables when an argument has not been
    provided (e.g. for the ``organization`` value). Additionally, you can also specify a
    configuration option that applies to a single magic method by prefixing it with the name of the
    magic (e.g. ``athena_organization`` or ``athena_region``).

.. tip:: You can list all available magics by typing ``%lsmagic`` into a cell. You can also
    display the documentation of any magic by prefixing it with a question mark (like
    ``?bigquery``).

.. automagics:: mindlab.magics.MindLabMagics
