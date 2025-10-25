"""
Copyright 2018 Goldman Sachs.
Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

  http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing,
software distributed under the License is distributed on an
"AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
KIND, either express or implied.  See the License for the
specific language governing permissions and limitations
under the License.
"""
import datetime as dt
import pandas as pd
import numpy as np
import pytest
from pandas.testing import assert_series_equal

from gs_quant.errors import MqValueError
from gs_quant.timeseries import first, last, last_value, count, Interpolate, compare, diff, lag, LagMode, repeat


def test_first():
    dates = [
        dt.date(2019, 1, 1),
        dt.date(2019, 1, 2),
        dt.date(2019, 1, 3),
        dt.date(2019, 1, 4),
    ]

    x = pd.Series([1.0, 2.0, 3.0, 4.0], index=dates)

    result = first(x)
    expected = pd.Series([1.0, 1.0, 1.0, 1.0], index=dates)
    assert_series_equal(result, expected, obj="First")


def test_last():
    dates = [
        dt.date(2019, 1, 1),
        dt.date(2019, 1, 2),
        dt.date(2019, 1, 3),
        dt.date(2019, 1, 4),
    ]

    x = pd.Series([1.0, 2.0, 3.0, 4.0], index=dates)

    result = last(x)
    expected = pd.Series([4.0, 4.0, 4.0, 4.0], index=dates)
    assert_series_equal(result, expected, obj="First")

    y = pd.Series([1.0, 2.0, 3.0, np.nan], index=dates)
    result = last(y)
    expected = pd.Series([3.0, 3.0, 3.0, 3.0], index=dates)
    assert_series_equal(result, expected, obj="Last non-NA")


def test_last_value():
    with pytest.raises(MqValueError):
        last_value(pd.Series(dtype=float))

    x = pd.Series([1.0, 2.0, 3.0, 4.0], index=(pd.date_range("2020-01-01", periods=4, freq="D")))
    assert last_value(x) == 4.0

    y = pd.Series([5])
    assert last_value(y) == 5

    y = pd.Series([1.0, 2.0, 3.0, np.nan], index=(pd.date_range("2020-01-01", periods=4, freq="D")))
    assert last_value(y) == 3.0


def test_count():
    dates = [
        dt.date(2019, 1, 1),
        dt.date(2019, 1, 2),
        dt.date(2019, 1, 3),
        dt.date(2019, 1, 4),
    ]

    x = pd.Series([1.0, 2.0, 3.0, 4.0], index=dates)

    result = count(x)
    expected = pd.Series([1.0, 2.0, 3.0, 4.0], index=dates)
    assert_series_equal(result, expected, obj="Count")


def test_compare():
    dates1 = [
        dt.date(2019, 1, 1),
        dt.date(2019, 1, 2),
        dt.date(2019, 1, 3),
        dt.date(2019, 1, 4),
    ]

    dates2 = [
        dt.date(2019, 1, 1),
        dt.date(2019, 1, 2),
        dt.date(2019, 1, 3),
    ]

    x = pd.Series([1.0, 2.0, 2.0, 4.0], index=dates1)
    y = pd.Series([2.0, 1.0, 2.0], index=dates2)

    expected = pd.Series([-1.0, 1.0, 0.0], index=dates2)
    result = compare(x, y, method=Interpolate.INTERSECT)
    assert_series_equal(expected, result, obj="Compare series intersect")

    expected = pd.Series([1.0, -1.0, 0], index=dates2)
    result = compare(y, x, method=Interpolate.INTERSECT)
    assert_series_equal(expected, result, obj="Compare series intersect 2")

    expected = pd.Series([-1.0, 1.0, 0, 0], index=dates1)
    result = compare(x, y, method=Interpolate.NAN)
    assert_series_equal(expected, result, obj="Compare series nan")

    expected = pd.Series([-1.0, 1.0, 0, 1.0], index=dates1)
    result = compare(x, y, method=Interpolate.ZERO)
    assert_series_equal(expected, result, obj="Compare series zero")

    expected = pd.Series([-1.0, 1.0, 0, 1.0], index=dates1)
    result = compare(x, y, method=Interpolate.STEP)
    assert_series_equal(expected, result, obj="Compare series step")

    dates2 = [
        dt.date(2019, 1, 2),
        dt.date(2019, 1, 4),
        dt.date(2019, 1, 6),
    ]

    dates1.append(dt.date(2019, 1, 5))
    xp = pd.Series([1, 2, 3, 4, 5], index=pd.to_datetime(dates1))
    yp = pd.Series([1, 4, 0], index=pd.to_datetime(dates2))
    result = compare(xp, yp, Interpolate.TIME)
    dates1.append(dt.date(2019, 1, 6))
    expected = pd.Series([0.0, 1.0, 1.0, 0.0, 1.0, 0.0], index=pd.to_datetime(dates1))
    assert_series_equal(result, expected, obj="Compare series greater time")


