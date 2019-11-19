import functools
import logging
import os
import mimetypes

import requests


class HuntflowAPI:
    def __init__(self, token, api_url, user_agent='test_task/1.0 (vshevchenko)', timeout=5):
        self.api_url = api_url if api_url.endswith('/') else api_url + '/'
        self.session = self.create_session(token, user_agent)
        self.session.request = functools.partial(self.session.request, timeout=timeout)

    @staticmethod
    def create_session(token, user_agent):
        s = requests.Session()
        s.headers.update({
            'User-Agent': user_agent,
            'Authorization': f'Bearer {token}'
        })
        return s

    # TODO: add repeater
    # TODO: cached
    def accounts(self):
        res = self.session.get(self.api_url + 'accounts')
        res.raise_for_status()
        res = res.json()['items']
        logging.debug(f'got {res} /accounts')
        return res

    # TODO: add repeater
    def upload(self, account_id, filename):
        files = {'file': (os.path.basename(filename),
                          open(filename, 'rb'),
                          mimetypes.MimeTypes().guess_type(filename)[0])}

        res = self.session.post(
            self.api_url + f'account/{account_id}/upload',
            headers={'X-File-Parse': 'true'},
            files=files
        )
        res.raise_for_status()
        res = res.json()
        logging.debug(f'uploaded {filename}, response "{res}"')
        return res

    # TODO: add repeater
    def vacancies(self, account_id, mine=None, opened=None):
        # TODO: adopt for pagination!
        params = {}
        if mine is not None:
            params['mine'] = mine
        if opened is not None:
            params['opened'] = opened

        res = self.session.get(self.api_url + f'account/{account_id}/vacancies', params=params)
        res.raise_for_status()
        res = res.json()

        items = res['items']
        if res['total'] > len(items):
            logging.warning(f'got only {len(items)} from {res["total"]} vacancies (TODO: exhaust)')

        logging.debug(f'got vacancies "{res}"')
        return items

    # TODO: add repeater
    # TODO: cached
    def vacancy_statuses(self, account_id):
        res = self.session.get(self.api_url + f'account/{account_id}/vacancy/statuses')
        res.raise_for_status()
        res = res.json()['items']
        logging.debug(f'got vacancy statuses "{res}"')
        return res

    # TODO: add repeater
    def add_applicant(self, account_id, data):
        res = self.session.post(self.api_url + f'account/{account_id}/applicants', json=data)
        res.raise_for_status()
        res = res.json()
        logging.debug(f'added applicant {data["last_name"]} {data["first_name"]} - "{res}"')
        return res

    def add_applicant_to_vacancy(self, account_id, applicant_id, data):
        res = self.session.post(self.api_url + f'account/{account_id}/applicants/{applicant_id}/vacancy',
                                json=data)
        res.raise_for_status()
        res = res.json()
        logging.debug(f'added applicant {applicant_id} to vacancy {data} - "{res}"')
        return res

# TODO: reduce dup code
