# set/wsgi.py

import os

from django.core.wsgi import get_wsgi_application

# 確保這裡的設定指向您的專案名稱 'set'
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'set.settings')

application = get_wsgi_application()