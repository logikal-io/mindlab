import os
from pathlib import Path
from typing import Dict

import pandas
from pandas.testing import assert_frame_equal
from pyspark.sql import SparkSession
from pytest import mark
from pytest_mock import MockerFixture

from mindlab.spark import spark_session


@mark.parametrize('org_creds, expected_type', [
    (True, 'USER_CREDENTIALS'),
    (False, 'APPLICATION_DEFAULT'),
])
def test_spark_gcs_auth(
    org_creds: bool,
    expected_type: str,
    mocker: MockerFixture,
) -> None:
    mocker.patch('mindlab.spark.SparkSession')
    mocker.patch('mindlab.spark.SparkContext')
    mocker.patch('mindlab.spark.json.loads', return_value={
        'client_id': None,
        'client_secret': None,
        'refresh_token': None,
    })
    gateway = mocker.patch('mindlab.spark.launch_gateway')
    gcp_auth = mocker.Mock()
    if not org_creds:
        gcp_auth.organization_credentials_path.return_value = None
    spark_session(gcp_auth=gcp_auth)
    conf = gateway.mock_calls[0].kwargs['conf']
    assert conf.get('spark.hadoop.google.cloud.auth.type') == expected_type


@mark.parametrize('env, expected_provider', [
    ({'AWS_ACCESS_KEY_ID': 'test', 'AWS_SECRET_ACCESS_KEY': 'test'},
     'com.amazonaws.auth.EnvironmentVariableCredentialsProvider'),
    ({'AWS_ACCESS_KEY_ID': '', 'AWS_SECRET_ACCESS_KEY': ''},
     'com.amazonaws.auth.profile.ProfileCredentialsProvider'),
])
def test_spark_aws_auth(
    env: Dict[str, str],
    expected_provider: str,
    mocker: MockerFixture,
) -> None:
    mocker.patch.dict(os.environ, env)
    mocker.patch('mindlab.spark.SparkSession')
    mocker.patch('mindlab.spark.SparkContext')
    gateway = mocker.patch('mindlab.spark.launch_gateway')
    spark_session()
    conf = gateway.mock_calls[0].kwargs['conf']
    assert conf.get('spark.hadoop.fs.s3a.aws.credentials.provider') == expected_provider


# See https://issues.apache.org/jira/browse/SPARK-38659
@mark.filterwarnings('ignore:unclosed.*socket.*:ResourceWarning')
@mark.parametrize('data_path', [
    'gs://test-data-mindlab-logikal-io/order_line_items.csv',
    's3://test-data-eu-central-1-mindlab-logikal-io/order_line_items/data.csv',
])
def test_cloud_read(data_path: str, spark: SparkSession) -> None:
    actual: pandas.DataFrame = spark.read.csv(data_path, inferSchema=True, header=True).toPandas()
    actual = actual.astype({column: 'int64' for column in actual.select_dtypes('int32').columns})
    expected = pandas.read_csv(Path(__file__).parent / 'data/order_line_items.csv')
    assert_frame_equal(actual, expected)
