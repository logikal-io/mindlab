Authentication
==============
Note that you must be authenticated towards the appropriate cloud provider for :ref:`magics:Magics`
and the :ref:`spark:Spark` cloud storage connectors to function properly.

Google Cloud Storage
--------------------
The default authentication mechanism first looks for a set of credentials in the
``$XDG_CONFIG_HOME/gcloud/credentials/{organization_id}.json`` file, where ``organization_id`` is
derived from the ``organization`` value in the ``tool.mindlab`` section of the ``pyproject.toml``
file. Note that you can also use your application default credentials by copying it to this
location or by creating a symlink to it. If the above-mentioned file does not exist, we look for
the application default credentials.

A default Google Cloud project can be set under the ``project`` key in the ``tool.mindlab`` section
of the ``pyproject.toml`` file.

.. autoclass:: mindlab.auth.GCPAuth

Amazon Web Services
-------------------
We look for the credentials of the ``organization_id`` named profile, where ``organization_id`` is
derived the same way as it is for the Google Cloud Storage authentication.

.. autoclass:: mindlab.auth.AWSAuth
