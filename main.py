import telebot
import os
import time
from datetime import datetime, timedelta
from database import DatabaseManager
from pdf_generator_new import PDFInvoiceGenerator
from admin_panel import AdminPanel
from config import *
from utils import *

# Security and rate limiting
user_last_action = {}
RATE_LIMIT_SECONDS = 2
MAX_REQUESTS_PER_MINUTE = 20
user_request_count = {}

# Initialize bot
bot = telebot.TeleBot(BOT_TOKEN)

# Initialize components
db = DatabaseManager()
pdf_generator = PDFInvoiceGenerator()
admin_panel = AdminPanel(bot, db)

# User states for multi-step operations
user_states = {}

def check_rate_limit(user_id: str) -> bool:
    """Check if user is rate limited"""
    current_time = time.time()
    
    # Check last action time
    if user_id in user_last_action:
        if current_time - user_last_action[user_id] < RATE_LIMIT_SECONDS:
            return False
    
    # Check requests per minute
    minute_ago = current_time - 60
    if user_id not in user_request_count:
        user_request_count[user_id] = []
    
    # Remove old requests
    user_request_count[user_id] = [req_time for req_time in user_request_count[user_id] if req_time > minute_ago]
    
    # Check if exceeded limit
    if len(user_request_count[user_id]) >= MAX_REQUESTS_PER_MINUTE:
        return False
    
    # Update tracking
    user_last_action[user_id] = current_time
    user_request_count[user_id].append(current_time)
    return True

def validate_user_input(text: str) -> bool:
    """Validate user input for security"""
    if not text or len(text) > 4000:
        return False
    
    # Check for suspicious patterns
    suspicious_patterns = ['<script>', 'javascript:', 'eval(', 'exec(', 'DROP TABLE', 'SELECT *']
    text_lower = text.lower()
    
    for pattern in suspicious_patterns:
        if pattern.lower() in text_lower:
            return False
    
    return True

@bot.message_handler(commands=['start'])
def send_welcome(message):
    """Handle /start command"""
    user_id = str(message.from_user.id)
    name = message.from_user.first_name or "المستخدم"
    
    # Rate limiting check
    if not check_rate_limit(user_id):
        bot.reply_to(message, "⏳ يرجى الانتظار قليلاً قبل إرسال طلب آخر")
        return
    
    # Validate input
    if not validate_user_input(name):
        name = "المستخدم"
    
    # Check if user is banned
    if db.is_user_banned(user_id):
        bot.reply_to(message, "❌ تم حظر حسابك من استخدام البوت")
        return
    
    # Create user if doesn't exist and approve immediately
    user = db.get_user(user_id)
    if not user:
        full_name = f"{message.from_user.first_name or ''} {message.from_user.last_name or ''}".strip()
        if db.create_user(user_id, full_name):
            # Approve all users immediately
            db.approve_user(user_id)
            user = db.get_user(user_id)
    
    balance = user.get("balance", 0) if user else 0
    
    welcome_text = WELCOME_MESSAGE.format(
        name=sanitize_text(name),
        user_id=user_id,
        balance=balance,
        currency=CURRENCY,
        store_name=STORE_NAME
    )
    
    markup = telebot.types.InlineKeyboardMarkup()
    markup.row(telebot.types.InlineKeyboardButton("🛍️ عرض المنتجات", callback_data="store"))
    markup.row(
        telebot.types.InlineKeyboardButton("💳 إعادة الشحن", callback_data="recharge"),
        telebot.types.InlineKeyboardButton("📝 تاريخ المشتريات", callback_data="history")
    )
    markup.row(telebot.types.InlineKeyboardButton("📞 التواصل", url=f"https://t.me/{OWNER_USERNAME.replace('@', '')}"))
    
    # Send welcome message with startup image
    startup_image = "https://i.imgur.com/ZLo9XQ1.jpg"
    try:
        bot.send_photo(message.chat.id, startup_image, caption=welcome_text, reply_markup=markup)
    except:
        bot.send_message(message.chat.id, welcome_text, reply_markup=markup)

@bot.message_handler(commands=['admin'])
def admin_command(message):
    """Handle /admin command"""
    if admin_panel.is_admin_user(message.from_user.id):
        admin_panel.show_admin_menu(message.chat.id)
    else:
        bot.reply_to(message, "⛔ غير مسموح لك بالوصول لهذه الصفحة")

