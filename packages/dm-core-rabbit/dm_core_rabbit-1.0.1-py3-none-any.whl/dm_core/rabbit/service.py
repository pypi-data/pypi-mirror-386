import pika
import logging
import json
import re
import ssl
import os
from abc import ABC
from django.conf import settings
from django.core.serializers.json import DjangoJSONEncoder
from dm_core.meta.service import MetaClient, ValidatorAbc
from dm_core.tracer.decorator import trace_message_producer, trace_message_consumer
from dm_core.tracer.models import MessageLogModel
from dm_core.redis.utils import singleton
from .models import MessageData, Method
from .utils import CaseConvert


logger = logging.getLogger()


@singleton
class RabbitClient(object):
    """
    RabbitClient: A singleton instance responsible to connect to RabbitMQ for sending/receiving messages
    """

    def __init__(self):
        config = settings.DM_RABBIT_CLIENT_SETTINGS
        assert ('service' in config)
        assert ('hosts' in config)
        assert ('username' in config)
        assert ('password' in config)
        assert ('port' in config)
        self.meta_client = MetaClient()
        credentials = pika.credentials.PlainCredentials(config['username'], config['password'])
        self.connection_params = self._native_machine_init(credentials, config['hosts'], config['port'])
        self.service = config['service']
        self.listeners = None

    def _aws_init(self, credentials, hosts, port) -> list:
        context = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)
        return [pika.ConnectionParameters(host=host,
                                          port=port,
                                          credentials=credentials,
                                          ssl_options=pika.SSLOptions(context)) for host in hosts.split(',')]

    def _native_machine_init(self, credentials, hosts, port) -> list:
        return [pika.ConnectionParameters(host=host, port=port, credentials=credentials) for host in hosts.split(',')]

    def listen(self, listeners, *args, **kwargs):
        self.listeners = listeners
        queues = self.meta_client.get_destination_queue(cache_refresh=True)
        connection = pika.BlockingConnection(self.connection_params)
        channel = connection.channel()
        channel.basic_qos(prefetch_count=1)
        for queue in queues:
            queue_id_tokens = queue['id'].split('.')
            assert (queue_id_tokens[0] == settings.SERVICE.lower())
            consumer_tag = '.'.join(queue_id_tokens[1:])
            channel.basic_consume(queue=queue['id'], on_message_callback=self.action, consumer_tag=consumer_tag)
        channel.start_consuming()

    def action(self, ch, method, properties, body):
        try:
            json_data = json.loads(body)
            msg = MessageData(**json_data)
            logger.info(f" [x] Received Exchange: {method.exchange} Routing: {method.routing_key}  Payload: {body}")
            MessageLogModel.objects.create(message_id=msg.message_id, request_id=msg.request_id,
                                           exchange_key=method.exchange, routing_key=method.routing_key,
                                           direction='INBOUND',
                                           data=msg.payload)
            assert len(method.exchange.split('.')) > 1
            self.__invoke_listener(method, msg, properties)
        except Exception as e:
            logger.exception(e, exc_info=True)
        finally:
            ch.basic_ack(delivery_tag=method.delivery_tag)

    @trace_message_producer()
    def send(self, exchange_key: str, routing_key: str, data: MessageData, carrier=None, *args, **kwargs):
        connection = pika.BlockingConnection(self.connection_params)
        channel = connection.channel()
        MessageLogModel.objects.create(message_id=data.message_id, request_id=data.request_id,
                                       exchange_key=exchange_key,
                                       routing_key=routing_key, direction='OUTBOUND', data=data.toDict())
        self.__send(channel, exchange_key, routing_key, data, carrier, *args, **kwargs)
        channel.close()
        connection.close()

    @trace_message_consumer()
    def __invoke_listener(self, method, message, properties):
        listeners = self.listeners
        message_method_callback = method.consumer_tag.split('.')
        for index, message_method in enumerate(message_method_callback):
            if index != len(message_method_callback) - 1:
                listeners = getattr(listeners, message_method)
            else:
                listeners = getattr(listeners, CaseConvert.to_camel(message_method))
        listeners(method, message)()

    def __send(self, channel, exchange_key: str, routing_key: str, data: MessageData, carrier, *args, **kwargs):
        assert len(exchange_key.split('.')) > 1
        channel.basic_publish(exchange=exchange_key, routing_key=routing_key,
                              properties=pika.BasicProperties(headers=carrier),
                              body=json.dumps(data.toDict(), cls=DjangoJSONEncoder))


class AbstractProducer(ABC):

    def __init__(self, exchange_key: str, service: str, routing_key: str = None):
        self._message = None
        self._service = service
        self._exchange_key = exchange_key
        self._routing_key = routing_key
        self._msg_validator = MessageValidator(exchange_key, type='source')
        self._rabbit_client = RabbitClient()

    def _send(self, *args, **kwargs):
        return self._rabbit_client.send(self._exchange_key, self._routing_key, self._message, *args, **kwargs)

    def _build(self, *args, **kwargs):
        self._message = MessageData(*args, **kwargs)
        return self

    def _validate(self):
        if self._routing_key is None:
            raise ValueError('routing_key cannot be null')
        self._msg_validator.validate(self._message, self._routing_key)
        return self

    def get_message(self):
        return self._message


class AbstractConsumer(ABC):

    def __init__(self, method: Method, message: MessageData):
        self._method = method
        self._message = message
        self._msg_validator = MessageValidator(self._method.exchange, type='destination')

    def _validate(self, *args, **kwargs):
        if self._method.consumer_tag != self.queue_id:
            raise AssertionError('CONSUMER TAG does not match the QUEUE ID')
        self._msg_validator.validate(self._message)


class MessageValidator(ValidatorAbc):

    def __init__(self, exchange_key, type='source', *args, **kwargs):
        cache_refresh = False
        self.type = type
        if type == 'source':
            self.message_spec = MetaClient().get_source_message(exchange_key, cache_key=exchange_key,
                                                                cache_refresh=cache_refresh)
        else:
            self.message_spec = MetaClient().get_destination_message(exchange_key, cache_key=exchange_key,
                                                                     cache_refresh=cache_refresh)

    def _validate_message(self, data) -> None:
        error_messages = self._validate_json(self.message_spec['validator'], data.toDict())
        if type(error_messages) == list and len(error_messages) > 0:
            raise ValueError(error_messages)
        return None

    def _validate_routing_key(self, key: str) -> None:
        """
        Find atleast one matching pattern
        """
        if key is None:
            raise ValueError('routing_key argument is required')
        if key == '':
            # This condition is true for fanout, where key is not required, and hence empty string is permitted
            return None
        for pattern in self.message_spec['routing_keys']:
            if key == pattern['value']:
                return None
            replaced = pattern['value'].replace(r'.#', r'[.\w]*').replace(r'.*', r'[.\w]').replace(r'.', r'\.')
            regex_string = f"^{replaced}$"
            match = re.search(regex_string, key)
            if match is not None:
                return None
        raise ValueError(f"Routing key does not match. Given key: {key} patterns: {self.message_spec['routing_keys']}")

    def validate(self, payload, routing_key=None, *args, **kwargs) -> None:
        if self.type == 'source':
            self._validate_routing_key(routing_key)
        self._validate_message(payload)
