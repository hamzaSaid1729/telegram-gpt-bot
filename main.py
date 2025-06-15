import os
import pandas as pd
from datetime import datetime
from telegram.ext import ApplicationBuilder, MessageHandler, ContextTypes, filters
from openai import OpenAI

# Environment variables
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
FILENAME = 'phd_opportunities.xlsx'

# OpenAI client
client = OpenAI(api_key=OPENAI_API_KEY)

def extract_info_with_gpt(phd_url):
    prompt = f"""
    Extract the following information from this PhD opportunity:
    - Title
    - University
    - Deadline
    - Country
    - One-line summary

    Link: {phd_url}

    Format:
    Title: ...
    University: ...
    Deadline: ...
    Country: ...
    Summary: ...
    """
    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Error: {str(e)}"

def parse_gpt_reply(reply, link):
    data = {'Link': link, 'Timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
    for line in reply.strip().split('\n'):
        if ':' in line:
            key, val = line.split(':', 1)
            data[key.strip()] = val.strip()
    return data

async def handle_message(update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if text.startswith("http"):
        await update.message.reply_text("🔍 Extracting info from the link...")
        gpt_reply = extract_info_with_gpt(text)
        await update.message.reply_text(f"📋 GPT Response:\n\n{gpt_reply}")

        structured_data = parse_gpt_reply(gpt_reply, text)

        try:
            df = pd.read_excel(FILENAME)
        except FileNotFoundError:
            df = pd.DataFrame(columns=['Link', 'Title', 'University', 'Deadline', 'Country', 'Summary', 'Timestamp'])

        df = pd.concat([df, pd.DataFrame([structured_data])], ignore_index=True)
        df.to_excel(FILENAME, index=False)

        await update.message.reply_text("✅ Saved to Excel.")
    else:
        await update.message.reply_text("❌ Please send a valid PhD opportunity link.")

# ✅ NEW Application, NO `.updater` anywhere

# ✅ NEW Application, NO `.updater` anywhere
app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

# ✅ Start the bot directly
if __name__ == "__main__":
    app.run_polling()
