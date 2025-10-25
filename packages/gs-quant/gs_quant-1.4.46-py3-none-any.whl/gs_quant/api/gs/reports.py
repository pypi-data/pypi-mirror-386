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
import logging
import urllib.parse
from enum import Enum
from typing import Tuple, List, Dict

import backoff

from gs_quant.base import EnumBase
from gs_quant.common import Currency, PositionTag
from gs_quant.errors import MqTimeoutError, MqInternalServerError, MqRateLimitedError
from gs_quant.session import GsSession
from gs_quant.target.reports import Report

_logger = logging.getLogger(__name__)


class OrderType(EnumBase, Enum):
    """Source object for position data"""

    Ascending = 'Ascending'
    Descending = 'Descending'


class FactorRiskTableMode(EnumBase, Enum):
    """Source object for position data"""

    Pnl = 'Pnl'
    Exposure = 'Exposure'
    ZScore = 'ZScore'
    Mctr = 'Mctr'


class GsReportApi:
    """GS Reports API client implementation"""

    @classmethod
    def create_report(cls, report: Report) -> Report:
        return GsSession.current._post('/reports', report, cls=Report)

    @classmethod
    def get_report(cls, report_id: str) -> Report:
        return GsSession.current._get('/reports/{id}'.format(id=report_id), cls=Report)

    @classmethod
    def get_reports(cls, limit: int = 100, offset: int = None, position_source_type: str = None,
                    position_source_id: str = None, status: str = None, report_type: str = None,
                    order_by: str = None, tags: Dict = None, scroll: str = None) -> Tuple[Report, ...]:
        def build_url(scroll_id=None):
            url = f'/reports?limit={limit}'
            if scroll:
                url += '&scroll={scroll}'.format(scroll=scroll)
            if scroll_id:
                url += f'&scrollId={scroll_id}'
            if offset:
                url += '&offset={offset}'.format(offset=offset)
            if position_source_type:
                url += f'&positionSourceType={position_source_type}'
            if position_source_id:
                url += f'&positionSourceId={position_source_id}'
            if status:
                url += f'&status={status}'
            if report_type:
                url += f'&reportType={urllib.parse.quote(report_type)}'
            if order_by:
                url += f'&orderBy={order_by}'
            return url

        response = GsSession.current._get(build_url(), cls=Report)
        results = response.get('results', [])

        while response.get('scrollId') and response.get('results'):
            response = GsSession.current._get(build_url(scroll_id=response.get('scrollId')), cls=Report)
            results += response.get('results', [])

        if tags is not None:
            tags_as_list = tuple(PositionTag(name=key, value=tags[key]) for key in tags)
            results = [r for r in results if r.parameters.tags == tags_as_list]
        else:
            results = [r for r in results if r.parameters.tags is None]
        return tuple(results)

    @classmethod
    def update_report(cls, report: Report) -> dict:
        return GsSession.current._put('/reports/{id}'.format(id=report.id), report, cls=Report)

    @classmethod
    def delete_report(cls, report_id: str) -> dict:
        return GsSession.current._delete('/reports/{id}'.format(id=report_id))

    @classmethod
    @backoff.on_exception(lambda: backoff.expo(base=2, factor=2),
                          (MqTimeoutError, MqInternalServerError),
                          max_tries=5)
    @backoff.on_exception(lambda: backoff.constant(90),
                          MqRateLimitedError,
                          max_tries=5)
    def schedule_report(cls, report_id: str, start_date: dt.date, end_date: dt.date, backcast: bool = False) -> dict:
        report_schedule_request = {
            'startDate': start_date.strftime('%Y-%m-%d'),
            'endDate': end_date.strftime('%Y-%m-%d')
        }
        if backcast:
            report_schedule_request['parameters'] = {'backcast': backcast}
        return GsSession.current._post('/reports/{id}/schedule'.format(id=report_id), report_schedule_request)

    @classmethod
    def get_report_status(cls, report_id: str) -> Tuple[dict, ...]:
        return GsSession.current._get('/reports/{id}/status'.format(id=report_id))

    @classmethod
    def get_report_jobs(cls, report_id: str) -> Tuple[dict, ...]:
        return GsSession.current._get('/reports/{id}/jobs'.format(id=report_id))['results']

    @classmethod
    def get_report_job(cls, report_job_id: str) -> dict:
        return GsSession.current._get('/reports/jobs/{report_job_id}'.format(report_job_id=report_job_id))

    @classmethod
    def reschedule_report_job(cls, report_job_id: str):
        return GsSession.current._post(f'/reports/jobs/{report_job_id}/reschedule', {})

    @classmethod
    def cancel_report_job(cls, report_job_id: str) -> dict:
        return GsSession.current._post('/reports/jobs/{report_job_id}/cancel'.format(report_job_id=report_job_id))

    @classmethod
    def update_report_job(cls, report_job_id: str, status: str) -> dict:
        status_body = {
            "status": '{status}'.format(status=status)
        }
        return GsSession.current._post('/reports/jobs/{report_job_id}/update'.format(report_job_id=report_job_id),
                                       status_body)

    @classmethod
    def get_custom_aum(cls,
                       report_id: str,
                       start_date: dt.date = None,
                       end_date: dt.date = None) -> dict:
        url = f'/reports/{report_id}/aum?'
        if start_date:
            url += f"&startDate={start_date.strftime('%Y-%m-%d')}"
        if end_date:
            url += f"&endDate={end_date.strftime('%Y-%m-%d')}"
        return GsSession.current._get(url)['data']

    @classmethod
    def upload_custom_aum(cls,
                          report_id: str,
                          aum_data: List[dict],
                          clear_existing_data: bool = None) -> dict:
        url = f'/reports/{report_id}/aum'
        payload = {'data': aum_data}
        if clear_existing_data:
            url += '?clearExistingData=true'
        return GsSession.current._post(url, payload)

    @classmethod
    @backoff.on_exception(lambda: backoff.expo(base=2, factor=2),
                          (MqTimeoutError, MqInternalServerError),
                          max_tries=5)
    @backoff.on_exception(lambda: backoff.constant(90),
                          MqRateLimitedError,
                          max_tries=5)
    def get_factor_risk_report_results(cls,
                                       risk_report_id: str,
                                       view: str = None,
                                       factors: List[str] = None,
                                       factor_categories: List[str] = None,
                                       currency: Currency = None,
                                       start_date: dt.date = None,
                                       end_date: dt.date = None,
                                       unit: str = None) -> dict:
        url = f'/risk/factors/reports/{risk_report_id}/results?'
        if view is not None:
            url += f'&view={view}'
        if factors is not None:
            factors = map(urllib.parse.quote, factors)  # to support factors like "Automobiles & Components"
            url += f'&factors={"&factors=".join(factors)}'
        if factor_categories is not None:
            url += f'&factorCategories={"&factorCategories=".join(factor_categories)}'
        if currency is not None:
            url += f'&currency={currency.value}'
        if start_date is not None:
            url += f'&startDate={start_date.strftime("%Y-%m-%d")}'
        if end_date is not None:
            url += f'&endDate={end_date.strftime("%Y-%m-%d")}'
        if unit is not None:
            url += f'&unit={unit}'

        return GsSession.current._get(url)

    @classmethod
    def get_factor_risk_report_view(cls,
                                    risk_report_id: str,
                                    factor: str = None,
                                    factor_category: str = None,
                                    currency: Currency = None,
                                    start_date: dt.date = None,
                                    end_date: dt.date = None,
                                    unit: str = None) -> dict:

        query_string = urllib.parse.urlencode(
            dict(filter(lambda item: item[1] is not None,
                        dict(factor=factor, factorCategory=factor_category,
                             currency=currency, startDate=start_date, endDate=end_date, unit=unit).items())))

        GsSession.current.api_version = "v2"
        url = f'/factor/risk/{risk_report_id}/views?{query_string}'
        response = GsSession.current._get(url)
        GsSession.current.api_version = "v1"
        return response

    @classmethod
    def get_factor_risk_report_table(cls,
                                     risk_report_id: str,
                                     mode: FactorRiskTableMode = None,
                                     unit: str = None,
                                     currency: Currency = None,
                                     date: dt.date = None,
                                     start_date: dt.date = None,
                                     end_date: dt.date = None) -> dict:

        GsSession.current.api_version = "v2"
        url = f'/factor/risk/{risk_report_id}/tables?'
        if mode is not None:
            url += f'&mode={mode.value}'
        if unit is not None:
            url += f'&unit={unit}'
        if currency is not None:
            url += f'&currency={currency.value}'
        if date is not None:
            url += f'&date={date.strftime("%Y-%m-%d")}'
        if start_date is not None:
            url += f'&startDate={start_date.strftime("%Y-%m-%d")}'
        if end_date is not None:
            url += f'&endDate={end_date.strftime("%Y-%m-%d")}'

        response = GsSession.current._get(url)
        GsSession.current.api_version = "v1"
        return response

    @classmethod
    def get_brinson_attribution_results(cls,
                                        portfolio_id: str,
                                        benchmark: str = None,
                                        currency: Currency = None,
                                        include_interaction: bool = None,
                                        aggregation_type: str = None,
                                        aggregation_category: str = None,
                                        start_date: dt.date = None,
                                        end_date: dt.date = None):
        url = f'/attribution/{portfolio_id}/brinson?'
        if benchmark is not None:
            url += f'&benchmark={benchmark}'
        if currency is not None:
            url += f'&currency={currency.value}'
        if include_interaction is not None:
            url += f'&includeInteraction={str(include_interaction).lower()}'
        if aggregation_type is not None:
            url += f'&aggregationType={aggregation_type}'
        if aggregation_category is not None:
            url += f'&aggregationCategory={aggregation_category}'
        if start_date is not None:
            url += f'&startDate={start_date.strftime("%Y-%m-%d")}'
        if end_date is not None:
            url += f'&endDate={end_date.strftime("%Y-%m-%d")}'

        return GsSession.current._get(url)
