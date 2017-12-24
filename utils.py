from forex_python.bitcoin import BtcConverter
from Bittrex3 import Bittrex3
from binance.client import Client
import urllib
import json
import re
import twitter
import datetime
import time


def query_url(url_addr):
    with urllib.request.urlopen(url_addr) as url:
        return json.loads(url.read().decode())


def bittrex_symbols_names_to_symbols():
    bittrex_coins = get_bittrex_market_names()
    buyable_coins = {}
    for symbol in bittrex_coins:
        buyable_coins[symbol.lower()] = 'BTC-' + symbol
        buyable_coins[bittrex_coins[symbol]['full_name'].lower()] = 'BTC-' + symbol
    return buyable_coins


def binance_symbols_names_to_symbols(binance):
    buyable_coins = {}
    products = binance.get_products()
    for coin in products['data']:
        market_currency = coin['quoteAssetName']
        if market_currency == "Bitcoin":
            market = coin['symbol']
            symbol = coin['baseAsset']
            full_name = coin['baseAssetName'].lower()

            buyable_coins[symbol.lower()] = market
            buyable_coins[full_name] = market
    return buyable_coins


def bitcoin_to_usd(bitcoin_amount):
    b = BtcConverter()
    latest_price = b.get_latest_price('USD')
    return latest_price * bitcoin_amount


def get_bittrex_account():
    with open("bittrex_secrets.json") as secrets_file:
        secrets = json.load(secrets_file)
        secrets_file.close()

    return Bittrex3(secrets['key'], secrets['secret'])


def get_binance_account():
    with open("binance_secrets.json") as secrets_file:
        secrets = json.load(secrets_file)
        secrets_file.close()

    return Client(secrets['key'], secrets['secret'])


def get_twitter_account():
    with open("twitter_secrets.json") as secrets_file:
        secrets = json.load(secrets_file)
        secrets_file.close()

    return twitter.Api(secrets['consumer_key'],
                       secrets['consumer_secret'],
                       secrets['access_token_key'],
                       secrets['access_token_secret'])


def get_updated_coinmarketcap_coins():
    return query_url("https://api.coinmarketcap.com/v1/ticker/?limit=2000")


def get_date_time():
    now = datetime.now()
    return "%s:%s:%s %s/%s/%s" % (now.hour, now.minute, now.second, now.month, now.day, now.year)


def time_stamp_to_date(timstamp):
    return datetime.fromtimestamp(int(timstamp)).strftime('%H:%M:%S %m/%d/%Y')


def print_and_write_to_logfile(log_text):
    if log_text is not None:
        print(log_text + '\n')

        with open('logs.txt', 'a') as myfile:
            myfile.write(log_text + '\n\n')


def get_total_bittrex_bitcoin(bittrex):
    result = bittrex.get_balance('BTC')
    if result['success']:
        return float(bittrex.get_balance('BTC')['result']['Available'])
    else:
        print_and_write_to_logfile("Bitcoin Balance Request Unsuccessful")
        return 0


def bittrex_coins():
    bittrex_data = query_url("https://bittrex.com/api/v1.1/public/getmarketsummaries")['result']
    coins = {}
    for coin in bittrex_data:
        key = coin['MarketName']
        coins[key] = coin
    return coins


def get_bittrex_market_names():
    bittrex_data = query_url("https://bittrex.com/api/v1.1/public/getmarkets")['result']
    coins = {}
    for coin in bittrex_data:
        if coin['BaseCurrency'] == 'BTC':
            key = coin['MarketCurrency']
            t = {}
            t['full_name'] = coin['MarketCurrencyLong']
            coins[key] = t
    return coins


def get_bitrex_rate_amount(bittrex, market, total_bitcoin):
    sell_book = bittrex.get_orderbook(market, 'sell', depth=20)['result']
    for order in sell_book:
        order_rate = float(order['Rate'])
        order_quantity = float(order['Quantity'])
        amount_to_buy = total_bitcoin * order_rate
        if amount_to_buy < order_quantity:
            return amount_to_buy, order_rate


def buy_from_bittrex(bittrex, market):
    total_bitcoin = get_total_bittrex_bitcoin(bittrex)

    while True:
        amount_to_buy, rate = get_bitrex_rate_amount(bittrex, market, total_bitcoin)
        buy_order = api.buy_limit(market, amount_to_buy, rate)

        time.sleep(10)

        get_open_orders = bittrex.get_open_orders(market)
        if get_open_order['success']:
            my_open_orders = get_open_orders['result']

        if len(my_open_orders) == 0:
            return 'Success'
        else:
            for order in my_open_orders:
                bittrex.cancel(order['OrderUuid'])

def buy_from_binance(binance, market):
