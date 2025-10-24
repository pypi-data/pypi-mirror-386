from celery import Celery

BROKER_URL = "amqp://myuser:mypassword@rabbitmq:5672//"
RESULT_BACKEND = "redis://atp-redis-rabbit-mq:6382/0"

celery_app = Celery(
    "pdf_service",
    broker=BROKER_URL,
    backend=RESULT_BACKEND,
)
