# app.py

import os
from flask import Flask, request, abort
import requests
import urllib.parse
import re
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage

# --- 1. LINE 凭证设定 ---
YOUR_CHANNEL_ACCESS_TOKEN = "jVPQmBqX+1AgqwC6jPlfFaKwZltWSPNlHrdwo8KXw2krfWFuq8KLaOeaWQfxGtrgQ/WI5KazdDSKhQQTBV4cBeA42WGjGkEMFf3tylBOpNinuzIBfRjgWUnIIWcWeERVwkWFfQ/cw5RwgvFn+VW+0AdB04t89/1O/w1cDnyilFU="
YOUR_CHANNEL_SECRET = "72c1dd7da164b7d96ae69d2cc0965f66"
# ---------------------------------

# Flask 初始化
app = Flask(__name__)

# LINE Bot 初始化
line_bot_api = LineBotApi(YOUR_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(YOUR_CHANNEL_SECRET)

port = int(os.environ.get('PORT', 5000))

# --- 2. Webhook 路由 ---
@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        print("Invalid signature. Please check your tokens.")
        abort(400)
    
    return 'OK'

# --- 3. 訊息處理 ---
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_brand = event.message.text.strip()
    reply_text = generate_news_summary(user_brand)

    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=reply_text)
    )

# --- 4. 核心功能：抓前 10 則 Google 新聞 ---
def generate_news_summary(brand_name):
    encoded_brand_name = urllib.parse.quote(brand_name)
    news_search_url = f"https://www.google.com/search?q={encoded_brand_name}+新闻&tbs=qdr:w&hl=zh-TW"

    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        r = requests.get(news_search_url, headers=headers, timeout=5)
        html = r.text
    except Exception as e:
        return f"抓取 {brand_name} 新闻时出错: {e}"

    # 正则抓取 /url?q= 開頭的連結，忽略 Google 自己的
    links = re.findall(r'/url\?q=(https?://[^&]+)&', html)
    news_links = []
    for link in links:
        if "google" not in link:
            news_links.append(link)
        if len(news_links) >= 10:
            break

    if not news_links:
        return f"找不到 {brand_name} 的新闻，可能是无相关结果。"

    # 組合回覆
    summary = f"🤖 {brand_name} 当周前 10 条最新新闻：\n\n"
    for i, url in enumerate(news_links, 1):
        summary += f"{i}. {url}\n"

    return summary

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=port)
