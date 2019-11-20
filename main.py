import configargparse
import logging


from applicants_db import ApplicantsDBXLSX
from huntflow_api import HuntflowAPI
from states_storage import StatesStorage
from worker import Worker
from utils import GracefulInterruptHandler


p = configargparse.ArgParser()
p.add_argument('-t', '--token', env_var='HUNTFLOW_PERSONAL_TOKEN',
               required=True, help='personal token for huntflow api')
p.add_argument('-d', '--db_dir', env_var='HUNTFLOW_DB_DIR',
               required=True, help='database directory (*.xlsx, resume)')
p.add_argument('-a', '--api_url', env_var='HUNTFLOW_API_URL',
               default='https://dev-100-api.huntflow.ru/', help='url of huntflow api')
p.add_argument('-v', '--verbose', action='store_true')


def set_logging(verbose):
    level = logging.WARNING
    if verbose:
        level = logging.DEBUG
    logging.basicConfig(format='%(asctime)s - %(message)s', level=level)


def get_applicants_db(db_dir):
    db = ApplicantsDBXLSX(db_dir)
    logging.debug(f'got applicants db "{db}"')
    return db


def get_huntflow_api(token, api_url):
    logging.debug(f'getting hunflow api via {api_url}')
    return HuntflowAPI(token, api_url)


def get_states_storage(storage_dir='./states'):
    logging.debug(f'getting states storage in {storage_dir}')
    return StatesStorage(storage_dir)


def main():
    options = p.parse_args()
    set_logging(options.verbose)

    db = get_applicants_db(options.db_dir)
    api = get_huntflow_api(options.token, options.api_url)
    states_storage = get_states_storage()
    worker = Worker(api, states_storage)

    with GracefulInterruptHandler() as h:
        for applicant in db.get_applicants():
            if h.interrupted:  # It can be more precision if it wrapped sub steps
                logging.debug('interrupted, exit')
                break
            logging.debug(f'start processing: "{applicant}"')
            worker.just_doit(applicant)


if __name__ == '__main__':
    # TODO: auto-tests
    main()
    # TODO: add non zero ret code if errors
