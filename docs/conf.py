import sys
from importlib.metadata import version as pkg_version

extensions = [
    'sphinx.ext.autosectionlabel',
    'sphinx.ext.autodoc',
    'sphinx.ext.napoleon',
    'sphinx.ext.intersphinx',
]
intersphinx_mapping = {
    'python': (f'https://docs.python.org/{sys.version_info[0]}.{sys.version_info[1]}', None),
    'pandas': (f'https://pandas.pydata.org/pandas-docs/version/{pkg_version("pandas")}', None),
    'matplotlib': (f'https://matplotlib.org/{pkg_version("matplotlib")}/', None),
    'pyspark': (f'https://spark.apache.org/docs/{pkg_version("pyspark")}/api/python/', None),
    'google.auth': (f'https://googleapis.dev/python/google-auth/{pkg_version("google-auth")}/',
                    None),
}
nitpick_ignore = [
    ('py:class', 'pandas.core.groupby.generic.DataFrameGroupBy'),
    ('py:class', 'pyspark.sql.session.SparkSession'),
]
