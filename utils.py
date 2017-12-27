from forex_python.bitcoin import BtcConverter
from Bittrex3 import Bittrex3
from binance.client import Client
import urllib
import json
import re
import twitter
from datetime import datetime
import time
import math
import OCRSpace
import tweepy
from tweepy import OAuthHandler
import re
import os
from PIL import Image
import math

def download_image(image_url, local_filename):
     urllib.request.urlretrieve(image_url, local_filename)


from resizeimage import resizeimage


def reduce_file_size(filename, size_limit):
    size_limit = size_limit / 4
    picture = Image.open(filename)
    height_original = picture.height
    width_original = picture.width

    height_new = math.floor(math.sqrt(size_limit*height_original/width_original))
    width_new = math.floor(size_limit/height_new)

    new_size = height_new*width_new
    resized_image = picture.resize((width_new, height_new), Image.ANTIALIAS)
    resized_image.save("image_to_ocr_scaled.jpg", quality=100)
    print_and_write_to_logfile("Reducing file size to: " + str(width_new) + " x " + str(height_new))


def get_image_text(ocr, image_url):
    local_filename = 'image_to_ocr.jpg'
    download_image(image_url, local_filename)

    file_size = os.stat(local_filename).st_size

    size_limit = 1048576
    if file_size > size_limit:
        reduce_file_size(filename, size_limit)

    ocr_data = ocr.ocr_file(local_filename)['ParsedResults'][0]['TextOverlay']['Lines']

    picture_text = ""
    for line in ocr_data:
        for word in line['Words']:
            picture_text += re.sub(r'\W+', '', word['WordText'])  + " "

    return picture_text

def get_coin_of_the_day_tweet(twitter, ocr):
    tweets = twitter.user_timeline(screen_name='officialmcafee',
                                   count=200, include_rts=False,
                                   exclude_replies=True)

    for status in tweets:
        tweet_text = status._json['text']

        media = status.entities.get('media', [])
        if len(media) > 0:
            image_link = media[0]['media_url']
            tweet_text += tweet_text + ' ' + get_image_text(ocr, image_link)
        lowered_tweet = tweet_text.lower()
        if 'coin of the day' in lowered_tweet:
            return lowered_tweet

    return coin_of_the_day_tweets



def query_url(url_addr):
    with urllib.request.urlopen(url_addr) as url:
        return json.loads(url.read().decode())


def get_seen_coins():
    with open('seen_coins.txt', 'r') as f:
        seen_coins = json.loads(f.read())
    return seen_coins


def add_to_seen_coins(binance_coins, bittrex_coins, symbol):
    seen_coins = get_seen_coins()

    full_name = ''
    if symbol in binance_coins:
        full_name = binance_coins[symbol][1]
    elif symbol in bittrex_coins:
        full_name = bittrex_coins[symbol][1]

    seen_coins.append(full_name)
    seen_coins.append(symbol)

    with open('seen_coins.txt', 'w') as f:
        f.write(json.dumps(seen_coins))


def bittrex_symbols_and_names_to_markets_and_names():
    bittrex_coins = get_bittrex_market_names()
    buyable_coins = {}
    for symbol in bittrex_coins:
        full_name = bittrex_coins[symbol]['full_name'].lower()
        buyable_coins[symbol.lower()] = ('BTC-' + symbol, full_name)
        buyable_coins[full_name] = ('BTC-' + symbol, full_name)
    return buyable_coins


def binance_symbols_and_names_to_markets_and_names(binance):
    buyable_coins = {}
    products = binance.get_products()
    for coin in products['data']:
        market_currency = coin['quoteAssetName']
        if market_currency == "Bitcoin":
            market = coin['symbol']
            symbol = coin['baseAsset']
            full_name = coin['baseAssetName'].lower()

            buyable_coins[symbol.lower()] = (market, full_name)
            buyable_coins[full_name] = (market, full_name)
    return buyable_coins


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

    consumer_key = secrets['consumer_key']
    consumer_secret = secrets['consumer_secret']
    access_token = secrets['access_token_key']
    access_secret = secrets['access_token_secret']

    auth = OAuthHandler(consumer_key, consumer_secret)
    auth.set_access_token(access_token, access_secret)

    return tweepy.API(auth)


