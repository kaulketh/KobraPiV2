import telepot
from werkzeug.security import generate_password_hash, check_password_hash
from flask_httpauth import HTTPBasicAuth
import mySecrets

# page auth
USR = mySecrets.page_user
PSSWD = mySecrets.page_pass
(uss) = {USR: generate_password_hash(PSSWD)}
auth = HTTPBasicAuth()


@auth.verify_password
def verify_password(name, psswd):
    if name in uss and check_password_hash(uss.get(name), psswd):
        return name


# telegram
TELEGRAM_TOKEN = mySecrets.telegram_token
CHAT_ID = mySecrets.telegram_chat_id

KOBRA_BOT = telepot.Bot(TELEGRAM_TOKEN)
