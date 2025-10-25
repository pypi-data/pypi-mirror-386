"""
Copyright 2018 Goldman Sachs.
Licensed under the Apache License, Version 2.0 (the 'License');
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

  http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing,
software distributed under the License is distributed on an
'AS IS' BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
KIND, either express or implied.  See the License for the
specific language governing permissions and limitations
under the License.
"""

import datetime as dt

import dateutil.parser as dup

from gs_quant.api.gs.portfolios import GsPortfolioApi, Portfolio, PositionSet
from gs_quant.common import Position
from gs_quant.session import Environment, GsSession


def test_get_many_portfolios(mocker):
    id_1 = 'MP1'
    id_2 = 'MP2'

    mock_response = {'results': (
        Portfolio.from_dict({'id': id_1, 'currency': 'USD', 'name': 'Example Port 1'}),
        Portfolio.from_dict({'id': id_2, 'currency': 'USD', 'name': 'Example Port 2'})
    ), 'totalResults': 2}

    expected_response = (
        Portfolio(id=id_1, currency='USD', name='Example Port 1'),
        Portfolio(id=id_2, currency='USD', name='Example Port 2')
    )

    # mock GsSession
    mocker.patch.object(
        GsSession.__class__,
        'default_value',
        return_value=GsSession.get(
            Environment.QA,
            'client_id',
            'secret'))
    mocker.patch.object(GsSession.current, '_get', return_value=mock_response)

    # run test
    response = GsPortfolioApi.get_portfolios()
    GsSession.current._get.assert_called_with('/portfolios?&limit=100', cls=Portfolio)
    assert response == expected_response


def test_get_portfolio(mocker):
    id_1 = 'MP1'
    mock_response = Portfolio(id=id_1, currency='USD', name='Example Port')

    # mock GsSession
    mocker.patch.object(
        GsSession.__class__,
        'default_value',
        return_value=GsSession.get(
            Environment.QA,
            'client_id',
            'secret'))
    mocker.patch.object(GsSession.current, '_get', return_value=mock_response)

    # run test
    response = GsPortfolioApi.get_portfolio(id_1)
    GsSession.current._get.assert_called_with('/portfolios/{id}'.format(id=id_1), cls=Portfolio)
    assert response == mock_response


def test_create_portfolio(mocker):
    id_1 = 'MP1'

    portfolio = Portfolio(id=id_1, currency='USD', name='Example Port')

    # mock GsSession
    mocker.patch.object(
        GsSession.__class__,
        'default_value',
        return_value=GsSession.get(
            Environment.QA,
            'client_id',
            'secret'))
    mocker.patch.object(GsSession.current, '_post', return_value=portfolio)

    # run test
    response = GsPortfolioApi.create_portfolio(portfolio)
    GsSession.current._post.assert_called_with('/portfolios', portfolio, cls=Portfolio)
    assert response == portfolio


def test_update_portfolio(mocker):
    id_1 = 'MP1'

    portfolio = Portfolio(id=id_1, currency='USD', name='Example Port Renamed')

    # mock GsSession
    mocker.patch.object(
        GsSession.__class__,
        'default_value',
        return_value=GsSession.get(
            Environment.QA,
            'client_id',
            'secret'))
    mocker.patch.object(GsSession.current, '_put', return_value=portfolio)

    # run test
    response = GsPortfolioApi.update_portfolio(portfolio)
    GsSession.current._put.assert_called_with('/portfolios/{id}'.format(id=id_1), portfolio, cls=Portfolio)
    assert response == portfolio


def test_delete_portfolio(mocker):
    id_1 = 'MP1'

    mock_response = "Successfully deleted portfolio."

    # mock GsSession
    mocker.patch.object(
        GsSession.__class__,
        'default_value',
        return_value=GsSession.get(
            Environment.QA,
            'client_id',
            'secret'))
    mocker.patch.object(GsSession.current, '_delete', return_value=mock_response)

    # run test
    response = GsPortfolioApi.delete_portfolio(id_1)
    GsSession.current._delete.assert_called_with('/portfolios/{id}'.format(id=id_1))
    assert response == mock_response


