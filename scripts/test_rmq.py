import pika

parameters = pika.ConnectionParameters(host='rabbitmq', port=5672)
try:
    connection = pika.BlockingConnection(parameters)
    print('RabbitMQ is reachable')
    connection.close()
except pika.exceptions.AMQPConnectionError:
    print('RabbitMQ is not reachable')