"""
ربات اصلی سیگنال‌دهی Nattaj CC
ورژن GitHub - اجرای ۲۴ ساعته
"""

import json
import time
import requests
from datetime import datetime

# ایمپورت تنظیمات از فایل کانفیگ
try:
    from bot_config import TELEGRAM_TOKEN, TELEGRAM_CHAT_ID, ALL_SYMBOLS, CHECK_INTERVAL, MA_FILTER_ENABLED
    print("✅ تنظیمات از bot_config.py بارگذاری شد")
except ImportError as e:
    print(f"⚠️ خطا در بارگذاری تنظیمات: {e}")
    # مقادیر پیش‌فرض اگر فایل کانفیگ نبود
    TELEGRAM_TOKEN = "8492497660:AAGQgmKTjrxi4c4IaRh6xg8PF9ZEYmbnZEc"
    TELEGRAM_CHAT_ID = "138228682"
    ALL_SYMBOLS = ["BTCUSDT", "ETHUSDT", "BNBUSDT"]
    CHECK_INTERVAL = 5
    MA_FILTER_ENABLED = True

print("="*50)
print("🤖 ربات سیگنال Nattaj CC")
print("="*50)

# فایل‌های ذخیره وضعیت
STATE_FILE = "user_state.json"
LOG_FILE = "bot_log.txt"

# ================================
# توابع اصلی
# ================================

def load_state():
    """بارگذاری وضعیت کاربر از فایل"""
    try:
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        # وضعیت پیش‌فرض
        return {
            "symbol": None,
            "active": False,
            "user_chat_id": TELEGRAM_CHAT_ID
        }

def save_state(symbol=None, active=True):
    """ذخیره وضعیت کاربر در فایل"""
    state = {
        "symbol": symbol,
        "active": active,
        "last_updated": datetime.now().isoformat(),
        "user_chat_id": TELEGRAM_CHAT_ID
    }
    try:
        with open(STATE_FILE, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"❌ خطا در ذخیره وضعیت: {e}")
        return False

def log_to_file(message):
    """ذخیره لاگ در فایل"""
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            f.write(f"[{timestamp}] {message}\n")
    except:
        pass

def send_telegram(message, chat_id=None):
    """ارسال پیام به تلگرام"""
    if chat_id is None:
        chat_id = TELEGRAM_CHAT_ID
    
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": message,
            "parse_mode": "HTML",
            "disable_web_page_preview": True
        }
        response = requests.post(url, json=payload, timeout=10)
        
        if response.status_code == 200:
            return True
        else:
            print(f"❌ خطای تلگرام: {response.text}")
            return False
    except Exception as e:
        print(f"❌ خطا در ارسال تلگرام: {e}")
        return False

