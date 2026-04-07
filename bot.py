import telebot
import sqlite3
import random
import time

TOKEN = "8792650374:AAG6iohQJQrghyRQ7N1E_j8oI-lwzRa-rmY"
bot = telebot.TeleBot(TOKEN)

ADMIN_ID = 7979064736  # apna telegram id dal

CHANNEL = "@codestore90"  # force join

# ---------- DB ----------
def db():
    return sqlite3.connect("bot.db", check_same_thread=False)

conn = db()
c = conn.cursor()

c.execute("""CREATE TABLE IF NOT EXISTS users(
    user_id INTEGER PRIMARY KEY,
    balance INTEGER DEFAULT 0,
    referrals INTEGER DEFAULT 0,
    ref_by INTEGER,
    last_bonus INTEGER DEFAULT 0
)""")

c.execute("""CREATE TABLE IF NOT EXISTS withdraw(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    amount INTEGER,
    status TEXT
)""")

conn.commit()

# ---------- FORCE JOIN ----------
def joined(user_id):
    try:
        status = bot.get_chat_member(CHANNEL, user_id).status
        return status in ["member", "administrator", "creator"]
    except:
        return False

# ---------- START ----------
@bot.message_handler(commands=['start'])
def start(msg):
    user_id = msg.from_user.id
    args = msg.text.split()

    if not joined(user_id):
        bot.reply_to(msg, f"❌ पहले चैनल जॉइन करो: {CHANNEL}")
        return

    ref = int(args[1]) if len(args) > 1 else None

    c.execute("SELECT * FROM users WHERE user_id=?", (user_id,))
    user = c.fetchone()

    if not user:
        c.execute("INSERT INTO users(user_id, ref_by) VALUES(?,?)", (user_id, ref))

        if ref:
            c.execute("UPDATE users SET balance=balance+10, referrals=referrals+1 WHERE user_id=?", (ref,))

        conn.commit()

    bot.reply_to(msg, "🎉 Welcome!\nUse /menu")

# ---------- MENU ----------
@bot.message_handler(commands=['menu'])
def menu(msg):
    bot.send_message(msg.chat.id,
    "📊 MENU\n\n"
    "/balance - Check balance\n"
    "/refer - Referral link\n"
    "/daily - Daily bonus\n"
    "/task - Tasks\n"
    "/withdraw - Withdraw\n"
    )

# ---------- BALANCE ----------
@bot.message_handler(commands=['balance'])
def balance(msg):
    c.execute("SELECT balance FROM users WHERE user_id=?", (msg.from_user.id,))
    bal = c.fetchone()
    bot.reply_to(msg, f"💰 Balance: {bal[0] if bal else 0}₹")

# ---------- REFER ----------
@bot.message_handler(commands=['refer'])
def refer(msg):
    link = f"https://t.me/YOUR_BOT_USERNAME?start={msg.from_user.id}"
    bot.reply_to(msg, f"👥 Your link:\n{link}")

# ---------- DAILY ----------
@bot.message_handler(commands=['daily'])
def daily(msg):
    user_id = msg.from_user.id
    now = int(time.time())

    c.execute("SELECT last_bonus FROM users WHERE user_id=?", (user_id,))
    last = c.fetchone()[0]

    if now - last < 86400:
        bot.reply_to(msg, "⏳ Already claimed today")
        return

    reward = random.randint(2,10)
    c.execute("UPDATE users SET balance=balance+?, last_bonus=? WHERE user_id=?", (reward, now, user_id))
    conn.commit()

    bot.reply_to(msg, f"🎁 Bonus: {reward}₹")

# ---------- TASK ----------
@bot.message_handler(commands=['task'])
def task(msg):
    bot.reply_to(msg,
    "📋 Tasks:\n"
    "1. Join channel = 5₹ (/claim1)\n"
    "2. Share bot = 3₹ (/claim2)"
    )

@bot.message_handler(commands=['claim1'])
def claim1(msg):
    c.execute("UPDATE users SET balance=balance+5 WHERE user_id=?", (msg.from_user.id,))
    conn.commit()
    bot.reply_to(msg, "✅ 5₹ Added")

@bot.message_handler(commands=['claim2'])
def claim2(msg):
    c.execute("UPDATE users SET balance=balance+3 WHERE user_id=?", (msg.from_user.id,))
    conn.commit()
    bot.reply_to(msg, "✅ 3₹ Added")

# ---------- WITHDRAW ----------
@bot.message_handler(commands=['withdraw'])
def withdraw(msg):
    bot.reply_to(msg, "💸 Send amount")

    bot.register_next_step_handler(msg, process_withdraw)

def process_withdraw(msg):
    try:
        amt = int(msg.text)
        user_id = msg.from_user.id

        c.execute("SELECT balance FROM users WHERE user_id=?", (user_id,))
        bal = c.fetchone()[0]

        if bal >= amt:
            c.execute("UPDATE users SET balance=balance-? WHERE user_id=?", (amt, user_id))
            c.execute("INSERT INTO withdraw(user_id,amount,status) VALUES(?,?,?)", (user_id, amt, "pending"))
            conn.commit()

            bot.send_message(ADMIN_ID, f"💸 Withdraw request\nUser: {user_id}\nAmount: {amt}")
            bot.reply_to(msg, "✅ Request sent")
        else:
            bot.reply_to(msg, "❌ Low balance")

    except:
        bot.reply_to(msg, "❌ Invalid")

# ---------- ADMIN ----------
@bot.message_handler(commands=['admin'])
def admin(msg):
    if msg.from_user.id != ADMIN_ID:
        return

    bot.reply_to(msg,
    "👑 ADMIN\n"
    "/users\n"
    "/broadcast"
    )