@bot.message_handler(commands=['help'])
def help_command(message):
    """Handle /help command"""
    help_text = f"""📋 مساعدة {STORE_NAME}

🔸 الأوامر المتاحة:
/start - بدء التفاعل مع البوت
/help - عرض هذه المساعدة

🔸 كيفية الاستخدام:
1️⃣ اضغط على "عرض المنتجات" لرؤية الخدمات المتاحة
2️⃣ اختر المنتج المطلوب وتأكد من رصيدك
3️⃣ اضغط على "تأكيد الشراء" للحصول على الكود
4️⃣ ستحصل على فاتورة PDF مع تفاصيل الشراء

🔸 إعادة الشحن:
اضغط على "إعادة الشحن" واتبع التعليمات

🔸 للدعم:
{OWNER_USERNAME}"""
    
    bot.send_message(message.chat.id, help_text)

@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    """Handle photo uploads for recharge requests"""
    user_id = str(message.from_user.id)
    
    # Check if user is in recharge state
    if user_id in user_states and user_states[user_id].get('state') == 'waiting_receipt':
        try:
            # Get the photo
            photo = message.photo[-1]  # Get the highest resolution photo
            file_info = bot.get_file(photo.file_id)
            
            # Store the receipt photo file_id
            user_states[user_id]['receipt_photo'] = photo.file_id
            
            # Ask for transfer date
            bot.send_message(
                message.chat.id,
                "✅ تم استلام صورة الإيصال\n\n📅 الآن أرسل تاريخ ووقت التحويل بالتفصيل\n\nمثال: 2025-07-01 الساعة 14:30"
            )
            user_states[user_id]['state'] = 'waiting_date'
            
        except Exception as e:
            bot.send_message(message.chat.id, "❌ حدث خطأ في معالجة الصورة، يرجى المحاولة مرة أخرى")
            print(f"Photo handling error: {e}")
    else:
        bot.send_message(message.chat.id, "❓ لم أفهم الغرض من هذه الصورة")

@bot.message_handler(func=lambda message: True)
def handle_text_messages(message):
    """Handle text messages"""
    user_id = str(message.from_user.id)
    
    # Handle recharge flow
    if user_id in user_states:
        state_data = user_states.get(user_id, {})
        state = state_data.get('state')
        
        if state == 'waiting_date':
            # Process transfer date
            transfer_date = message.text.strip()
            
            if len(transfer_date) < 5:
                bot.send_message(message.chat.id, "❌ يرجى إدخال تاريخ ووقت مفصل للتحويل")
                return
            
            # Create recharge request
            amount = state_data.get('amount')
            receipt_photo = state_data.get('receipt_photo')
            
            request_id = db.create_recharge_request(
                user_id=user_id,
                amount=amount,
                transfer_date=transfer_date,
                receipt_photo=receipt_photo
            )
            
            # Clear user state
            del user_states[user_id]
            
            # Notify user
            bot.send_message(
                message.chat.id,
                f"✅ تم إرسال طلب إعادة الشحن بنجاح!\n\n📄 رقم الطلب: {request_id}\n💰 المبلغ: {format_currency(amount)}\n\n⏳ سيتم مراجعة طلبك وإشعارك بالنتيجة قريباً"
            )
            
            # Notify admin
            user_info = db.get_user(user_id)
            admin_panel.send_admin_notification(
                f"🔔 طلب إعادة شحن جديد\n\n👤 المستخدم: {user_info.get('name', 'غير معروف')}\n🆔 ID: {user_id}\n💰 المبلغ: {format_currency(amount)}\n📅 تاريخ التحويل: {transfer_date}\n📄 رقم الطلب: {request_id}"
            )
            
            return
    
    # Default response for unrecognized text
    bot.send_message(message.chat.id, "❓ لم أفهم رسالتك، يرجى استخدام الأزرار المتاحة")

