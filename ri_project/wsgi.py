import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ri_project.settings')

application = get_wsgi_application()


from waitress import serve
from ri_project.wsgi import application

if __name__ == '__main__':
    serve(application, host='0.0.0.0', port=8000)
