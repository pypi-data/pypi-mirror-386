# 🛟 Crashpad - A Soft Landing for Your Django Crashes

Error tracking SDK for Django and Django REST Framework applications. When your code crashes, Crashpad catches it gracefully.

## ✨ Features

- 🎯 **Zero Configuration**: One line to set up, no middleware needed
- 🔍 **Full Context Capture**: Automatically captures request info, user details, and code snapshots
- 🚀 **Django & DRF Support**: Works seamlessly with both Django and Django REST Framework
- 🧵 **Thread-Safe**: Uses thread-local storage for reliable request tracking
- 📸 **Code Snapshots**: Shows the exact lines of code where errors occurred
- 🔄 **Reversed Stack Traces**: Error message first, most recent call first - easier to read
- 🤮 **Debug Mode**: Save errors locally with the hilarious `logs🤮` directory

## 📦 Installation

```bash
pip install crashpad
```

## 🚀 Quick Start

### Django Setup

In your Django `settings.py`:

```python
import crashpad

# Initialize with your API key URL - that's it!
crashpad.init(key="http://your-api-server.com/YOUR_PROJECT_KEY")
```

### Django REST Framework Setup

Same simple setup for DRF:

```python
import crashpad

# Initialize Crashpad
crashpad.init(key="http://your-api-server.com/YOUR_PROJECT_KEY")
```

That's it! No middleware, no additional configuration needed. Crashpad automatically captures all errors using Django signals.

## 📊 What Gets Tracked

When an error occurs, Crashpad automatically captures:

- **Error details**: Exception type, message, and reversed stack trace (error first!)
- **Code snapshot**: The exact lines of code around where the error occurred
- **Request information**:
  - HTTP method (GET, POST, PUT, DELETE, etc.)
  - Full URL path
  - Authenticated user or "anonymous"
- **File location**: Filename, function name, and line number
- **Timestamp**: Exact time when the error occurred

## 🎯 Example

Here's a complete example with Django settings:

```python
# settings.py

import crashpad

# Initialize Crashpad - one line!
crashpad.init(key="http://127.0.0.1:9000/your-project-key")

# Your regular Django/DRF settings continue...
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'rest_framework',
    # ... your apps
]

REST_FRAMEWORK = {
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 100,
}
```

## 🔧 How It Works

1. **Signal-Based Integration**: Connects to Django's `got_request_exception` signal
2. **Automatic Request Capture**: Uses a logging filter to extract request information
3. **Thread-Local Storage**: Safely stores request context during error handling
4. **No Middleware Required**: Works automatically without middleware configuration
5. **Universal Coverage**: Captures errors from views, DRF endpoints, background tasks, and logging calls
6. **Smart Extraction**: Safely extracts HTTP method, URL, and user information
7. **Flexible Deployment**: Send to API in production, save locally in debug mode

## 🐛 Debug Mode

Want to see errors saved locally? Enable debug mode:

```python
import crashpad

crashpad.DEBUG = True
crashpad.init(key="http://your-api-server.com/YOUR_PROJECT_KEY")
```

Errors will be saved to a `logs🤮` directory as JSON files. Yes, the emoji is intentional! 🤮

## 📋 Requirements

- Python 3.6+
- Django 3.2+
- Django REST Framework (optional, for DRF integration)

## 📄 License

MIT License - see LICENSE file for details

## 🤝 Contributing

Contributions are welcome! Feel free to open issues or submit pull requests.

## 🎯 Why "Crashpad"?

Because when your code takes a dive, it deserves a soft landing! 🛟

---

Made with ❤️ for Django developers who believe error tracking shouldn't be complicated.
