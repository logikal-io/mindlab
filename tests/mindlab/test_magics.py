import re
from datetime import date
from pathlib import Path

import awswrangler
import redshift_connector
from botocore import exceptions as aws_exceptions
from google.cloud.exceptions import BadRequest
from pandas import DataFrame, Series, read_csv
from pandas.testing import assert_frame_equal
from pytest import CaptureFixture
from pytest_mock import MockerFixture

from mindlab.magics import MindLabMagics, load_ipython_extension
from mindlab.utils import MINDLAB_CONFIG


def test_load_extension(mocker: MockerFixture) -> None:
    ipython = mocker.Mock()
    load_ipython_extension(ipython)
    ipython.register_magics.assert_called_with(MindLabMagics)


def test_mindlab_config(
    capsys: CaptureFixture[str], mocker: MockerFixture, magics: MindLabMagics,
) -> None:
    mocker.patch.dict(MINDLAB_CONFIG, clear=True)
    magics.mindlab_config(line='test_key test_value')  # set
    magics.mindlab_config(line='test_key')  # get
    assert capsys.readouterr().out == 'test_value\n'
    magics.mindlab_config(line='')  # get all
    assert capsys.readouterr().out == "{'test_key': 'test_value'}\n"


def test_bigquery(magics: MindLabMagics) -> None:
    query = (
        'SELECT date, daily_confirmed_cases FROM '
        'bigquery-public-data.covid19_ecdc_eu.covid_19_geographic_distribution_worldwide '
        'WHERE country_territory_code = \'CHE\' AND date >= \'2020-02-26\' ORDER BY date LIMIT 3'
    )
    expected = DataFrame({
        'date': Series([date(2020, 2, 26), date(2020, 2, 27), date(2020, 2, 28)], dtype='dbdate'),
        'daily_confirmed_cases': Series([1, 0, 7], dtype='Int64'),
    })

    actual = magics.bigquery(line='--info', cell=query)
    assert_frame_equal(actual, expected)

    # Test transpose
    actual = magics.bigquery(line='--transpose', cell=query)
    assert_frame_equal(actual, expected.transpose())

    # Test data output
    assert magics.bigquery(line='data', cell=query) is None
    assert_frame_equal(
        magics.shell.push.call_args_list[0].args[0]['data'],  # type: ignore[union-attr]
        expected,
    )


def test_bigquery_error(
    capsys: CaptureFixture[str], mocker: MockerFixture, magics: MindLabMagics,
) -> None:
    client = mocker.patch('mindlab.magics.bigquery.Client')
    query = client.return_value.__enter__.return_value.query.return_value
    query.to_dataframe.side_effect = BadRequest('Test')  # type: ignore[no-untyped-call]
    assert magics.bigquery(line='', cell='') is None
    assert capsys.readouterr().err == 'Error: 400 Test\n'


def test_athena(magics: MindLabMagics) -> None:
    query = 'SELECT * FROM test_mindlab.order_line_items'
    actual = magics.athena(line='--info', cell=query)
    for type_from, type_to in {'int32': 'int64', 'float32': 'float64'}.items():
        actual = actual.astype(
            {column: type_to for column in actual.select_dtypes(type_from).columns}
        )
    expected = read_csv(Path(__file__).parent / 'data/order_line_items.csv')
    expected = expected.astype({'sku': 'string'})
    assert_frame_equal(actual, expected)


def test_athena_error(
    capsys: CaptureFixture[str], mocker: MockerFixture, magics: MindLabMagics,
) -> None:
    read_sql_query = mocker.patch('mindlab.magics.awswrangler.athena.read_sql_query')

    read_sql_query.side_effect = aws_exceptions.UnauthorizedSSOTokenError
    assert magics.athena(line='', cell='') is None
    assert re.search('Error: .* SSO session .* invalid', capsys.readouterr().err)

    read_sql_query.side_effect = awswrangler.exceptions.QueryFailed('Test')
    assert magics.athena(line='', cell='') is None
    assert re.match('Error: Test', capsys.readouterr().err)


def test_redshift(mocker: MockerFixture, magics: MindLabMagics) -> None:
    query = 'SELECT * FROM test_mindlab.order_line_items'
    # Note: we don't run a Redshift cluster at the moment, so we will mock the response
    # - This should be replaced with a proper integration test once there is a test cluster to use
    # - The appropriate Glue Data Catalog connection should also be added to pyproject.toml then
    expected = read_csv(Path(__file__).parent / 'data/order_line_items.csv')
    mocker.patch('mindlab.magics.awswrangler.redshift.connect')
    read_sql_query = mocker.patch('mindlab.magics.awswrangler.redshift.read_sql_query')
    read_sql_query.return_value = expected
    actual = magics.redshift(line='--info --connection test', cell=query)
    assert_frame_equal(actual, expected)


def test_redshift_error(
    capsys: CaptureFixture[str], mocker: MockerFixture, magics: MindLabMagics,
) -> None:
    mocker.patch('mindlab.magics.awswrangler.redshift.connect')
    read_sql_query = mocker.patch('mindlab.magics.awswrangler.redshift.read_sql_query')

    read_sql_query.side_effect = aws_exceptions.UnauthorizedSSOTokenError
    assert magics.redshift(line='--connection test', cell='') is None
    assert re.search('Error: .* SSO session .* invalid', capsys.readouterr().err)

    read_sql_query.side_effect = redshift_connector.error.Error('Test')
    assert magics.redshift(line='--connection test', cell='') is None
    assert re.match('Error: Test', capsys.readouterr().err)
