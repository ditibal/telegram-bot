import logging
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from telegram.utils.helpers import mention_html
from telegram import ParseMode
import urllib.request
import ipaddress
import random
import yaml
from pathlib import Path
import sys
import traceback
from functools import wraps

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)


config_file = str(Path.home()) + '/.telegram-bot'

with open(config_file, 'r') as stream:
    try:
        config = yaml.safe_load(stream)
    except yaml.YAMLError as exc:
        logging.error('Failed to read config file')
        sys.exit(1)

LIST_OF_ADMINS = config['admins']

def restricted(func):
    @wraps(func)
    def wrapped(update, context, *args, **kwargs):
        user_id = update.effective_user.id
        if user_id not in LIST_OF_ADMINS:
            logger.info("Unauthorized access denied for {}.".format(user_id))
            return
        return func(update, context, *args, **kwargs)
    return wrapped


@restricted
def ip(update, context):
    ip = get_ip()

    if ip:
        update.message.reply_text(ip)
    else:
        update.message.reply_text('Не удалось получить ip')

@restricted
def test(update, context):
    update.message.reply_text('Test')

def error(update, context):
    logger.warning('Update "%s" caused error "%s"', update, context.error)
    # we want to notify the user of this problem. This will always work, but not notify users if the update is an
    # callback or inline query, or a poll update. In case you want this, keep in mind that sending the message
    # could fail
    if update.effective_message:
        text = "Hey. I'm sorry to inform you that an error happened while I tried to handle your update. " \
               "My developer(s) will be notified."
        update.effective_message.reply_text(text)
    # This traceback is created with accessing the traceback object from the sys.exc_info, which is returned as the
    # third value of the returned tuple. Then we use the traceback.format_tb to get the traceback as a string, which
    # for a weird reason separates the line breaks in a list, but keeps the linebreaks itself. So just joining an
    # empty string works fine.
    trace = "".join(traceback.format_tb(sys.exc_info()[2]))
    # lets try to get as much information from the telegram update as possible
    payload = ""
    # normally, we always have an user. If not, its either a channel or a poll update.
    if update.effective_user:
        payload += f' with the user {mention_html(update.effective_user.id, update.effective_user.first_name)}'
    # there are more situations when you don't get a chat
    if update.effective_chat:
        payload += f' within the chat <i>{update.effective_chat.title}</i>'
        if update.effective_chat.username:
            payload += f' (@{update.effective_chat.username})'
    # but only one where you have an empty payload by now: A poll (buuuh)
    if update.poll:
        payload += f' with the poll id {update.poll.id}.'
    # lets put this in a "well" formatted text
    text = f"Hey.\n The error <code>{context.error}</code> happened{payload}. The full traceback:\n\n<code>{trace}" \
           f"</code>"
    # and send it to the dev(s)
    for dev_id in LIST_OF_ADMINS:
        context.bot.send_message(dev_id, text, parse_mode=ParseMode.HTML)
    # we raise the error again, so the logger module catches it. If you don't use the logger module, use it.
    raise

def get_ip():
    urls = [
        'https://l2.io/ip',
        'https://eth0.me',
        'https://icanhazip.com',
        'https://ipecho.net/plain',
        'https://ifconfig.me/',
        'https://ifconfig.co/',
    ]

    random.shuffle(urls)

    for url in urls:
        try:
            req = urllib.request.Request(
                url,
                headers={'User-Agent': 'curl/7.68.0'}
            )

            logging.info('Get IP by ' + url)

            response = urllib.request.urlopen(req, timeout=2)
            ip = response.read().decode('UTF-8').strip()
            return str(ipaddress.ip_address(ip))
        except:
            logging.info('Failed get IP by ' + url)
            pass


def main():
    updater = Updater(config['token'], use_context=True, request_kwargs={'proxy_url': config['proxy']})

    dp = updater.dispatcher

    dp.add_handler(CommandHandler("ip", ip))

    dp.add_handler(CommandHandler("test", test))

    dp.add_error_handler(error)

    updater.start_polling()

    for admin_id in LIST_OF_ADMINS:
        updater.bot.send_message(admin_id, 'Started...')

    updater.idle()

if __name__ == '__main__':
    main()
