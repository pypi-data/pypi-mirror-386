valar for morghulis

# 1. installation

- you need to install valar in a django project

```shell
pip install valar
```

# 2. root app

- you only need 3 files in your root app
    - settings.py
    - asgi.py
    - urls.py

## 2.1 settings.py

```python
from pathlib import Path

""" Compulsory settings """
DEBUG = True
BASE_DIR = Path(__file__).resolve().parent.parent
BASE_APP = str(BASE_DIR.name)
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
SECRET_KEY = 'django-insecure-of@tfouoq^_f$l!yki#m=6j7)@&kjri$1_$!mca-=%7=+@f@5^'

""" Minimized compulsory settings """

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

INSTALLED_APPS = [
    'django.contrib.sessions',
    "corsheaders",
    'channels',
    'valar.apps.ValarConfig',
]

MIDDLEWARE = [
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'valar.auth.Middleware.ValarMiddleware'
]

CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels.layers.InMemoryChannelLayer"
    }
}

CORS_ORIGIN_ALLOW_ALL = True
CORS_ALLOW_CREDENTIALS = True
ROOT_URLCONF = "%s.urls" % BASE_APP
ASGI_APPLICATION = "%s.asgi.application" % BASE_APP

""" Optional settings """
ALLOWED_HOSTS = ['*']
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Asia/Shanghai'
USE_I18N = True
USE_TZ = False
SESSION_SAVE_EVERY_REQUEST = True
SESSION_COOKIE_AGE = 60 * 60
FILE_UPLOAD_MAX_MEMORY_SIZE = 1024 * 1024 * 100
DATA_UPLOAD_MAX_MEMORY_SIZE = 1024 * 1024 * 100

""" Valar Options """

HANDLER_MAPPING = "%s.urls.channel_mapping" % BASE_APP
MONGO_URI = 'mongodb://username:password@host:27017'
MINIO_URL = "s3://username:password@host:9000"
MINIO_ROOT = "https://host:9001"

""" Email Options """
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'xxx.xx.xx.xx'
EMAIL_PORT = 465
EMAIL_DOMAIN = 'http://xx.xx.xx'
EMAIL_HOST_USER = "xxx@xx.xx.xx"
EMAIL_HOST_PASSWORD = '*******'
EMAIL_USE_TLS = False
EMAIL_USE_SSL = True
```

## 2.2 asgi.py

```python
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from django.urls import re_path

from valar.channels.consumer import ValarConsumer

application = ProtocolTypeRouter({
    'http': get_asgi_application(),
    'websocket': URLRouter([
        re_path(r'(?P<client>\w+)/$', ValarConsumer.as_asgi()),
    ])
})


```

## 2.3 urls.py

- no need to provide urls for Valar, Valar will auto set urlpatterns for Morghulis (
  see https://www.npmjs.com/package/morghulis)
- go to section 4 to see how to register channel handlers (a Vue - Django async communication tool) in urls.

# 3. migrate

- no need to makemigrations and migrate for valar, valar will auto migration

# 4. how to register a channel handler for Morghulis async methods

## 4.1 create a handler

```python
import time
from valar.channels.sender import ValarChannelSender
from valar.channels.counter import Counter


def valar_test_handler(sender: ValarChannelSender):
    data = sender.data
    length = data.get('length', 100)
    counter = Counter(length)
    for i in range(length):
        time.sleep(0.1)
        tick = counter.tick()
        tick.update({'name': 'test1'})
        sender.load(tick)
```

### 4.2 create a dict (e.g. using the name 'channel_mapping') to save your handler

- I'd like to put it in the root urls.py, you can put it anywhere

```python
channel_mapping = {
    'test': valar_test_handler,
}
```

## 4.3 register the channel_mapping in the settings.py

```python
HANDLER_MAPPING = "%s.urls.channel_mapping" % BASE_APP
```

### 4.4 you can copy the following codes to your urls.py

```python
import json

from django.urls import path

from valar.classes.valar_response import ValarResponse
from valar.views.handler import valar_test_handler


def test_request(request):
    body = json.loads(request.body)
    return ValarResponse(body)


urlpatterns = [
    path('test', test_request),
]

channel_mapping = {
    'test_handler': valar_test_handler,
}

```

# 5. create an orm model extends the AbstractUser class, enable the authentication of Valar

```pycon

class User(AbstractUser):
    """
        any fields you want
    """
    description = models.TextField(null=True, verbose_name='备注')

    class Meta:
        verbose_name = 'User'

```