def test_get_portfolio_positions(mocker):
    id_1 = 'MP1'
    start_date = dt.date(2019, 2, 18)
    end_date = dt.date(2019, 2, 19)

    mock_response = {'positionSets': (
        {
            'id': 'mock1',
            'positionDate': '2019-02-18',
            'lastUpdateTime': '2019-02-19T12:10:32.401Z',
            'positions': [
                {'assetId': 'MQA123', 'quantity': 0.3},
                {'assetId': 'MQA456', 'quantity': 0.7}
            ]
        },
        {
            'id': 'mock2',
            'positionDate': '2019-02-19',
            'lastUpdateTime': '2019-02-20T05:04:32.981Z',
            'positions': [
                {'assetId': 'MQA123', 'quantity': 0.4},
                {'assetId': 'MQA456', 'quantity': 0.6}
            ]
        }
    )}

    expected_response = (
        PositionSet(
            id_='mock1',
            position_date=start_date,
            last_update_time=dup.parse('2019-02-19T12:10:32.401Z'),
            positions=(
                Position(assetId='MQA123', quantity=0.3),
                Position(assetId='MQA456', quantity=0.7)
            )),
        PositionSet(
            id_='mock2',
            position_date=end_date,
            last_update_time=dup.parse('2019-02-20T05:04:32.981Z'),
            positions=(
                Position(assetId='MQA123', quantity=0.4),
                Position(assetId='MQA456', quantity=0.6)
            ))
    )

    # mock GsSession
    mocker.patch.object(
        GsSession.__class__,
        'default_value',
        return_value=GsSession.get(
            Environment.QA,
            'client_id',
            'secret'))
    mocker.patch.object(GsSession.current, '_get', return_value=mock_response)

    # run test
    response = GsPortfolioApi.get_positions(id_1, start_date, end_date)

    GsSession.current._get.assert_called_with(
        '/portfolios/{id}/positions?type=close&startDate={sd}&endDate={ed}'.format(id=id_1, sd=start_date, ed=end_date))

    assert response == expected_response


def test_get_portfolio_positions_for_date(mocker):
    id_1 = 'MP1'
    date = dt.date(2019, 2, 18)

    mock_response = {'results': (
        PositionSet.from_dict({
            'id': 'mock1',
            'positionDate': '2019-02-18',
            'lastUpdateTime': '2019-02-19T12:10:32.401Z',
            'positions': [
                {'assetId': 'MQA123', 'quantity': 0.3},
                {'assetId': 'MQA456', 'quantity': 0.7}
            ]
        }),
    )}

    expected_response = (
        PositionSet(
            id_='mock1',
            position_date=date,
            last_update_time=dup.parse('2019-02-19T12:10:32.401Z'),
            positions=(
                Position(assetId='MQA123', quantity=0.3),
                Position(assetId='MQA456', quantity=0.7)
            ))
    )

    # mock GsSession
    mocker.patch.object(
        GsSession.__class__,
        'default_value',
        return_value=GsSession.get(
            Environment.QA,
            'client_id',
            'secret'))
    mocker.patch.object(GsSession.current, '_get', return_value=mock_response)

    # run test
    response = GsPortfolioApi.get_positions_for_date(id_1, date)

    GsSession.current._get.assert_called_with(
        '/portfolios/{id}/positions/{d}?type=close'.format(id=id_1, d=date),
        cls=PositionSet)

    assert response == expected_response


