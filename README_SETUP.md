# Setup Guide for Rizzo Trading Agent with Perplexity Support

## Quick Start

### 1. Prerequisites
- Python 3.10+ (or 3.8+)
- PostgreSQL (or a PostgreSQL-compatible database)
- API keys:
  - **OpenAI**: https://platform.openai.com/api-keys
  - **Perplexity**: https://www.perplexity.ai (if using Perplexity instead of OpenAI)
  - **CoinMarketCap Pro**: https://coinmarketcap.com/api/
  - **HyperLiquid**: Set up your account and generate API credentials

### 2. Installation

#### On Windows (PowerShell)
```powershell
# Clone or download the project
cd C:\Python\projects\rizzo-trading-agent

# Create and activate virtual environment
python -m venv .venv
.venv\Scripts\Activate.ps1

# Install dependencies
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

#### On macOS/Linux (Bash)
```bash
cd ~/projects/rizzo-trading-agent

# Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate

# Install dependencies
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

### 3. Configure Environment Variables

Copy `env.example` to `.env` and fill in your actual values:

```bash
cp env.example .env
# Then edit .env with your favorite editor
```

**Key variables:**
- `OPENAI_API_KEY`: Your OpenAI or Perplexity API key
- `OPENAI_API_BASE`: Leave empty for OpenAI; set to `https://api.perplexity.ai` for Perplexity
- `DATABASE_URL`: PostgreSQL connection string
- `PRIVATE_KEY`: HyperLiquid private key
- `WALLET_ADDRESS`: HyperLiquid wallet address
- `CMC_PRO_API_KEY`: CoinMarketCap API key

### 4. Database Setup (Ubuntu/Linux)

#### Install PostgreSQL
```bash
sudo apt update
sudo apt install -y postgresql postgresql-contrib
sudo systemctl enable --now postgresql
```

#### Create Database and User
```bash
sudo -u postgres psql

# Inside psql:
CREATE USER rzbot WITH PASSWORD 'StrongPassword123!';
CREATE DATABASE trading_db OWNER rzbot;
GRANT ALL PRIVILEGES ON DATABASE trading_db TO rzbot;
\q
```

#### Initialize Database Schema
```bash
source .venv/bin/activate
python db_utils.py  # Creates all required tables
```

#### Verify Connection
```bash
psql postgresql://rzbot:StrongPassword123!@localhost:5432/trading_db -c "\dt"
```

### 5. Using Perplexity Instead of OpenAI

#### Option A: Use environment variable (recommended)
Edit your `.env` file:
```
OPENAI_API_KEY=pplx-...    # Your Perplexity API key
OPENAI_API_BASE=https://api.perplexity.ai
```

#### Option B: Use environment variable (temporary, current session only)

**PowerShell (Windows):**
```powershell
$env:OPENAI_API_KEY="pplx-..."
$env:OPENAI_API_BASE="https://api.perplexity.ai"
python main.py
```

**Bash (macOS/Linux):**
```bash
export OPENAI_API_KEY="pplx-..."
export OPENAI_API_BASE="https://api.perplexity.ai"
python main.py
```

### 6. Run the Trading Agent

```bash
source .venv/bin/activate   # Or .venv\Scripts\Activate.ps1 on Windows
python main.py
```

The agent will:
1. Load configuration from `.env`
2. Analyze market indicators (BTC, ETH, SOL)
3. Fetch latest news and sentiment
4. Call the LLM (OpenAI or Perplexity) to generate a trading signal
5. Execute the signal via HyperLiquid API
6. Log all operations and errors to the PostgreSQL database

### 7. Test Configuration

#### Test Perplexity Connection
```bash
python -c "
import os
from dotenv import load_dotenv
load_dotenv()
print('API Key:', os.getenv('OPENAI_API_KEY')[:10] + '...' if os.getenv('OPENAI_API_KEY') else 'NOT SET')
print('Base URL:', os.getenv('OPENAI_API_BASE') or 'DEFAULT (OpenAI)')
print('Using Perplexity:', 'perplexity' in (os.getenv('OPENAI_API_BASE') or '').lower())
"
```

#### Test Database Connection
```bash
python -c "
import db_utils
try:
    with db_utils.get_connection() as conn:
        print('✓ Database connected successfully')
except Exception as e:
    print(f'✗ Database error: {e}')
"
```

#### Test LLM Call
```bash
python -c "
import os, json
from dotenv import load_dotenv
from trading_agent import previsione_trading_agent

load_dotenv()
test_prompt = 'Market is bullish. Recommend action.'
try:
    result = previsione_trading_agent(test_prompt)
    print('✓ LLM call successful')
    print('Response:', json.dumps(result, indent=2))
except Exception as e:
    print(f'✗ LLM error: {e}')
"
```

## Troubleshooting

### Perplexity API Errors

#### Error: `401 Unauthorized`
- Check that `OPENAI_API_KEY` is set to a valid Perplexity API key (format: `pplx-...`)
- Verify the key hasn't expired or been revoked

#### Error: `400 Bad Request`
- Perplexity may not support all OpenAI API features used (e.g., specific parameters)
- The code automatically falls back to Chat Completions API

#### Error: `404 Not Found`
- Verify `OPENAI_API_BASE` is exactly `https://api.perplexity.ai`
- Check that your request format matches Perplexity's API spec

### Database Errors

#### Error: `DATABASE_URL not impostata`
- Ensure `.env` file has `DATABASE_URL=postgresql://...`
- Test with: `python -c "import os; print(os.getenv('DATABASE_URL'))"`

#### Error: `could not connect to server: Connection refused`
- Ensure PostgreSQL is running: `sudo systemctl status postgresql`
- Verify the host/port/credentials in `DATABASE_URL`

### Module Not Found Errors

#### Error: `ModuleNotFoundError: No module named 'openai'`
- Reinstall requirements: `pip install -r requirements.txt`
- Ensure you're in the virtual environment: `source .venv/bin/activate`

## Switching Between OpenAI and Perplexity

To switch back to OpenAI from Perplexity, simply:
1. Edit `.env` and remove or comment out `OPENAI_API_BASE`
2. Set `OPENAI_API_KEY` to your OpenAI key
3. Restart the application

The code automatically detects which provider to use based on `OPENAI_API_BASE`.

## Additional Resources

- [Perplexity AI API Docs](https://docs.perplexity.ai)
- [OpenAI API Docs](https://platform.openai.com/docs)
- [HyperLiquid API](https://hyperliquid-testnet.firebaseapp.com/)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
