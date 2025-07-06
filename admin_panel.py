import telebot
from typing import Dict, List
from datetime import datetime
from database import DatabaseManager
from config import ADMIN_ID, STORE_NAME, CURRENCY
from utils import format_currency, sanitize_text, get_current_timestamp

class AdminPanel:
    def __init__(self, bot: telebot.TeleBot, db: DatabaseManager):
        self.bot = bot
        self.db = db
        self.admin_id = ADMIN_ID
    
    def is_admin_user(self, user_id: int) -> bool:
        """Check if user is admin"""
        return user_id == self.admin_id
    
    def send_admin_notification(self, message: str):
        """Send notification to admin"""
        try:
            self.bot.send_message(self.admin_id, message)
        except Exception as e:
            print(f"Failed to send admin notification: {e}")
    
    def show_admin_menu(self, chat_id: int):
        """Show main admin menu"""
        if not self.is_admin_user(chat_id):
            return
        
        text = f"""🔧 لوحة تحكم الأدمن - {STORE_NAME}

مرحباً بك في لوحة التحكم
اختر العملية المطلوبة:"""
        
        markup = telebot.types.InlineKeyboardMarkup()
        markup.row(
            telebot.types.InlineKeyboardButton("👥 إدارة المستخدمين", callback_data="admin_users"),
            telebot.types.InlineKeyboardButton("📦 إدارة المنتجات", callback_data="admin_products")
        )
        markup.row(
            telebot.types.InlineKeyboardButton("💰 طلبات الشحن", callback_data="admin_recharge"),
            telebot.types.InlineKeyboardButton("📊 تقارير المبيعات", callback_data="admin_sales")
        )
        markup.row(
            telebot.types.InlineKeyboardButton("📢 إرسال إذاعة", callback_data="admin_broadcast"),
            telebot.types.InlineKeyboardButton("⚙️ إعدادات", callback_data="admin_settings")
        )
        markup.row(
            telebot.types.InlineKeyboardButton("⚙️ شحن رصيد", callback_data="admin_balance"),
            telebot.types.InlineKeyboardButton("🚫 حظر مستخدم", callback_data="admin_ban")
        )
        
        try:
            self.bot.send_message(chat_id, text, reply_markup=markup)
        except Exception as e:
            print(f"Error showing admin menu: {e}")
    
    def handle_admin_callback(self, call):
        """Handle admin callback queries"""
        if not self.is_admin_user(call.from_user.id):
            self.bot.answer_callback_query(call.id, "❌ غير مصرح لك")
            return
        
        data = call.data
        
        try:
            if data == "admin_users":
                self.show_users_management(call)
            elif data == "admin_products":
                self.show_products_management(call)
            elif data == "admin_recharge":
                self.show_recharge_requests(call)
            elif data == "admin_sales":
                self.show_sales_stats(call)
            elif data == "admin_settings":
                self.show_settings(call)
            elif data == "admin_broadcast":
                self.show_broadcast_menu(call)
            elif data == "admin_balance":
                self.show_balance_management(call)
            elif data == "admin_ban":
                self.show_ban_management(call)
            elif data.startswith("approve_user_"):
                self.approve_new_user(call)
            elif data.startswith("reject_user_"):
                self.reject_new_user(call)
            elif data.startswith("approve_") and not data.startswith("approve_recharge_"):
                self.approve_user(call)
            elif data.startswith("reject_") and not data.startswith("reject_recharge_"):
                self.reject_user(call)
            elif data.startswith("delete_product_"):
                self.delete_product(call)
            elif data.startswith("approve_recharge_"):
                self.approve_recharge(call)
            elif data.startswith("reject_recharge_"):
                self.reject_recharge(call)
            elif data == "admin_menu":
                self.show_admin_menu(call.message.chat.id)
            else:
                self.bot.answer_callback_query(call.id, "❌ أمر غير معروف")
        except Exception as e:
            print(f"Error in admin callback: {e}")
            self.bot.answer_callback_query(call.id, "❌ حدث خطأ")
    
    def show_pending_users(self, call):
        """Show users pending approval"""
        pending_users = self.db.get_pending_users()
        
        if not pending_users:
            text = "✅ لا توجد طلبات موافقة معلقة"
            markup = telebot.types.InlineKeyboardMarkup()
            markup.row(telebot.types.InlineKeyboardButton("🔙 العودة", callback_data="admin_menu"))
            
            try:
                self.bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup)
            except:
                self.bot.send_message(call.message.chat.id, text, reply_markup=markup)
            return
        
        text = "🔔 المستخدمين المعلقين للموافقة:\n\n"
        
        markup = telebot.types.InlineKeyboardMarkup()
        
        for user in pending_users[:10]:  # Show first 10 pending users
            user_id = user.get('user_id')
            user_name = user.get('name', 'غير محدد')
            created_at = user.get('created_at', 'غير محدد')
            
            try:
                # Format date
                date_obj = datetime.fromisoformat(created_at)
                formatted_date = date_obj.strftime('%Y-%m-%d %H:%M')
            except:
                formatted_date = created_at
            
            text += f"👤 {user_name}\n🆔 {user_id}\n📅 {formatted_date}\n\n"
            
            markup.row(
                telebot.types.InlineKeyboardButton(f"✅ موافقة {user_name}", callback_data=f"approve_{user_id}"),
                telebot.types.InlineKeyboardButton(f"❌ رفض", callback_data=f"reject_{user_id}")
            )
        
        markup.row(telebot.types.InlineKeyboardButton("🔙 العودة", callback_data="admin_menu"))
        
        try:
            self.bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup)
        except:
            self.bot.send_message(call.message.chat.id, text, reply_markup=markup)
    
    def approve_user(self, call):
        """Approve pending user"""
        user_id = call.data.replace("approve_", "")
        
        if self.db.approve_user(user_id):
            user = self.db.get_user(user_id)
            user_name = user.get('name', 'المستخدم') if user else 'المستخدم'
            
            # Notify admin
            self.bot.answer_callback_query(call.id, f"✅ تم قبول {user_name}")
            
            # Notify user
            try:
                self.bot.send_message(
                    int(user_id),
                    f"🎉 مرحباً بك في {STORE_NAME}!\n\n✅ تم قبول طلبك ويمكنك الآن استخدام البوت\n\n/start للبدء"
                )
            except:
                pass
            
            # Refresh the pending users list
            self.show_pending_users(call)
        else:
            self.bot.answer_callback_query(call.id, "❌ فشل في الموافقة")
    
    def reject_user(self, call):
        """Reject pending user"""
        user_id = call.data.replace("reject_", "")
        
        user = self.db.get_user(user_id)
        if user:
            user_name = user.get('name', 'المستخدم')
            
            # Remove user from database
            users = self.db.get_all_users()
            if user_id in users:
                del users[user_id]
                from utils import save_json
                from config import USERS_FILE
                save_json(USERS_FILE, users)
            
            # Notify admin
            self.bot.answer_callback_query(call.id, f"❌ تم رفض {user_name}")
            
            # Notify user
            try:
                self.bot.send_message(
                    int(user_id),
                    "❌ نعتذر، لم يتم قبول طلبك للانضمام للمتجر"
                )
            except:
                pass
            
            # Refresh the pending users list
            self.show_pending_users(call)
        else:
            self.bot.answer_callback_query(call.id, "❌ المستخدم غير موجود")
    
    def show_products_management(self, call):
        """Show products management"""
        products = self.db.get_products()
        
        text = "📦 إدارة المنتجات\n\n"
        
        markup = telebot.types.InlineKeyboardMarkup()
        
        for product_id, product in products.items():
            stock = len(product.get('codes', []))
            status = "✅" if product.get('active', True) else "❌"
            
            text += f"{status} {product['name']}\n💰 {format_currency(product['price'])}\n📦 المخزون: {stock}\n\n"
            
            markup.row(
                telebot.types.InlineKeyboardButton(f"🗑️ حذف {product['name']}", callback_data=f"delete_product_{product_id}")
            )
        
        markup.row(telebot.types.InlineKeyboardButton("🔙 العودة", callback_data="admin_menu"))
        
        try:
            self.bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup)
        except:
            self.bot.send_message(call.message.chat.id, text, reply_markup=markup)
    
    def delete_product(self, call):
        """Delete product"""
        product_id = call.data.replace("delete_product_", "")
        
        product = self.db.get_product(product_id)
        if product:
            product_name = product.get('name', 'المنتج')
            
            if self.db.delete_product(product_id):
                self.bot.answer_callback_query(call.id, f"✅ تم حذف {product_name}")
                # Refresh products list
                self.show_products_management(call)
            else:
                self.bot.answer_callback_query(call.id, "❌ فشل في حذف المنتج")
        else:
            self.bot.answer_callback_query(call.id, "❌ المنتج غير موجود")
    
    def show_recharge_requests(self, call):
        """Show pending recharge requests"""
        pending_requests = self.db.get_pending_recharge_requests()
        
        if not pending_requests:
            text = "✅ لا توجد طلبات شحن معلقة"
            markup = telebot.types.InlineKeyboardMarkup()
            markup.row(telebot.types.InlineKeyboardButton("🔙 العودة", callback_data="admin_menu"))
            
            try:
                self.bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup)
            except:
                self.bot.send_message(call.message.chat.id, text, reply_markup=markup)
            return
        
        text = "💳 طلبات الشحن المعلقة:\n\n"
        
        markup = telebot.types.InlineKeyboardMarkup()
        
        for request in pending_requests[:5]:  # Show first 5 requests
            user_id = request.get('user_id')
            user_name = request.get('user_name', 'غير معروف')
            amount = request.get('amount', 0)
            request_id = request.get('request_id')
            transfer_date = request.get('transfer_date', 'غير محدد')
            
            text += f"👤 {user_name}\n🆔 {user_id}\n💰 {format_currency(amount)}\n📅 {transfer_date}\n📄 {request_id}\n\n"
            
            # Show receipt photo if available
            if request.get('receipt_photo'):
                try:
                    self.bot.send_photo(
                        call.message.chat.id,
                        request['receipt_photo'],
                        caption=f"🧾 إيصال {user_name}\n💰 {format_currency(amount)}"
                    )
                except:
                    pass
            
            markup.row(
                telebot.types.InlineKeyboardButton(f"✅ موافقة {format_currency(amount)}", callback_data=f"approve_recharge_{user_id}_{request_id}_{amount}"),
                telebot.types.InlineKeyboardButton(f"❌ رفض", callback_data=f"reject_recharge_{user_id}_{request_id}")
            )
        
        markup.row(telebot.types.InlineKeyboardButton("🔙 العودة", callback_data="admin_menu"))
        
        try:
            self.bot.send_message(call.message.chat.id, text, reply_markup=markup)
        except:
            pass
    
    def approve_recharge(self, call):
        """Approve recharge request"""
        try:
            parts = call.data.replace("approve_recharge_", "").split("_")
            user_id = parts[0]
            request_id = parts[1]
            amount = int(parts[2])
            
            # Update request status
            if self.db.update_recharge_request(user_id, request_id, "approved"):
                # Add balance to user
                if self.db.update_user_balance(user_id, amount):
                    user = self.db.get_user(user_id)
                    user_name = user.get('name', 'المستخدم') if user else 'المستخدم'
                    
                    # Notify admin
                    self.bot.answer_callback_query(call.id, f"✅ تم قبول طلب {user_name}")
                    
                    # Notify user
                    try:
                        balance = user.get('balance', 0) if user else 0
                        self.bot.send_message(
                            int(user_id),
                            f"✅ تم قبول طلب إعادة الشحن!\n\n💰 المبلغ: {format_currency(amount)}\n📄 رقم الطلب: {request_id}\n\n💎 رصيدك الجديد: {format_currency(balance)}"
                        )
                    except:
                        pass
                    
                    # Refresh requests list
                    self.show_recharge_requests(call)
                else:
                    self.bot.answer_callback_query(call.id, "❌ فشل في إضافة الرصيد")
            else:
                self.bot.answer_callback_query(call.id, "❌ فشل في تحديث الطلب")
        except Exception as e:
            print(f"Error approving recharge: {e}")
            self.bot.answer_callback_query(call.id, "❌ حدث خطأ")
    
    def reject_recharge(self, call):
        """Reject recharge request"""
        try:
            parts = call.data.replace("reject_recharge_", "").split("_")
            user_id = parts[0]
            request_id = parts[1]
            
            # Update request status
            if self.db.update_recharge_request(user_id, request_id, "rejected"):
                user = self.db.get_user(user_id)
                user_name = user.get('name', 'المستخدم') if user else 'المستخدم'
                
                # Notify admin
                self.bot.answer_callback_query(call.id, f"❌ تم رفض طلب {user_name}")
                
                # Notify user
                try:
                    self.bot.send_message(
                        int(user_id),
                        f"❌ تم رفض طلب إعادة الشحن\n\n📄 رقم الطلب: {request_id}\n\n💡 يرجى التأكد من صحة البيانات والمحاولة مرة أخرى"
                    )
                except:
                    pass
                
                # Refresh requests list
                self.show_recharge_requests(call)
            else:
                self.bot.answer_callback_query(call.id, "❌ فشل في تحديث الطلب")
        except Exception as e:
            print(f"Error rejecting recharge: {e}")
            self.bot.answer_callback_query(call.id, "❌ حدث خطأ")
    
    def show_sales_stats(self, call):
        """Show sales statistics"""
        stats = self.db.get_sales_stats()
        
        text = f"""📊 إحصائيات المبيعات

🛒 إجمالي المبيعات: {stats['total_sales']}
💰 إجمالي الإيرادات: {format_currency(stats['total_revenue'])}
👥 العملاء الفريدين: {stats['unique_customers']}
📅 تاريخ التقرير: {datetime.now().strftime('%Y-%m-%d %H:%M')}"""
        
        markup = telebot.types.InlineKeyboardMarkup()
        markup.row(telebot.types.InlineKeyboardButton("🔙 العودة", callback_data="admin_menu"))
        
        try:
            self.bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup)
        except:
            self.bot.send_message(call.message.chat.id, text, reply_markup=markup)
    
    def show_users_management(self, call):
        """Show users management"""
        users = self.db.get_all_users()
        
        text = f"👥 إجمالي المستخدمين: {len(users)}\n\n"
        
        # Show recent users
        recent_users = list(users.items())[-5:]  # Last 5 users
        
        for user_id, user_data in recent_users:
            name = user_data.get('name', 'غير محدد')
            balance = user_data.get('balance', 0)
            text += f"👤 {name}\n🆔 {user_id}\n💰 {format_currency(balance)}\n\n"
        
        markup = telebot.types.InlineKeyboardMarkup()
        markup.row(telebot.types.InlineKeyboardButton("🔙 العودة", callback_data="admin_menu"))
        
        try:
            self.bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup)
        except:
            self.bot.send_message(call.message.chat.id, text, reply_markup=markup)
    
    def show_broadcast_menu(self, call):
        """Show broadcast menu"""
        text = "📢 إرسال إذاعة\n\nهذه الميزة قيد التطوير"
        
        markup = telebot.types.InlineKeyboardMarkup()
        markup.row(telebot.types.InlineKeyboardButton("🔙 العودة", callback_data="admin_menu"))
        
        try:
            self.bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup)
        except:
            self.bot.send_message(call.message.chat.id, text, reply_markup=markup)
    
    def show_balance_management(self, call):
        """Show balance management"""
        text = "⚙️ شحن رصيد\n\nهذه الميزة قيد التطوير"
        
        markup = telebot.types.InlineKeyboardMarkup()
        markup.row(telebot.types.InlineKeyboardButton("🔙 العودة", callback_data="admin_menu"))
        
        try:
            self.bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup)
        except:
            self.bot.send_message(call.message.chat.id, text, reply_markup=markup)
    
    def show_ban_management(self, call):
        """Show ban management"""
        text = "🚫 حظر مستخدم\n\nهذه الميزة قيد التطوير"
        
        markup = telebot.types.InlineKeyboardMarkup()
        markup.row(telebot.types.InlineKeyboardButton("🔙 العودة", callback_data="admin_menu"))
        
        try:
            self.bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup)
        except:
            self.bot.send_message(call.message.chat.id, text, reply_markup=markup)
    
    def approve_new_user(self, call):
        """Approve new user from direct request"""
        try:
            user_id = call.data.replace("approve_user_", "")
            
            # Approve user
            if self.db.approve_user(user_id):
                # Notify user
                try:
                    self.bot.send_message(
                        int(user_id),
                        "🎉 مرحباً بك! تم قبول طلبك للانضمام إلى المتجر\n\n" + 
                        "يمكنك الآن تصفح المنتجات وإعادة الشحن\n" +
                        "اضغط /start للبدء"
                    )
                except:
                    pass
                
                # Update admin message
                user_info = self.db.get_user(user_id)
                user_name = user_info.get('name', 'غير معروف') if user_info else 'غير معروف'
                
                new_text = f"✅ تم قبول المستخدم\n\n👤 الاسم: {user_name}\n🆔 المعرف: {user_id}"
                
                try:
                    self.bot.edit_message_text(
                        new_text, 
                        call.message.chat.id, 
                        call.message.message_id
                    )
                except:
                    pass
                    
                self.bot.answer_callback_query(call.id, "✅ تم قبول المستخدم بنجاح")
            else:
                self.bot.answer_callback_query(call.id, "❌ فشل في قبول المستخدم")
                
        except Exception as e:
            print(f"Error approving new user: {e}")
            self.bot.answer_callback_query(call.id, "❌ حدث خطأ")
    
    def reject_new_user(self, call):
        """Reject new user from direct request"""
        try:
            user_id = call.data.replace("reject_user_", "")
            
            # Get user info before rejecting
            user_info = self.db.get_user(user_id)
            user_name = user_info.get('name', 'غير معروف') if user_info else 'غير معروف'
            
            # Remove user from database
            users_data = self.db.get_all_users()
            if user_id in users_data:
                del users_data[user_id]
                from utils import save_json
                save_json('users.json', users_data)
            
            # Notify user
            try:
                self.bot.send_message(
                    int(user_id),
                    "❌ نأسف، لم يتم قبول طلبك للانضمام إلى المتجر"
                )
            except:
                pass
            
            # Update admin message
            new_text = f"❌ تم رفض المستخدم\n\n👤 الاسم: {user_name}\n🆔 المعرف: {user_id}"
            
            try:
                self.bot.edit_message_text(
                    new_text, 
                    call.message.chat.id, 
                    call.message.message_id
                )
            except:
                pass
                
            self.bot.answer_callback_query(call.id, "❌ تم رفض المستخدم")
            
        except Exception as e:
            print(f"Error rejecting new user: {e}")
            self.bot.answer_callback_query(call.id, "❌ حدث خطأ")
    
    def show_settings(self, call):
        """Show settings menu"""
        text = "⚙️ إعدادات البوت\n\nهذه الميزة قيد التطوير"
        
        markup = telebot.types.InlineKeyboardMarkup()
        markup.row(telebot.types.InlineKeyboardButton("🔙 العودة", callback_data="admin_menu"))
        
        try:
            self.bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup)
        except:
            self.bot.send_message(call.message.chat.id, text, reply_markup=markup)