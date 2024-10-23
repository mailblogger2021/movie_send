import json
import urllib
from flask import Flask, request
from dbhelper import DBHelper
import aiohttp
import asyncio

app = Flask(__name__)
db = DBHelper()

# TOKEN
TOKEN = "7910154011:AAFlqDOHHS_K-5zhmSpLJxlfM_NWJaoXpss"
URL = f"https://api.telegram.org/bot{TOKEN}/"


async def get_url(session, url):
    async with session.get(url) as response:
        content = await response.text()
        return content


async def send_message(session, text, chat_id, reply_markup=None, reply_to_message_id=None):
    if not text:
        return
    text = urllib.parse.quote_plus(text)
    url = URL + f"sendMessage?text={text}&chat_id={chat_id}&parse_mode=Markdown"

    if reply_markup:
        url += f"&reply_markup={reply_markup}"
    if reply_to_message_id:
        url += f"&reply_to_message_id={reply_to_message_id}"

    response = await get_url(session, url)
    return json.loads(response)


def build_keyboard(items):
    keyboard = [[item] for item in items]
    reply_markup = {"keyboard": keyboard, "one_time_keyboard": True}
    return json.dumps(reply_markup)


@app.route(f"/{TOKEN}", methods=["POST"])
async def webhook():
    if request.method == "POST":
        update = request.get_json()

        if "message" in update:
            chat_id = update["message"]["chat"]["id"]
            message_id = update["message"]["message_id"]
            text = update["message"].get("text")

            async with aiohttp.ClientSession() as session:
                if text == "/start":
                    await send_message(session, "Welcome to your To Do list. Send any text to store it as an item.", chat_id)
                elif text == "/done":
                    items = db.get_items(chat_id)
                    keyboard = build_keyboard(items)
                    await send_message(session, "Select an item to delete", chat_id, keyboard)
                else:
                    items = db.get_value(text)
                    await send_message(session, f"{','.join(items)}", chat_id, reply_to_message_id=message_id)

    return "OK", 200


if __name__ == "__main__":
    app.run(port=5000)
