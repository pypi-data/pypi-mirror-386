_logger_initialized = False


import logging

from .api_call import verify_user
from .error_processing import process_error
from .error_integration import RequestContextFilter

DEBUG = False

# Custom handler
class CrashpadHandler(logging.Handler):
    def __init__(self, project_name, base_url):
        super().__init__()
        self.project_name = project_name
        self.base_url = base_url

        # Add request context filter to this handler
        self.addFilter(RequestContextFilter())

    def emit(self, record):
        try:
            process_error(
                record,
                project_name=self.project_name,
                base_url=self.base_url,
                debug=DEBUG,
            )
        except:
            pass


def init(key):
    global _logger_initialized
    if _logger_initialized:
        return

    # Call API without requests
    response = verify_user(key)
    exists = response.get("exists", False)
    project_name = response.get("project_name", None)
    base_url = response.get("url", None)

    if not exists:
        raise ValueError("Invalid API key")

    # Setup logging
    handler = CrashpadHandler(project_name=project_name, base_url=base_url)
    handler.setLevel(logging.WARNING)

    root_logger = logging.getLogger()
    root_logger.addHandler(handler)

    django_logger = logging.getLogger("django")
    django_logger.addHandler(handler)

    _logger_initialized = True

