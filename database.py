from typing import Dict, List, Optional, Any
import json
from datetime import datetime
from utils import load_json, save_json, backup_json, generate_invoice_id, generate_request_id, get_current_timestamp
from config import USERS_FILE, PRODUCTS_FILE, SALES_FILE, RECHARGE_REQUESTS_FILE

class DatabaseManager:
    def __init__(self):
        self.initialize_files()
    
    def initialize_files(self):
        """Initialize all JSON files with default data"""
        # Initialize users file
        if not load_json(USERS_FILE):
            save_json(USERS_FILE, {})
        
        # Initialize products file with default products
        default_products = {
            "vpn_1month": {
                "name": "VPN 1 شهر",
                "price": 5000,
                "description": "خدمة VPN عالية الجودة لمدة شهر كامل مع دعم جميع الأجهزة وسرعة عالية",
                "codes": [
                    "vpn-code-001",
                    "vpn-code-002",
                    "vpn-code-003"
                ],
                "image": "https://i.imgur.com/YqzqHvz.jpg",
                "category": "vpn",
                "active": True
            },
            "netflix_account": {
                "name": "حساب نتفليكس مشاركة",
                "price": 8000,
                "description": "حساب نتفليكس مشاركة عالي الجودة مع إمكانية المشاهدة بدقة 4K على جهازين",
                "codes": [
                    "netflix-acc1:pass123",
                    "netflix-acc2:pass456"
                ],
                "image": "https://i.imgur.com/bOGJIqw.jpg",
                "category": "streaming",
                "active": True
            },
            "spotify_premium": {
                "name": "Spotify Premium شهر",
                "price": 3000,
                "description": "اشتراك Spotify Premium لمدة شهر كامل مع إمكانية التحميل والاستماع بدون إعلانات",
                "codes": [
                    "spotify-code-001",
                    "spotify-code-002"
                ],
                "image": "https://i.imgur.com/kN6QUxl.jpg",
                "category": "music",
                "active": True
            }
        }
        
        current_products = load_json(PRODUCTS_FILE)
        if not current_products:
            save_json(PRODUCTS_FILE, default_products)
        
        # Initialize sales file
        if not load_json(SALES_FILE):
            save_json(SALES_FILE, {})
        
        # Initialize recharge requests file
        if not load_json(RECHARGE_REQUESTS_FILE):
            save_json(RECHARGE_REQUESTS_FILE, {})
    
    # User Management
    def get_user(self, user_id: str) -> Optional[Dict]:
        """Get user data"""
        users = load_json(USERS_FILE)
        return users.get(user_id)
    
    def create_user(self, user_id: str, name: str) -> bool:
        """Create new user"""
        users = load_json(USERS_FILE)
        if user_id not in users:
            users[user_id] = {
                "balance": 0,
                "name": name,
                "created_at": get_current_timestamp(),
                "total_spent": 0,
                "purchase_count": 0,
                "banned": False,
                "pending_approval": True
            }
            return save_json(USERS_FILE, users)
        return False
    
    def update_user_balance(self, user_id: str, amount: int) -> bool:
        """Update user balance"""
        users = load_json(USERS_FILE)
        if user_id in users:
            users[user_id]["balance"] += amount
            return save_json(USERS_FILE, users)
        return False
    
    def set_user_balance(self, user_id: str, balance: int) -> bool:
        """Set user balance to specific amount"""
        users = load_json(USERS_FILE)
        if user_id in users:
            users[user_id]["balance"] = balance
            return save_json(USERS_FILE, users)
        return False
    
    def ban_user(self, user_id: str, banned: bool = True) -> bool:
        """Ban or unban user"""
        users = load_json(USERS_FILE)
        if user_id in users:
            users[user_id]["banned"] = banned
            return save_json(USERS_FILE, users)
        return False
    
    def is_user_banned(self, user_id: str) -> bool:
        """Check if user is banned"""
        user = self.get_user(user_id)
        return user.get("banned", False) if user else False
    
    def approve_user(self, user_id: str) -> bool:
        """Approve pending user"""
        users = load_json(USERS_FILE)
        if user_id in users:
            users[user_id]["pending_approval"] = False
            users[user_id]["approved_at"] = get_current_timestamp()
            return save_json(USERS_FILE, users)
        return False
    
    def is_user_pending(self, user_id: str) -> bool:
        """Check if user is pending approval"""
        user = self.get_user(user_id)
        return user.get("pending_approval", False) if user else False
    
    def get_all_users(self) -> Dict:
        """Get all users"""
        return load_json(USERS_FILE)
    
    def get_pending_users(self) -> List[Dict]:
        """Get users pending approval"""
        users = load_json(USERS_FILE)
        pending_users = []
        
        for user_id, user_data in users.items():
            if user_data.get("pending_approval", False):
                user_info = user_data.copy()
                user_info["user_id"] = user_id
                pending_users.append(user_info)
        
        return pending_users
    
    # Product Management
    def get_products(self) -> Dict:
        """Get all products"""
        return load_json(PRODUCTS_FILE)
    
    def get_product(self, product_id: str) -> Optional[Dict]:
        """Get specific product"""
        products = self.get_products()
        return products.get(product_id)
    
    def get_available_products(self) -> Dict:
        """Get products that are active and have stock"""
        products = self.get_products()
        available = {}
        for product_id, product in products.items():
            # Check if product is active (default to True for backward compatibility)
            is_active = product.get("active", True)
            # Check if product has codes available
            has_stock = len(product.get("codes", [])) > 0
            
            if is_active and has_stock:
                available[product_id] = product
        return available
    
    def add_product_code(self, product_id: str, code: str) -> bool:
        """Add code to product"""
        products = load_json(PRODUCTS_FILE)
        if product_id in products:
            if "codes" not in products[product_id]:
                products[product_id]["codes"] = []
            products[product_id]["codes"].append(code)
            return save_json(PRODUCTS_FILE, products)
        return False
    
    def remove_product_code(self, product_id: str) -> Optional[str]:
        """Remove and return first available code"""
        products = load_json(PRODUCTS_FILE)
        if product_id in products and products[product_id].get("codes"):
            code = products[product_id]["codes"].pop(0)
            save_json(PRODUCTS_FILE, products)
            return code
        return None
    
    def update_product(self, product_id: str, updates: Dict) -> bool:
        """Update product information"""
        products = load_json(PRODUCTS_FILE)
        if product_id in products:
            products[product_id].update(updates)
            return save_json(PRODUCTS_FILE, products)
        return False
    
    def create_product(self, product_id: str, product_data: Dict) -> bool:
        """Create new product"""
        products = load_json(PRODUCTS_FILE)
        if product_id not in products:
            products[product_id] = product_data
            return save_json(PRODUCTS_FILE, products)
        return False
    
    def delete_product(self, product_id: str) -> bool:
        """Delete product"""
        products = load_json(PRODUCTS_FILE)
        if product_id in products:
            del products[product_id]
            return save_json(PRODUCTS_FILE, products)
        return False
    
    # Sales Management
    def record_sale(self, user_id: str, product_name: str, code: str, price: int) -> str:
        """Record a sale and return invoice ID"""
        sales = load_json(SALES_FILE)
        users = load_json(USERS_FILE)
        
        if user_id not in sales:
            sales[user_id] = []
        
        invoice_id = generate_invoice_id()
        sale_record = {
            "product": product_name,
            "code": code,
            "price": price,
            "date": get_current_timestamp(),
            "invoice_id": invoice_id
        }
        
        sales[user_id].append(sale_record)
        save_json(SALES_FILE, sales)
        
        # Update user statistics
        if user_id in users:
            users[user_id]["total_spent"] = users[user_id].get("total_spent", 0) + price
            users[user_id]["purchase_count"] = users[user_id].get("purchase_count", 0) + 1
            save_json(USERS_FILE, users)
        
        return invoice_id
    
    def get_user_purchases(self, user_id: str) -> List[Dict]:
        """Get user purchase history"""
        sales = load_json(SALES_FILE)
        return sales.get(user_id, [])
    
    def get_all_sales(self) -> Dict:
        """Get all sales data"""
        return load_json(SALES_FILE)
    
    def get_sales_stats(self) -> Dict:
        """Get sales statistics"""
        sales = load_json(SALES_FILE)
        total_sales = 0
        total_revenue = 0
        
        for user_sales in sales.values():
            total_sales += len(user_sales)
            total_revenue += sum(sale["price"] for sale in user_sales)
        
        return {
            "total_sales": total_sales,
            "total_revenue": total_revenue,
            "unique_customers": len(sales)
        }
    
    # Recharge Request Management
    def create_recharge_request(self, user_id: str, amount: int, transfer_date: str = None, receipt_photo: str = None) -> str:
        """Create recharge request with transfer details"""
        requests = load_json(RECHARGE_REQUESTS_FILE)
        
        if user_id not in requests:
            requests[user_id] = []
        
        request_id = generate_request_id()
        request_data = {
            "amount": amount,
            "status": "pending",
            "date": get_current_timestamp(),
            "request_id": request_id,
            "transfer_date": transfer_date,
            "receipt_photo": receipt_photo
        }
        
        requests[user_id].append(request_data)
        save_json(RECHARGE_REQUESTS_FILE, requests)
        return request_id
    
    def get_recharge_requests(self, status: str = None) -> Dict:
        """Get recharge requests, optionally filtered by status"""
        requests = load_json(RECHARGE_REQUESTS_FILE)
        if status:
            filtered_requests = {}
            for user_id, user_requests in requests.items():
                filtered_user_requests = [req for req in user_requests if req.get("status") == status]
                if filtered_user_requests:
                    filtered_requests[user_id] = filtered_user_requests
            return filtered_requests
        return requests
    
    def update_recharge_request(self, user_id: str, request_id: str, status: str) -> bool:
        """Update recharge request status"""
        requests = load_json(RECHARGE_REQUESTS_FILE)
        
        if user_id in requests:
            for request in requests[user_id]:
                if request.get("request_id") == request_id:
                    request["status"] = status
                    request["processed_at"] = get_current_timestamp()
                    return save_json(RECHARGE_REQUESTS_FILE, requests)
        return False
    
    def get_pending_recharge_requests(self) -> List[Dict]:
        """Get all pending recharge requests with user info"""
        requests = load_json(RECHARGE_REQUESTS_FILE)
        users = load_json(USERS_FILE)
        pending_requests = []
        
        for user_id, user_requests in requests.items():
            user_info = users.get(user_id, {})
            for request in user_requests:
                if request.get("status") == "pending":
                    request_info = request.copy()
                    request_info["user_id"] = user_id
                    request_info["user_name"] = user_info.get("name", "مستخدم غير معروف")
                    pending_requests.append(request_info)
        
        return pending_requests
    
    # Process purchase transaction
    def process_purchase(self, user_id: str, product_id: str) -> Dict:
        """Process complete purchase transaction"""
        result = {"success": False, "message": "", "data": {}}
        
        try:
            # Get user and product data
            user = self.get_user(user_id)
            product = self.get_product(product_id)
            
            if not user:
                result["message"] = "المستخدم غير موجود"
                return result
            
            if not product:
                result["message"] = "المنتج غير موجود"
                return result
            
            # Check if user has sufficient balance
            user_balance = user.get("balance", 0)
            product_price = product.get("price", 0)
            
            if user_balance < product_price:
                result["message"] = f"رصيدك غير كافي. تحتاج إلى {product_price - user_balance:,} {self.get_currency()} إضافية"
                return result
            
            # Check if product has available codes
            available_codes = product.get("codes", [])
            if not available_codes:
                result["message"] = "المنتج غير متوفر حالياً"
                return result
            
            # Process the purchase
            product_code = self.remove_product_code(product_id)
            if not product_code:
                result["message"] = "فشل في الحصول على كود المنتج"
                return result
            
            # Deduct balance
            new_balance = user_balance - product_price
            if not self.set_user_balance(user_id, new_balance):
                # Restore the code if balance update fails
                self.add_product_code(product_id, product_code)
                result["message"] = "فشل في تحديث الرصيد"
                return result
            
            # Record the sale
            invoice_id = self.record_sale(
                user_id=user_id,
                product_name=product.get("name", "منتج غير معروف"),
                code=product_code,
                price=product_price
            )
            
            result["success"] = True
            result["message"] = "تم الشراء بنجاح"
            result["data"] = {
                "product_name": product.get("name"),
                "code": product_code,
                "price": product_price,
                "invoice_id": invoice_id,
                "new_balance": new_balance
            }
            
        except Exception as e:
            result["message"] = f"حدث خطأ أثناء معالجة الطلب: {str(e)}"
            
        return result
    
    def get_currency(self) -> str:
        """Get currency symbol"""
        from config import CURRENCY
        return CURRENCY
