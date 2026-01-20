import json
from kafka import KafkaProducer


class KafkaSink:
    def __init__(self, bootstrap_servers="localhost:9092", topic="raw_news") -> None:
        self.producer = KafkaProducer(
            bootstrap_servers=bootstrap_servers,
            value_serializer=lambda v: json.dumps(v).encode("utf-8"),
        )
        self.topic = topic

    def send(self, item) -> None:
        self.producer.send(self.topic, dict(item))

    def close(self) -> None:
        self.producer.flush()
