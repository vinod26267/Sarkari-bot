import os
from flask import Flask
import threading
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, LabeledPrice
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, PreCheckoutQueryHandler, filters, ContextTypes
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime
import io

# Render ke liye Flask
app = Flask('')
@app.route('/')
def home(): return "BOT IS LIVE - @chatbotley"
def run(): app.run(host='0.0.0.0', port=8080)
threading.Thread(target=run).start()

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_USERNAME = os.getenv("CHANNEL_USERNAME", "@chatbotley")
REQUIRED_CHANNEL = CHANNEL_USERNAME

# Font load
def get_font(size, bold=False):
    try:
        if bold:
            return ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", size)
        return ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", size)
    except:
        return ImageFont.load_default()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    # Channel check
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
            f"👋 Hello {user.first_name}!\n\nSarkari Photo banane ke liye pehle hamara channel join karo:\n{REQUIRED_CHANNEL}\n\nJoin karke Check Again dabao.",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return

    # Sample - Bina watermark ke clean (jo tumne approve kiya)
    try:
        # Agar sample.jpg hai to bhejo
        if os.path.exists("sample.jpg"):
            await update.message.reply_photo(
                photo=open("sample.jpg", "rb"),
                caption="📸 *SAMPLE - Aisa photo banega*\n\n✅ White Background\n✅ Neeche Name + Date (Professional Font)\n✅ 20kb & 50kb Govt Format\n\nApni photo bhejo banane ke liye 👇",
                parse_mode="Markdown"
            )
        else:
            await update.message.reply_text("📸 Apni passport photo bhejo - White background me bana dunga!")
    except:
        await update.message.reply_text("📸 Apni photo bhejo!")

async def check_join_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user = query.from_user
    try:
        member = await context.bot.get_chat_member(REQUIRED_CHANNEL, user.id)
        if member.status not in ['left', 'kicked']:
            await query.message.reply_text("✅ Joined! Ab apni photo bhejo 👇")
        else:
            await query.message.reply_text(f"❌ Abhi join nahi kiya. Join karo: {REQUIRED_CHANNEL}")
    except:
        await query.message.reply_text(f"❌ Join karo: {REQUIRED_CHANNEL}")

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    # Save user photo id
    photo_file = await update.message.photo[-1].get_file()
    file_bytes = await photo_file.download_as_bytearray()
    context.user_data['photo_bytes'] = file_bytes
    await update.message.reply_text("✍️ Apna pura naam bhejo (Jaise: Rohit Sharma)")

async def handle_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if 'photo_bytes' not in context.user_data:
        return
    name = update.message.text.strip()
    context.user_data['name'] = name
    date_str = datetime.now().strftime("%d-%m-%Y")
    context.user_data['date_str'] = date_str

    # DEMO banao - REAL PHOTO + WATERMARK (Payment se pehle)
    try:
        img = Image.open(io.BytesIO(context.user_data['photo_bytes'])).convert("RGB")
        W, H_PHOTO, H_STRIP = 400, 430, 70
        img_resized = img.resize((W, H_PHOTO), Image.LANCZOS)
        final = Image.new("RGB", (W, H_PHOTO + H_STRIP), "white")
        final.paste(img_resized, (0,0))
        draw = ImageDraw.Draw(final)
        font_bold = get_font(16, bold=True)
        font_wm = get_font(22, bold=True)

        # White strip me Name + Date - Professional
        text = f"{name} {date_str}"
        bbox = draw.textbbox((0,0), text, font=font_bold)
        tw = bbox[2]-bbox[0]
        th = bbox[3]-bbox[1]
        x = (W - tw)//2
        y = H_PHOTO + (H_STRIP - th)//2 - 2
        draw.text((x,y), text, fill="black", font=font_bold)

        # WATERMARK - DEMO ke liye (Payment tak)
        draw.text((W//2 - 90, H_PHOTO//2 - 15), "DEMO @chatbotley", fill=(255,0,0,120), font=font_wm)

        final.save("demo.jpg", quality=90)
        context.user_data['final_pil'] = final.copy()

        keyboard = [[InlineKeyboardButton("💳 Pay 99 Stars - Watermark Hatane Ke Liye", callback_data="pay_stars")]]
        await update.message.reply_photo(
            photo=open("demo.jpg","rb"),
            caption=f"✅ DEMO Ready!\n\n{name} {date_str}\n\n⚠️ Watermark hataane ke liye 99 Stars Pay karo - fir 20kb & 50kb clean milega (Govt Approved)",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    except Exception as e:
        await update.message.reply_text(f"Error: {e}")

async def handle_pay_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    # Telegram Stars Invoice
    prices = [LabeledPrice("Sarkari Photo - No Watermark", 99)]
    await context.bot.send_invoice(
        chat_id=query.message.chat_id,
        title="Sarkari Photo Clean",
        description="Watermark hat jayega, 20kb + 50kb govt format milega",
        payload="sarkari_photo_99",
        provider_token="",
        currency="XTR",
        prices=prices
    )

async def precheckout(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.pre_checkout_query.answer(ok=True)

async def successful_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # FINAL - Bina Watermark ke Clean (Payment ke baad)
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

        # 20kb
        final_clean.save("20kb.jpg", quality=60, optimize=True)
        # 50kb
        final_clean.save("50kb.jpg", quality=85, optimize=True)

        await update.message.reply_text("✅ Payment Received! Clean photos bhej raha hu...")
        await update.message.reply_document(document=open("20kb.jpg","rb"), filename="20kb.jpg", caption="20kb - Govt Format")
        await update.message.reply_document(document=open("50kb.jpg","rb"), filename="50kb.jpg", caption="50kb - Govt Format")
    except Exception as e:
        await update.message.reply_text(f"Error in final: {e}")

def main():
    app_bot = Application.builder().token(BOT_TOKEN).build()
    app_bot.add_handler(CommandHandler("start", start))
    app_bot.add_handler(CallbackQueryHandler(check_join_callback, pattern="check_join"))
    app_bot.add_handler(CallbackQueryHandler(handle_pay_callback, pattern="pay_stars"))
    app_bot.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app_bot.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_name))
    app_bot.add_handler(PreCheckoutQueryHandler(precheckout))
    app_bot.add_handler(MessageHandler(filters.SUCCESSFUL_PAYMENT, successful_payment))
    print("BOT IS LIVE NOW - @chatbotley")
    app_bot.run_polling()

if __name__ == "__main__":
    main()
