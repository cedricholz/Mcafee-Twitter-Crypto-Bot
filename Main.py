import utils
import time
import math
import threading
from threading import Thread

# CONSTANTS # # # # # # # #
SELL_THRESHOLD = -0.08    # % drop/gain in the timespan of CHECK_TIMER
CHECK_TIMER = 10          # calculates the drop/gain over the last X seconds
# # # # # # # # # # # # # #

state = {}
state['binance'] = False
state['bittrex'] = False

utils.reduce_file_size('image_to_ocr.jpg', pow(2, 17))

utils.print_and_write_to_logfile('STARTING...')

binance = utils.get_binance_account()
bittrex = utils.get_bittrex_account()

binance_coins = utils.binance_symbols_and_names_to_markets_and_names(binance)
bittrex_coins = utils.bittrex_symbols_and_names_to_markets_and_names()

twitter = utils.get_twitter_account()
twitter_user = 'officialmcafee'

ocr = utils.get_ocr_account()

seen_coins = utils.get_seen_coins()

twitter = utils.get_twitter_account()


def check_statuses(twitter, twitter_user, seen_coins):


    coin_of_the_day_tweet = utils.get_coin_of_the_day_tweet(twitter, ocr)

    finished = False

    for word in coin_of_the_day_tweet.split(" "):
        lowered_word = word.lower()

        if lowered_word in binance_coins and lowered_word not in seen_coins:
            utils.print_and_write_to_logfile("FOUND COIN: " + lowered_word)
            market = binance_coins[lowered_word][0]
            utils.buy_from_binance(binance, market)
            symbol = market.split('BTC')[0].lower()
            utils.add_to_seen_coins(binance_coins, bittrex_coins, symbol)
            finished = True
            state['binance'] = True

        if lowered_word in bittrex_coins and lowered_word not in seen_coins:
            utils.print_and_write_to_logfile("FOUND COIN: " + lowered_word)
            market = bittrex_coins[lowered_word][0]
            utils.buy_from_bittrex(bittrex, market)
            symbol = market.split('-')[1].lower()
            utils.add_to_seen_coins(binance_coins, bittrex_coins, symbol)
            seen_coins = utils.get_seen_coins()
            if lowered_word not in seen_coins:
                utils.add_to_seen_coins(binance_coins, bittrex_coins, symbol)
            finished = True
            state['bittrex'] = True

        if finished:
            state['symbol'] = symbol
            return True, symbol
    return False, ''

def wait_for_tweet_and_buy():
    bought = False
    while not bought:
        bought, symbol = check_statuses(twitter, twitter_user, seen_coins)
        time.sleep(4)
    return symbol

def get_price_bittrex(bittrex, symbol):
    market = 'BTC-' + symbol.upper()
    ticker = bittrex.get_ticker(market)
    return ticker['result']['Last']

def get_price_binance(binance, symbol):
    market = symbol.upper() + 'BTC'
    prices = binance.get_orderbook_tickers()
    price = list(filter(lambda m: m['symbol'] == market, prices))
    return float(price[0]['askPrice'])


def sell_at_peak(state, symbol):
    if state['bittrex']:
        last_price_bittrex = get_price_bittrex(bittrex, symbol)
    if state['binance']:
        last_price_binance = get_price_binance(binance, symbol)

    while state['bittrex'] or state['binance']:
        time.sleep(CHECK_TIMER)

        if state['bittrex']:
            cur_price_bittrex = get_price_bittrex(bittrex, symbol)
            delta = (cur_price_bittrex - last_price_bittrex) / last_price_bittrex
            last_price_bittrex = cur_price_bittrex

            utils.print_and_write_to_logfile('CHECKING PRICE ON BITTREX')
            utils.print_and_write_to_logfile("CURRENT PRICE: " + str(last_price_bittrex))
            utils.print_and_write_to_logfile("DELTA: " + str(delta) + '\n')

            if delta < SELL_THRESHOLD:
                utils.print_and_write_to_logfile("THRESHOLD REACHED | SELLING ON BITTREX...")
                utils.sell_on_bittrex(bittrex, 'BTC-' + symbol.upper())
                state['bittrex'] = False

        if state['binance']:
            cur_price_binance = get_price_binance(binance, symbol)
            delta = (cur_price_binance - last_price_binance) / last_price_binance
            last_price_binance = cur_price_binance

            utils.print_and_write_to_logfile('CHECKING PRICE ON BINANCE')
            utils.print_and_write_to_logfile("CURRENT PRICE: " + str(last_price_binance))
            utils.print_and_write_to_logfile("DELTA: " + str(delta) + '\n')

            if delta < SELL_THRESHOLD:
                utils.print_and_write_to_logfile("THRESHOLD REACHED | SELLING ON BINANCE...")

                # sell TODO

                state['bittrex'] = False

# # # # #  MAIN  # # # # #
utils.print_and_write_to_logfile('STARTING BUY PHASE')
bought_symbol = wait_for_tweet_and_buy()
utils.print_and_write_to_logfile('STARTING SELL PHASE')
sell_at_peak(state, bought_symbol)
utils.print_and_write_to_logfile('TERMNINATING...')
