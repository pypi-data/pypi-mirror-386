"""
Copyright 2020 Goldman Sachs.
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
from math import sqrt

import pandas as pd
import pytest
from testfixtures import Replacer
from testfixtures.mock import Mock

import gs_quant.timeseries.measures_risk_models as mrm
from gs_quant.data.core import DataContext
from gs_quant.errors import MqValueError
from gs_quant.models.risk_model import FactorRiskModel as Factor_Risk_Model
from gs_quant.markets.securities import Stock
from gs_quant.target.risk_models import RiskModel, RiskModelCoverage, RiskModelTerm, RiskModelUniverseIdentifier, \
    RiskModelType

mock_risk_model_obj = RiskModel(
    id_='model_id',
    name='Fake Risk Model',
    coverage=RiskModelCoverage.Country,
    term=RiskModelTerm.Long,
    universe_identifier=RiskModelUniverseIdentifier.gsid,
    vendor='GS',
    version=1.0,
    type_=RiskModelType.Factor
)

mock_risk_model_data = {
    'totalResults': 2,
    'missingDates': [],
    'results': [
        {
            'date': '2020-01-01',
            'factorData': [
                {'factorId': '1', 'factorCategory': 'Style'},
                {'factorId': '2', 'factorCategory': 'Style'},
                {'factorId': '3', 'factorCategory': 'Style'},
            ]
        },
        {
            'date': '2020-01-02',
            'factorData': [
                {'factorId': '1', 'factorCategory': 'Style'},
                {'factorId': '2', 'factorCategory': 'Style'},
                {'factorId': '3', 'factorCategory': 'Style'},
            ]
        },
        {
            'date': '2020-01-03',
            'factorData': [
                {'factorId': '1', 'factorCategory': 'Style'},
                {'factorId': '2', 'factorCategory': 'Style'},
                {'factorId': '3', 'factorCategory': 'Style'},
            ]
        }
    ]
}

mock_risk_model_factor_data_intraday = {
    'totalResults': 2,
    'missingDates': [],
    'results': [
        {
            'time': '2020-01-01T10:10:10Z',
            'factor': 'Factor Name',
            'factorCategory': 'Style',
            "factorId": "factor_id",
            "factorReturn": 1.022
        },
        {
            'time': '2020-01-01T10:10:20Z',
            'factor': 'Factor Name 1',
            'factorCategory': 'Style',
            "factorId": "factor_id_1",
            "factorReturn": 1.033
        }
    ]
}

mock_risk_model_factor_data = [{
    'identifier': 'factor_id',
    'type': 'Factor',
    'name': "Factor Name",
}]

mock_covariance_curve = {
    '2020-01-01': 1.01,
    '2020-01-02': 1.02,
    '2020-01-03': 1.03
}

mock_volatility_curve = {
    '2020-01-01': sqrt(1.01),
    '2020-01-02': sqrt(1.02),
    '2020-01-03': sqrt(1.03)
}

mock_correlation_curve = {
    '2020-01-01': 1.0,
    '2020-01-02': 1.0,
    '2020-01-03': 1.0
}


def mock_risk_model():
    replace = Replacer()

    # mock getting risk model entity()
    mock = replace('gs_quant.api.gs.risk_models.GsRiskModelApi.get_risk_model', Mock())
    mock.return_value = mock_risk_model_obj

    actual = Factor_Risk_Model.get(model_id='model_id')
    replace.restore()
    return actual


def test_risk_model_measure():
    replace = Replacer()

    # mock getting risk model entity()
    mock = replace('gs_quant.api.gs.risk_models.GsRiskModelApi.get_risk_model', Mock())
    mock.return_value = mock_risk_model_obj

    # mock getting risk model factor entity
    mock = replace('gs_quant.api.gs.risk_models.GsFactorRiskModelApi.get_risk_model_data', Mock())
    mock.return_value = mock_risk_model_data

    # mock getting risk model factor entity
    mock = replace('gs_quant.api.gs.risk_models.GsFactorRiskModelApi.get_risk_model_factor_data', Mock())
    mock.return_value = mock_risk_model_factor_data

    # mock getting asset gsid
    mock = replace('gs_quant.markets.securities.Asset.get_identifier', Mock())
    mock.return_value = '14593'

    # mock getting risk model dates
    mock = replace('gs_quant.api.gs.risk_models.GsRiskModelApi.get_risk_model_dates', Mock())
    mock.return_value = ['2020-01-01', '2020-01-02', '2020-01-03']

    # mock getting risk model data
    mock = replace('gs_quant.models.risk_model.MarqueeRiskModel.get_data', Mock())
    mock.return_value = {
        'totalResults': 3,
        'missingDates': [],
        'results': [
            {'date': '2024-08-19', 'assetData': {'universe': ['14593'], 'bidAskSpread30d': [0.1]}},
            {'date': '2024-08-20', 'assetData': {'universe': ['14593'], 'bidAskSpread30d': [0.2]}},
            {'date': '2024-08-21', 'assetData': {'universe': ['14593'], 'bidAskSpread30d': [0.3]}}
        ]
    }

    with DataContext(dt.date(2020, 1, 1), dt.date(2020, 1, 3)):
        actual = mrm.risk_model_measure(Stock(id_='id', name='Fake Asset'), 'model_id',
                                        mrm.ModelMeasureString.BID_AKS_SPREAD_30D)
        assert all(actual.values == [0.1, 0.2, 0.3])

    with pytest.raises(AttributeError):
        mrm.risk_model_measure(Stock(id_='id', name='Fake Asset'), 'model_id', 'Wrong Factor Name')
    replace.restore()


def test_factor_zscore():
    replace = Replacer()

    # mock getting risk model entity()
    mock = replace('gs_quant.api.gs.risk_models.GsRiskModelApi.get_risk_model', Mock())
    mock.return_value = mock_risk_model_obj

    # mock getting risk model factor entity
    mock = replace('gs_quant.api.gs.risk_models.GsFactorRiskModelApi.get_risk_model_data', Mock())
    mock.return_value = mock_risk_model_data

    # mock getting risk model factor entity
    mock = replace('gs_quant.api.gs.risk_models.GsFactorRiskModelApi.get_risk_model_factor_data', Mock())
    mock.return_value = mock_risk_model_factor_data

    # mock getting asset gsid
    mock = replace('gs_quant.markets.securities.Asset.get_identifier', Mock())
    mock.return_value = '12345'

    # mock getting risk model dates
    mock = replace('gs_quant.api.gs.risk_models.GsRiskModelApi.get_risk_model_dates', Mock())
    mock.return_value = ['2020-01-01', '2020-01-02', '2020-01-03']

    # mock getting risk model data
    mock = replace('gs_quant.models.risk_model.MarqueeRiskModel.get_data', Mock())
    mock.return_value = {
        'results': [
            {
                'date': '2020-01-01',
                'assetData': {
                    'factorExposure': [
                        {
                            'factor_id': 1.01,
                            'factor_id_1': 1.23
                        }
                    ]
                }
            },
            {
                'date': '2020-01-02',
                'assetData': {
                    'factorExposure': [
                        {
                            'factor_id': 1.02,
                            'factor_id_1': 1.23
                        }
                    ]
                }
            },
            {
                'date': '2020-01-03',
                'assetData': {
                    'factorExposure': [
                        {
                            'factor_id': 1.03,
                            'factor_id_1': 1.23
                        }
                    ]
                }
            }
        ]
    }

    with DataContext(dt.date(2020, 1, 1), dt.date(2020, 1, 3)):
        actual = mrm.factor_zscore(Stock(id_='id', name='Fake Asset'), 'model_id', 'Factor Name')
        assert all(actual.values == [1.01, 1.02, 1.03])

    with pytest.raises(MqValueError):
        mrm.factor_zscore(Stock(id_='id', name='Fake Asset'), 'model_id', 'Wrong Factor Name')
    replace.restore()


def test_factor_covariance():
    replace = Replacer()

    # mock getting risk model entity()
    mock = replace('gs_quant.api.gs.risk_models.GsRiskModelApi.get_risk_model', Mock())
    mock.return_value = mock_risk_model_obj

    # mock getting risk model dates
    mock = replace('gs_quant.api.gs.risk_models.GsRiskModelApi.get_risk_model_dates', Mock())
    mock.return_value = ['2020-01-01', '2020-01-02', '2020-01-03']

    # mock getting risk model factor entity
    mock = replace('gs_quant.api.gs.risk_models.GsFactorRiskModelApi.get_risk_model_data', Mock())
    mock.return_value = mock_risk_model_data

    # mock getting risk model factor entity
    mock = replace('gs_quant.api.gs.risk_models.GsFactorRiskModelApi.get_risk_model_factor_data', Mock())
    mock.return_value = mock_risk_model_factor_data

    # mock getting covariances
    mock = replace('gs_quant.markets.factor.Factor.covariance', Mock())
    mock.return_value = mock_covariance_curve

    with DataContext(dt.date(2020, 1, 1), dt.date(2020, 1, 3)):
        actual = mrm.factor_covariance(mock_risk_model(), 'Factor Name', 'Factor Name')
        assert all(actual.values == [1.01, 1.02, 1.03])

    with pytest.raises(MqValueError):
        mrm.factor_covariance(mock_risk_model(), 'Wrong Factor Name', 'Factor Name')
    replace.restore()


def test_factor_volatility():
    replace = Replacer()

    # mock getting risk model factor entity
    mock = replace('gs_quant.api.gs.risk_models.GsFactorRiskModelApi.get_risk_model_data', Mock())
    mock.return_value = mock_risk_model_data

    # mock getting risk model factor entity
    mock = replace('gs_quant.api.gs.risk_models.GsFactorRiskModelApi.get_risk_model_factor_data', Mock())
    mock.return_value = mock_risk_model_factor_data

    # mock getting risk model entity()
    mock = replace('gs_quant.api.gs.risk_models.GsRiskModelApi.get_risk_model', Mock())
    mock.return_value = mock_risk_model_obj

    # mock getting risk model dates
    mock = replace('gs_quant.api.gs.risk_models.GsRiskModelApi.get_risk_model_dates', Mock())
    mock.return_value = ['2020-01-01', '2020-01-02', '2020-01-03']

    # mock getting covariances
    mock = replace('gs_quant.markets.factor.Factor.volatility', Mock())
    mock.return_value = mock_volatility_curve

    with DataContext(dt.date(2020, 1, 1), dt.date(2020, 1, 3)):
        actual = mrm.factor_volatility(mock_risk_model(), 'Factor Name')
        assert all(actual.values == [sqrt(1.01) * 100, sqrt(1.02) * 100, sqrt(1.03) * 100])

    with pytest.raises(MqValueError):
        mrm.factor_covariance(mock_risk_model(), 'Wrong Factor Name', 'Factor Name')
    replace.restore()


def test_factor_correlation():
    replace = Replacer()

    # mock getting risk model factor entity
    mock = replace('gs_quant.api.gs.risk_models.GsFactorRiskModelApi.get_risk_model_data', Mock())
    mock.return_value = mock_risk_model_data

    # mock getting risk model factor entity
    mock = replace('gs_quant.api.gs.risk_models.GsFactorRiskModelApi.get_risk_model_factor_data', Mock())
    mock.return_value = mock_risk_model_factor_data

    # mock getting risk model entity()
    mock = replace('gs_quant.api.gs.risk_models.GsRiskModelApi.get_risk_model', Mock())
    mock.return_value = mock_risk_model_obj

    # mock getting risk model dates
    mock = replace('gs_quant.api.gs.risk_models.GsRiskModelApi.get_risk_model_dates', Mock())
    mock.return_value = ['2020-01-01', '2020-01-02', '2020-01-03']

    # mock getting covariances
    mock = replace('gs_quant.markets.factor.Factor.correlation', Mock())
    mock.return_value = mock_correlation_curve

    with DataContext(dt.date(2020, 1, 1), dt.date(2020, 1, 3)):
        actual = mrm.factor_correlation(mock_risk_model(), 'Factor Name', 'Factor Name')
        assert all(actual.values == [1, 1, 1])
    replace.restore()


def test_factor_performance():
    replace = Replacer()

    # mock getting risk model factor entity
    mock = replace('gs_quant.api.gs.risk_models.GsFactorRiskModelApi.get_risk_model_data', Mock())
    mock.return_value = mock_risk_model_data

    # mock getting risk model factor entity
    mock = replace('gs_quant.api.gs.risk_models.GsFactorRiskModelApi.get_risk_model_factor_data', Mock())
    mock.return_value = mock_risk_model_factor_data

    # mock getting risk model entity()
    mock = replace('gs_quant.api.gs.risk_models.GsRiskModelApi.get_risk_model', Mock())
    mock.return_value = mock_risk_model_obj

    # mock getting risk model dates
    mock = replace('gs_quant.api.gs.risk_models.GsRiskModelApi.get_risk_model_dates', Mock())
    mock.return_value = ['2020-01-01', '2020-01-02', '2020-01-03']

    # mock getting factor returns
    mock = replace('gs_quant.markets.factor.Factor.returns', Mock())
    mock.return_value = pd.DataFrame.from_dict(mock_covariance_curve, orient='index', columns=['return'])

    with DataContext(dt.date(2020, 1, 1), dt.date(2020, 1, 3)):
        actual = mrm.factor_performance(mock_risk_model(), 'Factor Name')
        assert len(actual.values) == 3
    replace.restore()


def test_factor_returns_intraday():
    replace = Replacer()

    # mock getting risk model factor entity
    mock = replace('gs_quant.api.gs.risk_models.GsFactorRiskModelApi.get_risk_model_factor_data', Mock())
    mock.return_value = mock_risk_model_factor_data

    # mock getting risk model entity()
    mock = replace('gs_quant.api.gs.risk_models.GsRiskModelApi.get_risk_model', Mock())
    mock.return_value = mock_risk_model_obj

    # mock getting factor returns
    mock = replace('gs_quant.markets.factor.Factor.intraday_returns', Mock())
    mock.return_value = (pd.DataFrame(mock_risk_model_factor_data_intraday.get('results')).set_index('time')
                         .drop(columns=["factorCategory", "factor", "factorId"], errors='ignore'))

    with DataContext(dt.datetime(2025, 1, 1, 0, 0, 0), dt.datetime(2025, 1, 1, 23, 59, 59)):
        actual = mrm.factor_returns_intraday(mock_risk_model(), 'Factor Name')
        assert len(actual.values) == 2
    replace.restore()


if __name__ == '__main__':
    pytest.main(args=[__file__])
