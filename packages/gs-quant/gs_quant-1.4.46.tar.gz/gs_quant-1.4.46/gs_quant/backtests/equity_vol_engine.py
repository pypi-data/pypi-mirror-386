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
import copy
import re
import warnings
from functools import reduce
from typing import Union

import datetime as dt
import pandas as pd

from gs_quant.api.gs.backtests_xasset.response_datatypes.backtest_datatypes import TransactionCostConfig, \
    TradingCosts, FixedCostModel, ScaledCostModel, TransactionCostScalingType, AggregateCostModel, CostAggregationType
from gs_quant.backtests import actions as a
from gs_quant.backtests import triggers as t
from gs_quant.backtests.backtest_objects import TransactionModel, ConstantTransactionModel, ScaledTransactionModel, \
    AggregateTransactionModel

from gs_quant.backtests.strategy_systematic import StrategySystematic, DeltaHedgeParameters, TradeInMethod
from gs_quant.base import get_enum_value
from gs_quant.common import OptionType, BuySell
from gs_quant.instrument import EqOption, EqVarianceSwap
from gs_quant.markets.portfolio import Portfolio
from gs_quant.risk import EqDelta, EqSpot, EqGamma, EqVega
from gs_quant.target.backtests import BacktestSignalSeriesItem, BacktestTradingQuantityType, EquityMarketModel, \
    FlowVolBacktestMeasure
from gs_quant.common import TradeAs


def get_backtest_trading_quantity_type(scaling_type, risk):
    if scaling_type == a.ScalingActionType.size:
        return a.BacktestTradingQuantityType.quantity
    if scaling_type == a.ScalingActionType.NAV:
        return a.BacktestTradingQuantityType.NAV
    if risk == EqSpot:
        return BacktestTradingQuantityType.notional
    if risk == EqGamma:
        return BacktestTradingQuantityType.gamma
    if risk == EqVega:
        return BacktestTradingQuantityType.vega
    raise ValueError(f"unable to translate {scaling_type} and {risk}")


def is_synthetic_forward(priceable):
    is_portfolio = isinstance(priceable, Portfolio)
    is_syn_fwd = is_portfolio
    if is_portfolio:
        is_size_two = len(priceable) == 2
        is_syn_fwd = is_size_two
        if is_size_two:
            has_two_eq_options = isinstance(priceable[0], EqOption) and isinstance(priceable[1], EqOption)
            is_syn_fwd &= has_two_eq_options
            if has_two_eq_options:
                is_syn_fwd &= (priceable[0].underlier == priceable[1].underlier) and \
                              (priceable[0].expiration_date == priceable[1].expiration_date) and \
                              (priceable[0].strike_price == priceable[1].strike_price)
                is_syn_fwd &= (OptionType.Call, BuySell.Buy) and (OptionType.Put, BuySell.Sell) in {
                              (priceable[0].option_type, priceable[0].buy_sell),
                              (priceable[1].option_type, priceable[1].buy_sell)}

    return is_syn_fwd


class BacktestResult:
    def __init__(self, results):
        self._results = results

    def get_measure_series(self, measure: FlowVolBacktestMeasure):
        data = next(iter(r.timeseries for r in self._results.risks if r.name == measure.value), ())
        df = pd.DataFrame.from_records(data)
        if len(df) == 0:
            return df

        df['date'] = pd.to_datetime(df['date'])
        return df.set_index('date').value

    def get_portfolio_history(self):
        data = []
        for item in self._results.portfolio:
            positions = list(map(lambda x: dict({'date': item['date'], 'quantity': x['quantity']}, **x['instrument']),
                                 item['positions']))
            data = data + positions

        return pd.DataFrame(data)

    def get_trade_history(self):
        data = []
        for item in self._results.portfolio:
            for transaction in item['transactions']:
                trades = list(map(lambda x: dict(
                    {'date': item['date'], 'quantity': x['quantity'], 'transactionType': transaction['type'],
                     'price': x['price'], 'cost': transaction.get('cost') if len(transaction['trades']) == 1 else None},
                    **x['instrument']), transaction['trades']))
                data = data + trades

        return pd.DataFrame(data)