def get_ocr_account():
    with open("ocr_secret.json") as secret_file:
        secret = json.load(secret_file)
        secret_file.close()
    key = secret['api_key']
    return OCRSpace.OCRSpace(secret['api_key'])


def get_date_time():
    now = datetime.now()
    return "%s:%s:%s %s/%s/%s" % (now.hour, now.minute, now.second, now.month, now.day, now.year)


def print_and_write_to_logfile(log_text):
    timestamp = '[' + get_date_time() + '] '
    log_text = timestamp + log_text
    if log_text is not None:
        print(log_text)

        with open('logs.txt', 'a') as myfile:
            myfile.write(log_text + '\n')


def get_total_bittrex_bitcoin(bittrex):
    result = bittrex.get_balance('BTC')
    if result['success']:
        total_bitcoin = float(bittrex.get_balance('BTC')['result']['Available'])
        total_bitcoin = total_bitcoin - .0025 * total_bitcoin
        return total_bitcoin
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


def get_bittrex_rate_amount(bittrex, market, total_bitcoin):
    sell_book = bittrex.get_orderbook(market, 'sell', depth=20)['result']
    sell_book_list = [order for order in sell_book]

    sell_order_to_start_with = 0

    for i in range(sell_order_to_start_with, len(sell_book_list)):
        order = sell_book_list[i]
        order_rate = float(order['Rate'])
        order_quantity = float(order['Quantity'])
        amount_to_buy = total_bitcoin / order_rate
        if amount_to_buy < order_quantity:
            return math.floor(amount_to_buy), order_rate

def get_bittrex_amount_to_sell_and_price(bittrex, market):
    amount_to_sell = float(bittrex.get_balance(market.split('-')[1])['result']['Balance'])
    rate = float(bittrex.get_ticker(market)['result']['Ask'])
    return amount_to_sell, rate

def sell_on_bittrex(bittrex, market):
    while True:
        amount_to_sell, rate = get_bittrex_amount_to_sell_and_price(bittrex, market)

        sell_order = bittrex.sell_limit(market, amount_to_sell, rate)

        while not sell_order['success']:
            print_and_write_to_logfile("Buy Unsucessful")
            time.sleep(4)
            sell_order = bittrex.sell_market(market, amount_to_buy, rate)

        # Wait for order to go through
        time.sleep(10)

        get_open_orders = bittrex.get_open_orders(market)
        while not get_open_orders['success']:
            print_and_write_to_logfile("Get Open Orders Unsuccessful")
            time.sleep(4)
            get_open_orders = bittrex.get_open_orders(market)

        my_open_orders = get_open_orders['result']

        if len(my_open_orders) == 0:
            print_and_write_to_logfile("SUCCESSFUL ORDER ON BITTREX")
            print_and_write_to_logfile("MARKET: " + market)
            print_and_write_to_logfile("AMOUNT: " + str(amount_to_sell))
            print_and_write_to_logfile("RATE: " + str(rate))
            return 'Success'
        else:
            print_and_write_to_logfile("UNABLE TO SELL AT THIS PRICE")
            for order in my_open_orders:
                print_and_write_to_logfile("Canceling " + order['OrderUuid'])
                canceled = bittrex.cancel(order['OrderUuid'])
                while not canceled['success']:
                    print_and_write_to_logfile("Cancel unsuccessful")
                    time.sleep(4)
                    canceled = bittrex.cancel(order['OrderUuid'])
            # Wait for sell to go through
            time.sleep(10)


