import os
from pathlib import Path
from typing import Dict, Optional

import pandas
from pandas.testing import assert_frame_equal
from py4j.protocol import Py4JJavaError  # type: ignore[import]
from pyspark.sql import SparkSession
from pytest import mark, param, raises
from pytest_mock import MockerFixture

from mindlab.spark import lib_jar, spark_session


def test_lib_jar(mocker: MockerFixture, tmp_path: Path) -> None:
    mocker.patch.dict(os.environ, {}, clear=True)
    with raises(RuntimeError, match='install Hadoop'):
        lib_jar('test')
    with raises(RuntimeError, match='install "test"'):
        lib_jar('test', hadoop_common_libs=tmp_path)
    for lib_jar_file in ['test-1.jar', 'test-2.jar']:
        (tmp_path / lib_jar_file).touch()
    with raises(RuntimeError, match='Multiple library files found'):
        lib_jar('test', hadoop_common_libs=tmp_path)


@mark.parametrize('org_creds, expected_type', [
    (Path('org_creds'), 'SERVICE_ACCOUNT_JSON_KEYFILE'),
    (None, 'APPLICATION_DEFAULT'),
])
def test_spark_gcs_auth(
    org_creds: Optional[Path],
    expected_type: str,
    mocker: MockerFixture,
) -> None:
    mocker.patch('mindlab.spark.SparkSession')
    mocker.patch('mindlab.spark.SparkContext')
    gateway = mocker.patch('mindlab.spark.launch_gateway')
    gcp_auth = mocker.Mock()
    gcp_auth.organization_credentials_path.return_value = org_creds
    spark_session(gcp_auth=gcp_auth)
    conf = gateway.mock_calls[0].kwargs['conf']
    assert conf.get('spark.hadoop.google.cloud.auth.type') == expected_type


@mark.parametrize('env, expected_provider', [
    ({'AWS_ACCESS_KEY_ID': 'test', 'AWS_SECRET_ACCESS_KEY': 'test'},
     'com.amazonaws.auth.EnvironmentVariableCredentialsProvider'),
    ({}, 'com.amazonaws.auth.profile.ProfileCredentialsProvider'),
])
def test_spark_aws_auth(
    env: Dict[str, str],
    expected_provider: str,
    mocker: MockerFixture,
) -> None:
    mocker.patch.dict(os.environ, env, clear=True)
    mocker.patch('mindlab.spark.SparkSession')
    mocker.patch('mindlab.spark.SparkContext')
    gateway = mocker.patch('mindlab.spark.launch_gateway')
    spark_session()
    conf = gateway.mock_calls[0].kwargs['conf']
    assert conf.get('spark.hadoop.fs.s3a.aws.credentials.provider') == expected_provider


# See https://issues.apache.org/jira/browse/SPARK-38659
@mark.filterwarnings('ignore:unclosed.*socket.*:ResourceWarning')
@mark.parametrize('path', [
    param(
        'gs://test-data-mindlab-logikal-io',
        marks=mark.xfail(
            # See https://github.com/GoogleCloudDataproc/hadoop-connectors/issues/671
            # Note: make sure to delete the `pytest-opts: --no-docs` exception from the
            # test-pull-request workflow once this issue is fixed
            condition='GITHUB_ACTIONS' in os.environ,
            reason='auth bug', raises=Py4JJavaError, strict=True,
        ),
    ),
    's3a://test-data-eu-central-2-mindlab-logikal-io',
])
def test_cloud_read(path: str, spark: SparkSession) -> None:
    data_file = 'order_line_items.csv'
    data_path = f'{path}/{data_file}'
    actual: pandas.DataFrame = spark.read.csv(data_path, inferSchema=True, header=True).toPandas()
    actual = actual.astype({column: 'int64' for column in actual.select_dtypes('int32').columns})
    expected = pandas.read_csv(Path(__file__).parent / 'data' / data_file)
    assert_frame_equal(actual, expected)