def get_binance_price(symbol):
    """گرفتن قیمت لحظه‌ای از Binance"""
    try:
        url = f"https://api.binance.com/api/v3/ticker/price?symbol={symbol}"
        response = requests.get(url, timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            price = float(data["price"])
            return price
        else:
            print(f"❌ خطا در دریافت قیمت: {response.status_code}")
            return None
    except Exception as e:
        print(f"❌ خطا در اتصال به Binance: {e}")
        return None

def check_signal(symbol, price):
    """
    بررسی شرایط سیگنال با فیلتر MA
    
    این تابع باید با منطق REAL اندیکاتورهای شما جایگزین شود
    فعلاً یک شبیه‌سازی هوشمند داریم
    """
    
    # اینجا شبیه‌سازی می‌کنیم. در نسخه واقعی، باید:
    # 1. از TradingView Webhook دریافت کنی
    # 2. یا از API دیگری اندیکاتور رو بگیریم
    
    import random
    import hashlib
    
    # ایجاد یک شناسه یکتا بر اساس زمان و قیمت
    unique_str = f"{symbol}{price}{datetime.now().minute}"
    hash_val = int(hashlib.md5(unique_str.encode()).hexdigest(), 16)
    
    # 15% شانس تولید سیگنال (برای تست)
    if hash_val % 7 == 0:  # حدود 14% شانس
        # تصمیم‌گیری نوع سیگنال
        signal_type = "BUY" if hash_val % 2 == 0 else "SELL"
        
        # موقعیت فرضی نسبت به MA
        # در حالت واقعی، این باید از اندیکاتور دوم (SSL Hybrid) گرفته شود
        ma_position = "below" if signal_type == "BUY" else "above"
        
        # اعمال فیلتر MA (اگر فعال باشد)
        if MA_FILTER_ENABLED:
            if signal_type == "BUY" and ma_position != "below":
                print(f"   🔸 فیلتر MA: سیگنال BUY رد شد (نیاز به below MA)")
                return {"signal": False}
            if signal_type == "SELL" and ma_position != "above":
                print(f"   🔸 فیلتر MA: سیگنال SELL رد شد (نیاز به above MA)")
                return {"signal": False}
        
        return {
            "signal": True,
            "type": signal_type,
            "price": price,
            "ma_position": ma_position,
            "confidence": "HIGH" if hash_val % 3 == 0 else "MEDIUM",
            "time": datetime.now().strftime("%H:%M:%S")
        }
    
    return {"signal": False}

def run_monitoring_cycle():
    """اجرای یک سیکل کامل مانیتورینگ"""
    
    # بارگذاری وضعیت فعلی
    state = load_state()
    
    # اگر ربات فعال نیست یا ارزی انتخاب نشده
    if not state.get("active") or not state.get("symbol"):
        print("⏸️  ربات غیرفعال است. برای فعال‌سازی به تلگرام بروید.")
        return False
    
    symbol = state["symbol"]
    chat_id = state.get("user_chat_id", TELEGRAM_CHAT_ID)
    
    print(f"\n{'='*40}")
    print(f"🔍 شروع چک برای {symbol}")
    print(f"{'='*40}")
    
    # ======== قسمت ۱: دریافت قیمت ========
    price = get_binance_price(symbol)
    
    if price is None:
        print(f"❌ دریافت قیمت {symbol} ناموفق بود")
        log_to_file(f"FAILED_PRICE {symbol}")
        return False
    
    # نمایش قیمت در کنسول
    price_formatted = f"{price:,.2f}"
    print(f"💰 قیمت لحظه‌ای: ${price_formatted}")
    log_to_file(f"PRICE {symbol} ${price_formatted}")
    
    # ======== قسمت ۲: بررسی سیگنال ========
    print("🎯 در حال بررسی شرایط سیگنال...")
    signal_data = check_signal(symbol, price)
    
    # ======== قسمت ۳: ارسال سیگنال (اگر وجود داشت) ========
    if signal_data.get("signal"):
        signal_type = signal_data["type"]
        ma_position = signal_data["ma_position"]
        
        print(f"🚨 سیگنال {signal_type} شناسایی شد!")
        print(f"   📊 موقعیت MA: {ma_position}")
        print(f"   🎯 اعتبار: {signal_data.get('confidence', 'MEDIUM')}")
        
        # ساخت پیام سیگنال
        emoji = "🟢" if signal_type == "BUY" else "🔴"
        
        message = f"""
{emoji} <b>سیگنال {signal_type}</b> {emoji}

📊 <b>ارز:</b> {symbol}
💰 <b>قیمت:</b> ${price:,.2f}
📈 <b>موقعیت نسبت به MA:</b> {ma_position}

🎯 <b>اعتبار سیگنال:</b> {signal_data.get('confidence', 'MEDIUM')}
⏰ <b>زمان شناسایی:</b> {signal_data.get('time', 'N/A')}

{"✅ <b>فیلتر MA فعال:</b> سیگنال معتبر است" if MA_FILTER_ENABLED else "⚠️ <b>فیلتر MA غیرفعال</b>"}

⚠️ <i>این یک پیام تست است. تصمیم نهایی با شماست.</i>
"""
        
        # ارسال به تلگرام
        if send_telegram(message, chat_id):
            print(f"✅ پیام سیگنال به تلگرام ارسال شد")
            log_to_file(f"SIGNAL_SENT {symbol} {signal_type} ${price}")
        else:
            print(f"❌ ارسال پیام سیگنال ناموفق بود")
            log_to_file(f"SIGNAL_FAILED {symbol}")
    else:
        print(f"🔸 هیچ سیگنالی یافت نشد")
        log_to_file(f"NO_SIGNAL {symbol}")
    
    print(f"{'='*40}\n")
    return True

def send_welcome_message():
    """ارسال پیام خوشآمدگویی و راهنما"""
    
    welcome_msg = f"""
🤖 <b>ربات سیگنال Nattaj CC فعال شد!</b>

🎯 <b>وضعیت فعلی:</b>
• ربات روی GitHub اجرا شده است
• هر ۵ دقیقه بازار را بررسی می‌کند
• فیلتر MA: {'فعال ✅' if MA_FILTER_ENABLED else 'غیرفعال ⚠️'}

📋 <b>برای تنظیم ربات:</b>
1. یک پیام به ربات در تلگرام بفرستید
2. از دستور /start استفاده کنید
3. ارز مورد نظر را انتخاب کنید

🔧 <b>پشتیبانی:</b>
اگر مشکل دارید، کدهای ربات را در ریپازیتوری چک کنید.

⏰ <b>زمان راه‌اندازی:</b> {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
"""
    
    return send_telegram(welcome_msg)

# ================================
# نقطه شروع برنامه
# ================================

if __name__ == "__main__":
    print("🚀 در حال راه‌اندازی ربات...")
    log_to_file("="*50)
    log_to_file("🤖 ربات Nattaj CC شروع به کار کرد")
    log_to_file(f"تاریخ: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # ارسال پیام شروع
    print("📤 ارسال پیام شروع به تلگرام...")
    if send_welcome_message():
        print("✅ پیام شروع ارسال شد")
    else:
        print("⚠️ ارسال پیام شروع ناموفق بود")
    
    # اجرای یک سیکل مانیتورینگ
    print("\n🔧 اجرای اولین چک...")
    run_monitoring_cycle()
    
    print("\n" + "="*50)
    print("✅ اجرای ربات کامل شد")
    print("📝 لاگ‌ها در فایل bot_log.txt ذخیره شدند")
    print("🔄 ربات دوباره در اجرای بعدی GitHub Actions اجرا می‌شود")
    print("="*50)
    
    log_to_file("✅ اجرای ربات به پایان رسید")
    log_to_file("="*50)