@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    """Handle all callback queries"""
    try:
        # Answer callback immediately to prevent loading
        bot.answer_callback_query(call.id)
        
        user_id = str(call.from_user.id)
        data = call.data
        
        # Rate limiting check
        if not check_rate_limit(user_id):
            return
        
        # Create user if doesn't exist and approve immediately
        user = db.get_user(user_id)
        if not user:
            full_name = f"{call.from_user.first_name or ''} {call.from_user.last_name or ''}".strip()
            db.create_user(user_id, full_name)
            db.approve_user(user_id)
            user = db.get_user(user_id)
        
        # Check if user is banned
        if not data.startswith("admin_") and db.is_user_banned(user_id):
            bot.send_message(call.message.chat.id, "❌ تم حظر حسابك")
            return
        
        if data == "store":
            show_products(call)
        elif data.startswith("product_"):
            show_product_details(call)
        elif data.startswith("buy_"):
            process_purchase(call)
        elif data == "recharge":
            show_recharge_options(call)
        elif data.startswith("recharge_"):
            process_recharge_request(call)
        elif data == "history":
            show_purchase_history(call)
        elif data == "check_balance":
            show_user_balance(call)
        elif data == "back":
            back_to_main(call)
        elif data.startswith("admin_") or data.startswith("approve_") or data.startswith("reject_") or data.startswith("delete_product_") or data.startswith("approve_recharge_") or data.startswith("reject_recharge_") or data.startswith("approve_user_") or data.startswith("reject_user_"):
            admin_panel.handle_admin_callback(call)
        elif data == "out_of_stock":
            bot.send_message(call.message.chat.id, "❌ هذا المنتج غير متوفر حالياً")
        else:
            bot.send_message(call.message.chat.id, "❓ أمر غير معروف")
            
    except Exception as e:
        print(f"Error handling callback {data}: {e}")
        try:
            bot.send_message(call.message.chat.id, "❌ حدث خطأ، يرجى المحاولة مرة أخرى")
        except:
            pass

def show_products(call):
    """Show available products"""
    products = db.get_available_products()
    
    if not products:
        text = "❌ لا توجد منتجات متاحة حالياً\nيرجى المحاولة لاحقاً"
        markup = telebot.types.InlineKeyboardMarkup()
        markup.row(telebot.types.InlineKeyboardButton("🔙 العودة", callback_data="back"))
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup)
        return
    
    text = STORE_MESSAGE
    
    markup = telebot.types.InlineKeyboardMarkup()
    for product_id, product in products.items():
        stock = len(product.get('codes', []))
        if stock > 0:
            button_text = f"{product['name']} - {format_currency(product['price'])}"
            markup.row(telebot.types.InlineKeyboardButton(button_text, callback_data=f"product_{product_id}"))
        else:
            button_text = f"❌ {product['name']} - نفذ المخزون"
            markup.row(telebot.types.InlineKeyboardButton(button_text, callback_data="out_of_stock"))
    
    markup.row(telebot.types.InlineKeyboardButton("🔙 العودة", callback_data="back"))
    
    try:
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup)
    except:
        bot.send_message(call.message.chat.id, text, reply_markup=markup)

def show_product_details(call):
    """Show detailed product information"""
    product_id = call.data.replace("product_", "")
    product = db.get_product(product_id)
    user = db.get_user(str(call.from_user.id))
    
    if not product:
        bot.answer_callback_query(call.id, "❌ المنتج غير موجود")
        return
    
    if not user:
        bot.answer_callback_query(call.id, "❌ خطأ في بيانات المستخدم")
        return
    
    user_balance = user.get("balance", 0)
    stock = len(product.get('codes', []))
    
    text = f"""📦 تفاصيل المنتج

🏷️ الاسم: {product['name']}
💰 السعر: {format_currency(product['price'])}
📦 المتاح: {stock} قطعة
📄 الوصف: {sanitize_text(product.get('description', 'منتج رقمي عالي الجودة'))}

👤 رصيدك الحالي: {format_currency(user_balance)}"""
    
    markup = telebot.types.InlineKeyboardMarkup()
    
    if stock > 0 and user_balance >= product['price']:
        text += "\n✅ يمكنك شراء هذا المنتج"
        markup.row(telebot.types.InlineKeyboardButton("✅ تأكيد الشراء", callback_data=f"buy_{product_id}"))
    elif stock > 0:
        needed = product['price'] - user_balance
        text += f"\n❌ رصيدك غير كافي\nتحتاج إلى: {format_currency(needed)} إضافية"
        markup.row(telebot.types.InlineKeyboardButton("💳 إعادة شحن", callback_data="recharge"))
    else:
        text += "\n❌ نفذ المخزون"
    
    markup.row(telebot.types.InlineKeyboardButton("🔙 العودة للمتجر", callback_data="store"))
    
    # Send with product image if available
    product_image = product.get('image')
    if product_image:
        try:
            bot.send_photo(call.message.chat.id, product_image, caption=text, reply_markup=markup)
        except:
            bot.send_message(call.message.chat.id, text, reply_markup=markup)
    else:
        bot.send_message(call.message.chat.id, text, reply_markup=markup)

