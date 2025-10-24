#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys
import ssl
import certifi

# SSL 設定
os.environ["GRPC_DEFAULT_SSL_ROOTS_FILE_PATH"] = certifi.where()
ssl._create_default_https_context = ssl._create_unverified_context
print("✅ SSL 憑證初始化完成")

def main():
    """Run administrative tasks."""
    # 🌟 請注意這裡，您的配置目錄名稱是 'set' 🌟
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'set.settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)

if __name__ == '__main__':
    main()
