# app.py

import os
from flask import Flask, request, abort
import urllib.parse
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage

# --- 1. LINE Credentials ---
# Note: Render will use environment variables (if set) first.
YOUR_CHANNEL_ACCESS_TOKEN = os.environ.get('LINE_BOT_ACCESS_TOKEN', "K34uCEOUEhVUYr6THN9oV+04VH0Ytyg2l7e5XrsQHa8QPcHtkeoBzOWAzXbC8oRGQ/WI5KazdDSKhQQTBV4cBeA42WGjGkEMFf3tylBOpNhdyxuKRA4QPz1BR27uglGvb4gDDR3NQxEs7VpHTBBBagdB04t89/1O/w1cDnyilFU=")
YOUR_CHANNEL_SECRET = os.environ.get('LINE_BOT_SECRET', "72c1dd7da164b7d96ae69d2cc0965f66")
# ---------------------------

app = Flask(__name__)

line_bot_api = LineBotApi(YOUR_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(YOUR_CHANNEL_SECRET)

port = int(os.environ.get('PORT', 5000))

# --- 2. Webhook Route ---
@app.route("/callback", methods=['POST'])
def callback():
    """Handles POST requests from LINE Webhook."""
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        print("Invalid signature. Check your tokens.")
        abort(400)
    
    return 'OK'

# --- 3. Message Handler ---
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    """Handles incoming text messages."""
    user_brand = event.message.text.strip()
    
    reply_text = generate_news_summary(user_brand)
    
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=reply_text)
    )

# --- 4. Core Logic: Generate Google Search Link (No API) ---
def generate_news_summary(brand_name):
    """Generates a Google search link for the past week's news."""
    
    encoded_brand_name = urllib.parse.quote(brand_name)
    
    # qdr:w parameter for "Past week"
    news_search_url = f"https://www.google.com/search?q={encoded_brand_name}+新聞&tbs=qdr:w&hl=zh-TW"
    
    # LINE Bot API automatically makes the URL clickable
    summary = f"🤖 **{brand_name} 當週新聞摘要** 整理如下：\n\n"
    summary += f"**1. 新聞摘要：** 請點擊下方連結，直接查看 Google 針對 '{brand_name}' 的當週新聞。\n\n"
    summary += f"**2. 當週新聞網址：**\n"
    summary += f"🔗 [點擊查看 {brand_name} 最新當週新聞]({news_search_url})\n\n"
    summary += f"(資訊來源：Google 搜索，時間範圍：過去一周)"

    return summary


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=port)