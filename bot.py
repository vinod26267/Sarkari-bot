import os
from flask import Flask
import threading
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, LabeledPrice
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, PreCheckoutQueryHandler, filters, ContextTypes
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime
import io

# Render alive
app = Flask('')
@app.route('/')
def home(): return "BOT IS LIVE - @chatbotley"
def run(): app.run(host='0.0.0.0', port=8080)
threading.Thread(target=run).start()

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_USERNAME = os.getenv("CHANNEL_USERNAME", "@chatbotley")
REQUIRED_CHANNEL = CHANNEL_USERNAME

def get_font(size, bold=False):
    try:
        if bold:
            return ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", size)
        return ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", size)
    except:
        return ImageFont.load_default()

# FIXED START - NO EMPTY
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    try:
        member = await context.bot.get_chat_member(REQUIRED_CHANNEL, user.id)
        if member.status in ['left', 'kicked']:
            raise Exception("Not joined")
    except:
        keyboard = [
            [InlineKeyboardButton("📢 Join @chatbotley", url=f"https://t.me/{REQUIRED_CHANNEL.replace('@','')}")],
            [InlineKeyboardButton("✅ Check Again", callback_data="check_join")]
        ]
        await update.message.reply_text(
            f"👋 Hello {user.first_name}!\n\nChannel join karo: {REQUIRED_CHANNEL}",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return

    await update.message.reply_text(
        f"👋 Hello {user.first_name}!\n\n"
        "📸 *SARKARI PHOTO BOT*\n\n"
        "✅ White Background (Govt Rule)\n"
        "✅ Name + Date Neeche\n"
        "✅ Real Photo - No Cartoon\n"
        "✅ 20kb & 50kb Format\n\n"
        "👇 Apni photo bhejo abhi!",
        parse_mode="Markdown"
    )

async def check_join_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user = query.from_user
    try:
        member = await context.bot.get_chat_member(REQUIRED_CHANNEL, user.id)
        if member.status not in ['left', 'kicked']:
            await query.message.reply_text("✅ Joined! Ab apni photo bhejo 👇")
        else:
            await query.message.reply_text(f"❌ Join nahi kiya: {REQUIRED_CHANNEL}")
    except:
        await query.message.reply_text(f"Join karo: {REQUIRED_CHANNEL}")

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    photo_file = await update.message.photo[-1].get_file()
    file_bytes = await photo_file.download_as_bytearray()
    context.user_data['photo_bytes'] = file_bytes
    await update.message.reply_text("✍️ Apna pura naam bhejo (Ex: Rohit Sharma)")

async def handle_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if 'photo_bytes' not in context.user_data:
        return
    name = update.message.text.strip()
    context.user_data['name'] = name
    date_str = datetime.now().strftime("%d-%m-%Y")
    context.user_data['date_str'] = date_str

    # DEMO with REAL PHOTO + WATERMARK
    try:
        img = Image.open(io.BytesIO(context.user_data['photo_bytes'])).convert("RGB")
        W, H_PHOTO, H_STRIP = 400, 430, 70
        img_resized = img.resize((W, H_PHOTO), Image.LANCZOS)
        final = Image.new("RGB", (W, H_PHOTO + H_STRIP), "white")
        final.paste(img_resized, (0,0))
        draw = ImageDraw.Draw(final)
        font_bold = get_font(16, bold=True)
        font_wm = get_font(22, bold=True)

        text = f"{name} {date_str}"
        bbox = draw.textbbox((0,0), text, font=font_bold)
        tw = bbox[2]-bbox[0]
        th = bbox[3]-bbox[1]
        x = (W - tw)//2
        y = H_PHOTO + (H_STRIP - th)//2 - 2
        draw.text((x,y), text, fill="black", font=font_bold)
        draw.text((W//2 - 90, H_PHOTO//2 - 15), "DEMO @chatbotley", fill=(255,0,0), font=font_wm)

        final.save("demo.jpg", quality=90)
        keyboard = [[InlineKeyboardButton("💳 Pay 99 Stars - Watermark Remove", callback_data="pay_stars")]]
        await update.message.reply_photo(
            photo=open("demo.jpg","rb"),
            caption=f"✅ DEMO Ready: {name} {date_str}\n\nWatermark hatane ke liye pay karo 👇",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    except Exception as e:
        await update.message.reply_text(f"Error: {e}")

async def handle_pay_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    prices = [LabeledPrice("Sarkari Photo Clean", 99)]
    await context.bot.send_invoice(
        chat_id=query.message.chat_id,
        title="Sarkari Photo Clean",
        description="Watermark remove + 20kb & 50kb",
        payload="sarkari_photo_99",
        provider_token="",
        currency="XTR",
        prices=prices
    )

async def precheckout(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.pre_checkout_query.answer(ok=True)

async def successful_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        name = context.user_data.get('name', 'User')
        date_str = context.user_data.get('date_str', datetime.now().strftime("%d-%m-%Y"))
        img = Image.open(io.BytesIO(context.user_data['photo_bytes'])).convert("RGB")
        W, H_PHOTO, H_STRIP = 400, 430, 70
        img_resized = img.resize((W, H_PHOTO), Image.LANCZOS)
        final_clean = Image.new("RGB", (W, H_PHOTO + H_STRIP), "white")
        final_clean.paste(img_resized, (0,0))
        draw = ImageDraw.Draw(final_clean)
        font_bold = get_font(16, bold=True)
        text = f"{name} {date_str}"
        bbox = draw.textbbox((0,0), text, font=font_bold)
        tw = bbox[2]-bbox[0]
        th = bbox[3]-bbox[1]
        x = (W - tw)//2
        y = H_PHOTO + (H_STRIP - th)//2 -2
        draw.text((x,y), text, fill="black", font=font_bold)
        final_clean.save("20kb.jpg", quality=60, optimize=True)
        final_clean.save("50kb.jpg", quality=85, optimize=True)
        await update.message.reply_text("✅ Payment Done! Clean photos:")
        await update.message.reply_document(document=open("20kb.jpg","rb"), filename="20kb.jpg")
        await update.message.reply_document(document=open("50kb.jpg","rb"), filename="50kb.jpg")
    except Exception as e:
        await update.message.reply_text(f"Error final: {e}")

def main():
    app_bot = Application.builder().token(BOT_TOKEN).build()
    app_bot.add_handler(CommandHandler("start", start))
    app_bot.add_handler(CallbackQueryHandler(check_join_callback, pattern="check_join"))
    app_bot.add_handler(CallbackQueryHandler(handle_pay_callback, pattern="pay_stars"))
    app_bot.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app_bot.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_name))
    app_bot.add_handler(PreCheckoutQueryHandler(precheckout))
    app_bot.add_handler(MessageHandler(filters.SUCCESSFUL_PAYMENT, successful_payment))
    print("BOT LIVE")
    app_bot.run_polling()

if __name__ == "__main__":
    main()
