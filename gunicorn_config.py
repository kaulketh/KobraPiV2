"""
A configuration module for Gunicorn server.

This module defines various configuration settings for the Gunicorn server,
which are used to control server behavior, such as binding address, number of
workers, threads per worker, timeout duration, and logging options. These
settings optimize the performance of the server for the given workload.

Attributes:
    bind (str): The address and port on which the server will listen.
    workers (int): The number of worker processes handling requests.
    threads (int): The number of threads per worker for handling requests.
    timeout (int): The maximum time (in seconds) a request can take before
        timing out.
    backlog (int): The maximum number of pending connections waiting to be
        accepted.
    accesslog (str): The file path or '-' to log HTTP access requests.
    errorlog (str): The file path or '-' to log server errors.
    worker_class (str): The type of worker process used. Default is 'gthread',
        which enables threading.
"""

bind = '0.0.0.0:8000'

workers = 9

threads = 4

timeout = 300

backlog = 2048

accesslog = '-'
errorlog = '-'
worker_class = 'gthread'  # 'gthread' enables threading and is suitable
