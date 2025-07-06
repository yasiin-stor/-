import json
import os
from datetime import datetime
from typing import Dict, List, Any, Optional

def ensure_directory(path: str) -> None:
    """Ensure directory exists"""
    directory = os.path.dirname(path)
    if directory and not os.path.exists(directory):
        os.makedirs(directory, exist_ok=True)

def load_json(filename: str, default: Any = None) -> Any:
    """Load JSON file with error handling"""
    if default is None:
        default = {}
    
    try:
        ensure_directory(filename)
        if os.path.exists(filename):
            with open(filename, 'r', encoding='utf-8') as f:
                return json.load(f)
        else:
            # Create file with default data
            save_json(filename, default)
            return default
    except (json.JSONDecodeError, FileNotFoundError) as e:
        print(f"Error loading {filename}: {e}")
        return default
    except Exception as e:
        print(f"Unexpected error loading {filename}: {e}")
        return default

def save_json(filename: str, data: Any) -> bool:
    """Save JSON file with error handling"""
    try:
        ensure_directory(filename)
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"Error saving {filename}: {e}")
        return False

def backup_json(filename: str) -> bool:
    """Create backup of JSON file"""
    try:
        if os.path.exists(filename):
            backup_name = f"{filename}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            import shutil
            shutil.copy2(filename, backup_name)
            return True
    except Exception as e:
        print(f"Error creating backup for {filename}: {e}")
    return False

def generate_invoice_id() -> str:
    """Generate unique invoice ID"""
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    return f"INV-{timestamp}"

def generate_request_id() -> str:
    """Generate unique request ID"""
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    return f"REQ-{timestamp}"

def format_currency(amount: int, currency: str = "IQD") -> str:
    """Format currency with proper formatting"""
    return f"{amount:,.0f} {currency}"

def validate_user_id(user_id: str) -> bool:
    """Validate Telegram user ID format"""
    try:
        int(user_id)
        return len(user_id) > 0
    except (ValueError, TypeError):
        return False

def sanitize_text(text: str, max_length: int = 4000) -> str:
    """Sanitize text for Telegram messages"""
    if not text:
        return ""
    
    # Remove any potentially harmful characters
    sanitized = str(text).strip()
    
    # Truncate if too long
    if len(sanitized) > max_length:
        sanitized = sanitized[:max_length-3] + "..."
    
    return sanitized

def get_current_timestamp() -> str:
    """Get current timestamp in ISO format"""
    return datetime.now().isoformat()

def parse_timestamp(timestamp_str: str) -> Optional[datetime]:
    """Parse ISO timestamp string"""
    try:
        return datetime.fromisoformat(timestamp_str)
    except (ValueError, TypeError):
        return None

def is_admin(user_id: int, admin_id: int) -> bool:
    """Check if user is admin"""
    return user_id == admin_id

def clean_old_backups(filename: str, keep_count: int = 5) -> None:
    """Clean old backup files, keeping only the most recent ones"""
    try:
        directory = os.path.dirname(filename) or "."
        base_name = os.path.basename(filename)
        
        # Find all backup files
        backup_files = []
        for file in os.listdir(directory):
            if file.startswith(base_name + ".backup_"):
                full_path = os.path.join(directory, file)
                backup_files.append((full_path, os.path.getmtime(full_path)))
        
        # Sort by modification time (newest first)
        backup_files.sort(key=lambda x: x[1], reverse=True)
        
        # Remove old backups
        for file_path, _ in backup_files[keep_count:]:
            try:
                os.remove(file_path)
            except OSError:
                pass
    except Exception as e:
        print(f"Error cleaning backups: {e}")
