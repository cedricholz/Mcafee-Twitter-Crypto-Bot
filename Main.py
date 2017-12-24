import utils
import time
import math


binance = utils.get_binance_account()

bittrex = utils.get_bittrex_account()

binance_coins = utils.binance_symbols_names_to_symbols(binance)
bittrex_coins = utils.bittrex_symbols_names_to_symbols()

twitter = utils.get_twitter_account()
twitter_user = 'officialmcafee'

seen_coins = ['dgb', 'digibyte', 'burst']

def check_statuses(twitter, twitter_user):
    statuses = twitter.GetUserTimeline(screen_name=twitter_user)
    coin_of_the_day_tweets = [s.text for s in statuses if "coin of the day" in s.text.lower()]

    for tweet in coin_of_the_day_tweets:
        for word in tweet.split(" "):
            lowered_word = word.lower()
            if lowered_word in binance_coins and lowered_word not in seen_coins:
                # utils.buy_from_binance(binance, binance_coins[lowered_word])
                print(lowered_word)
                return True
            elif lowered_word in bittrex_coins and lowered_word not in seen_coins:
                # utils.buy_from_bittrex(bittrex, bittrex_coins[lowered_word])
                print(lowered_word)
                return True
    return False


done = False
while not done:
    done = check_statuses(twitter, twitter_user)
    time.sleep(10)
