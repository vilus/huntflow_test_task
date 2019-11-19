Тестовое задание для Huntflow
=============================


  ::

    git clone https://github.com/vilus/huntflow_test_task.git
    cd huntflow_test_task
    virtualenv .venv
    . .venv/bin/activate

    pip install requirements.txt

    python main.py -h
    python main.py -t "personal_token" -a "https://dev-100-api.huntflow.ru/" -d ../huntflow_files/ -v


tested on linux + python 3.7