def process_purchase(call):
    """Process product purchase"""
    product_id = call.data.replace("buy_", "")
    user_id = str(call.from_user.id)
    
    # Process purchase through database
    result = db.process_purchase(user_id, product_id)
    
    if result["success"]:
        # Purchase successful
        purchase_data = result["data"]
        user_data = db.get_user(user_id)
        if user_data:
            user_data["user_id"] = user_id  # Add user_id for PDF
        else:
            user_data = {"user_id": user_id, "name": "مستخدم"}
        
        # Format code with monospace for easy copying - Fixed version
        success_text = f"""🎉 تهانينا! تم الشراء بنجاح! 🎉

━━━━━━━━━━━━━━━━━━━━━━━
📦 المنتج: {purchase_data['product_name']}
💰 المبلغ المدفوع: {format_currency(purchase_data['price'])}

🔐 كود المنتج (اضغط للنسخ):
`{purchase_data['code']}`

💎 رصيدك الجديد: {format_currency(purchase_data['new_balance'])}
📄 رقم الفاتورة: {purchase_data['invoice_id']}
━━━━━━━━━━━━━━━━━━━━━━━

💡 اضغط على الكود أعلاه مرة واحدة لنسخه تلقائياً

📧 ستصلك فاتورة PDF تحتوي على جميع التفاصيل"""
        
        markup = telebot.types.InlineKeyboardMarkup()
        markup.row(telebot.types.InlineKeyboardButton("🛍️ شراء منتج آخر", callback_data="store"))
        markup.row(telebot.types.InlineKeyboardButton("📝 تاريخ المشتريات", callback_data="history"))
        markup.row(telebot.types.InlineKeyboardButton("🔙 العودة للقائمة الرئيسية", callback_data="back"))
        
        bot.send_message(call.message.chat.id, success_text, reply_markup=markup, parse_mode='Markdown')
        
        # Generate and send PDF invoice
        try:
            sale_data = {
                'invoice_id': purchase_data['invoice_id'],
                'product_name': purchase_data['product_name'],
                'price': purchase_data['price'],
                'code': purchase_data['code'],
                'timestamp': get_current_timestamp()
            }
            
            pdf_buffer = pdf_generator.create_invoice(sale_data, user_data)
            bot.send_document(
                call.message.chat.id,
                pdf_buffer,
                visible_file_name="Yasiin store.pdf"
            )
        except Exception as e:
            print(f"PDF generation error: {e}")
            bot.send_message(call.message.chat.id, "❌ حدث خطأ في إنشاء الفاتورة")
    else:
        # Purchase failed
        bot.send_message(call.message.chat.id, f"❌ فشل الشراء: {result['message']}")

def show_recharge_options(call):
    """Show recharge options with bank information"""
    text = RECHARGE_INSTRUCTIONS.format(
        bank_name=BANK_INFO['bank_name'],
        account_number=BANK_INFO['account_number'],
        account_holder=BANK_INFO['account_holder'],
        iban=BANK_INFO['iban'],
        swift_code=BANK_INFO['swift_code'],
        owner_username=OWNER_USERNAME
    )
    
    markup = telebot.types.InlineKeyboardMarkup()
    
    # Add recharge amount buttons
    for amount in RECHARGE_AMOUNTS:
        markup.row(telebot.types.InlineKeyboardButton(
            f"💳 {format_currency(amount)}", 
            callback_data=f"recharge_{amount}"
        ))
    
    markup.row(telebot.types.InlineKeyboardButton("🔙 العودة", callback_data="back"))
    
    try:
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup)
    except:
        bot.send_message(call.message.chat.id, text, reply_markup=markup)

def process_recharge_request(call):
    """Process recharge request"""
    amount = int(call.data.replace("recharge_", ""))
    user_id = str(call.from_user.id)
    
    # Set user state for recharge flow
    user_states[user_id] = {
        'state': 'waiting_receipt',
        'amount': amount
    }
    
    text = f"""💳 طلب إعادة شحن بمبلغ {format_currency(amount)}

📸 الآن أرسل صورة واضحة من إيصال التحويل البنكي

⚠️ تأكد من:
• وضوح الصورة وجميع التفاصيل
• ظهور المبلغ المحول بوضوح
• ظهور تاريخ ووقت التحويل
• رقم الحساب المرسل إليه

📤 أرسل الصورة الآن..."""
    
    bot.send_message(call.message.chat.id, text)

