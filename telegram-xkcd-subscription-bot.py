#!/usr/bin/env python3.4

import telegram
import xkcd
import logging
from time import sleep
import atexit
import api_token # add your token here

logging.basicConfig(level=logging.INFO)
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)

last_latest = 0
bot = telegram.Bot(token = api_token.api_token)
subscribed_chat_ids = set()  # this is a set
updates_per_minute = 30
sub_filename = "subscribed_chat_ids"

def main():
    last_update_id = 0
    read_subscription_file_to_set(subscribed_chat_ids)

    run = True
    while run:
        # check for new subscriptions
        updates = bot.getUpdates(offset=last_update_id+1)
        if len(updates) > 0:
            last_update_id = updates[-1].update_id
            logging.info("New last_update_id %d" % last_update_id)
            process_updates(updates)

        # check and send out new comics
        try:
            is_new_comic, number = check_new_comic()
            if is_new_comic:
                send_new_comic_to_all(number)
        except ConnectionResetError as cre:
            logging.warning(cre)
        except TimeoutError as toe:
            logging.warning(toe)

        # sleep some time
        sleep(60 / updates_per_minute)

def process_updates(updates):
    for update in updates:
        message = update.message
        logging.info("processing message '%s' from user '%s'" % (message.text, message.from_user))
        if '/start' in message.text:
            logging.info("received /start from %s" % message.from_user)
            if message.chat_id not in subscribed_chat_ids:
                bot.sendMessage(chat_id=message.chat_id,
                                text="You just subscribed to XKCD updates. To stop receiving updates type /stop")
            subscribed_chat_ids.add(message.chat_id)
            write_subscription_file()

        if '/stop' in message.text:
            logging.info("received /stop from %s" % message.from_user)
            if message.chat_id in subscribed_chat_ids:
                bot.sendMessage(chat_id=message.chat_id,
                                text="You will not receive any XKCD updates from now on.")
            subscribed_chat_ids.remove(message.chat_id)
            write_subscription_file()

        if '/help' in message.text:
            logging.info("received /help from %s" % message.from_user)
            bot.sendMessage(chat_id=message.chat_id, text="You asked for help. What is wrong?")


def send_new_comic_to_all(number):
    for id in subscribed_chat_ids:
        send_new_comic(number, id)

def send_new_comic(number, chat_id):
    comic = xkcd.getComic(number)
    bot.sendMessage(chat_id=chat_id, text="Title:\n%s" % comic.getTitle())
    bot.sendPhoto(chat_id=chat_id, photo=comic.getImageLink())
    bot.sendMessage(chat_id=chat_id, text="Alt text:\n%s" % comic.getAltText())

def check_new_comic():
    global last_latest
    latest = xkcd.getLatestComicNum()
    if latest > last_latest:
        last_latest = latest
        return (True, latest)
    return (False, latest)

def read_subscription_file_to_set(subscribed_chat_ids):
    logging.info("Reading subscription file")
    with open(sub_filename, 'r') as file:
        for line in file:
            subscribed_chat_ids.add(int(line))

def write_subscription_file():
    logging.info("Writing subscription file")
    with open(sub_filename, "w") as file_chat_ids:
        file_chat_ids.writelines(["%s\n" % str(i) for i in subscribed_chat_ids])

if __name__ == '__main__':
    atexit.register(write_subscription_file)
    main()


