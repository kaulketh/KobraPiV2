# gunicorn.conf.py

# This binds Gunicorn to all interfaces on port 8000
bind = '0.0.0.0:8000'

# Number of worker processes for parallel processing
workers = 9

# Threads per worker to support concurrent connections
threads = 4

# Timeout in seconds for long requests (e.g., for video streams)
# Maximum time (in seconds) that Gunicorn will wait for a request will wait
# for a request
timeout = 300

# Maximum number of connections that are accepted simultaneously
# Maximum number of queues (connections)
backlog = 2048

# Error log and access log configurations
accesslog = '-'  # All access logs to the standard output (stdout)
errorlog = '-'  # All error logs to the standard output (stderr)

# The number of connections that can be processed simultaneously
# (no blocking IO operations)
worker_class = 'gthread'  # 'gthread' enables threading and is suitable
# well suited for I/O-heavy applications such as streaming