def test_get_latest_portfolio_positions(mocker):
    id_1 = 'MP1'
    date = dt.date(2019, 2, 18)

    mock_response = {
        'results': {
            'id': 'mock1',
            'positionDate': '2019-02-18',
            'lastUpdateTime': '2019-02-19T12:10:32.401Z',
            'positions': [
                {'assetId': 'MQA123', 'quantity': 0.3},
                {'assetId': 'MQA456', 'quantity': 0.7}
            ]
        }
    }

    expected_response = PositionSet(
        id_='mock1',
        position_date=date,
        last_update_time=dup.parse('2019-02-19T12:10:32.401Z'),
        positions=(
            Position(assetId='MQA123', quantity=0.3),
            Position(assetId='MQA456', quantity=0.7)
        ))

    # mock GsSession
    mocker.patch.object(
        GsSession.__class__,
        'default_value',
        return_value=GsSession.get(
            Environment.QA,
            'client_id',
            'secret'))
    mocker.patch.object(GsSession.current, '_get', return_value=mock_response)

    # run test
    response = GsPortfolioApi.get_latest_positions(id_1)

    GsSession.current._get.assert_called_with(
        '/portfolios/{id}/positions/last?type=close'.format(id=id_1))

    assert response == expected_response


def test_get_portfolio_position_dates(mocker):
    id_1 = 'MP1'

    mock_response = {'results': ('2019-02-18', '2019-02-19'), 'totalResults': 2}

    expected_response = (dt.date(2019, 2, 18), dt.date(2019, 2, 19))

    # mock GsSession
    mocker.patch.object(
        GsSession.__class__,
        'default_value',
        return_value=GsSession.get(
            Environment.QA,
            'client_id',
            'secret'))
    mocker.patch.object(GsSession.current, '_get', return_value=mock_response)

    # run test
    response = GsPortfolioApi.get_position_dates(id_1)

    GsSession.current._get.assert_called_with('/portfolios/{id}/positions/dates'.format(id=id_1))

    assert response == expected_response


def test_portfolio_positions_data(mocker):
    mock_response = {'results': [
        {
            'underlyingAssetId': 'MA4B66MW5E27UAFU2CD',
            'divisor': 8305900333.262549,
            'quantity': 0.016836826158,
            'positionType': 'close',
            'bbid': 'EXPE UW',
            'assetId': 'MA4B66MW5E27U8P32SB',
            'positionDate': '2019-11-07',
            'assetClassificationsGicsSector': 'Consumer Discretionary',
            'closePrice': 98.29,
            'ric': 'EXPE.OQ'
        },
    ]}

    expected_response = [
        {
            'underlyingAssetId': 'MA4B66MW5E27UAFU2CD',
            'divisor': 8305900333.262549,
            'quantity': 0.016836826158,
            'positionType': 'close',
            'bbid': 'EXPE UW',
            'assetId': 'MA4B66MW5E27U8P32SB',
            'positionDate': '2019-11-07',
            'assetClassificationsGicsSector': 'Consumer Discretionary',
            'closePrice': 98.29,
            'ric': 'EXPE.OQ'
        },
    ]

    # mock GsSession
    mocker.patch.object(
        GsSession.__class__,
        'default_value',
        return_value=GsSession.get(
            Environment.QA,
            'client_id',
            'secret'))
    mocker.patch.object(GsSession.current, '_get', return_value=mock_response)

    # run test
    response = GsPortfolioApi.get_positions_data('portfolio_id', dt.date(2020, 1, 1), dt.date(2021, 1, 1))

    GsSession.current._get.assert_called_with(
        '/portfolios/portfolio_id/positions/data?startDate=2020-01-01&endDate=2021-01-01')

    assert response == expected_response


def test_get_risk_models_by_coverage(mocker):
    mock_response = {'results': [
        {
            'model': "AXUS4S",
            'businessDate': "2021-03-18",
            'percentInModel': 0.9984356667970278
        },
        {
            'model': "AXUS4M",
            'businessDate': "2021-03-18",
            'percentInModel': 0.9984356667970278
        }
    ]
    }

    expected_response = [
        {
            'model': "AXUS4S",
            'businessDate': "2021-03-18",
            'percentInModel': 0.9984356667970278
        },
        {
            'model': "AXUS4M",
            'businessDate': "2021-03-18",
            'percentInModel': 0.9984356667970278
        }
    ]

    # mock GsSession
    mocker.patch.object(
        GsSession.__class__,
        'default_value',
        return_value=GsSession.get(
            Environment.QA,
            'client_id',
            'secret'))
    mocker.patch.object(GsSession.current, '_get', return_value=mock_response)

    # run test
    response = GsPortfolioApi.get_risk_models_by_coverage('portfolio_id')

    GsSession.current._get.assert_called_with('/portfolios/portfolio_id/models?sortByTerm=Medium')

    assert response == expected_response


