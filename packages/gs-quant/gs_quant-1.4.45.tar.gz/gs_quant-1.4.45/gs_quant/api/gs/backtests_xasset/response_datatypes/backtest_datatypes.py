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
import dataclasses
import datetime as dt
from abc import abstractmethod

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, Tuple, Dict, Union, Any

from dataclasses_json import dataclass_json, LetterCase, config

from gs_quant.api.gs.backtests_xasset.json_encoders.request_encoders import legs_decoder
from gs_quant.api.gs.backtests_xasset.json_encoders.response_datatypes.generic_datatype_encoders import \
    decode_daily_portfolio
from gs_quant.instrument import Instrument
from gs_quant.interfaces.algebra import AlgebraicType
from gs_quant.json_convertors import decode_optional_date, encode_date_tuple, decode_date_tuple, \
    decode_dict_date_key_or_float
from gs_quant.target.backtests import BacktestTradingQuantityType, EquityMarketModel
from gs_quant.common import Currency, CurrencyName, PricingLocation


class TransactionCostModel(Enum):
    Fixed = 'Fixed'


class TransactionDirection(Enum):
    Entry = 'Entry'
    Exit = 'Exit'


class RollDateMode(Enum):
    OTC = 'OTC'
    Listed = 'Listed'

    @classmethod
    def _missing_(cls, value):
        if value is None:
            return None
        for member in cls:
            if member.value.lower() == value.lower():
                return member
        return None


class TransactionCostScalingType(Enum):
    Quantity = 'Quantity'
    Notional = 'Notional'
    Delta = 'Delta'
    Vega = 'Vega'


class CostAggregationType(Enum):
    Sum = 'Sum'
    Max = 'Max'
    Min = 'Min'


@dataclass_json(letter_case=LetterCase.CAMEL)
@dataclass
class Transaction:
    portfolio: Tuple[Instrument, ...]
    portfolio_price: Optional[float] = None
    cost: Optional[float] = None
    currency: Optional[Union[Currency, CurrencyName, str]] = None
    direction: Optional[TransactionDirection] = None
    quantity: Optional[float] = None


@dataclass_json(letter_case=LetterCase.CAMEL)
@dataclass
class AdditionalResults:
    hedges: Optional[Dict[dt.date, Tuple[Instrument, ...]]] = field(default=None,
                                                                    metadata=config(decoder=decode_daily_portfolio))
    hedge_pnl: Optional[Dict[dt.date, float]] = None
    no_of_calculations: Optional[int] = None

    @classmethod
    def from_dict_custom(cls, data: Any, decode_instruments: bool = True):
        if decode_instruments:
            return cls.from_dict(data)
        return AdditionalResults(hedges=decode_daily_portfolio(data['hedges'], decode_instruments),
                                 hedge_pnl=data['hedge_pnl'],
                                 no_of_calculations=data['no_of_calculations'])


@dataclass_json(letter_case=LetterCase.CAMEL)
@dataclass(unsafe_hash=True, repr=False)
class DateConfig:
    start_date: dt.date = field(default=None, metadata=config(decoder=decode_optional_date))
    end_date: dt.date = field(default=None, metadata=config(decoder=decode_optional_date))
    frequency: str = '1b'
    holiday_calendar: Optional[str] = None


@dataclass_json(letter_case=LetterCase.CAMEL)
@dataclass(unsafe_hash=True, repr=False)
class Trade:
    legs: Optional[Tuple[Instrument, ...]] = field(default=None, metadata=config(decoder=legs_decoder))
    buy_frequency: str = None
    buy_dates: Optional[Tuple[dt.date, ...]] = field(default=None, metadata=config(encoder=encode_date_tuple,
                                                                                   decoder=decode_date_tuple))
    holding_period: str = None
    exit_dates: Optional[Tuple[dt.date, ...]] = field(default=None, metadata=config(encoder=encode_date_tuple,
                                                                                    decoder=decode_date_tuple))
    quantity: Optional[Union[float, dict[dt.date, float]]] = field(default=None,
                                                                   metadata=config(
                                                                       decoder=decode_dict_date_key_or_float))
    quantity_type: BacktestTradingQuantityType = BacktestTradingQuantityType.quantity


