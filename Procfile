web: python manage.py migrate && python manage.py collectstatic --noinput --upload-unhashed-files && gunicorn myproject.wsgi:application --bind 0.0.0.0:$PORT
