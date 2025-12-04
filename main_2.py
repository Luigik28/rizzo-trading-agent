from indicators import analyze_multiple_tickers
from news_feed import fetch_latest_news
from trading_agent import previsione_trading_agent
from whalealert import format_whale_alerts_to_string
from sentiment import get_sentiment
from forecaster import get_crypto_forecasts
from hyperliquid_trader import HyperLiquidTrader
import os
import json
import db_utils
import time
import logging
# Disabilita log verbosi PRIMA di caricare .env e eseguire operazioni
logging.getLogger('cmdstanpy').disabled = True
logging.getLogger('prophet').setLevel(logging.WARNING)
from datetime import datetime
from dotenv import load_dotenv
load_dotenv()

# Configurazione del ciclo
CYCLE_INTERVAL = 9000  # secondi (2.5 ore)
RUN_CONTINUOUSLY = True  # Imposta False per eseguire una sola volta

# Collegamento ad Hyperliquid
TESTNET = False   # True = testnet, False = mainnet (occhio!)
VERBOSE = True    # stampa informazioni extra
PRIVATE_KEY = os.getenv("PRIVATE_KEY")
WALLET_ADDRESS = os.getenv("WALLET_ADDRESS")

if not PRIVATE_KEY or not WALLET_ADDRESS:
    raise RuntimeError("PRIVATE_KEY o WALLET_ADDRESS mancanti nel .env")

def run_trading_cycle():
    """Esegue un ciclo completo di trading"""
    try:
        print(f"\n{'='*60}")
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Inizio ciclo di trading")
        print(f"{'='*60}\n")
        
        bot = HyperLiquidTrader(
            secret_key=PRIVATE_KEY,
            account_address=WALLET_ADDRESS,
            testnet=TESTNET
        )

        # Calcolo delle informazioni in input per Ticker
        tickers = ['BTC', 'ETH', 'SOL']
        print("📊 Raccolta indicatori tecnici...")
        indicators_txt, indicators_json = analyze_multiple_tickers(tickers)
        
        print("📰 Raccolta notizie...")
        news_txt = fetch_latest_news()
        
        print("💭 Analisi sentiment...")
        sentiment_txt, sentiment_json = get_sentiment()
        
        print("🔮 Generazione forecast...")
        forecasts_txt, forecasts_json = get_crypto_forecasts()

        msg_info = f"""<indicatori>\n{indicators_txt}\n</indicatori>\n\n
        <news>\n{news_txt}</news>\n\n
        <sentiment>\n{sentiment_txt}\n</sentiment>\n\n
        <forecast>\n{forecasts_txt}\n</forecast>\n\n"""

        print("💰 Verifica stato account...")
        account_status = bot.get_account_status()
        portfolio_data = f"{json.dumps(account_status)}"
        snapshot_id = db_utils.log_account_status(account_status)
        print(f"[db_utils] Snapshot account salvato con id={snapshot_id}")

        # Creating System prompt
        with open('system_prompt.txt', 'r') as f:
            system_prompt = f.read()
        system_prompt = system_prompt.format(portfolio_data, msg_info)
            
        print("🤖 L'agente sta decidendo la sua azione...")
        out = previsione_trading_agent(system_prompt)
        
        print(f"\n📋 Decisione: {out['operation'].upper()} {out['symbol']}")
        print(f"   Direzione: {out.get('direction', 'N/A')}")
        print(f"   Motivazione: {out['reason']}\n")
        print(f"   Motivazione ita: {out['reason_ita']}\n")
        
        bot.execute_signal(out)

        op_id = db_utils.log_bot_operation(
            out, 
            system_prompt=system_prompt, 
            indicators=indicators_json, 
            news_text=news_txt, 
            sentiment=sentiment_json, 
            forecasts=forecasts_json
        )
        print(f"[db_utils] Operazione salvata con id={op_id}")
        
        print(f"\n✅ Ciclo completato con successo!")
        return True

    except Exception as e:
        print(f"\n❌ Errore durante il ciclo: {e}")
        try:
            db_utils.log_error(
                e, 
                context={
                    "tickers": tickers,
                    "indicators": indicators_json if 'indicators_json' in locals() else None,
                    "news": news_txt if 'news_txt' in locals() else None,
                    "sentiment": sentiment_json if 'sentiment_json' in locals() else None,
                    "forecasts": forecasts_json if 'forecasts_json' in locals() else None,
                    "balance": account_status if 'account_status' in locals() else None
                }, 
                source="trading_agent"
            )
        except:
            pass
        return False

# Main loop
if __name__ == "__main__":
    print(f"\n🚀 Avvio Trading Agent")
    print(f"{'='*60}")
    print(f"Modalità: {'TESTNET' if TESTNET else '⚠️  MAINNET'}")
    print(f"Intervallo ciclo: {CYCLE_INTERVAL} secondi ({CYCLE_INTERVAL/60:.1f} minuti)")
    print(f"Esecuzione continua: {'Sì' if RUN_CONTINUOUSLY else 'No'}")
    print(f"{'='*60}\n")
    
    if RUN_CONTINUOUSLY:
        cycle_count = 0
        while True:
            cycle_count += 1
            print(f"\n🔄 Ciclo #{cycle_count}")
            
            success = run_trading_cycle()
            
            if success:
                print(f"\n⏰ Prossimo ciclo tra {CYCLE_INTERVAL} secondi...")
                print(f"   (Prossima esecuzione: {datetime.fromtimestamp(time.time() + CYCLE_INTERVAL).strftime('%H:%M:%S')})")
            else:
                print(f"\n⚠️  Ciclo fallito, riprovo tra {CYCLE_INTERVAL} secondi...")
            
            try:
                time.sleep(CYCLE_INTERVAL)
            except KeyboardInterrupt:
                print("\n\n🛑 Interruzione manuale ricevuta")
                print("Arresto del trading agent...")
                break
    else:
        # Esecuzione singola
        run_trading_cycle()
        print("\n✅ Esecuzione completata (modalità singola)")