@dataclass_json(letter_case=LetterCase.CAMEL)
@dataclass(unsafe_hash=True, repr=False)
class Model(AlgebraicType):
    pass

    @property
    @abstractmethod
    def scaling_property(self):
        ...

    def set_scaling_property(self, value: float):
        setattr(self, self.scaling_property, value)

    def __add__(self, other):
        if not isinstance(other, Model):
            raise TypeError('Can only add to another cost model')
        if isinstance(other, AggregateCostModel):
            return other + self
        scaling_prop_name = self.scaling_property
        can_add_scaling = type(self) is type(other) and \
            other == dataclasses.replace(self, **{scaling_prop_name: getattr(other, scaling_prop_name)})
        if can_add_scaling:
            result = dataclasses.replace(self)
            result.set_scaling_property(getattr(self, scaling_prop_name) + getattr(other, scaling_prop_name))
            return result
        return AggregateCostModel((self, other), CostAggregationType.Sum)

    def __sub__(self, other):
        raise NotImplementedError('Multiplication not implemented for cost models')

    def __mul__(self, other):
        raise NotImplementedError('Multiplication not implemented for cost models')

    def __div__(self, other):
        raise NotImplementedError('Division not implemented for cost models')


@dataclass_json(letter_case=LetterCase.CAMEL)
@dataclass(unsafe_hash=True, repr=False)
class FixedCostModel(Model):
    cost: float = 0.0
    type: str = 'FixedCostModel'

    @property
    def scaling_property(self):
        return 'cost'

    def __eq__(self, other):
        if not isinstance(other, FixedCostModel):
            return False
        return (self.cost,) == (other.cost,)


@dataclass_json(letter_case=LetterCase.CAMEL)
@dataclass(unsafe_hash=True, repr=False)
class ScaledCostModel(Model):
    scaling_level: float = 0.0
    scaling_quantity_type: TransactionCostScalingType = TransactionCostScalingType.Quantity
    type: str = 'ScaledCostModel'

    @property
    def scaling_property(self):
        return 'scaling_level'

    def __eq__(self, other):
        if not isinstance(other, ScaledCostModel):
            return False
        return (self.scaling_level, self.scaling_quantity_type) == (other.scaling_level, other.scaling_quantity_type)


_type_to_basic_model_map = {
    'fixed_cost_model': FixedCostModel,
    'scaled_cost_model': ScaledCostModel,
    'FixedCostModel': FixedCostModel,
    'ScaledCostModel': ScaledCostModel
}


def basic_tc_tuple_decoder(data: Optional[Tuple[dict, ...]]) -> Optional[Union[FixedCostModel, ScaledCostModel]]:
    if data is None:
        return None
    return tuple(_type_to_basic_model_map[m['type']].from_dict(m) for m in data)


@dataclass_json(letter_case=LetterCase.CAMEL)
@dataclass(unsafe_hash=True, repr=False)
class AggregateCostModel(Model):
    models: Tuple[Union[FixedCostModel, ScaledCostModel], ...] = field(metadata=config(decoder=basic_tc_tuple_decoder))
    aggregation_type: CostAggregationType
    type: str = 'AggregateCostModel'

    @property
    def scaling_property(self):
        return None

    def set_scaling_property(self, value: float):
        pass

    def __add__(self, other):
        if isinstance(other, AggregateCostModel) and self.aggregation_type is other.aggregation_type:
            return AggregateCostModel(self.models + other.models, self.aggregation_type)
        raise TypeError('Can only add with AggregateCostModels with the same aggregation type')

    def __eq__(self, other):
        if not isinstance(other, AggregateCostModel):
            return False
        return (self.models, self.aggregation_type) == (other.models, other.aggregation_type)


def tcm_decoder(data: Optional[dict]) -> Optional[Union[FixedCostModel, ScaledCostModel, AggregateCostModel]]:
    full_type_map = {**_type_to_basic_model_map,
                     **{'aggregate_cost_model': AggregateCostModel, 'AggregateCostModel': AggregateCostModel}}
    return full_type_map[data['type']].from_dict(data) if data is not None else None


@dataclass_json(letter_case=LetterCase.CAMEL)
@dataclass(unsafe_hash=True, repr=False)
class TradingCosts:
    entry: Union[FixedCostModel, ScaledCostModel, AggregateCostModel] = \
        field(default=FixedCostModel(0), metadata=config(decoder=tcm_decoder))
    exit: Optional[Union[FixedCostModel, ScaledCostModel, AggregateCostModel]] = \
        field(default=None, metadata=config(decoder=tcm_decoder))


@dataclass_json(letter_case=LetterCase.CAMEL)
@dataclass(unsafe_hash=True, repr=False)
class TransactionCostConfig:
    trade_cost_model: TradingCosts
    hedge_cost_model: Optional[TradingCosts] = None


@dataclass_json(letter_case=LetterCase.CAMEL)
@dataclass(unsafe_hash=True, repr=False)
class Configuration:
    market_data_location: Optional[PricingLocation] = None
    market_model: Optional[EquityMarketModel] = None
    cash_accrual: bool = False
    roll_date_mode: Optional[RollDateMode] = None
    combine_roll_signal_entries: bool = False
