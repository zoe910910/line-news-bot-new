# app.py

import os
from flask import Flask, request, abort
import urllib.parse
import requests
from bs4 import BeautifulSoup
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage

YOUR_CHANNEL_ACCESS_TOKEN = os.environ.get('jVPQmBqX+1AgqwC6jPlfFaKwZltWSPNlHrdwo8KXw2krfWFuq8KLaOeaWQfxGtrgQ/WI5KazdDSKhQQTBV4cBeA42WGjGkEMFf3tylBOpNinuzIBfRjgWUnIIWcWeERVwkWFfQ/cw5RwgvFn+VW+0AdB04t89/1O/w1cDnyilFU=', "")
YOUR_CHANNEL_SECRET = os.environ.get('72c1dd7da164b7d96ae69d2cc0965f66', "")

app = Flask(__name__)

line_bot_api = LineBotApi(YOUR_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(YOUR_CHANNEL_SECRET)

port = int(os.environ.get('PORT', 5000))

@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return 'OK'

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    brand = event.message.text.strip()
    reply_msg = fetch_top10_news(brand)

    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=reply_msg)
    )

# -------------------------------------------
# 👇 核心功能：抓 Google News 前 10 則新聞
# -------------------------------------------
def fetch_top10_news(brand):
    encoded = urllib.parse.quote(brand)
    url = f"https://www.google.com/search?q={encoded}+新聞&tbm=nws&tbs=qdr:w&hl=zh-TW"

    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    r = requests.get(url, headers=headers)
    soup = BeautifulSoup(r.text, "html.parser")

    results = soup.select("a")  # 先抓所有 a

    news_links = []
    for a in results:
        href = a.get("href", "")

        # Google news link pattern: /url?q=...
        if href.startswith("/url?q=") and "google" not in href:
            link = href.replace("/url?q=", "").split("&")[0]
            news_links.append(link)

        if len(news_links) >= 10:
            break

    # 如果沒有新聞
    if not news_links:
        return f"找不到 {brand} 的新聞，可能是無相關結果。"

    # 組合回 LINE
    reply = f"📰 {brand} 當週前 10 則最新新聞：\n\n"
    for i, url in enumerate(news_links, 1):
        reply += f"{i}. {url}\n"

    return reply


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=port)
