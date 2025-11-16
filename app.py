# app.py

import os
import json
from flask import Flask, request, abort
import requests
import urllib.parse
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage

# --- 1. 凭证设定 (请使用您的真实凭证) ---
# 建议在实际部署时使用 os.environ.get 来读取环境变量，但为了保持与您现有代码的连续性，暂时保留硬编码。
# 请确认这两个值是您在 LINE Developers Console 获得的真实凭证！
YOUR_CHANNEL_ACCESS_TOKEN = "T0fMOgvUjHHicsv+2KGAsyym/1g+QHBfeh+vTVwdoHMkSWOZ+Qj1dRwZWGR9Buz/Q/WI5KazdDSKhQQTBV4cBeA42WGjGkEMFf3tylBOpNjqEXGuEWKWHeScvvEwCcLX9woZUs3QOTsUFH0pqA4MWwdB04t89/1O/w1cDnyilFU="
YOUR_CHANNEL_SECRET = "72c1dd7da164b7d96ae69d2cc0965f66"
# ---------------------------------------------

# Gemini API 配置
API_KEY = "" # 由 Canvas/Render 环境注入
GEMINI_API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-preview-09-2025:generateContent?key={API_KEY}"

# Flask 应用程序初始化
app = Flask(__name__)

# LINE Bot API 初始化
line_bot_api = LineBotApi(YOUR_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(YOUR_CHANNEL_SECRET)

# 端口设定（Render 需要）
port = int(os.environ.get('PORT', 5000))

# --- 2. 路由：接收 LINE Webhook 的唯一入口 ---
@app.route("/callback", methods=['POST'])
def callback():
    """处理来自 LINE 的 Webhook 请求"""
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        print("Invalid signature. Please check your channel access token/secret.")
        abort(400)
    
    return 'OK'

# --- 3. 事件处理器：处理用户发送的文本消息 ---
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    """处理用户发送的文字消息"""
    user_brand = event.message.text.strip()
    
    # 调用生成摘要的函数
    reply_text = generate_news_summary(user_brand)
    
    # 发送回复
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=reply_text)
    )

# --- 4. 核心逻辑：使用 Google Search 和 Gemini API 生成摘要 ---
def generate_news_summary(brand_name):
    """
    1. 使用 Google Search 工具获取当周新闻。
    2. 将搜索结果传递给 Gemini 模型生成摘要和格式化链接。
    """
    
    user_query = f"請搜尋過去一周內，品牌 '{brand_name}' 的相關新聞。請提供 5 個最相關的中文新聞連結及摘要。"

    # --- 1. 构造 Gemini API 请求 Payload ---
    system_prompt = (
        f"你是一个专业的品牌新闻分析师。你的任务是根据用户提供的品牌名称，调用 Google Search 工具，"
        f"然后根据搜索结果（限定为当周新闻），提供一份简洁的摘要和完整的可点击链接清单。"
        f"请使用繁体中文回复，且回复内容必须包含：\n"
        f"1. 标题：'{brand_name} 當週新聞摘要'\n"
        f"2. 簡潔摘要：针对本周新闻的重点整理（2-3句话）。\n"
        f"3. 新闻链接：将所有找到的新闻标题和 URL 整理成 LINE 可点击的 Markdown 链接格式。确保每个链接都是可点击的。"
        f"範例格式: [新聞标题](URL)"
    )

    payload = {
        "contents": [{"parts": [{"text": user_query}]}],
        "tools": [{"google_search": {}}],
        "systemInstruction": {"parts": [{"text": system_prompt}]},
    }
    
    # --- 2. 发送请求到 Gemini API ---
    try:
        response = requests.post(
            GEMINI_API_URL, 
            headers={"Content-Type": "application/json"}, 
            json=payload,
            timeout=30 
        )
        response.raise_for_status() 
        
        result = response.json()
        
        candidate = result.get('candidates', [{}])[0]
        generated_text = candidate.get('content', {}).get('parts', [{}])[0].get('text', "")

        if generated_text:
            return generated_text
        else:
            return f"❌ 抱歉，模型未能为 '{brand_name}' 生成摘要，请稍后重试。"
    
    except requests.exceptions.Timeout:
        return "❌ 抱歉，生成新聞摘要超時了，請再試一次。"
    except requests.exceptions.RequestException as e:
        app.logger.error(f"Gemini API Request Failed: {e}")
        return f"❌ 抱歉，Gemini API 调用失败，错误信息: {e}"
    except Exception as e:
        app.logger.error(f"An unexpected error occurred: {e}")
        return f"❌ 发生未知错误：{e}"


if __name__ == "__main__":
    # 在本地环境中运行
    app.run(host='0.0.0.0', port=port)