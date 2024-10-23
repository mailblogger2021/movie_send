import json
import aiohttp
import asyncio
import time
import urllib
from dbhelper import DBHelper

db = DBHelper()

# TOKEN = config.token
TOKEN = "7910154011:AAFlqDOHHS_K-5zhmSpLJxlfM_NWJaoXpss"
URL = "https://api.telegram.org/bot{}/".format(TOKEN)


async def get_url(session, url):
    async with session.get(url) as response:
        content = await response.text()
        return content


async def get_json_from_url(session, url):
    content = await get_url(session, url)
    js = json.loads(content)
    return js


async def get_updates(session, offset=None):
    url = URL + "getUpdates"
    if offset:
        url += "?offset={}".format(offset)
    js = await get_json_from_url(session, url)
    return js


def get_last_update_id(updates):
    update_ids = [int(update["update_id"]) for update in updates["result"]]
    return max(update_ids)


async def handle_update(session, update):
    print(update)
    try:
        text = update["message"]["text"]
        chat = update["message"]["chat"]["id"]
        message_id = update["message"]["message_id"]
    except KeyError:
        return

    items = db.get_items(chat)
    if text == "/done":
        keyboard = build_keyboard(items)
        await send_message(session, "Select an item to delete", chat, keyboard)
    elif text == "/start":
        await send_message(session, "Welcome to your personal To Do list. Send any text to me and I'll store it as an item. Send /done to remove items", chat)
    elif text.startswith("/"):
        return
    else:
        items = db.get_value(text)
        await send_message(session, f"{','.join(items)}", chat, reply_to_message_id=message_id)
    # if text in items:
    #     db.delete_item(text, chat)
    #     items = db.get_items(chat)
    #     keyboard = build_keyboard(items)
    #     await send_message(session, "Select an item to delete", chat, keyboard)
    # else:
    #     db.add_item(text, chat)
    #     items = db.get_items(chat)
    #     message = "\n".join(items)
    #     await send_message(session, message, chat)


async def handle_updates(session, updates):
    tasks = []
    for update in updates["result"]:
        tasks.append(handle_update(session, update))
    await asyncio.gather(*tasks)


def build_keyboard(items):
    keyboard = [[item] for item in items]
    reply_markup = {"keyboard": keyboard, "one_time_keyboard": True}
    return json.dumps(reply_markup)


async def send_message(session, text=None, chat_id=None, reply_markup=None, reply_to_message_id=None):
    if text == None or text == '':
        return
    text = urllib.parse.quote_plus(text)
    url = URL + "sendMessage?text={}&chat_id={}&parse_mode=Markdown".format(text, chat_id)
    if reply_markup:
        url += "&reply_markup={}".format(reply_markup)
    if reply_to_message_id:
        url += "&reply_to_message_id={}".format(reply_to_message_id)

    print(url)
    response = await get_url(session, url)
    response_js = json.loads(response)

    while not response_js["ok"]:
        if response_js["error_code"] == 429:  # Rate limit error
            retry_after = response_js["parameters"]["retry_after"]
            print(response_js['description'])
            await asyncio.sleep(min(60,retry_after))  # Wait for the specified time or 60 sec
            response = await get_url(session, url)
            response_js = json.loads(response)
        else:
            print(response_js['description'])

    return response


async def main():
    start_time = time.time()
    time_limit = 5.5 * 60 * 60 * 60  # 5.5 hours in seconds
    time_limit = 60  # 5.5 hours in seconds

    db.setup()
    last_update_id = None

    async with aiohttp.ClientSession() as session:
        # await send_message("Bot started...",644121036)

        while True:
            updates = await get_updates(session, last_update_id)
            print(updates)
            if len(updates["result"]) > 0:
                last_update_id = get_last_update_id(updates) + 1
                await handle_updates(session, updates)

            elapsed_time = time.time() - start_time
            if elapsed_time > time_limit:
                print("Time limit exceeded.")
                break
            await asyncio.sleep(0.5)

        # await send_message("Bot Ended...",644121036)


if __name__ == '__main__':
    
    asyncio.run(main())