class EquityVolEngine(object):

    @classmethod
    def check_strategy(cls, strategy):
        check_results = []
        if len(strategy.initial_portfolio) > 0:
            check_results.append('Error: initial_portfolio must be empty or None')

        # Validate Triggers

        if len(strategy.triggers) > 3:
            check_results.append('Error: Maximum of 3 triggers')

        if not all(isinstance(x, (t.AggregateTrigger, t.PeriodicTrigger)) for x in strategy.triggers):
            check_results.append('Error: Only AggregateTrigger and PeriodTrigger supported')

        # aggregate triggers composed of a dated and portfolio trigger define a signal
        aggregate_triggers = [x for x in strategy.triggers if isinstance(x, t.AggregateTrigger)]
        for at in aggregate_triggers:
            if not len(at.trigger_requirements.triggers) == 2:
                check_results.append('Error: AggregateTrigger must be composed of 2 triggers')
            if not len([x for x in at.trigger_requirements.triggers if isinstance(x, t.DateTriggerRequirements)]) == 1:
                check_results.append('Error: AggregateTrigger must be contain 1 DateTrigger')
            portfolio_triggers = [x for x in at.trigger_requirements.triggers
                                  if isinstance(x, t.PortfolioTriggerRequirements)]
            if not len(portfolio_triggers) == 1:
                check_results.append('Error: AggregateTrigger must be contain 1 PortfolioTrigger')
            if not (portfolio_triggers[0].data_source == 'len' and
                    portfolio_triggers[0].trigger_level == 0):
                check_results.append(
                    'Error: PortfolioTrigger.trigger_requirements must have data_source = \'len\' '
                    'and trigger_level = 0')

        # Validate Actions

        all_actions = reduce(lambda acc, x: acc + x, (map(lambda x: x.actions, strategy.triggers)), [])

        if any(isinstance(x, a.ExitPositionAction) for x in all_actions):
            warnings.warn('ExitPositionAction will be deprecated soon, use ExitTradeAction.', DeprecationWarning, 2)
        if any(isinstance(x, a.EnterPositionQuantityScaledAction) for x in all_actions):
            warnings.warn('EnterPositionQuantityScaledAction will be deprecated soon, use AddScaledTradeAction.',
                          DeprecationWarning, 2)

        if not all(isinstance(x, (a.EnterPositionQuantityScaledAction, a.HedgeAction, a.ExitPositionAction,
                                  a.ExitTradeAction, a.AddTradeAction, a.AddScaledTradeAction)) for x in all_actions):
            check_results.append(
                'Error: actions must be one of EnterPositionQuantityScaledAction, HedgeAction, ExitPositionAction, '
                'ExitTradeAction, AddTradeAction, AddScaledTradeAction')

        # no duplicate actions
        if not len(set(map(lambda x: type(x), all_actions))) == len(all_actions):
            check_results.append('Error: There are multiple actions of the same type')

        all_child_triggers = reduce(lambda acc, x: acc + x, map(lambda x: x.trigger_requirements.triggers if isinstance(
            x, t.AggregateTriggerRequirements) else [x], strategy.triggers), [])

        for trigger in all_child_triggers:
            if isinstance(trigger, t.PortfolioTrigger):
                continue

            # action one of enter position, exit position, hedge
            if len(trigger.actions) != 1:
                check_results.append('Error: All triggers must contain only 1 action')

            for action in trigger.actions:
                if isinstance(action, (a.EnterPositionQuantityScaledAction, a.AddTradeAction, a.AddScaledTradeAction)):
                    if isinstance(trigger, t.PeriodicTrigger) and \
                            not trigger.trigger_requirements.frequency == action.trade_duration:
                        check_results.append(
                            f'Error: {type(action).__name__}: PeriodicTrigger frequency must be the same '
                            'as trade_duration')
                    if not all((isinstance(p, (EqOption, EqVarianceSwap)))
                               for p in action.priceables):
                        check_results.append(
                            f'Error: {type(action).__name__}: Only EqOption or EqVarianceSwap supported')
                    if isinstance(action, a.EnterPositionQuantityScaledAction):
                        if action.trade_quantity is None or action.trade_quantity_type is None:
                            check_results.append('Error: EnterPositionQuantityScaledAction trade_quantity or '
                                                 'trade_quantity_type is None')
                    if isinstance(action, a.AddScaledTradeAction):
                        if action.scaling_level is None or action.scaling_type is None:
                            check_results.append('Error: AddScaledTradeAction scaling_level or scaling_type is None')
                    expiry_date_modes = map(lambda x: TenorParser(x.expirationDate).get_mode(),
                                            action.priceables)
                    expiry_date_modes = list(set(expiry_date_modes))
                    if len(expiry_date_modes) > 1:
                        check_results.append(
                            f'Error: {type(action).__name__} all priceable expiration_date modifiers must '
                            'be the same. Found [' + ', '.join([str(edm) for edm in expiry_date_modes]) + ']')
                    if expiry_date_modes[0] is not None and expiry_date_modes[0] not in ['otc', 'listed']:
                        check_results.append(
                            f'Error: {type(action).__name__} invalid expiration_date '
                            'modifier ' + expiry_date_modes[0])

                    size_fields = ('quantity', 'number_of_options', 'multiplier')
                    priceable_size_values = [[getattr(p, sf, 1) or 1 for sf in size_fields] for p in action.priceables]
                    priceable_sizes = [reduce(lambda x, y: x * y, size_vals, 1) for size_vals in priceable_size_values]

                    if not all(priceable_size == 1 for priceable_size in priceable_sizes):
                        check_results.append(
                            f'Error: {type(action).__name__} every priceable should have a unit size of 1. '
                            'Found [' + ', '.join([str(s) for s in priceable_sizes]) + ']'
                        )
                elif isinstance(action, a.HedgeAction):
                    if not is_synthetic_forward(action.priceable):
                        check_results.append(
                            'Error: HedgeAction: Hedge instrument must be a synthetic forward - a portfolio of two '
                            'equity options (long call and short put) with the same underlier, strike price and '
                            'expiration date')
                    if not trigger.trigger_requirements.frequency == action.trade_duration:
                        check_results.append(
                            'Error: HedgeAction: PeriodicTrigger frequency must be the same as trade_duration')
                    if not action.risk == EqDelta:
                        check_results.append('Error: HedgeAction: risk type must be EqDelta')
                elif isinstance(action, (a.ExitPositionAction, a.ExitTradeAction)):
                    continue
                else:
                    check_results.append('Error: Unsupported action type \'{}\''.format(type(action)))

        return check_results

    @classmethod
    def supports_strategy(cls, strategy):
        check_result = cls.check_strategy(strategy)
        if len(check_result):
            return False

        return True

    @classmethod
    def run_backtest(cls, strategy, start, end, market_model=EquityMarketModel.SFK, cash_accrual=True):
        check_result = cls.check_strategy(strategy)
        if len(check_result):
            raise RuntimeError(check_result)

        underlier_list = None
        roll_frequency = None
        trade_quantity = None
        trade_quantity_type = None
        trade_in_signals = None
        trade_out_signals = None
        hedge = None

        transaction_cost = TransactionCostConfig(None)
        for trigger in strategy.triggers:
            if isinstance(trigger, t.AggregateTrigger):
                child_triggers = trigger.trigger_requirements.triggers

                date_trigger = [x for x in child_triggers if isinstance(x, t.DateTriggerRequirements)][0]
                date_signal = list(map(lambda x: BacktestSignalSeriesItem(x, True),
                                       date_trigger.dates))

                portfolio_trigger = [x for x in child_triggers if isinstance(x, t.PortfolioTriggerRequirements)][0]
                if portfolio_trigger.direction == t.TriggerDirection.EQUAL and \
                        portfolio_trigger.trigger_level == 0:
                    is_trade_in = True
                else:
                    is_trade_in = False

                if is_trade_in:
                    trade_in_signals = date_signal
                else:
                    trade_out_signals = date_signal

            action = trigger.actions[0]
            if isinstance(action, a.EnterPositionQuantityScaledAction):
                underlier_list = cls.__get_underlier_list(action.priceables)
                tp = TenorParser(action.trade_duration)
                roll_frequency = tp.get_date()
                roll_date_mode = tp.get_mode()
                trade_quantity = action.trade_quantity
                trade_quantity_type = action.trade_quantity_type
                expiry_date_mode = TenorParser(action.priceables[0].expiration_date).get_mode()
                transaction_cost.trade_cost_model = TradingCosts(cls.__map_tc_model(action.transaction_cost),
                                                                 cls.__map_tc_model(action.transaction_cost_exit))
            elif isinstance(action, a.AddTradeAction):
                underlier_list = cls.__get_underlier_list(action.priceables)
                tp = TenorParser(action.trade_duration)
                roll_frequency = tp.get_date()
                roll_date_mode = tp.get_mode()
                trade_quantity = 1
                trade_quantity_type = BacktestTradingQuantityType.quantity
                expiry_date_mode = TenorParser(action.priceables[0].expiration_date).get_mode()
                transaction_cost.trade_cost_model = TradingCosts(cls.__map_tc_model(action.transaction_cost),
                                                                 cls.__map_tc_model(action.transaction_cost_exit))
            elif isinstance(action, a.AddScaledTradeAction):
                underlier_list = cls.__get_underlier_list(action.priceables)
                tp = TenorParser(action.trade_duration)
                roll_frequency = tp.get_date()
                roll_date_mode = tp.get_mode()
                trade_quantity = action.scaling_level
                trade_quantity_type = get_backtest_trading_quantity_type(action.scaling_type, action.scaling_risk)
                expiry_date_mode = TenorParser(action.priceables[0].expiration_date).get_mode()
                transaction_cost.trade_cost_model = TradingCosts(cls.__map_tc_model(action.transaction_cost),
                                                                 cls.__map_tc_model(action.transaction_cost_exit))
            elif isinstance(action, a.HedgeAction):
                hedge = DeltaHedgeParameters(frequency=trigger.trigger_requirements.frequency)
                transaction_cost.hedge_cost_model = TradingCosts(cls.__map_tc_model(action.transaction_cost),
                                                                 cls.__map_tc_model(action.transaction_cost_exit))

        transaction_cost_config = transaction_cost \
            if (transaction_cost.trade_cost_model or transaction_cost.hedge_cost_model) else None

        strategy = StrategySystematic(name="Flow Vol Backtest",
                                      underliers=underlier_list,
                                      index_initial_value=0,
                                      delta_hedge=hedge,
                                      quantity=trade_quantity,
                                      quantity_type=trade_quantity_type,
                                      trade_in_method=TradeInMethod.FixedRoll,
                                      roll_frequency=roll_frequency,
                                      trade_in_signals=trade_in_signals,
                                      trade_out_signals=trade_out_signals,
                                      market_model=market_model,
                                      expiry_date_mode=expiry_date_mode,
                                      roll_date_mode=roll_date_mode,
                                      cash_accrual=cash_accrual,
                                      transaction_cost_config=transaction_cost_config,
                                      use_xasset_backtesting_service=True
                                      )

        result = strategy.backtest(start, end)
        return BacktestResult(result)

    @classmethod
    def __get_underlier_list(cls, priceables):
        priceables_copy = copy.deepcopy(priceables)
        for priceable in priceables_copy:
            edp = TenorParser(priceable.expiration_date)
            priceable.expiration_date = edp.get_date()
            if hasattr(priceable, 'trade_as'):
                expiry_date_mode = get_enum_value(TradeAs, edp.get_mode())
                priceable.trade_as = priceable.trade_as or expiry_date_mode \
                    if isinstance(expiry_date_mode, TradeAs) else None
                print(priceable.trade_as)
        return priceables_copy

    @classmethod
    def __map_tc_model(cls, model: TransactionModel):
        if isinstance(model, ConstantTransactionModel):
            return FixedCostModel(cost=model.cost)
        elif isinstance(model, ScaledTransactionModel):
            if model.scaling_type == EqVega:
                scaling_quantity_type = TransactionCostScalingType.Vega
            else:
                scaling_quantity_type = get_enum_value(TransactionCostScalingType, model.scaling_type)
                if not isinstance(scaling_quantity_type, TransactionCostScalingType):
                    raise RuntimeError(f'unsupported scaled transaction quantity type "{model.scaling_type}"')
            return ScaledCostModel(scaling_quantity_type=scaling_quantity_type, scaling_level=model.scaling_level)
        elif isinstance(model, AggregateTransactionModel):
            return AggregateCostModel(models=[cls.__map_tc_model(m) for m in model.transaction_models],
                                      aggregation_type=CostAggregationType(model.aggregate_type.value))
        return None


class TenorParser(object):

    # match expiration dates expressed as 3m@listed
    expiry_regex = '(.*)@(.*)'

    def __init__(self, expiry: Union[str, dt.date]):
        self.expiry = expiry

    def get_date(self):
        if isinstance(self.expiry, dt.date):
            return self.expiry

        parts = re.search(self.expiry_regex, self.expiry)
        if parts:
            return parts.group(1)
        else:
            return self.expiry

    def get_mode(self):
        if isinstance(self.expiry, dt.date):
            return None

        parts = re.search(self.expiry_regex, self.expiry)
        if parts:
            return parts.group(2)
        else:
            return None
