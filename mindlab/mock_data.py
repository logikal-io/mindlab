from datetime import date

import numpy as np
from pandas import DataFrame, concat, date_range
from pandas.core.groupby.generic import DataFrameGroupBy


def stock_prices(  # pylint: disable=too-many-arguments
    companies: int = 3,
    days: int = 180,
    start_date: date = date(2022, 11, 1),
    start_price_mean: float = 100,
    start_price_sd: float = 4,
    increment_mean: float = 0.1,
    increment_sd: float = 1,
    name_prefix: str = 'RND',
    seed: int = 18,
) -> DataFrameGroupBy:
    """
    Generate mock stock prices.
    """
    generator = np.random.default_rng(seed=seed)
    data = DataFrame()
    for company in range(companies):
        start = np.array([generator.normal(loc=start_price_mean, scale=start_price_sd)])
        increments = generator.normal(loc=increment_mean, scale=increment_sd, size=days - 1)
        stock_price = np.concatenate([start, increments]).cumsum()
        data = concat([data, DataFrame(
            {'stock_price': stock_price, 'company': f'{name_prefix}{company + 1}'},
            index=date_range(start_date, periods=days),
        )])
    return data.groupby('company')
