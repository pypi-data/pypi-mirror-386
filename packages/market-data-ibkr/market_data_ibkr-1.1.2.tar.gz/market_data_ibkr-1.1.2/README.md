# market-data-ibkr

**Version**: 1.0.0  
**Status**: Production Ready  

Interactive Brokers provider implementation for [`market-data-core`](https://github.com/mjdevaccount/market-data-core). This package implements the `MarketDataProvider` protocol to deliver real-time and historical market data from IBKR Gateway/TWS.

---

## 🎯 Features

- ✅ **Real-time quote streaming** - Live bid/ask/last prices
- ✅ **Real-time bar streaming** - 5-second OHLCV bars
- ✅ **Historical data** - Request historical bars with automatic pacing
- ✅ **Automatic reconnection** - Exponential backoff on disconnection
- ✅ **Rate limiting** - TokenBucket algorithm prevents IBKR pacing violations
- ✅ **Error mapping** - Canonical error types from Core
- ✅ **Contract caching** - Minimize redundant IBKR API calls
- ✅ **Async context manager** - Clean resource management
- 🚧 **Tick-by-tick trades** - Coming soon
- 🚧 **Options chain streaming** - Coming soon

---

## 📦 Installation

### From Git (Recommended)

```bash
pip install git+https://github.com/YOUR_ORG/market-data-ibkr.git@v1.0.0
```

### From Local Clone

```bash
git clone https://github.com/YOUR_ORG/market-data-ibkr.git
cd market-data-ibkr
pip install -e .
```

### Development Installation

```bash
git clone https://github.com/YOUR_ORG/market-data-ibkr.git
cd market-data-ibkr
pip install -e ".[dev]"
```

---

## 🚀 Quick Start

### Basic Quote Streaming

```python
import asyncio
from market_data_core import Instrument
from market_data_ibkr import IBKRProvider, IBKRSettings

async def main():
    settings = IBKRSettings(
        host="127.0.0.1",
        port=4002,  # Paper trading
        client_id=17,
    )
    
    async with IBKRProvider(settings) as provider:
        instruments = [Instrument(symbol="AAPL")]
        
        async for quote in provider.stream_quotes(instruments):
            print(f"{quote.symbol}: ${quote.last}")

asyncio.run(main())
```

### Historical Data

```python
from datetime import datetime, timedelta

async def fetch_history():
    settings = IBKRSettings(host="127.0.0.1", port=4002)
    
    async with IBKRProvider(settings) as provider:
        instrument = Instrument(symbol="AAPL")
        end = datetime.now()
        start = end - timedelta(days=7)
        
        async for bar in provider.request_historical_bars(
            instrument=instrument,
            start=start,
            end=end,
            resolution="1d"
        ):
            print(f"{bar.ts}: O={bar.open} H={bar.high} L={bar.low} C={bar.close}")

asyncio.run(fetch_history())
```

---

## ⚙️ Configuration

### IBKRSettings

All connection and behavior settings are configured via `IBKRSettings`:

```python
from market_data_ibkr import IBKRSettings

settings = IBKRSettings(
    # Connection
    host="127.0.0.1",              # IBKR Gateway/TWS host
    port=4002,                     # 4002=Paper, 4001=Live, 7497=TWS
    client_id=17,                  # Unique client ID (0-9999)
    read_timeout_sec=30.0,         # Socket timeout
    
    # Market data
    market_data_type=1,            # 1=Live, 2=Frozen, 3=Delayed, 4=Delayed frozen
    snapshot_mode=False,           # True for snapshots instead of streaming
    
    # Reconnection
    reconnect_enabled=True,        # Auto-reconnect on disconnect
    reconnect_backoff_ms=250,      # Initial backoff
    reconnect_backoff_max_ms=5000, # Max backoff
    max_reconnect_attempts=10,     # 0 = infinite
    
    # Historical data pacing
    hist_pacing_window_sec=600,    # 10-min cooldown window
    hist_max_bars_per_request=2000,
    
    # Options (future)
    options_semaphore_size=5,
    options_base_delay=0.1,
)
```

### Environment Variables

You can use a `.env` file:

```env
IBKR_HOST=127.0.0.1
IBKR_PORT=4002
IBKR_CLIENT_ID=17
```

Then load with `python-dotenv`:

```python
from dotenv import load_dotenv
import os

load_dotenv()

settings = IBKRSettings(
    host=os.getenv("IBKR_HOST", "127.0.0.1"),
    port=int(os.getenv("IBKR_PORT", 4002)),
    client_id=int(os.getenv("IBKR_CLIENT_ID", 17)),
)
```

---

## 🏗️ Architecture

### Protocol Conformance

This package implements the `MarketDataProvider` protocol from `market-data-core`:

- ✅ `stream_quotes(instruments)` → `AsyncIterable[Quote]`
- ✅ `stream_bars(resolution, instruments)` → `AsyncIterable[Bar]`
- ✅ `request_historical_bars(...)` → `AsyncIterable[Bar]`
- 🚧 `stream_trades(instruments)` → `AsyncIterable[Trade]`
- 🚧 `stream_options(instrument, ...)` → `AsyncIterable[OptionSnapshot]`

### Module Structure

```
src/market_data_ibkr/
├── __init__.py         # Public API
├── settings.py         # IBKRSettings (Pydantic)
├── session.py          # IBKRSessionManager (connection lifecycle)
├── errors.py           # IBKR → Core error mapping
├── pacing.py           # TokenBucket + PacingManager
├── mapping.py          # DTO conversions (Ticker→Quote, BarData→Bar)
└── provider.py         # IBKRProvider (main implementation)
```

### Error Handling

All IBKR errors are mapped to Core canonical exception types:

| IBKR Code | Core Exception       | Description                |
|-----------|----------------------|----------------------------|
| 420       | `PacingViolation`    | Rate limit exceeded        |
| 162       | (varies)             | Ambiguous umbrella code    |
| 200       | `InvalidInstrument`  | Security not found         |
| 354       | `PermissionsMissing` | No market data permissions |
| 504       | `ConnectionFailed`   | Not connected              |
| 1100      | `ConnectionFailed`   | TWS connection lost        |
| 2110      | `FarmTransient`      | Server connectivity issue  |

### Rate Limiting

IBKR enforces strict rate limits:

- **Historical data**: 60 requests per 10 minutes
- **Pacing violations**: 10-minute cooldown

This provider handles rate limiting with:

1. **TokenBucket**: Smooth rate limiting (6 req/min)
2. **PacingManager**: Tracks cooldown per scope (symbol)
3. **Automatic backoff**: Exponential delays on errors

---

## 🧪 Testing

Run the test suite:

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest tests/ -v

# With coverage
pytest tests/ --cov=market_data_ibkr --cov-report=html
```

### Test Structure

```
tests/
├── conftest.py         # Fixtures (mock_ib, ibkr_settings)
├── test_settings.py    # Settings validation
├── test_session.py     # Connection management
├── test_errors.py      # Error code mapping
├── test_pacing.py      # Rate limiting
├── test_mapping.py     # DTO conversions
└── test_provider.py    # Provider implementation
```

---

## 📚 Examples

See the `examples/` directory:

- **`basic_streaming.py`**: Stream real-time quotes
- **`historical_data.py`**: Fetch historical bars with pacing

Run examples:

```bash
python examples/basic_streaming.py
python examples/historical_data.py
```

---

## 🔧 Requirements

### System Requirements

- **Python**: 3.11+
- **IBKR Gateway or TWS**: Running and connected
- **IBKR Account**: Paper or live with market data subscriptions

### IBKR Setup

1. **Download IBKR Gateway** or TWS from [Interactive Brokers](https://www.interactivebrokers.com/)
2. **Configure API settings**:
   - Enable API connections
   - Set socket port (4001=Live, 4002=Paper, 7497=TWS)
   - Add trusted IPs (127.0.0.1 for localhost)
3. **Start Gateway/TWS** and login
4. **Verify connection**: Check Gateway status shows "Listening"

### Market Data Subscriptions

Ensure your account has subscriptions for:

- US Securities Snapshot and Futures Value Bundle (for US stocks)
- Any other asset classes you plan to trade

Without proper subscriptions, you'll get `PermissionsMissing` errors (code 354).

---

## 🐛 Troubleshooting

### "Connection refused" (ConnectionFailed)

- ✅ Check IBKR Gateway/TWS is running
- ✅ Verify correct port (4002 for paper, 4001 for live)
- ✅ Check firewall allows connections to 127.0.0.1

### "No market data permissions" (PermissionsMissing)

- ✅ Verify market data subscriptions in Account Management
- ✅ Try `market_data_type=3` (delayed data) if live data not subscribed
- ✅ Check symbol is valid and trading on specified exchange

### "Pacing violation" (PacingViolation)

- ✅ Slow down requests (built-in rate limiter helps but may need tuning)
- ✅ Wait for cooldown (10 minutes for historical data)
- ✅ Use `PacingManager.clear_cooldown(scope)` to manually reset (use cautiously)

### Historical data returns empty

- ✅ Check date range is valid (not future dates)
- ✅ Verify market hours (use `useRTH=True` in settings)
- ✅ Ensure instrument has data for requested period

---

## 🗂️ Migration from Legacy Code

If upgrading from the old `src/ibkr_client.py` architecture:

### Old Code (Legacy)

```python
from src.market_data_collector import MarketDataCollector

collector = MarketDataCollector()
await collector.connect()
data = await collector.collect_historical_data(["AAPL"], "1 M", "1 day")
await collector.disconnect()
```

### New Code (v1.0.0)

```python
from market_data_ibkr import IBKRProvider, IBKRSettings
from market_data_core import Instrument
from datetime import datetime, timedelta

settings = IBKRSettings(host="127.0.0.1", port=4002)

async with IBKRProvider(settings) as provider:
    instrument = Instrument(symbol="AAPL")
    end = datetime.now()
    start = end - timedelta(days=30)
    
    async for bar in provider.request_historical_bars(
        instrument, start, end, resolution="1d"
    ):
        print(bar)
```

### Key Changes

- **Protocol conformance**: All methods return Core DTOs
- **Async context manager**: `async with` for automatic cleanup
- **Settings-based config**: No more raw env vars in code
- **Error handling**: Canonical exceptions instead of generic errors
- **Rate limiting**: Built-in pacing management

### Legacy Code Location

Old code has been moved to `legacy/` for reference:

```
legacy/
├── config.py
├── main.py
├── requirements.txt
├── __init__.py
├── data_store.py
├── ibkr_client.py
└── market_data_collector.py
```

⚠️ **Note**: `data_store.py` (SQLite storage) is not part of the Core protocol. Storage is handled downstream by consumers of the provider.

---

## 🐳 Docker Deployment

### Running as a Service

This provider can run as a containerized HTTP service for integration with the market-data platform infrastructure.

#### Build the Image

```bash
docker build -t market-data-ibkr:latest .
```

#### Run Standalone

```bash
docker run -d \
  --name ibkr \
  -p 8084:8084 \
  -e IBKR_HOST=host.docker.internal \
  -e IBKR_GATEWAY_PORT=4002 \
  -e IBKR_CLIENT_ID=17 \
  market-data-ibkr:latest
```

**Note**: Use `host.docker.internal` to connect to IBKR Gateway running on your host machine.

#### Run with Docker Compose

This service is designed to integrate with the `market_data_infra` compose stack:

```yaml
# In market_data_infra/docker-compose.yml
ibkr:
  build: ../market_data_ibkr
  container_name: ibkr
  environment:
    IBKR_ACCOUNT: ${IBKR_ACCOUNT}
    IBKR_GATEWAY_PORT: ${IBKR_GATEWAY_PORT}
    CORE_URL: ${CORE_URL}
  ports: ["8084:8084"]
  depends_on:
    core:
      condition: service_healthy
  healthcheck:
    test: ["CMD-SHELL", "curl -fsS http://localhost:8084/health || exit 1"]
    interval: 10s
    timeout: 3s
    retries: 10
  networks: [mdnet]
  profiles: ["pipeline"]
```

Start the service:

```bash
# From market_data_infra directory
docker compose --profile pipeline up -d ibkr
```

### HTTP API Endpoints

Once running, the service exposes:

#### Health Check

```bash
curl http://localhost:8084/health
```

Response:
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "connected": true
}
```

#### Prometheus Metrics

```bash
curl http://localhost:8084/metrics
```

#### Stream Quotes (SSE)

```bash
curl -X POST http://localhost:8084/api/v1/stream/quotes \
  -H "Content-Type: application/json" \
  -d '{"symbols": ["AAPL", "MSFT"]}'
```

#### Historical Bars

```bash
curl -X POST http://localhost:8084/api/v1/historical/bars \
  -H "Content-Type: application/json" \
  -d '{
    "symbol": "AAPL",
    "start": "2024-01-01T00:00:00Z",
    "end": "2024-01-31T00:00:00Z",
    "resolution": "1d"
  }'
```

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `IBKR_HOST` | `127.0.0.1` | IBKR Gateway/TWS host |
| `IBKR_GATEWAY_PORT` | `4002` | IBKR Gateway port |
| `IBKR_CLIENT_ID` | `17` | Client ID for connection |
| `PORT` | `8084` | HTTP service port |

### Using with IBKR Gateway

When running in Docker, you need to ensure the container can reach your IBKR Gateway:

**Option 1**: Run IBKR Gateway on host, use `host.docker.internal`

```bash
docker run -e IBKR_HOST=host.docker.internal ...
```

**Option 2**: Run IBKR Gateway in same Docker network

```bash
# Not recommended - IBKR Gateway has complex requirements
```

**Option 3**: Expose Gateway port and connect by host IP

```bash
docker run -e IBKR_HOST=192.168.1.100 ...
```

### Health Checks

The Docker image includes a built-in health check that runs every 10 seconds:

```bash
# Check container health
docker inspect ibkr --format='{{.State.Health.Status}}'
```

Healthy containers will show: `healthy`

---

## 📝 Roadmap

### v1.0.0 (Current)

- ✅ Quote streaming
- ✅ Bar streaming (5s real-time)
- ✅ Historical bars with pacing
- ✅ Auto-reconnection
- ✅ Error mapping
- ✅ Contract caching

### v1.1.0 (Planned)

- 🚧 Tick-by-tick trade streaming
- 🚧 Options chain streaming
- 🚧 Futures support
- 🚧 Forex support

### v2.0.0 (Future)

- 🔮 Multi-threaded contract resolution
- 🔮 Advanced pacing strategies
- 🔮 WebSocket alternative (if IBKR adds support)

---

## 🤝 Contributing

Contributions welcome! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/your-feature`)
3. Add tests for new functionality
4. Ensure all tests pass (`pytest tests/`)
5. Run linter (`ruff check src/`)
6. Submit a pull request

---

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details.

---

## 🔗 Links

- **market-data-core**: https://github.com/mjdevaccount/market-data-core
- **ib_insync Documentation**: https://ib-insync.readthedocs.io/
- **IBKR API Documentation**: https://interactivebrokers.github.io/tws-api/
- **Issues**: https://github.com/YOUR_ORG/market-data-ibkr/issues

---

## 💬 Support

For questions or issues:

1. Check [Troubleshooting](#-troubleshooting) section
2. Search [existing issues](https://github.com/YOUR_ORG/market-data-ibkr/issues)
3. Open a [new issue](https://github.com/YOUR_ORG/market-data-ibkr/issues/new) with:
   - Python version
   - IBKR Gateway/TWS version
   - Minimal reproduction code
   - Full error traceback

---

**Happy Trading! 📈**
