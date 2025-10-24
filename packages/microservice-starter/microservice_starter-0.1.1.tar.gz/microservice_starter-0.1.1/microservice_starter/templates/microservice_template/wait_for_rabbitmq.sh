#!/bin/bash

# Wait for RabbitMQ to be available
while ! nc -z rabbitmq 5672; do
    echo "Waiting for RabbitMQ..."
    sleep 2
done
echo "RabbitMQ is available!"

# Wait for Redis to be available
while ! nc -z atp-redis-rabbit-mq 6382; do
    echo "Waiting for Redis..."
    sleep 2
done
echo "Redis is available!"
