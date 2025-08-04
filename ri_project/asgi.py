import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
import ri_produccion.routing

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ri_project.settings')
