from datetime import date

from google.cloud.exceptions import BadRequest
from pandas import DataFrame, Series
from pandas.testing import assert_frame_equal
from pytest import CaptureFixture
from pytest_mock import MockerFixture

from mindlab.magics import MindLabMagics, load_ipython_extension


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

    data = magics.bigquery(line='', cell=query)
    assert_frame_equal(data, expected)

    data = magics.bigquery(line='--info --transpose', cell=query)
    assert_frame_equal(data, expected.transpose())

    assert magics.bigquery(line='data', cell=query) is None
    assert_frame_equal(magics.shell.push.call_args_list[0].args[0]['data'], expected)


def test_bigquery_error(
    capsys: CaptureFixture[str], mocker: MockerFixture, magics: MindLabMagics,
) -> None:
    client = mocker.patch('mindlab.magics.bigquery.Client')
    query = client.return_value.__enter__.return_value.query.return_value
    query.to_dataframe.side_effect = BadRequest('Test')  # type: ignore[no-untyped-call]
    assert magics.bigquery(line='', cell='') is None
    assert capsys.readouterr().err == 'Error: 400 Test\n'


def test_load_extension(mocker: MockerFixture) -> None:
    ipython = mocker.Mock()
    load_ipython_extension(ipython)
    ipython.register_magics.assert_called_with(MindLabMagics)
