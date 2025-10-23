import os
import json
import traceback
from datetime import datetime
from .api_call import post_error


def _format_exception_reversed(exc_info):
    """Format exception with error message first (reversed)"""
    if not exc_info:
        return None

    lines = traceback.format_exception(*exc_info)
    if len(lines) > 1:
        # Get the error message (last line)
        error_line = lines[-1]
        # Get the traceback (everything except last line)
        traceback_lines = lines[:-1]
        # Reverse the traceback so most recent call appears first
        reversed_traceback = list(reversed(traceback_lines))
        # Put error first, then reversed traceback
        result = [
            error_line,
            "\n--- Traceback (most recent call last) ---\n",
        ] + reversed_traceback
        return "".join(result)

    return "".join(lines)


def process_error(record, project_name, base_url, debug=False):
    """Process and send error data"""
    log_dir = "logs🤮" if debug else None
    if debug:
        os.makedirs(log_dir, exist_ok=True)

    # Get error location from traceback or record
    file_info = {"pathname": None, "filename": None, "function": None, "lineno": None}
    code_snapshot = None

    if record.exc_info:
        try:
            tb = record.exc_info[2]
            # Walk to the LAST frame (where the actual error occurred)
            while tb.tb_next:
                tb = tb.tb_next

            file_info = {
                "pathname": tb.tb_frame.f_code.co_filename,
                "filename": os.path.basename(tb.tb_frame.f_code.co_filename),
                "function": tb.tb_frame.f_code.co_name,
                "lineno": tb.tb_lineno,
            }

            # Get code snapshot
            if os.path.exists(file_info["pathname"]):
                try:
                    with open(file_info["pathname"], "r", encoding="utf-8") as f:
                        lines = f.readlines()

                    start = max(0, tb.tb_lineno - 6)
                    end = min(len(lines), tb.tb_lineno + 4)

                    code_snapshot = {
                        "file": file_info["filename"],
                        "pathname": file_info["pathname"],
                        "function": file_info["function"],
                        "error_line": tb.tb_lineno,
                        "code": [
                            {
                                "line_number": i + 1,
                                "content": lines[i].rstrip("\n"),
                                "is_error_line": i + 1 == tb.tb_lineno,
                            }
                            for i in range(start, end)
                        ],
                    }
                except:
                    pass
        except:
            pass
    else:
        # Fallback to record location when no exception
        file_info = {
            "pathname": getattr(record, "pathname", None),
            "filename": (
                os.path.basename(getattr(record, "pathname", ""))
                if getattr(record, "pathname", None)
                else None
            ),
            "function": getattr(record, "funcName", None),
            "lineno": getattr(record, "lineno", None),
        }

    # Extract request information from record or thread-local context
    request_method = getattr(record, "request_method", None)
    request_url = getattr(record, "request_url", None)
    request_user = getattr(record, "user", None)

    # If not in record, try to get from thread-local context
    if not request_method and not request_url:
        try:
            from .error_integration import get_request_context, extract_request_info

            request = get_request_context()
            if request:
                request_method, request_url, request_user = extract_request_info(
                    request
                )
        except:
            pass

    # Build error data
    error_data = {
        "timestamp": datetime.now().isoformat(),
        "level": record.levelname,
        "message": record.getMessage(),
        "code_snapshot": code_snapshot,
        "exc_info": _format_exception_reversed(record.exc_info),
        "request": {
            "method": request_method,
            "url": request_url,
            "user": request_user,
        },
        "project": project_name,
    }

    # Save to local file in debug mode
    if debug and log_dir:
        try:
            filename = os.path.join(
                log_dir, f"{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}.json"
            )
            with open(filename, "w") as f:
                json.dump(error_data, f, indent=2)
        except:
            pass
    else:
        # Send to API
        api_url = f"{base_url}/api/logs"
        post_error(api_url, error_data)

