from mindlab.plot import Figure, use_mindlab_styles
from mindlab.utils import _missing_extra

try:
    from mindlab.spark import spark_session
except ImportError:
    spark_session = _missing_extra('spark')

__all__ = ['Figure', 'use_mindlab_styles', 'spark_session']
