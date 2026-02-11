import multiprocessing

# Timeout for graceful workers restart
timeout = 300  # 5 minutes

# Number of worker processes
workers = 2

# Worker class
worker_class = 'sync'

# Maximum number of requests a worker will process before restarting
max_requests = 1000
max_requests_jitter = 50

# Logging
accesslog = '-'
errorlog = '-'
loglevel = 'info'

# Preload the application
preload_app = False