@bot.message_handler(commands=['users'])
def users(msg):
    if msg.from_user.id != ADMIN_ID:
        return

    c.execute("SELECT COUNT(*) FROM users")
    total = c.fetchone()[0]
    bot.reply_to(msg, f"👥 Users: {total}")

@bot.message_handler(commands=['broadcast'])
def bc(msg):
    if msg.from_user.id != ADMIN_ID:
        return

    bot.reply_to(msg, "Send message")

    bot.register_next_step_handler(msg, send_all)

def send_all(msg):
    text = msg.text

    c.execute("SELECT user_id FROM users")
    users = c.fetchall()

    for u in users:
        try:
            bot.send_message(u[0], text)
        except:
            pass

# ---------- RUN ----------
print("🤖 Bot Running...")
bot.infinity_polling()
# ---------- EXTRA TABLES ----------
c.execute("""CREATE TABLE IF NOT EXISTS promo(
    code TEXT,
    reward INTEGER
)""")

c.execute("""CREATE TABLE IF NOT EXISTS banned(
    user_id INTEGER
)""")

c.execute("""CREATE TABLE IF NOT EXISTS claimed(
    user_id INTEGER,
    task TEXT
)""")

conn.commit()

# ---------- PROFILE ----------
@bot.message_handler(commands=['profile'])
def profile(msg):
    user_id = msg.from_user.id
    c.execute("SELECT balance, referrals FROM users WHERE user_id=?", (user_id,))
    data = c.fetchone()

    bot.reply_to(msg,
    f"👤 Profile\n\n"
    f"🆔 ID: {user_id}\n"
    f"💰 Balance: {data[0]}\n"
    f"👥 Referrals: {data[1]}"
    )

# ---------- LEADERBOARD ----------
@bot.message_handler(commands=['leaderboard'])
def leaderboard(msg):
    c.execute("SELECT user_id, referrals FROM users ORDER BY referrals DESC LIMIT 5")
    top = c.fetchall()

    text = "🏆 Top Users:\n"
    for i, u in enumerate(top):
        text += f"{i+1}. {u[0]} - {u[1]} refs\n"

    bot.reply_to(msg, text)

# ---------- SPIN ----------
@bot.message_handler(commands=['spin'])
def spin(msg):
    reward = random.choice([0,1,2,5,10])
    c.execute("UPDATE users SET balance=balance+? WHERE user_id=?", (reward, msg.from_user.id))
    conn.commit()

    bot.reply_to(msg, f"🎰 You won {reward}₹")

# ---------- PROMO ----------
@bot.message_handler(commands=['promo'])
def promo(msg):
    bot.reply_to(msg, "Send promo code")
    bot.register_next_step_handler(msg, apply_promo)

def apply_promo(msg):
    code = msg.text
    c.execute("SELECT reward FROM promo WHERE code=?", (code,))
    p = c.fetchone()

    if p:
        c.execute("UPDATE users SET balance=balance+? WHERE user_id=?", (p[0], msg.from_user.id))
        conn.commit()
        bot.reply_to(msg, "✅ Promo applied")
    else:
        bot.reply_to(msg, "❌ Invalid code")

# ---------- STATS ----------
@bot.message_handler(commands=['stats'])
def stats(msg):
    c.execute("SELECT COUNT(*) FROM users")
    users = c.fetchone()[0]

    c.execute("SELECT SUM(balance) FROM users")
    total = c.fetchone()[0]

    bot.reply_to(msg, f"📊 Stats\n👥 Users: {users}\n💰 Total Balance: {total}")

# ---------- SUPPORT ----------
@bot.message_handler(commands=['support'])
def support(msg):
    bot.reply_to(msg, "Send your problem")
    bot.register_next_step_handler(msg, send_support)

def send_support(msg):
    bot.send_message(ADMIN_ID, f"📩 Support from {msg.from_user.id}:\n{msg.text}")
    bot.reply_to(msg, "✅ Sent to admin")

# ---------- BAN SYSTEM ----------
@bot.message_handler(commands=['ban'])
def ban(msg):
    if msg.from_user.id != ADMIN_ID:
        return

    try:
        user_id = int(msg.text.split()[1])
        c.execute("INSERT INTO banned(user_id) VALUES(?)", (user_id,))
        conn.commit()
        bot.reply_to(msg, "🚫 User banned")
    except:
        bot.reply_to(msg, "Usage: /ban user_id")

# ---------- ADD BALANCE ----------
@bot.message_handler(commands=['addbal'])
def addbal(msg):
    if msg.from_user.id != ADMIN_ID:
        return

    try:
        _, user_id, amt = msg.text.split()
        c.execute("UPDATE users SET balance=balance+? WHERE user_id=?", (amt, user_id))
        conn.commit()
        bot.reply_to(msg, "✅ Added")
    except:
        bot.reply_to(msg, "Usage: /addbal user_id amount")

# ---------- DEDUCT BAL ----------
@bot.message_handler(commands=['cutbal'])
def cutbal(msg):
    if msg.from_user.id != ADMIN_ID:
        return

    try:
        _, user_id, amt = msg.text.split()
        c.execute("UPDATE users SET balance=balance-? WHERE user_id=?", (amt, user_id))
        conn.commit()
        bot.reply_to(msg, "❌ Deducted")
    except:
        bot.reply_to(msg, "Usage: /cutbal user_id amount")

# ---------- WITHDRAW HISTORY ----------
@bot.message_handler(commands=['history'])
def history(msg):
    c.execute("SELECT amount,status FROM withdraw WHERE user_id=?", (msg.from_user.id,))
    data = c.fetchall()

    if not data:
        bot.reply_to(msg, "No history")
        return

    text = "📜 History:\n"
    for d in data:
        text += f"{d[0]}₹ - {d[1]}\n"

    bot.reply_to(msg, text)
