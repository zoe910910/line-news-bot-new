# app.py

import os
from flask import Flask, request, abort
import requests
import urllib.parse
import xml.etree.ElementTree as ET
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage

# --- 1. LINE 凭证设定 ---
YOUR_CHANNEL_ACCESS_TOKEN = "jVPQmBqX+1AgqwC6jPlfFaKwZltWSPNlHrdwo8KXw2krfWFuq8KLaOeaWQfxGtrgQ/WI5KazdDSKhQQTBV4cBeA42WGjGkEMFf3tylBOpNinuzIBfRjgWUnIIWcWeERVwkWFfQ/cw5RwgvFn+VW+0AdB04t89/1O/w1cDnyilFU="
YOUR_CHANNEL_SECRET = "72c1dd7da164b7d96ae69d2cc0965f66"
# ---------------------------------

app = Flask(__name__)
line_bot_api = LineBotApi(YOUR_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(YOUR_CHANNEL_SECRET)

port = int(os.environ.get('PORT', 5000))

# --- 2. Webhook Route ---
@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        print("Invalid signature. Check your tokens.")
        abort(400)
    
    return 'OK'

# --- 3. LINE 訊息處理 ---
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_brand = event.message.text.strip()
    reply_text = generate_news_summary(user_brand)

    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=reply_text)
    )

# --- 4. 核心功能：抓取 Google News RSS 前10則新聞 ---
def generate_news_summary(brand_name):
    encoded_brand_name = urllib.parse.quote(brand_name)
    rss_url = f"https://news.google.com/rss/search?q={encoded_brand_name}+when:7d&hl=zh-TW&gl=TW&ceid=TW:zh-Hant"

    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        r = requests.get(rss_url, headers=headers, timeout=5)
        r.raise_for_status()
        xml = r.text
        root = ET.fromstring(xml)
        items = root.findall(".//item")
    except Exception as e:
        return f"抓取 {brand_name} 新聞時出錯: {e}"

    if not items:
        return f"找不到 {brand_name} 的新聞"

    summary = f"🤖 {brand_name} 當週前 10 則最新新聞：\n\n"
    for i, item in enumerate(items[:10], 1):
        title = item.find("title").text
        link = item.find("link").text
        summary += f"**{i}. {title}**\n連結: {link}\n----------\n"

    return summary

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=port)
