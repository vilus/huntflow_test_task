import logging


UPLOAD_RESUME = 'upload_resume'
ADD_APPLICANT = 'add_applicant'
ADD_APPLICANT_TO_VACANCY = 'add_application_to_vacancy'


class WorkerError(Exception):
    pass


class Worker:
    def __init__(self, api, states_storage):
        self.api = api
        self.states_storage = states_storage

    def just_doit(self, applicant):
        """
        upload resume
        add applicant
        attach applicant to vacancy
        :param applicant: from db
        """
        try:
            state = self.states_storage.get_state(applicant.uuid)
            if state.is_done():
                logging.debug(f'already processed: "{applicant}"')
                return True

            account_id = self.get_account_id()

            # TODO: should we no break if upload failed ?
            resume_data = self.upload_resume(applicant, account_id, state)

            applicant_data = self.prepare_add_applicant_data(applicant, resume_data)
            added_applicant = self.add_applicant(account_id, applicant_data, state)

            self.add_applicant_to_vacancy(account_id, added_applicant['id'], applicant, state)

            logging.debug(f'finish processing: "{applicant}"')
            state.done()
        except Exception:
            logging.exception(f'exception on processing {applicant}')
            return False
        return True

    def get_account_id(self):
        accounts = self.api.accounts()
        if len(accounts) != 1:
            msg = f'can not choose account id from "{accounts}" (maybe need to pass the id (as todo))'
            raise WorkerError(msg)
        return accounts[0]['id']

    def upload_resume(self, applicant, account_id, state):
        saved_step = state.get_step_by(UPLOAD_RESUME)
        if saved_step:
            logging.debug(f'resume for {applicant} was already uploaded')
            return saved_step['data']

        res = self.api.upload(account_id, applicant.resume_file)
        state.append_step({'name': UPLOAD_RESUME, 'data': res})  # TODO: refact hardcode (as ctx_mng)
        return res

    def add_applicant(self, account_id, data, state):
        saved_step = state.get_step_by(ADD_APPLICANT)
        if saved_step:
            logging.debug(f'applicant {data["last_name"]} {data["first_name"]} was already added')
            return saved_step['data']

        res = self.api.add_applicant(account_id, data)
        # is applicant doubles unimportant?
        state.append_step({'name': ADD_APPLICANT, 'data': res})  # TODO: refact hardcode (as ctx_mng)
        return res

    def add_applicant_to_vacancy(self, account_id, applicant_id, applicant, state):
        saved_step = state.get_step_by(ADD_APPLICANT_TO_VACANCY)
        if saved_step:
            logging.debug(f'applicant {applicant_id} was already attached to vacancy')
            return saved_step['data']

        data = {
            'vacancy': self.get_vacancy_id_by(account_id, applicant.position),
            'status': self.get_status_id_by(account_id, applicant.status),
            'comment': applicant.comment,
            # 'files' - seems like it's not uploaded resume
        }
        res = self.api.add_applicant_to_vacancy(account_id, applicant_id, data)
        state.append_step({'name': ADD_APPLICANT_TO_VACANCY, 'data': res})  # TODO: refact hardcode (as ctx_mng)
        return res

    def get_vacancy_id_by(self, account_id, position):
        # move to HuntflowAPI ?
        vacs = self.api.vacancies(account_id)
        # can be several vacancies with the same position? (seems like no)
        vac = next((vac for vac in vacs if vac['position'] == position), None)
        if not vac:
            raise WorkerError(f'failed to find vacancy id for "{position}"')

        return vac['id']

    def get_status_id_by(self, account_id, status):
        vac_stats = self.api.vacancy_statuses(account_id)
        res = next((s for s in vac_stats if s['name'] == status), None)
        if not res:
            raise WorkerError(f'failed to find status id by "{status}"')

        return res['id']

    @staticmethod
    def prepare_add_applicant_data(applicant, resume_data):
        photo = resume_data.get('photo', {}).get('id')
        text = resume_data.get('text', '')
        file_id = resume_data.get('id')
        resume_data = resume_data['fields']
        data = {}

        names = applicant.fio.split()
        data['last_name'] = names[0]
        data['first_name'] = names[1]

        if len(names) == 3:
            data['middle_name'] = names[2]

        phones = resume_data.get('phones')
        if phones:
            data['phone'] = phones[-1]  # last phone seems like is most actually

        email = resume_data.get('email')
        if email:
            data['email'] = email

        data['position'] = applicant.position  # or resume_data.get('position') ?
        # TODO: find out company, I can not determine if applicant is workless by data from upload resume (expirience)
        data['money'] = resume_data.get('salary') or applicant.money

        birthdate = resume_data.get('birthdate')
        if birthdate:
            data['birthday_day'] = birthdate.get('day')
            data['birthday_month'] = birthdate.get('month')
            data['birthday_year'] = birthdate.get('year')

        if photo:
            data['photo'] = photo

        data['externals'] = [{
            'data': {'body': text},
            'auth_type': 'NATIVE',  # just hardcode?
            'files': [],
        }]
        if file_id:
            data['externals'][0]['files'] = [{'id': file_id}]

        return data

# TODO: reduce dup code