def buy_from_bittrex(bittrex, market):
    total_bitcoin = get_total_bittrex_bitcoin(bittrex)

    while True:
        amount_to_buy, rate = get_bittrex_rate_amount(bittrex, market, total_bitcoin)
        print_and_write_to_logfile("Buying " + str(amount_to_buy) + " at " + str(rate))

        # Attempt to make buy order
        buy_order = bittrex.buy_limit(market, amount_to_buy, rate)

        while not buy_order['success']:
            print_and_write_to_logfile("Buy Unsucessful")
            time.sleep(4)
            buy_order = bittrex.buy_limit(market, amount_to_buy, rate)

        # Wait for order to go through
        time.sleep(10)

        # Attempt to get list of open orders
        get_open_orders = bittrex.get_open_orders(market)
        while not get_open_orders['success']:
            print_and_write_to_logfile("Get Open Orders Unsuccessful")
            time.sleep(4)
            get_open_orders = bittrex.get_open_orders(market)

        my_open_orders = get_open_orders['result']

        if len(my_open_orders) == 0:
            print_and_write_to_logfile("SUCCESSFUL ORDER ON BITTREX")
            print_and_write_to_logfile("MARKET: " + market)
            print_and_write_to_logfile("AMOUNT: " + str(amount_to_buy))
            print_and_write_to_logfile("TOTAL: " + str(total_bitcoin))
            return 'Success'
        else:
            for order in my_open_orders:
                print_and_write_to_logfile("Canceling " + order['OrderUuid'])
                canceled = bittrex.cancel(order['OrderUuid'])
                while not canceled['success']:
                    print_and_write_to_logfile("Cancel unsuccessful")
                    time.sleep(4)
                    canceled = bittrex.cancel(order['OrderUuid'])
            # Wait for cancel to go through
            time.sleep(10)


def get_binance_amount_to_buy(binance, market, total_bitcoin):
    tickers = binance.get_exchange_info()['symbols']

    ticker = [ticker for ticker in tickers if ticker['symbol'] == market][0]

    constraints = ticker['filters'][1]

    minQty = float(constraints['minQty'])
    maxQty = float(constraints['maxQty'])
    stepSize = float(constraints['stepSize'])

    trades = binance.get_recent_trades(symbol=market)
    for trade in trades:
        order_rate = float(trade['price'])
        order_quantity = float(trade['qty'])

        amount_to_buy = total_bitcoin / order_rate

        constrained_amount_to_buy = math.floor((1 / stepSize) * amount_to_buy) * stepSize
        if amount_to_buy < order_quantity:
            if constrained_amount_to_buy < minQty or constrained_amount_to_buy > maxQty:
                return 0
            return amount_to_buy


def get_total_binance_bitcoin(binance):
    accounts = binance.get_account()['balances']
    for coin in accounts:
        if coin['asset'] == 'BTC':
            total_bitcoin = float(coin['free'])
            total_bitcoin = total_bitcoin - .001 * total_bitcoin
            return total_bitcoin
    return 0


def buy_from_binance(binance, market):
    total_bitcoin = get_total_binance_bitcoin(binance)

    amount = get_binance_amount_to_buy(binance, market, total_bitcoin)

    order = binance.order_market_buy(
        symbol=market,
        quantity=amount)
    print_and_write_to_logfile("SUCCESSFUL ORDER ON BINANCE")
    print_and_write_to_logfile("MARKET: " + market)
    print_and_write_to_logfile("AMOUNT: " + str(amount))
    print_and_write_to_logfile("TOTAL: " + str(total_bitcoin))



def get_binance_amount_to_sell(binance, symbol, market):

    tickers = binance.get_exchange_info()['symbols']

    ticker = [ticker for ticker in tickers if ticker['symbol'] == market][0]

    constraints = ticker['filters'][1]

    minQty = float(constraints['minQty'])
    maxQty = float(constraints['maxQty'])
    stepSize = float(constraints['stepSize'])

    accounts = binance.get_account()['balances']
    for coin in accounts:
        if coin['asset'] == symbol:
            amount_held =  float(coin['free'])
            amount_to_sell = math.floor((1 / stepSize) * amount_held) * stepSize
            if amount_to_sell < minQty or amount_to_sell > maxQty:
                return 0
            else:
                return amount_to_sell
    return 0

def sell_on_binance(binance, symbol):
    symbol = symbol.upper()
    market = symbol + 'BTC'

    amount = get_binance_amount_to_sell(binance, symbol, market)

    if amount > 0:
        order = binance.order_market_sell(
            symbol=market,
            quantity=amount)

        print_and_write_to_logfile("SELL ORDER ON BINANCE SUCCESSFUL")
        print_and_write_to_logfile("MARKET: " + symbol)
        print_and_write_to_logfile("AMOUNT" + str(amount))

    else:
        print_and_write_to_logfile("NOT ENOUGH COIN TO MAKE SELL ORDER")
