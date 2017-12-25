import utils
import time
import math


binance = utils.get_binance_account()

bittrex = utils.get_bittrex_account()

binance_coins = utils.binance_symbols_and_names_to_markets_and_names(binance)
bittrex_coins = utils.bittrex_symbols_and_names_to_markets_and_names()

twitter = utils.get_twitter_account()
twitter_user = 'officialmcafee'


seen_coins = utils.get_seen_coins()


def check_statuses(twitter, twitter_user, seen_coins):
    statuses = twitter.GetUserTimeline(screen_name=twitter_user)
    coin_of_the_day_tweets = [s.text for s in statuses if "coin of the day" in s.text.lower()]

    finished = False
    for tweet in coin_of_the_day_tweets:
        for word in tweet.split(" "):
            lowered_word = word.lower()

            if lowered_word in binance_coins and lowered_word not in seen_coins:
                utils.print_and_write_to_logfile("Binance: Buying " + lowered_word)

                market = binance_coins[lowered_word][0]

                utils.buy_from_binance(binance, market)

                symbol = market.split('BTC')[0].lower()
                utils.add_to_seen_coins(binance_coins, bittrex_coins, symbol)


                finished = True
            if lowered_word in bittrex_coins and lowered_word not in seen_coins:
                utils.print_and_write_to_logfile("Bittrex: Buying " + lowered_word)

                market = bittrex_coins[lowered_word][0]

                utils.buy_from_bittrex(bittrex, market)

                symbol = market.split('-')[1].lower()
                utils.add_to_seen_coins(binance_coins, bittrex_coins, symbol)

                seen_coins = utils.get_seen_coins()
                if lowered_word not in seen_coins:
                    utils.add_to_seen_coins(binance_coins, bittrex_coins, symbol)

                finished = True
            if finished:
                return True, symbol
    return False, ''

def wait_for_tweet_and_buy():
    bought = False
    while not bought:
        bought, symbol = check_statuses(twitter, twitter_user, seen_coins)
        time.sleep(4)
    return symbol

def sell_at_peak(symbol):
    if symbol in binance_coins:
        return
    if symbol in bittrex_coins:
        return
    return


bought_symbol = wait_for_tweet_and_buy()

sell_at_peak(bought_symbol)




