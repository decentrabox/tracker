import requests
import time
from eth_utils import to_checksum_address
from wallets import WALLETS
ETHERSCAN_API_KEY = ""
TELEGRAM_BOT_TOKEN = ""  # From @BotFather
TELEGRAM_CHAT_ID = ""  # Your chat ID
CHECK_INTERVAL = 60  # Seconds between checks
WALLETS = WALLETS

# Function to get transactions from Etherscan

def get_transactions(address, startblock=0):
    url = f'https://api.etherscan.io/api'
    params = {
        'module': 'account',
        'action': 'txlist',
        'address': address,
        'startblock': startblock,
        'endblock': 99999999,
        'sort': 'asc',
        'apikey': ETHERSCAN_API_KEY
    }
    response = requests.get(url, params=params)
    data = response.json()
    if 'result' in data and isinstance(data['result'], list):
        return data['result']
    else:
        print(f"Error fetching transactions: {data}")
        return []

# Function to get latest block number

def get_latest_block_number():
    url = f'https://api.etherscan.io/api?module=proxy&action=eth_blockNumber&apikey={ETHERSCAN_API_KEY}'
    response = requests.get(url).json()
    if 'result' in response:
        return int(response['result'], 16)
    return 0

# Function to send messages to Telegram

def send_telegram_message(message):
    url = f'https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage'
    payload = {
        'chat_id': TELEGRAM_CHAT_ID,
        'text': message
    }
    requests.post(url, json=payload)

# Function to determine transaction type

def categorize_transaction(tx):
    if int(tx['value']) > 0:
        return "ETH Transfer"
    elif len(tx['input']) > 10:
        return "Possible Swap / Contract Interaction"
    return "Other"

# Main monitoring loop

def monitor_wallets():
    last_seen = {wallet: get_latest_block_number() for wallet in WALLETS}

    while True:
        for wallet in WALLETS:
            transactions = get_transactions(wallet, last_seen[wallet])

            for tx in transactions:
                if isinstance(tx, dict) and 'blockNumber' in tx:
                    if int(tx['blockNumber']) > last_seen[wallet]:
                        last_seen[wallet] = int(tx['blockNumber'])

                        direction = 'INCOMING' if tx['to'].lower() == wallet.lower() else 'OUTGOING'
                        tx_type = categorize_transaction(tx)
                        maker_address = tx['from']
                        checksum_address = to_checksum_address(maker_address)
                        dexscreener_link = f"https://dexscreener.com/ethereum/{tx['to']}?maker={checksum_address}"
                        etherscan_link = f"https://etherscan.io/tx/{tx['hash']}"
                        message = (
                            f"📢 New {direction} transaction detected:\n"
                            f"Type: {tx_type}\n"
                            f"From: {tx['from']}\n"
                            f"To: {tx['to']}\n"
                            f"Amount: {int(tx['value']) / 10**18} ETH\n"
                            f"Tx Link: {etherscan_link}\n"
                            f"Time: {time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(int(tx['timeStamp'])))}\n"
                            f"Dexscreener: {dexscreener_link}"
                        )
                        send_telegram_message(message)
                else:
                    print(f"Unexpected transaction format: {tx}")

        time.sleep(CHECK_INTERVAL)

if __name__ == '__main__':
    monitor_wallets()
