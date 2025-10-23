import threading
import logging


# Thread-local storage for request context
_request_context = threading.local()


def get_request_context():
    """Get request from thread-local storage"""
    return getattr(_request_context, "request", None)


def extract_request_info(request):
    """Extract request information safely"""
    
    if not request:
        return None, None, None

    method = getattr(request, "method", None)

    # Get URL safely
    url = None
    if hasattr(request, "build_absolute_uri"):
        try:
            url = request.build_absolute_uri()
        except:
            pass
    if not url and hasattr(request, "get_full_path"):
        try:
            url = request.get_full_path()
        except:
            pass
    
    
    # Get user safely
    user = None
    if hasattr(request, "user"):
        try:
            user_obj = getattr(request, "user", None)
            if user_obj:
                # Check if user is authenticated
                is_authenticated = getattr(user_obj, "is_authenticated", None)
                if callable(is_authenticated):
                    is_authenticated = is_authenticated()

                if is_authenticated:
                    # Try to get username or email
                    if hasattr(user_obj, "username") and user_obj.username:
                        user = user_obj.username
                    elif hasattr(user_obj, "email") and user_obj.email:
                        user = user_obj.email
                    elif hasattr(user_obj, "id"):
                        user = f"user_{user_obj.id}"
                    else:
                        user = str(user_obj)
                else:
                    user = "anonymous"
        except Exception as e:
            user = f"error_extracting_user: {str(e)}"

    return method, url, user


class RequestContextFilter(logging.Filter):
    """
    Logging filter that adds request information to log records.
    Automatically captures request context from Django internals.
    """

    def filter(self, record):
        """Add request context to the log record"""
        # Try to get request from thread-local storage first
        request = get_request_context()

        # If not in thread-local, try to get it from the log record itself
        if not request and hasattr(record, "request"):
            request = record.request

        # Extract and attach request info to record
        if request:
            method, url, user = extract_request_info(request)
            record.request_method = method
            record.request_url = url
            record.user = user
        else:
            # Set to None if no request available
            if not hasattr(record, "request_method"):
                record.request_method = None
            if not hasattr(record, "request_url"):
                record.request_url = None
            if not hasattr(record, "user"):
                record.user = None

        return True

