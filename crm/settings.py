CRONJOBS = [
    ('0 */12 * * *', 'crm.cron.update_low_stock'),
]



CELERY_BEAT_SCHEDULE = {
    'generate-crm-report': {
        'task': 'crm.tasks.generate_crm_report',
        'schedule': crontab(day_of_week='mon', hour=6, minute=0),
    },
}