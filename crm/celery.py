from celery import Celery

app=Celery(
    'crm',
    broker='redis://localhost:6379/0'
)