Authentication
==============
.. note:: You must be authenticated towards the appropriate cloud provider for :ref:`magics:Magics`
    and the :ref:`spark:Spark` cloud storage connectors to function properly.

MindLab uses `Stormware <https://docs.logikal.io/stormware/latest/>`_ for authentication, therefore
we can simply follow the steps for the appropriate platforms in the :doc:`Authentication section
<stormware:auth>` of the Stormware documentation.

Configuration
-------------
Note that the authentication configuration can be also added to the ``[tool.mindlab]`` section of
the project's ``pyproject.toml`` file (instead of or in addition to the ``[tool.stormware]``
section) as follows:

.. code-block:: toml

    [tool.mindlab]
    organization = 'example.com'
    project = 'my-project'

When a configuration option is set in both the ``mindlab`` and ``stormware`` sections, the value in
the ``mindlab`` section takes precedence.
