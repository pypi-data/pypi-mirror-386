{% set template_domain_import = "shared.domain"|compute_base_path(template.name) %}
{% set template_infra_import = "shared.infra"|compute_base_path(template.name) %}
from pika.adapters.blocking_connection import BlockingChannel
from pika.spec import Basic, BasicProperties

{% if template_domain_import %}
from {{ general.source_name }}.{{ template_domain_import }}.event.domain_event import DomainEvent
from {{ general.source_name }}.{{ template_domain_import }}.event.domain_event_subscriber import (
    DomainEventSubscriber,
)
{% else %}
from {{ general.source_name }}.event.domain_event import DomainEvent
from {{ general.source_name }}.event.domain_event_subscriber import (
    DomainEventSubscriber,
)
{% endif %}
{% if template_infra_import %}
from {{ general.source_name }}.{{ template_infra_import }}.event.domain_event_json_deserializer import (
    DomainEventJsonDeserializer,
)
from {{ general.source_name }}.{{ template_infra_import }}.event.rabbit_mq.rabbit_mq_connection import (
    RabbitMqConnection,
)
from {{ general.source_name }}.{{ template_infra_import }}.event.rabbit_mq.rabbit_mq_queue_formatter import (
    RabbitMqQueueFormatter,
)
{% else %}
from {{ general.source_name }}.event.domain_event_json_deserializer import (
    DomainEventJsonDeserializer,
)
from {{ general.source_name }}.event.rabbit_mq.rabbit_mq_connection import (
    RabbitMqConnection,
)
from {{ general.source_name }}.event.rabbit_mq.rabbit_mq_queue_formatter import (
    RabbitMqQueueFormatter,
)
{% endif %}


class RabbitMqConsumer:
    _queue_formatter: RabbitMqQueueFormatter
    _subscriber: DomainEventSubscriber[DomainEvent]
    _client: RabbitMqConnection

    def __init__(
        self,
        client: RabbitMqConnection,
        subscriber: DomainEventSubscriber[DomainEvent],
        queue_formatter: RabbitMqQueueFormatter,
    ) -> None:
        self._queue_formatter = queue_formatter
        self._subscriber = subscriber
        self._client = client
        self._event_deserializer = DomainEventJsonDeserializer(subscriber=subscriber)

    def _on_call(
        self,
        channel: BlockingChannel,
        method: Basic.Deliver,
        properties: BasicProperties,
        body: bytes,
    ) -> None:
        event = self._deserialize_event(body)
        self._subscriber.on(event)
        channel.basic_ack(delivery_tag=method.delivery_tag)

    def start_consuming(self) -> None:
        self._client.consume(
            queue_name=self._queue_formatter.format(self._subscriber),
            callback=self._on_call,
        )

    def stop_consuming(self) -> None:
        self._client.close_connection()

    def _deserialize_event(self, body: bytes) -> DomainEvent:
        return self._event_deserializer.deserialize(body)