def test_diff():
    dates = [
        dt.date(2019, 1, 1),
        dt.date(2019, 1, 2),
        dt.date(2019, 1, 3),
        dt.date(2019, 1, 4),
    ]

    x = pd.Series([1.0, 2.0, 3.0, 4.0], index=dates)

    result = diff(x)
    expected = pd.Series([np.nan, 1.0, 1.0, 1.0], index=dates)
    assert_series_equal(result, expected, obj="Diff")

    result = diff(x, 2)
    expected = pd.Series([np.nan, np.nan, 2.0, 2.0], index=dates)
    assert_series_equal(result, expected, obj="Diff")

    empty = pd.Series(dtype=float)
    result = diff(empty)
    assert (len(result) == 0)


def test_lag():
    dates = pd.date_range("2019-01-01", periods=4, freq="D")
    x = pd.Series([1.0, 2.0, 3.0, 4.0], index=dates)

    result = lag(x, '1m')
    expected = pd.Series([1.0, 2.0, 3.0, 4.0], index=pd.date_range("2019-01-31", periods=4, freq="D"))
    expected.index.freq = None
    assert_series_equal(result, expected, obj="Lag 1m")

    result = lag(x, '2d', LagMode.TRUNCATE)
    expected = pd.Series([1.0, 2.0], index=pd.date_range("2019-01-03", periods=2, freq="D"))
    expected.index.freq = None
    assert_series_equal(result, expected, obj="Lag 2d truncate")

    result = lag(x, mode=LagMode.TRUNCATE)
    expected = pd.Series([np.nan, 1.0, 2.0, 3.0], index=dates)
    expected.index.freq = None
    assert_series_equal(result, expected, obj="Lag")

    result = lag(x, 2, LagMode.TRUNCATE)
    expected = pd.Series([np.nan, np.nan, 1.0, 2.0], index=dates)
    expected.index.freq = None
    assert_series_equal(result, expected, obj="Lag 2")

    result = lag(x, 2, LagMode.EXTEND)
    expected = pd.Series([np.nan, np.nan, 1.0, 2.0, 3.0, 4.0], index=pd.date_range("2019-01-01", periods=6, freq="D"))
    assert_series_equal(result, expected, obj="Lag 2 Extend")

    result = lag(x, -2, LagMode.EXTEND)
    expected = pd.Series([1.0, 2.0, 3.0, 4.0, np.nan, np.nan], index=pd.date_range("2018-12-30", periods=6, freq="D"))
    assert_series_equal(result, expected, obj="Lag Negative 2 Extend")

    result = lag(x, 2)
    expected = pd.Series([np.nan, np.nan, 1.0, 2.0, 3.0, 4.0], index=pd.date_range("2019-01-01", periods=6, freq="D"))
    assert_series_equal(result, expected, obj="Lag 2 Default")

    y = pd.Series([0] * 4, index=pd.date_range('2020-01-01T00:00:00Z', periods=4, freq='S'))
    with pytest.raises(Exception):
        lag(y, 5, LagMode.EXTEND)

    z = pd.Series([10, 11, 12], index=pd.date_range('2020-02-28', periods=3, freq='D'))
    result = lag(z, '2y')
    expected = pd.Series([10, 12], index=pd.date_range('2022-02-28', periods=2, freq='D'))
    expected.index.freq = None
    assert_series_equal(result, expected, obj="Lag RDate 2y")


def test_repeat_empty_series():
    # Test case for an empty series
    empty_series = pd.Series(dtype=float)
    result = repeat(empty_series)
    assert result.empty, "The result should be an empty series when input is empty."


def test_lag_empty_series():
    empty_series = pd.Series(dtype=float)
    result = lag(empty_series)
    assert result.empty, "The result should be an empty series when input is empty."
