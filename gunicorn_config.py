"""
Configuration settings for the Gunicorn application server.

This configuration is used to define network binding, worker counts,
timeouts, logging, and worker classes. Gunicorn leverages these
settings to manage concurrency, request processing, and logging
output.

Attributes
----------
bind : str
    Network address and port where the Gunicorn server listens for
    incoming connections.
workers : int
    Number of worker processes enabled for handling client requests.
threads : int
    Number of threads per worker for concurrent request handling.
timeout : int
    Time in seconds before a worker terminates unprocessed requests.
backlog : int
    Maximum number of pending connections allowed in the request queue.
accesslog : str
    Destination for access logs, typically standard output.
errorlog : str
    Destination for error logs, typically standard error.
worker_class : str
    The type of worker class used for request processing, optimized
    for specific use cases like I/O-heavy applications.
"""

bind = '0.0.0.0:8000'

workers = 9

threads = 4

timeout = 300

backlog = 2048

accesslog = '-'
errorlog = '-'
worker_class = 'gthread'  # 'gthread' enables threading and is suitable
