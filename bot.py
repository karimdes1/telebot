import os
from dotenv import load_dotenv
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from rembg import remove


# Load environment variables from .env file
load_dotenv()

# Get the token from the .env file
TOKEN = os.getenv('BOT_TOKEN')

# Safety check: stop if the token is missing
if not TOKEN:
    raise ValueError("BOT_TOKEN not found in .env file!")

# Create a new TeleBot instance
bot = telebot.TeleBot(TOKEN)

# Track which users are waiting to send a photo for background removal
user_states = {}

def main_menu_markup():
    """Build the inline keyboard with three buttons."""
    markup = InlineKeyboardMarkup(row_width=1)
    markup.add(
        InlineKeyboardButton("إزالة الخلفية", callback_data="remove_bg"),
        InlineKeyboardButton("الخطوط", callback_data="fonts"),
        InlineKeyboardButton("خدمة العملاء", callback_data="customer_service")
    )
    return markup

# Handle /start command
@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.send_message(
        message.chat.id,
        "<b>🎨 أهلاً بك في بوت التصميم المساعد!</b>\n\n"
        "<i>أنا هنا لمساعدتك في كل ما يخص التصميم:\n"
        "🖋️  شراء خطوط\n"
        "📁  ملحقات تصميم\n"
        "🖼️   ازالة خلفية للصور\n"
        "وأكثر..</i>\n\n"
        "<b>كيف أقدر أساعدك اليوم؟</b>",
        parse_mode='HTML',
        reply_markup=main_menu_markup()
    )

# Handle button taps
@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    if call.data == "remove_bg":
        # Mark this user as waiting for a photo
        user_states[call.from_user.id] = "waiting_for_photo"
        bot.answer_callback_query(call.id, "إزالة الخلفية")
        bot.send_message(call.message.chat.id, "📤 أرسل الصورة من فضلك")
    
    elif call.data == "fonts":
        bot.answer_callback_query(call.id, "لقد اخترت: خطوط")
        bot.send_message(call.message.chat.id, "سأعرض لك بعض الخطوط المميزة قريباً!")
    
    elif call.data == "customer_service":
        bot.answer_callback_query(call.id, "لقد اخترت: خدمة العملاء")
        bot.send_message(
            call.message.chat.id,
            "هذا يوزر المصمم و المطور: @Karim_des1\n\n"
            "يرجى إرسال رسالة واحدة مختصرة وواضحة وسيتم الرد عليك في أقرب وقت ممكن. شكراً لتواصلك معنا."
        )

# Handle incoming photos
@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    user_id = message.from_user.id
    
    # Only process if the user clicked "remove background" first
    if user_states.get(user_id) == "waiting_for_photo":
        # Get the largest photo (last item in the list = highest resolution)
        file_id = message.photo[-1].file_id
        file_info = bot.get_file(file_id)
        
        # Download the file bytes
        downloaded_file = bot.download_file(file_info.file_path)
        
        # Save it as input.png
        with open("input.png", "wb") as f:
            f.write(downloaded_file)
        
        # Remove background
        with open("input.png", "rb") as f:
            input_data = f.read()
        output_data = remove(input_data)
        with open("output.png", "wb") as f:
            f.write(output_data)
        
        # Send the result as a document (uncompressed file)
        with open('output.png', 'rb') as photo_file:
            bot.send_document(
                message.chat.id, 
                photo_file, 
                caption="هذه الصورة بعد إزالة الخلفية. شكراً لاستخدامك البوت! 🎨"
            )
        
        # ============================================================
        # DELETE BOTH FILES AFTER SENDING
        # ============================================================
        try:
            if os.path.exists("input.png"):
                os.remove("input.png")
            if os.path.exists("output.png"):
                os.remove("output.png")
        except Exception as e:
            print(f"Error deleting files: {e}")
        # ============================================================
        
        # Remove the user from the waiting state
        del user_states[user_id]
        
    else:
        # If they send a photo without clicking the button first
        bot.send_message(
            message.chat.id,
            "📤 أرسل الصورة من فضلك",
            reply_markup=main_menu_markup()
        )

# Fallback for all other text messages
@bot.message_handler(func=lambda msg: True)
def echo_message(message):
    bot.reply_to(
        message,
        "<b>القائمة الرئيسية</b>\n\n"
        "<i>أنا هنا لمساعدتك في كل ما يخص التصميم:\n"
        "🖋️  شراء خطوط\n"
        "📁  ملحقات تصميم\n"
        "🖼️   ازالة خلفية للصور\n"
        "وأكثر..</i>\n\n"
        "<b>كيف أقدر أساعدك اليوم؟</b>",
        parse_mode='HTML',
        reply_markup=main_menu_markup()
    )

# Start polling
if __name__ == '__main__':
    print("Starting bot...")
    bot.polling()