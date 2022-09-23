import os
import json
import time

import requests
import urllib

from .exceptions import (
    ResourceNotFoundException,
    ErrorResponseException,
    ParameterException,
    TimeoutException,
    SQLErrorException,
)


class RedashAPIClient(object):
    def __init__(self, api_key=None, host=None, proxy=None, timeout=None):
        if api_key:
            self.api_key = api_key
        else:
            self.api_key = os.environ.get('REDASH_API_KEY')
        if host:
            self.host = host
        else:
            self.host = os.environ.get('REDASH_SERVICE_URL')
        if timeout:
            self.timeout = timeout
        else:
            self.timeout = os.environ.get('REDASH_TIMEOUT') if os.environ.get('REDASH_TIMEOUT') else 10

        if proxy:
            self.proxy = proxy
        else:
            self.proxy = os.environ.get('REDASH_HTTP_PROXY') if os.environ.get('REDASH_HTTP_PROXY') else None

        self._validate_init()
        self.s = requests.Session()
        self.s.headers.update({'Authorization': f'Key {self.api_key}'})
        if self.proxy:
            self.s.proxies.update({'http': self.proxy, 'https': self.proxy})

    def get_server_version(self):
        res = self._get('status.json', prefix='')
        return res['version']

    def is_exist_by_query_id(self, query_id: int):
        return self.get_query_by_id(query_id) is not None

    def create_query(self, name, data_source_name: str, query: str, description='', is_publish: bool = True):
        data_source = self.get_data_source_by_name(data_source_name)
        data_source_id = data_source['id']
        payload = {
            'name': name,
            'data_source_id': data_source_id,
            'query': query,
            'description': description,
        }
        res = self._post('queries', payload)

        if is_publish:
            return self.update_query(
                query_id=res['id'],
                is_publish=is_publish,
            )
        return res

    def update_query(
            self,
            query_id: int,
            name=None,
            data_source_name: str = None,
            query: str = None,
            description: str = None,
            is_publish: bool = True
    ):
        payload = {}
        if name:
            payload['name'] = name
        if data_source_name:
            data_source = self.get_data_source_by_name(data_source_name)
            payload['data_source_id'] = data_source['id']
        if query:
            payload['query'] = query
        if description:
            payload['description'] = description
        # draft false is published
        payload['is_draft'] = not is_publish

        return self._post(f'queries/{query_id}', payload)

    def update_or_create_query(
            self,
            query_id: int,
            name=None,
            data_source_name: str = None,
            query: str = None,
            description: str = None,
            is_publish: bool = True
    ):
        if self.is_exist_by_query_id(query_id=query_id):
            return self.update_query(
                query_id,
                name,
                data_source_name,
                query,
                description,
                is_publish
            )
        else:
            return self.create_query(
                name,
                data_source_name,
                query,
                description,
                is_publish
            )

    def get_query_by_id(self, query_id):
        try:
            return self._get(f'queries/{query_id}')
        except ResourceNotFoundException:
            return None

    def get_data_sources(self):
        """
        [
            {
                "name": "hogehoge",
                "pause_reason": null,
                "syntax": "sql",
                "paused": 0,
                "view_only": false,
                "type": "pg",
                "id": 1
            },
            {
                "name": "fugafuga",
                "pause_reason": null,
                "syntax": "sql",
                "paused": 0,
                "view_only": false,
                "type": "athena",
                "id": 2
            },
        ]
        :return:
        """
        return self._get('data_sources')

    def get_data_source_by_name(self, name: str):
        """
        {
            "name": "hogehoge",
            "pause_reason": null,
            "syntax": "sql",
            "paused": 0,
            "view_only": false,
            "type": "pg",
            "id": 1
        },
        :param name:
        :return:
        """
        data_sources = self.get_data_sources()
        for data_source in data_sources:
            if data_source['name'] == name:
                return data_source
        raise ResourceNotFoundException(f'{name} is not found')

    def get_query_results_by_id(self, query_id: int, retry_count=5, **kwargs):
        """
        {
            "query_result": {
                "retrieved_at": "2019-08-30T08:30:27.967Z",
                "query_hash": "xxxxxxxxx",
                "query": "select count(*) from hoge;",
                "runtime": 0.1,
                "data": {
                    "rows": [
                        {
                            "count(*)": 0
                        }
                    ],
                    "columns": [
                        {
                            "friendly_name": "count(*)",
                            "type": "integer",
                            "name": "count(*)"
                        }
                    ]
                },
                "id": 1,
                "data_source_id": 1
            }
        }
        :param query_id:
        :param retry_count:
        :param kwargs:
        :return:
        """
        res = self._post('queries/{}/results'.format(query_id), payload=kwargs)
        # already has a result
        if 'query_result' in res:
            return res

        # running job now
        job_id = res['job']['id']
        return self._check_and_wait_query_result(job_id=job_id, retry_count=retry_count)

    def get_adhoc_query_result(
            self, query: str, data_source_name: str, retry_count=5, max_age=-1, retry_interval=0, **kwargs
    ):
        """
        {
            "query_result": {
                "retrieved_at": "2019-08-30T08:30:27.967Z",
                "query_hash": "xxxxxxxxx",
                "query": "select count(*) from hoge;",
                "runtime": 0.1,
                "data": {
                    "rows": [
                        {
                            "count(*)": 0
                        }
                    ],
                    "columns": [
                        {
                            "friendly_name": "count(*)",
                            "type": "integer",
                            "name": "count(*)"
                        }
                    ]
                },
                "id": 1,
                "data_source_id": 1
            }
        }
        :param query:
        :param data_source_name:
        :param retry_count:
        :param kwargs:
        :return:
        """
        data_source = self.get_data_source_by_name(data_source_name)
        data_source_id = data_source['id']
        params = {
            'query': query,
            'query_id': 'adhoc',
            'data_source_id': data_source_id,
            'max_age': max_age,
            'parameters': kwargs,
        }
        res = self._post('query_results', payload=params)
        # already has a result
        if 'query_result' in res:
            return res

        # running job now
        job_id = res['job']['id']
        return self._check_and_wait_query_result(job_id=job_id, retry_count=retry_count, retry_interval=retry_interval)

    def get_data_source_schema(self, data_source_name, retry_count=5):
        """
        {
            "schema": [
                {
                    "name": "XXXXX",
                    "columns": [
                        "deal_name",
                        "deal_id",
                        "company_id",
                        "pipeline_id"
                    ]
                },
                {
                    "name": "VVVVVV",
                    "columns": [
                        "pipeline_id",
                        "display_order",
                        "label",
                        "active"
                    ]
                },
            ]
        }


        """
        data_source = self.get_data_source_by_name(data_source_name)
        data_source_id = data_source['id']
        res = self._get(f'data_sources/{data_source_id}/schema')
        # running job now
        if 'job' in res:
            job_id = res['job']['id']
            return self._check_and_wait_query_result(job_id=job_id, retry_count=retry_count)
        return res

    def _check_and_wait_query_result(self, job_id, retry_count, retry_interval=0):
        """
        wait return result for job
        """
        # running job now
        retry = 0
        while True:
            res = self._get(f'jobs/{job_id}')
            job = res['job']
            if job['query_result_id']:
                break
            # error
            if job['status'] == 4:
                raise SQLErrorException(job['error'])
            retry += 1
            if retry_count <= retry:
                raise TimeoutException('Query Result not returned.(retried {})'.format(retry_count))
            time.sleep(retry_interval)
        query_result_id = job['query_result_id']
        return self._get(f'query_results/{query_result_id}')

    def _get(self, uri, prefix='/api/'):
        url = urllib.parse.urljoin(f'{self.host}{prefix}', uri)
        res = self.s.get(url, timeout=self.timeout)
        if res.status_code != 200:
            if res.status_code == 404:
                raise ResourceNotFoundException(f'Retrieve data from URL: {url} failed.')
            raise ErrorResponseException(f'Retrieve data from URL: {url} failed.', status_code=res.status_code)

        return res.json()

    def _post(self, uri, payload=None, prefix='/api/'):
        url = f'{self.host}{prefix}{uri}'
        if not payload:
            data = json.dumps({})
        else:
            data = json.dumps(payload)

        self.s.headers.update({'Content-Type': 'application/json'})
        res = self.s.post(f'{url}', data=data)

        if res.status_code != 200:
            if res.status_code == 404:
                raise ResourceNotFoundException(f'Post data from URL: {url} failed.')
            raise ErrorResponseException(f'Post data to URL: {url} failed.', status_code=res.status_code)

        return res.json()

    def _delete(self, uri, prefix='/api/'):
        url = f'{self.host}{prefix}{uri}'
        res = self.s.delete(f'{url}')

        if res.status_code != 200:
            if res.status_code == 404:
                raise ResourceNotFoundException(f'Delete data from URL: {url} failed.')
            else:
                raise ErrorResponseException(f'Delete data from URL: {url} failed.', status_code=res.status_code)

        return res.json()

    def _validate_init(self):
        if not self.api_key:
            raise ParameterException('not set REDASH_API_KEY environment value')

        if not self.host:
            raise ParameterException('not set REDASH_SERVICE_URL environment value')

