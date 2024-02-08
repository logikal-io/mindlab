import json
import subprocess
from os import environ
from typing import Optional

from pyspark.conf import SparkConf
from pyspark.context import SparkContext
from pyspark.java_gateway import launch_gateway
from pyspark.sql import SparkSession
from stormware.amazon.auth import AWSAuth
from stormware.google.auth import GCPAuth

from mindlab.utils import get_config


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
    organization = get_config('organization', organization)
    aws_auth = aws_auth or AWSAuth()
    gcp_auth = gcp_auth or GCPAuth()

    conf = SparkConf()

    # GCS connector authentication
    # (https://github.com/GoogleCloudDataproc/hadoop-connectors/blob/master/gcs/CONFIGURATION.md)
    if keyfile := gcp_auth.organization_credentials_path(organization):
        credentials = json.loads(keyfile.read_text())
        conf.set('spark.hadoop.google.cloud.auth.type', 'USER_CREDENTIALS')
        conf.set('spark.hadoop.google.cloud.auth.client.id', credentials['client_id'])
        conf.set('spark.hadoop.google.cloud.auth.client.secret', credentials['client_secret'])
        conf.set('spark.hadoop.google.cloud.auth.refresh.token', credentials['refresh_token'])
    else:
        conf.set('spark.hadoop.google.cloud.auth.type', 'APPLICATION_DEFAULT')

    # AWS S3 connector class
    # (https://hadoop.apache.org/docs/stable/hadoop-aws/tools/hadoop-aws/index.html)
    conf.set('spark.hadoop.fs.s3.impl', 'org.apache.hadoop.fs.s3a.S3AFileSystem')
    # See https://spark.apache.org/docs/latest/cloud-integration.html#hadoop-s3a-committers
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
        environ.setdefault('AWS_PROFILE', aws_auth.profile(organization) or '')
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
