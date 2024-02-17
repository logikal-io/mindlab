.. Documentation structure
.. toctree::
    :caption: Documentation
    :hidden:

    self
    auth
    plotting
    magics
    spark
    development
    license

.. toctree::
    :caption: External Links
    :hidden:

    Release Notes <https://github.com/logikal-io/mindlab/releases>
    Issue Tracker <https://github.com/logikal-io/mindlab/issues>
    Source Code <https://github.com/logikal-io/mindlab>

.. Install kernel configuration
.. jupyter-execute::
    :hide-code:
    :hide-output:

    from mindlab.lab import install_config

    install_config()

.. Start a new kernel
.. jupyter-kernel:: python3

Getting Started
===============
.. contents::
    :local:
    :depth: 1

Installation
------------
The MindLab is the ultimate toolbox for high quality, efficient data science work. You can simply
install it from `pypi <https://pypi.org/project/mindlab/>`_:

.. code-block:: shell

    pip install mindlab

Plotting
--------
Drawing professional plots is now trivial:

.. jupyter-execute::

    from mindlab import Figure, mock_data

    figure = Figure(title='Mock Stock Prices', xtics='month', ylabel='Stock Price [USD]')
    figure.line(mock_data.stock_prices())

The :class:`mindlab.Figure` class provides a convenient but powerful interface to `Matplotlib
<https://matplotlib.org/>`_ figures. No more fiddling with legends and tick locators, and no more
plots with tiny fonts or unreadable tick labels! Make sure to check out the
:ref:`plotting:Plotting` section of the documentation for a complete reference.

Jupyter
-------
You can install MindLab with `Jupyter <https://jupyter.org/>`_ support too:

.. code-block:: shell

    pip install mindlab[jupyter]

This provides the ``lab`` command which starts a pre-configured JupyterLab session with sensible
defaults and auto-completion:

.. code-block:: console

    $ lab
    ...
    [I ... ServerApp] Jupyter Server is running at:
    [I ... ServerApp] http://localhost:8888/lab?token={token}

Executing queries against various data sources is extremely simple using the provided :ref:`MindLab
Magics <magics:Magics>` (after :ref:`authentication <auth:Authentication>`):

.. jupyter-execute::

    %%bigquery
    SELECT title, `by` AS author, DATETIME(`timestamp`) AS posted_at, score
    FROM bigquery-public-data.hacker_news.full
    WHERE type = 'story'
    ORDER BY timestamp NULLS LAST
    LIMIT 3

Of course, true power lies in combining the magics with MindLab's plotting capabilities:

.. jupyter-execute::

    %%bigquery scores
    SELECT score, COUNT(*) AS frequency, EXTRACT(YEAR FROM `timestamp`) as `year`
    FROM bigquery-public-data.hacker_news.full
    WHERE type = 'story' AND score IS NOT NULL
          AND `timestamp` >= TIMESTAMP '2007-01-01' AND `timestamp` < TIMESTAMP '2015-01-01'
    GROUP BY score, `year`

.. jupyter-execute::

    figure = Figure(
        title='Hacker News Score Distribution',
        xlabel='Score', ylabel='Frequency', xscale='log', yscale='log',
    )
    figure.scatter(scores.groupby('year'), cmap='viridis', alpha=0.5)

Spark
-----
MindLab also provides `Spark <https://spark.apache.org/docs/latest/>`_ support (via `PySpark
<https://spark.apache.org/docs/latest/api/python/>`_) when installed with the ``spark`` extra:

.. code-block:: shell

    pip install mindlab[spark]

This allows you to execute Spark queries locally, even if your data set is located in cloud
storage:

.. jupyter-execute::
    :hide-output:

    from mindlab import spark_session

    with spark_session() as spark:
        path = 'gs://test-data-mindlab-logikal-io/order_line_items.csv'
        data = spark.read.csv(path, inferSchema=True, header=True).toPandas()

.. jupyter-execute::

    data.head()

For more information check out the :ref:`spark:Spark` section of the documentation.