def test_get_portfolio_analyze(mocker):
    mock_response = {
        "positionDate": "2024-05-27",
        "bonds": {
            "summary": {
                "trade": {
                    "numberOfBonds": 1,
                    "faceValue": 1000000.0,
                    "marketValue": 972564.12,
                    "DV01": 223.5730399056,
                    "bvalMidPrice": 97.256412,
                    "bvalUpdateTime": "2024-07-15T20:00:00Z",
                    "gSpread": 19.588,
                    "zSpread": 36.634,
                    "yieldToConvention": 4.494023,
                    "modifiedDuration": 2.2988,
                    "spreadToBenchmark": 28.5952,
                    "ratingSecondHighest": "AAA",
                    "ratingStandardAndPoors": "AA+",
                    "gsLiquidityScore": 1.75825,
                    "illiquidPercentage": 0.0,
                    "percentOfIssueOutstanding": 0.044444444444444446,
                    "didNotQuotePercentage": 0.0,
                    "chargeInDollars": 0.055893259976399996,
                    "chargeInBps": 2.5,
                    "chargeInEntityCurrency": 0.055893259976399996,
                    "weight": 100.0,
                    "girESG": {
                        "gPercentile": 87.88,
                        "gRegionalPercentile": 74.57,
                        "esPercentile": 92.78,
                        "esDisclosurePercentage": 80.95,
                        "esMomentumPercentile": 0.0
                    },
                    "carbon": {
                        "emissionsIntensityEnterpriseValue": 0.0,
                        "emissionsIntensityRevenue": 0.0
                    }
                },
                "buys": {
                    "numberOfBonds": 1,
                    "faceValue": 1000000.0,
                    "marketValue": 972564.12,
                    "DV01": 223.5730399056,
                    "bvalMidPrice": 97.256412,
                    "bvalUpdateTime": "2024-07-15T20:00:00Z",
                    "gSpread": 19.588,
                    "zSpread": 36.634,
                    "yieldToConvention": 4.494023,
                    "modifiedDuration": 2.2988,
                    "spreadToBenchmark": 28.5952,
                    "ratingSecondHighest": "AAA",
                    "ratingStandardAndPoors": "AA+",
                    "gsLiquidityScore": 1.75825,
                    "illiquidPercentage": 0.0,
                    "percentOfIssueOutstanding": 0.044444444444444446,
                    "didNotQuotePercentage": 0.0,
                    "chargeInDollars": 0.055893259976399996,
                    "chargeInBps": 2.5,
                    "chargeInEntityCurrency": 0.055893259976399996,
                    "weight": 100.0,
                    "girESG": {
                        "gPercentile": 87.88,
                        "gRegionalPercentile": 74.57,
                        "esPercentile": 92.78,
                        "esDisclosurePercentage": 80.95,
                        "esMomentumPercentile": 0.0
                    },
                    "carbon": {
                        "emissionsIntensityEnterpriseValue": 0.0,
                        "emissionsIntensityRevenue": 0.0
                    }
                },
                "sells": {
                    "numberOfBonds": 0,
                    "faceValue": 0.0,
                    "marketValue": 0.0,
                    "weight": 0.0
                }
            },
            "secondHighestRatingGroups": [
                {
                    "name": "AAA",
                    "yieldToConvention": 4.494023,
                    "modifiedDuration": 2.2988,
                    "spreadToBenchmark": 28.5952,
                    "marketValue": 972564.12,
                    "weight": 100.0
                }
            ],
            "standardAndPoorsRatingGroups": [
                {
                    "name": "AA+",
                    "yieldToConvention": 4.494023,
                    "modifiedDuration": 2.2988,
                    "spreadToBenchmark": 28.5952,
                    "marketValue": 972564.12,
                    "weight": 100.0,
                    "buyDirectionWeight": 1.0,
                    "sellDirectionWeight": "NaN"
                }
            ],
            "maturityGroups": [
                {
                    "name": "1-3y",
                    "yieldToConvention": 4.494023,
                    "modifiedDuration": 2.2988,
                    "spreadToBenchmark": 28.5952,
                    "marketValue": 972564.12,
                    "weight": 100.0
                }
            ],
            "sectorGroups": [
                {
                    "name": "Information Technology",
                    "yieldToConvention": 4.494023,
                    "modifiedDuration": 2.2988,
                    "spreadToBenchmark": 28.5952,
                    "marketValue": 972564.12,
                    "weight": 100.0,
                    "buyDirectionWeight": 1.0,
                    "sellDirectionWeight": "NaN"
                }
            ],
            "modifiedDurationGroups": [
                {
                    "name": "1-3y",
                    "yieldToConvention": 4.494023,
                    "modifiedDuration": 2.2988,
                    "spreadToBenchmark": 28.5952,
                    "marketValue": 972564.12,
                    "weight": 100.0
                }
            ],
            "gsLiquidityScoreGroups": [
                {
                    "name": "L1",
                    "yieldToConvention": 4.494023,
                    "modifiedDuration": 2.2988,
                    "spreadToBenchmark": 28.5952,
                    "marketValue": 972564.12,
                    "weight": 100.0
                }
            ],
            "seniorityGroups": [
                {
                    "name": "Senior",
                    "yieldToConvention": 4.494023,
                    "modifiedDuration": 2.2988,
                    "spreadToBenchmark": 28.5952,
                    "marketValue": 972564.12,
                    "weight": 100.0
                }
            ],
            "tradesByTicker": [
                {
                    "id": "MA3VNAYYHWQ52SA5",
                    "ticker": "AAPL",
                    "numberOfTrades": 1,
                    "weight": 100.0,
                    "faceValue": 1000000.0,
                    "marketValue": 972564.12,
                    "gsLiquidityScore": 1.75825,
                    "percentOfIssueOutstanding": 0.044444444444444446
                }
            ],
            "constituents": [
                {
                    "assetId": "MA3VNAYYHWQ52SA5",
                    "name": "AAPL 3.350 02/09/2027",
                    "assetClass": "Credit",
                    "type": "Bond",
                    "isin": "US037833CJ77",
                    "bbid": "AM3834018",
                    "cusip": "037833CJ7",
                    "ticker": "AAPL",
                    "currency": "USD",
                    "region": "Americas",
                    "sector": "Information Technology",
                    "seniority": "Senior",
                    "ratingSecondHighest": "AAA",
                    "ratingSecondHighestLinear": 1,
                    "ratingStandardAndPoors": "AA+",
                    "ratingStandardAndPoorsLinear": 2,
                    "gsLiquidityScore": 1.75825,
                    "gsLiquidityScoreGroup": "L1",
                    "percentOfIssueOutstanding": 0.044444444444444446,
                    "maturity": 2.0,
                    "coupon": 3.35,
                    "bvalMidPrice": 97.256412,
                    "dirtyPrice": 97.270928666667,
                    "gSpread": 19.588,
                    "zSpread": 36.634,
                    "bvalUpdateTime": "2024-07-15T20:00:00Z",
                    "yieldToConvention": 4.494023,
                    "modifiedDuration": 2.2988,
                    "spreadToBenchmark": 28.5952,
                    "benchmark": "GV91282CKZ3",
                    "quoteConvention": "Spread",
                    "chargeInQuoteConvention": "2.5 bps",
                    "chargeInQuoteConventionTwo": "2.5 bps",
                    "chargeInLocalCurrency": 0.055893259976399996,
                    "chargeInEntityCurrency": 0.055893259976399996,
                    "chargeInBps": 2.5,
                    "fxSpot": 1.0,
                    "direction": "Buy",
                    "faceValue": 1000000.0,
                    "currentFaceValue": 1000000.0,
                    "accruedInterestStandard": 0.014516666667,
                    "marketValue": 972564.12,
                    "dirtyMarketValue": 972709.28666667,
                    "DV01": 223.5730399056,
                    "weightOfFaceValue": 100.0,
                    "weightOfMarketValue": 100.0,
                    "weightOfDV01": 100.0,
                    "indicativePrice": 97.289,
                    "indicativeQuantity": 5000000.0,
                    "indicativeSpread": 25.0,
                    "indicativeYield": 4.48,
                    "girFactors": {
                        "carry": 1.0,
                        "value": 3.0,
                        "risk": 1.0,
                        "momentum": 1.0,
                        "liquidity": 4.0,
                        "highLeverage": 0.0,
                        "lowLeverage": 0.0,
                        "highInterestCoverage": 0.0,
                        "lowInterestCoverage": 0.0,
                        "cyclical": 1.0,
                        "defensive": 0.0,
                        "commoditiesRelated": 0.0,
                        "tax": 4.0
                    },
                    "girESG": {
                        "gPercentile": 87.88,
                        "gRegionalPercentile": 74.57,
                        "esPercentile": 92.78,
                        "esDisclosurePercentage": 80.95,
                        "esMomentumPercentile": 0.0
                    },
                    "carbon": {
                        "scienceBasedTarget": "Yes",
                        "netZeroEmissionsTarget": "Yes"
                    },
                    "pbData": {
                        "indicativeShortFinancingLabel": "GC",
                        "indicativeLongFinancingLabel": "IG Funding Rate"
                    },
                    "bbgData": {
                        "countryOfRisk": "US",
                        "paymentRank": "Sr Unsecured",
                        "industrySector": "Technology",
                        "industryGroup": "Computers",
                        "industrySubGroup": "Computers"
                    }
                }
            ]
        }
    }

    expected_response = {
        "positionDate": "2024-05-27",
        "bonds": {
            "summary": {
                "trade": {
                    "numberOfBonds": 1,
                    "faceValue": 1000000.0,
                    "marketValue": 972564.12,
                    "DV01": 223.5730399056,
                    "bvalMidPrice": 97.256412,
                    "bvalUpdateTime": "2024-07-15T20:00:00Z",
                    "gSpread": 19.588,
                    "zSpread": 36.634,
                    "yieldToConvention": 4.494023,
                    "modifiedDuration": 2.2988,
                    "spreadToBenchmark": 28.5952,
                    "ratingSecondHighest": "AAA",
                    "ratingStandardAndPoors": "AA+",
                    "gsLiquidityScore": 1.75825,
                    "illiquidPercentage": 0.0,
                    "percentOfIssueOutstanding": 0.044444444444444446,
                    "didNotQuotePercentage": 0.0,
                    "chargeInDollars": 0.055893259976399996,
                    "chargeInBps": 2.5,
                    "chargeInEntityCurrency": 0.055893259976399996,
                    "weight": 100.0,
                    "girESG": {
                        "gPercentile": 87.88,
                        "gRegionalPercentile": 74.57,
                        "esPercentile": 92.78,
                        "esDisclosurePercentage": 80.95,
                        "esMomentumPercentile": 0.0
                    },
                    "carbon": {
                        "emissionsIntensityEnterpriseValue": 0.0,
                        "emissionsIntensityRevenue": 0.0
                    }
                },
                "buys": {
                    "numberOfBonds": 1,
                    "faceValue": 1000000.0,
                    "marketValue": 972564.12,
                    "DV01": 223.5730399056,
                    "bvalMidPrice": 97.256412,
                    "bvalUpdateTime": "2024-07-15T20:00:00Z",
                    "gSpread": 19.588,
                    "zSpread": 36.634,
                    "yieldToConvention": 4.494023,
                    "modifiedDuration": 2.2988,
                    "spreadToBenchmark": 28.5952,
                    "ratingSecondHighest": "AAA",
                    "ratingStandardAndPoors": "AA+",
                    "gsLiquidityScore": 1.75825,
                    "illiquidPercentage": 0.0,
                    "percentOfIssueOutstanding": 0.044444444444444446,
                    "didNotQuotePercentage": 0.0,
                    "chargeInDollars": 0.055893259976399996,
                    "chargeInBps": 2.5,
                    "chargeInEntityCurrency": 0.055893259976399996,
                    "weight": 100.0,
                    "girESG": {
                        "gPercentile": 87.88,
                        "gRegionalPercentile": 74.57,
                        "esPercentile": 92.78,
                        "esDisclosurePercentage": 80.95,
                        "esMomentumPercentile": 0.0
                    },
                    "carbon": {
                        "emissionsIntensityEnterpriseValue": 0.0,
                        "emissionsIntensityRevenue": 0.0
                    }
                },
                "sells": {
                    "numberOfBonds": 0,
                    "faceValue": 0.0,
                    "marketValue": 0.0,
                    "weight": 0.0
                }
            },
            "secondHighestRatingGroups": [
                {
                    "name": "AAA",
                    "yieldToConvention": 4.494023,
                    "modifiedDuration": 2.2988,
                    "spreadToBenchmark": 28.5952,
                    "marketValue": 972564.12,
                    "weight": 100.0
                }
            ],
            "standardAndPoorsRatingGroups": [
                {
                    "name": "AA+",
                    "yieldToConvention": 4.494023,
                    "modifiedDuration": 2.2988,
                    "spreadToBenchmark": 28.5952,
                    "marketValue": 972564.12,
                    "weight": 100.0,
                    "buyDirectionWeight": 1.0,
                    "sellDirectionWeight": "NaN"
                }
            ],
            "maturityGroups": [
                {
                    "name": "1-3y",
                    "yieldToConvention": 4.494023,
                    "modifiedDuration": 2.2988,
                    "spreadToBenchmark": 28.5952,
                    "marketValue": 972564.12,
                    "weight": 100.0
                }
            ],
            "sectorGroups": [
                {
                    "name": "Information Technology",
                    "yieldToConvention": 4.494023,
                    "modifiedDuration": 2.2988,
                    "spreadToBenchmark": 28.5952,
                    "marketValue": 972564.12,
                    "weight": 100.0,
                    "buyDirectionWeight": 1.0,
                    "sellDirectionWeight": "NaN"
                }
            ],
            "modifiedDurationGroups": [
                {
                    "name": "1-3y",
                    "yieldToConvention": 4.494023,
                    "modifiedDuration": 2.2988,
                    "spreadToBenchmark": 28.5952,
                    "marketValue": 972564.12,
                    "weight": 100.0
                }
            ],
            "gsLiquidityScoreGroups": [
                {
                    "name": "L1",
                    "yieldToConvention": 4.494023,
                    "modifiedDuration": 2.2988,
                    "spreadToBenchmark": 28.5952,
                    "marketValue": 972564.12,
                    "weight": 100.0
                }
            ],
            "seniorityGroups": [
                {
                    "name": "Senior",
                    "yieldToConvention": 4.494023,
                    "modifiedDuration": 2.2988,
                    "spreadToBenchmark": 28.5952,
                    "marketValue": 972564.12,
                    "weight": 100.0
                }
            ],
            "tradesByTicker": [
                {
                    "id": "MA3VNAYYHWQ52SA5",
                    "ticker": "AAPL",
                    "numberOfTrades": 1,
                    "weight": 100.0,
                    "faceValue": 1000000.0,
                    "marketValue": 972564.12,
                    "gsLiquidityScore": 1.75825,
                    "percentOfIssueOutstanding": 0.044444444444444446
                }
            ],
            "constituents": [
                {
                    "assetId": "MA3VNAYYHWQ52SA5",
                    "name": "AAPL 3.350 02/09/2027",
                    "assetClass": "Credit",
                    "type": "Bond",
                    "isin": "US037833CJ77",
                    "bbid": "AM3834018",
                    "cusip": "037833CJ7",
                    "ticker": "AAPL",
                    "currency": "USD",
                    "region": "Americas",
                    "sector": "Information Technology",
                    "seniority": "Senior",
                    "ratingSecondHighest": "AAA",
                    "ratingSecondHighestLinear": 1,
                    "ratingStandardAndPoors": "AA+",
                    "ratingStandardAndPoorsLinear": 2,
                    "gsLiquidityScore": 1.75825,
                    "gsLiquidityScoreGroup": "L1",
                    "percentOfIssueOutstanding": 0.044444444444444446,
                    "maturity": 2.0,
                    "coupon": 3.35,
                    "bvalMidPrice": 97.256412,
                    "dirtyPrice": 97.270928666667,
                    "gSpread": 19.588,
                    "zSpread": 36.634,
                    "bvalUpdateTime": "2024-07-15T20:00:00Z",
                    "yieldToConvention": 4.494023,
                    "modifiedDuration": 2.2988,
                    "spreadToBenchmark": 28.5952,
                    "benchmark": "GV91282CKZ3",
                    "quoteConvention": "Spread",
                    "chargeInQuoteConvention": "2.5 bps",
                    "chargeInQuoteConventionTwo": "2.5 bps",
                    "chargeInLocalCurrency": 0.055893259976399996,
                    "chargeInEntityCurrency": 0.055893259976399996,
                    "chargeInBps": 2.5,
                    "fxSpot": 1.0,
                    "direction": "Buy",
                    "faceValue": 1000000.0,
                    "currentFaceValue": 1000000.0,
                    "accruedInterestStandard": 0.014516666667,
                    "marketValue": 972564.12,
                    "dirtyMarketValue": 972709.28666667,
                    "DV01": 223.5730399056,
                    "weightOfFaceValue": 100.0,
                    "weightOfMarketValue": 100.0,
                    "weightOfDV01": 100.0,
                    "indicativePrice": 97.289,
                    "indicativeQuantity": 5000000.0,
                    "indicativeSpread": 25.0,
                    "indicativeYield": 4.48,
                    "girFactors": {
                        "carry": 1.0,
                        "value": 3.0,
                        "risk": 1.0,
                        "momentum": 1.0,
                        "liquidity": 4.0,
                        "highLeverage": 0.0,
                        "lowLeverage": 0.0,
                        "highInterestCoverage": 0.0,
                        "lowInterestCoverage": 0.0,
                        "cyclical": 1.0,
                        "defensive": 0.0,
                        "commoditiesRelated": 0.0,
                        "tax": 4.0
                    },
                    "girESG": {
                        "gPercentile": 87.88,
                        "gRegionalPercentile": 74.57,
                        "esPercentile": 92.78,
                        "esDisclosurePercentage": 80.95,
                        "esMomentumPercentile": 0.0
                    },
                    "carbon": {
                        "scienceBasedTarget": "Yes",
                        "netZeroEmissionsTarget": "Yes"
                    },
                    "pbData": {
                        "indicativeShortFinancingLabel": "GC",
                        "indicativeLongFinancingLabel": "IG Funding Rate"
                    },
                    "bbgData": {
                        "countryOfRisk": "US",
                        "paymentRank": "Sr Unsecured",
                        "industrySector": "Technology",
                        "industryGroup": "Computers",
                        "industrySubGroup": "Computers"
                    }
                }
            ]
        }
    }

    # mock GsSession
    mocker.patch.object(
        GsSession.__class__,
        'default_value',
        return_value=GsSession.get(
            Environment.QA,
            'client_id',
            'secret'))
    mocker.patch.object(GsSession.current, '_get', return_value=mock_response)

    # run test
    response = GsPortfolioApi.get_portfolio_analyze('portfolio_id')

    GsSession.current._get.assert_called_with('/portfolios/portfolio_id/analyze')

    assert response == expected_response