def show_purchase_history(call):
    """Show user purchase history"""
    user_id = str(call.from_user.id)
    purchases = db.get_user_purchases(user_id)
    
    if not purchases:
        text = "📝 لا توجد مشتريات سابقة"
        markup = telebot.types.InlineKeyboardMarkup()
        markup.row(telebot.types.InlineKeyboardButton("🔙 العودة", callback_data="back"))
        bot.send_message(call.message.chat.id, text, reply_markup=markup)
        return
    
    text = "📝 تاريخ المشتريات:\n\n"
    
    for i, purchase in enumerate(purchases[-10:], 1):  # Show last 10 purchases
        date = purchase.get('date', 'غير محدد')
        try:
            # Format date
            date_obj = datetime.fromisoformat(date)
            formatted_date = date_obj.strftime('%Y-%m-%d %H:%M')
        except:
            formatted_date = date
        
        text += f"{i}️⃣ {purchase.get('product', 'منتج غير محدد')}\n"
        text += f"💰 {format_currency(purchase.get('price', 0))}\n"
        text += f"📄 {purchase.get('invoice_id', 'غير محدد')}\n"
        text += f"📅 {formatted_date}\n"
        text += f"🔐 `{purchase.get('code', 'غير محدد')}`\n\n"
    
    markup = telebot.types.InlineKeyboardMarkup()
    markup.row(telebot.types.InlineKeyboardButton("🔙 العودة", callback_data="back"))
    
    bot.send_message(call.message.chat.id, text, reply_markup=markup, parse_mode='Markdown')

def show_user_balance(call):
    """Show user balance"""
    user_id = str(call.from_user.id)
    user = db.get_user(user_id)
    
    if not user:
        bot.answer_callback_query(call.id, "❌ خطأ في بيانات المستخدم")
        return
    
    balance = user.get("balance", 0)
    total_spent = user.get("total_spent", 0)
    purchase_count = user.get("purchase_count", 0)
    
    text = f"""💎 معلومات الرصيد

👤 الاسم: {user.get('name', 'غير محدد')}
🆔 معرف المستخدم: {user_id}
💰 الرصيد الحالي: {format_currency(balance)}
💸 إجمالي المصروف: {format_currency(total_spent)}
🛒 عدد المشتريات: {purchase_count}"""
    
    markup = telebot.types.InlineKeyboardMarkup()
    markup.row(telebot.types.InlineKeyboardButton("💳 إعادة شحن", callback_data="recharge"))
    markup.row(telebot.types.InlineKeyboardButton("🔙 العودة", callback_data="back"))
    
    try:
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup)
    except:
        bot.send_message(call.message.chat.id, text, reply_markup=markup)

def back_to_main(call):
    """Return to main menu"""
    user_id = str(call.from_user.id)
    user = db.get_user(user_id)
    
    if not user:
        bot.answer_callback_query(call.id, "❌ خطأ في بيانات المستخدم")
        return
    
    balance = user.get("balance", 0)
    name = user.get("name", "المستخدم")
    
    welcome_text = WELCOME_MESSAGE.format(
        name=sanitize_text(name),
        user_id=user_id,
        balance=balance,
        currency=CURRENCY,
        store_name=STORE_NAME
    )
    
    markup = telebot.types.InlineKeyboardMarkup()
    markup.row(telebot.types.InlineKeyboardButton("🛍️ عرض المنتجات", callback_data="store"))
    markup.row(
        telebot.types.InlineKeyboardButton("💳 إعادة الشحن", callback_data="recharge"),
        telebot.types.InlineKeyboardButton("📝 تاريخ المشتريات", callback_data="history")
    )
    markup.row(telebot.types.InlineKeyboardButton("📞 التواصل", url=f"https://t.me/{OWNER_USERNAME.replace('@', '')}"))
    
    try:
        bot.edit_message_text(welcome_text, call.message.chat.id, call.message.message_id, reply_markup=markup)
    except:
        bot.send_message(call.message.chat.id, welcome_text, reply_markup=markup)

def main():
    """Main function to run the bot"""
    print(f"🤖 بدء تشغيل {STORE_NAME}")
    print(f"👤 الأدمن: {ADMIN_ID}")
    print("🔄 البوت يعمل الآن...")
    
    try:
        bot.infinity_polling(timeout=20, long_polling_timeout=20)
    except Exception as e:
        print(f"خطأ في تشغيل البوت: {e}")
        time.sleep(5)
        main()  # Restart on error

if __name__ == "__main__":
    main()