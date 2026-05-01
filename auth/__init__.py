"""
A module for authenticating HTTP requests and sending messages using Telegram.

This module handles user authentication through HTTP basic authentication and
provides functionality for integrating with the Telegram API to send messages.
It uses hashed passwords for secure authentication.

It relies on external secrets for sensitive information such as Telegram token,
chat ID, and basic authentication credentials, which are imported from a
separate secure file.
"""
import telepot
from flask_httpauth import HTTPBasicAuth
from werkzeug.security import generate_password_hash, check_password_hash

from .mySecrets import *  # no public deployment ;-)

# page auth
USR = page_user
PSSWD = page_pass
(uss) = {USR: generate_password_hash(PSSWD)}
AUTH = HTTPBasicAuth()


@AUTH.verify_password
def verify_password(name, psswd):
    if name in uss and check_password_hash(uss.get(name), psswd):
        return name
    return None


# telegram
TELEGRAM_TOKEN = telegram_token
CHAT_ID = telegram_chat_id
KOBRA_BOT = telepot.Bot(TELEGRAM_TOKEN)
