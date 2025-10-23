"""
Copyright 2019 Goldman Sachs.
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
from enum import Enum

from dataclasses import dataclass
from dataclasses_json import dataclass_json

from typing import Callable, Tuple, Union

from gs_quant.common import CurrencyName
from gs_quant.datetime.relative_date import RelativeDate
from gs_quant.instrument import Instrument
from gs_quant.timeseries import interpolate, Interpolate


class CalcType(Enum):
    simple = 'simple'
    semi_path_dependent = 'semi_path_dependent'
    path_dependent = 'path_dependent'


@dataclass_json
@dataclass
class CustomDuration:
    durations: Tuple[Union[str, dt.date, dt.timedelta], ...]
    function: Callable[[Tuple[Union[str, dt.date, dt.timedelta], ...]], Union[str, dt.date, dt.timedelta]]

    def __hash__(self):
        return hash((self.durations, self.function))


def make_list(thing):
    if thing is None:
        return []
    if isinstance(thing, str):
        return [thing]
    else:
        try:
            iter(thing)
        except TypeError:
            return [thing]
        else:
            return list(thing)


final_date_cache = {}


def get_final_date(inst, create_date, duration, holiday_calendar=None, trigger_info=None):
    cache_key = (inst, create_date, duration, holiday_calendar)
    if cache_key in final_date_cache:
        return final_date_cache[cache_key]

    if duration is None:
        final_date_cache[cache_key] = dt.date.max
        return dt.date.max
    if isinstance(duration, (dt.datetime, dt.date)):
        final_date_cache[cache_key] = duration
        return duration
    if hasattr(inst, str(duration)):
        final_date_cache[cache_key] = getattr(inst, str(duration))
        return getattr(inst, str(duration))
    if str(duration).lower() == 'next schedule':
        if hasattr(trigger_info, 'next_schedule'):
            return trigger_info.next_schedule or dt.date.max
        raise RuntimeError('Next schedule not supported by action')
    if isinstance(duration, CustomDuration):
        return duration.function(*(get_final_date(inst, create_date, d, holiday_calendar, trigger_info) for
                                 d in duration.durations))

    final_date_cache[cache_key] = RelativeDate(duration, create_date).apply_rule(holiday_calendar=holiday_calendar)
    return final_date_cache[cache_key]


def scale_trade(inst: Instrument, ratio: float):
    new_inst = inst.scale(ratio)
    return new_inst


def map_ccy_name_to_ccy(currency_name: Union[str, CurrencyName]):
    map = {'United States Dollar': 'USD',
           'Australian Dollar': 'AUD',
           'Canadian Dollar': 'CAD',
           'Swiss Franc': 'CHF',
           'Yuan Renminbi (Hong Kong)': 'CNH',
           'Czech Republic Koruna': 'CZK',
           'Euro': 'EUR',
           'Pound Sterling': 'GBP',
           'Japanese Yen': 'JPY',
           'South Korean Won': 'KRW',
           'Malasyan Ringgit': 'MYR',
           'Norwegian Krone': 'NOK',
           'New Zealand Dollar': 'NZD',
           'Polish Zloty': 'PLN',
           'Russian Rouble': 'RUB',
           'Swedish Krona': 'SEK',
           'South African Rand': 'ZAR',
           'Yuan Renminbi (Onshore)': 'CHY'}

    return map.get(currency_name.value if isinstance(currency_name, CurrencyName) else currency_name)


def interpolate_signal(signal: dict[dt.date, float], method=Interpolate.STEP) -> pd.Series:
    min_date = min(signal.keys())
    max_date = max(signal.keys())
    all_dates = [min_date + dt.timedelta(days=day) for day in range((max_date - min_date).days + 1)]
    signal_curve = interpolate(pd.Series(signal).sort_index(), all_dates, method=method)
    return signal_curve
