Spark
=====
.. note:: You need to install and configure `Hadoop
    <https://hadoop.apache.org/docs/stable/hadoop-project-dist/hadoop-common/SingleCluster.html>`_,
    the `Google Cloud Storage connector
    <https://github.com/GoogleCloudDataproc/hadoop-connectors/blob/master/gcs>`_ and the
    `Hadoop-AWS module
    <https://hadoop.apache.org/docs/current3/hadoop-aws/tools/hadoop-aws/index.html>`_ for this
    feature to work properly.

.. note:: You must be :ref:`authenticated <auth:Authentication>` towards the appropriate cloud
    provider for the cloud storage connectors to function.

You can easily create Spark sessions that are automatically configured and authenticated towards
the appropriate cloud storage providers using :func:`mindlab.spark_session`.

.. autofunction:: mindlab.spark_session
