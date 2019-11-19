import os
import json
import logging


class StatesStorageError(Exception):
    pass


class State:
    def __init__(self, filename):
        """
        represent:
        {
          'steps': [
              {'name': 'something upload'},
              {'name': 'something add'},
              {'name': 'something attach'},
              ...
          ]
          'done': False,
        }
        :param filename:
        """
        self.filename = filename

        if os.path.exists(filename):
            with open(filename, 'r') as state_file:
                self.data = json.load(state_file)
        else:
            self.data = {'steps': [], 'done': False}
            self.save()

    def get_steps(self):
        return self.data['steps']

    def get_step_by(self, name):
        return next((step for step in self.get_steps() if step['name'] == name), None)

    def append_step(self, step):
        self.data['steps'].append(step)
        self.save()

    def is_done(self):
        return self.data['done']

    def done(self):
        self.data['done'] = True
        self.save()

    def save(self):
        with open(self.filename, 'w') as write_file:
            json.dump(self.data, write_file, indent=4)


class StatesStorage:
    def __init__(self, states_dir='./states'):
        self.states_dir = os.path.abspath(states_dir)
        self.prepare()

    def prepare(self):
        if os.path.exists(self.states_dir):
            if os.path.isdir(self.states_dir):
                return
            else:
                msg = f'{self.states_dir} is not directory (pls delete it)'
                logging.error(msg)
                raise StatesStorageError(msg)
        os.mkdir(self.states_dir)

    def get_state(self, uuid):
        filename = os.path.join(self.states_dir, f'{uuid}.json')
        return State(filename)

    def cleanup(self):
        # TODO
        raise NotImplementedError
