import os

# Bot Configuration
BOT_TOKEN = os.getenv("BOT_TOKEN", "8150903745:AAFJDCGq7cB2LuBy0uON9iErqnhV_fpuG9k")
ADMIN_ID = int(os.getenv("ADMIN_ID", "7434574509"))

# File paths
DATA_DIR = "."
USERS_FILE = os.path.join(DATA_DIR, "users.json")
PRODUCTS_FILE = os.path.join(DATA_DIR, "products.json")
SALES_FILE = os.path.join(DATA_DIR, "sales.json")
RECHARGE_REQUESTS_FILE = os.path.join(DATA_DIR, "recharge_requests.json")

# Bot Settings
CURRENCY = "IQD"
STORE_NAME = "متجر ياسين للخدمات الرقمية"
OWNER_USERNAME = "@yn_hh"
CHANNEL_LINK = "@HN_BALL"

# Bank Information for Recharge
BANK_INFO = {
    "bank_name": "بنك الاهلي العراقي",
    "account_number": "12345678901234",
    "account_holder": "ياسين حسن محمد",
    "iban": "IQ98AHLI123456789012345",
    "swift_code": "AHLIQABA"
}

# Recharge amounts
RECHARGE_AMOUNTS = [5000, 10000, 25000, 50000, 100000]

# Discount coupons
COUPONS = {
    "WELCOME10": {"discount": 10, "type": "percentage", "max_uses": 100, "used": 0},
    "SAVE500": {"discount": 500, "type": "fixed", "max_uses": 50, "used": 0},
    "VIP20": {"discount": 20, "type": "percentage", "max_uses": 20, "used": 0}
}

# Messages
WELCOME_MESSAGE = """🌟 أهلاً وسهلاً بك، {name} 🌟

🆔 معرف المستخدم: {user_id}
💎 رصيدك الحالي: {balance:,.0f} {currency}

🏆 مرحباً بك في {store_name} - متجرك المفضل للخدمات الرقمية

✨ اختر ما تحتاجه من القائمة أدناه:"""

ADMIN_WELCOME = """🔧 لوحة تحكم الأدمن

مرحباً بك في لوحة التحكم
اختر العملية المطلوبة:"""

STORE_MESSAGE = """🛒 متجر الخدمات الرقمية المميز

🚀 نقدم لك خدمات رقمية عالية الجودة مع التسليم الفوري
⚡ أسعار منافسة وضمان جودة 100%

🎯 اختر من منتجاتنا المميزة:"""

# Recharge Instructions
RECHARGE_INSTRUCTIONS = """💳 تعليمات إعادة الشحن

🏦 معلومات التحويل البنكي:
• اسم البنك: {bank_name}
• رقم الحساب: {account_number}
• اسم صاحب الحساب: {account_holder}
• IBAN: {iban}
• SWIFT Code: {swift_code}

📋 خطوات التحويل:
1️⃣ قم بتحويل المبلغ المطلوب إلى الحساب أعلاه
2️⃣ احتفظ بإيصال التحويل وصورة من العملية
3️⃣ أرسل صورة واضحة من إيصال التحويل
4️⃣ اكتب تاريخ ووقت العملية بالتفصيل

⚠️ تنبيه مهم:
• تأكد من صحة المبلغ قبل التحويل
• احتفظ بإيصال التحويل حتى تتم الموافقة
• سيتم مراجعة طلبك في أقرب وقت ممكن
• لا تحذف رسائل التحويل حتى تتم الموافقة

📞 للمساعدة: {owner_username}"""

# Invoice Settings
INVOICE_HEADER = "Thank you for purchasing from Yassin Store"
INVOICE_FOOTER = "By: Yasiin"
INVOICE_FILENAME = "Yasiin store"
INVOICE_CONTACT_INFO = f"""
Store Information:
Owner: {OWNER_USERNAME}
Channel: {CHANNEL_LINK}

Thank you for your purchase!
For support, contact us through the above channels.
"""

# Rate Limiting Settings
RATE_LIMIT_SECONDS = 1.5
MAX_REQUESTS_PER_MINUTE = 15

# Security Settings
MAX_INPUT_LENGTH = 1000
DANGEROUS_PATTERNS = [
    '<script', 'javascript:', 'DROP TABLE', 'DELETE FROM', 
    'UPDATE SET', 'INSERT INTO', 'SELECT *', '--', ';--'
]
