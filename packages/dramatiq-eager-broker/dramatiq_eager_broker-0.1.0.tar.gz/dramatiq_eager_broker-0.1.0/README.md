# dramatiq-eager-broker

An eager broker for [Dramatiq](https://dramatiq.io) that executes tasks synchronously and immediately, without queuing. Perfect for testing and development environments.

## Features

- Synchronous task execution
- No message broker required (Redis, RabbitMQ, etc.)
- Pipeline support
- Middleware support
- Drop-in replacement for testing

## Installation

```bash
pip install dramatiq-eager-broker
```

Or with [uv](https://github.com/astral-sh/uv):

```bash
uv add dramatiq-eager-broker
```

## Usage

```python
import dramatiq
from dramatiq_eager_broker import EagerBroker

broker = EagerBroker()
dramatiq.set_broker(broker)

@dramatiq.actor
def send_email(email, message):
    print(f"Sending email to {email}: {message}")

# Tasks are executed immediately and synchronously
send_email.send("user@example.com", "Hello!")
```

## Testing Example

```python
import dramatiq
import pytest
from dramatiq_eager_broker import EagerBroker


@pytest.fixture
def eager_broker():
    broker = EagerBroker(middleware=[])
    dramatiq.set_broker(broker)
    yield broker
    dramatiq.set_broker(None)


def test_my_actor(eager_broker):
    results = []

    @dramatiq.actor
    def my_task(value):
        results.append(value)

    my_task.send("test")
    assert results == ["test"]
```

## Pipeline Support

The eager broker supports Dramatiq pipelines:

```python
@dramatiq.actor
def add(x, y):
    return x + y

@dramatiq.actor
def multiply(result, factor):
    return result * factor

# Create and execute a pipeline
pipeline = add.message(2, 3) | multiply.message(factor=10)
broker.enqueue(pipeline.messages[0])
```
