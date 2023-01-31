import subprocess
from os import environ
from pathlib import Path
from typing import List, Optional

from pyspark.conf import SparkConf
from pyspark.context import SparkContext
from pyspark.java_gateway import launch_gateway
from pyspark.sql import SparkSession
from stormware.amazon.auth import AWSAuth
from stormware.google.auth import GCPAuth

from mindlab.pyproject import MINDLAB_CONFIG


def lib_jar(lib: str, hadoop_common_libs: Optional[Path] = None) -> Path:
    hadoop_common_libs_env = 'HADOOP_COMMON_LIBS_JAR_DIR'
    if not hadoop_common_libs and hadoop_common_libs_env not in environ:
        raise RuntimeError(f'You must install Hadoop and set {hadoop_common_libs_env}')
    hadoop_common_libs = hadoop_common_libs or Path(environ[hadoop_common_libs_env])

    lib_files = list(hadoop_common_libs.glob(f'{lib}-*.jar'))
    if not lib_files:
        raise RuntimeError(f'You must install "{lib}" under "{hadoop_common_libs}"')
    if len(lib_files) > 1:
        raise RuntimeError(f'Multiple library files found: {lib_files}')

    return lib_files[0]


def spark_session(
    organization: Optional[str] = None,
    aws_auth: Optional[AWSAuth] = None,
    gcp_auth: Optional[GCPAuth] = None,
) -> SparkSession:
    """
    Create a new Spark session.

    Returns:
        A pre-configured :class:`SparkSession <pyspark.sql.SparkSession>` instance.

    """
    organization = organization or MINDLAB_CONFIG.get('organization')
    aws_auth = aws_auth or AWSAuth()
    gcp_auth = gcp_auth or GCPAuth()

    conf = SparkConf()
    extra_classes: List[Path] = []

    # GCS connector class
    extra_classes.append(lib_jar('gcs-connector-hadoop3'))
    conf.set('spark.hadoop.fs.AbstractFileSystem.gs.impl',
             'com.google.cloud.hadoop.fs.gcs.GoogleHadoopFS')

    # GCS connector authentication
    # (https://github.com/GoogleCloudDataproc/hadoop-connectors/blob/master/gcs/CONFIGURATION.md)
    if keyfile := gcp_auth.organization_credentials_path(organization):
        conf.set('spark.hadoop.google.cloud.auth.type', 'SERVICE_ACCOUNT_JSON_KEYFILE')
        conf.set('spark.hadoop.google.cloud.auth.service.account.enable', 'true')
        conf.set('spark.hadoop.google.cloud.auth.service.account.json.keyfile', str(keyfile))
    else:
        conf.set('spark.hadoop.google.cloud.auth.type', 'APPLICATION_DEFAULT')

    # AWS S3 connector class
    extra_classes.append(lib_jar('hadoop-aws'))
    extra_classes.append(lib_jar('aws-java-sdk-bundle'))
    conf.set('spark.hadoop.fs.s3a.committer.name', 'directory')
    conf.set('spark.sql.sources.commitProtocolClass',
             'org.apache.spark.internal.io.cloud.PathOutputCommitProtocol')
    conf.set('spark.sql.parquet.output.committer.class',
             'org.apache.spark.internal.io.cloud.BindingParquetOutputCommitter')

    # AWS S3 connector authentication
    if environ.get('AWS_ACCESS_KEY_ID') and environ.get('AWS_SECRET_ACCESS_KEY'):
        conf.set('spark.hadoop.fs.s3a.aws.credentials.provider',
                 'com.amazonaws.auth.EnvironmentVariableCredentialsProvider')
    else:
        environ['AWS_PROFILE'] = aws_auth.organization_id(organization)
        conf.set('spark.hadoop.fs.s3a.aws.credentials.provider',
                 'com.amazonaws.auth.profile.ProfileCredentialsProvider')

    # Recommended settings (see https://spark.apache.org/docs/latest/cloud-integration.html)
    conf.set('spark.hadoop.mapreduce.fileoutputcommitter.algorithm.version', '2')
    conf.set('spark.hadoop.parquet.enable.summary-metadata', 'false')
    conf.set('spark.sql.parquet.mergeSchema', 'false')
    conf.set('spark.sql.parquet.filterPushdown', 'true')
    conf.set('spark.sql.hive.metastorePartitionPruning', 'true')
    conf.set('spark.sql.orc.filterPushdown', 'true')
    conf.set('spark.sql.orc.splits.include.file.footer', 'true')
    conf.set('spark.sql.orc.cache.stripe.details.size', '10000')
    conf.set('spark.sql.hive.metastorePartitionPruning', 'true')

    # Extra classes
    conf.set('spark.driver.extraClassPath', ':'.join(str(path) for path in extra_classes))

    # Redirect Spark standard error to standard output to avoid log messages breaking things
    popen_kwargs = {'stderr': subprocess.STDOUT}
    gateway = launch_gateway(conf=conf, popen_kwargs=popen_kwargs)  # type: ignore[no-untyped-call]
    session = SparkSession(SparkContext(gateway=gateway)).builder.getOrCreate()

    # Suppress unnecessary logs
    log4j = session._jvm.org.apache.log4j  # type: ignore # pylint: disable=protected-access
    log_levels = {
        'org.apache.hadoop.metrics2.impl.MetricsConfig': log4j.Level.ERROR,
        # See https://github.com/aws/aws-sdk-java/issues/1707
        'com.amazonaws.auth.profile.internal.BasicProfileConfigLoader': log4j.Level.ERROR,
    }
    for logger, log_level in log_levels.items():
        log4j.LogManager.getLogger(logger).setLevel(log_level)

    return session
