# KAQ_QUANT_COMMON

A simple Python package that does amazing things.

## Features

- Feature 1: Does X
- Feature 2: Does Y

## Installation

You can install this package using:

```bash
pip install my-package
```

## Pub
Command:
```bash
twine upload dist/* --verbose
```

## Simulated Exchange WS

- Server: `WsExchangeServer(exchange, mysql_host, mysql_port, mysql_user, mysql_passwd, mysql_db, start_time, speed_multiplier, use_realtime_event_time, inject_sample_on_empty, port)`
- Client: `WsExchangeClient(url)`
- Topics:
  - `funding_rate.all`
  - `funding_rate.<symbol>`
- Notes:
  - `inject_sample_on_empty`: when DB has no rows, inject small sample events for testing; set to `False` in production to avoid synthetic pushes.

### Example

```python
from kaq_quant_common.api.ws.exchange.ws_exchange_server import WsExchangeServer
from kaq_quant_common.api.ws.exchange.ws_exchange_client import WsExchangeClient

# Start server
server = WsExchangeServer(
    exchange="binance",
    mysql_host="192.168.0.17",
    mysql_port=3306,
    mysql_user="root",
    mysql_passwd="mysql_8x48BF",
    mysql_db="db_kaq_binance",
    start_time=1730000000000,  # ms timestamp
    speed_multiplier=10.0,
    use_realtime_event_time=True,
    inject_sample_on_empty=True,  # disable in production
    port=8768,
)
server.run_with_thread(block=False)

# Client subscribe
client = WsExchangeClient(url="ws://localhost:8768")
client.connect()
client.subscribe_all(lambda evt: print(evt))

client.disconnect()
server.shutdown_with_thread()
```