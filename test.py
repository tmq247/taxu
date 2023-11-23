import telebot
import requests
import random
import os
from telebot.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup
from datetime import datetime, timedelta
import time
import atexit
from telebot import TeleBot, types
import pytz
import threading

# Thay thế giá trị dưới đây bằng token của bot Telegram của bạn
API_KEY = '6784844273:AAGdaEkuudWmwe-PsfYLFXKBzW_TF_pWIDM'
# Khởi tạo bot
bot = telebot.TeleBot(API_KEY, parse_mode=None)
# Dùng trạng thái (state) để theo dõi quá trình cược
user_state = {}
# Dùng từ điển để lưu số dư của người dùng
user_balance = {}
# Tạo từ điển lưu lịch sử cược và lịch sử rút tiền
user_bet_history = {}
user_withdraw_history = {}
# Tạo từ điển gitcodes
used_gitcodes = []
gitcode_amounts = {}
user_pending_gitcodes = {}
# Define a separate dictionary to track user game states
user_game_state = {}
# Dictionary to store user balances (user_id: balance)
user_balances = {}
# Dictionary to store user bets
user_bets = {}  # {user_id: {"bet_type": "", "amount": 0, "chosen_number": ""}}
# Inside your message handler function
vietnam_timezone = pytz.timezone(
    'Asia/Ho_Chi_Minh')  # Define the Vietnam timezone
# Get the current time in Vietnam timezone
current_time_vietnam = datetime.now(
    tz=vietnam_timezone).strftime("%Y-%m-%d %H:%M:%S")
group_chat_id2 = "-1002121532989"  # Replace with your second group chat ID
# Định nghĩa id của nhóm mà bạn muốn gửi thông báo
group_chat_id = '-1002121532989'
def get_user_info(user_id):
  try:
    user = bot.get_chat(user_id)
    return user
  except telebot.apihelper.ApiException as e:
    print("Error fetching user info:", e)
    return None


# Hàm để lưu tất cả số dư vào tệp văn bản
def save_balance_to_file():
  with open("id.txt", "w") as f:
    for user_id, balance in user_balance.items():
      f.write(f"{user_id} {balance}\n")


# Hàm để đọc số dư từ tệp văn bản và cập nhật vào từ điển user_balance
def load_balance_from_file():
  if os.path.exists("id.txt"):
    with open("id.txt", "r") as f:
      for line in f:
        user_id, balance_str = line.strip().split()
        balance = float(balance_str)
        if balance.is_integer():
          balance = int(balance)
        user_balance[int(user_id)] = balance


# Gọi hàm load_balance_from_file khi chương trình chạy để tải số dư từ tệp
load_balance_from_file()


# Hàm xử lý khi bot bị tắt hoặc lỗi, để lưu số dư vào tệp id.txt trước khi thoát
def on_exit():
  save_balance_to_file()


# Xử lý khi bot bị tắt hoặc lỗi
atexit.register(save_balance_to_file)

# Add these variables for Gitcode handling
GITCODE_FILE = "gitcode.txt"
# Function to create a Gitcode with a custom amount
def create_gitcode(amount):
    gitcode = ''.join(random.choices('ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789', k=8))
    gitcode_amounts[gitcode] = amount
    with open(GITCODE_FILE, "a") as f:
        f.write(f"{gitcode}:{amount}\n")
    return gitcode

# Function to read Gitcodes from the file
def read_gitcodes():
    if not os.path.exists(GITCODE_FILE):
        return
    with open(GITCODE_FILE, "r") as f:
        for line in f:
            gitcode, amount = line.strip().split(":")
            gitcode_amounts[gitcode] = int(amount)

# Function to remove a used Gitcode
def remove_gitcode(gitcode):
    with open(GITCODE_FILE, "r") as f:
        lines = f.readlines()
    with open(GITCODE_FILE, "w") as f:
        for line in lines:
            if not line.startswith(gitcode):
                f.write(line)

# Read Gitcodes from the file
read_gitcodes()

# Define the admin's user ID
admin_user_id = 6337933296, 6630692765 # Replace with the actual admin user ID

@bot.message_handler(commands=['regcode'])
def create_gitcode_handler(message):
    # Check if the user is the admin
    if message.from_user.id == 6337933296 or 6630692765:
        bot.reply_to(message, "Vui lòng nhập số tiền cho gitcode:")
        bot.register_next_step_handler(message, process_gitcode_amount)
    else:
        bot.reply_to(message, "Bạn không có quyền thực hiện lệnh này.")

def process_gitcode_amount(message):
    try:
        amount = int(message.text)
        formatted_amount = "{:,.0f}".format(amount).replace(".", ",")
        gitcode = create_gitcode(amount)
        bot.reply_to(message, f"Đã tạo gitcode thành công. Gitcode của bạn là: {gitcode} ({formatted_amount} đồng).")
    except ValueError:
        bot.reply_to(message, "Số tiền không hợp lệ.")

@bot.message_handler(func=lambda message: message.text.lower() == 'code')
def naptien_gitcode(message):
    bot.reply_to(message, "Bạn Đã Chọn Nhập Code\nBạn Hãy Nhập Code\n➡️VD: ABCD")
    bot.register_next_step_handler(message, process_naptien_gitcode)

def process_naptien_gitcode(message):
    gitcode = message.text
    user_id = message.from_user.id  # Get the user's ID
    if gitcode in gitcode_amounts:
        amount = gitcode_amounts[gitcode]

        # Check if the user's balance exists in the dictionary, initialize it if not
        if user_id not in user_balance:
            user_balance[user_id] = 0

        user_balance[user_id] += amount
        remove_gitcode(gitcode)
        bot.reply_to(message, f"Gitcode Thành Công!\nSố dư của bạn là: {user_balance[user_id]:,}đ.\n💹Chúc Bạn May Mắn Nhé💖")
        
        # Sử dụng phương thức send_message để gửi thông báo vào nhóm
        bot.send_message(group_chat_id, f"""
Người chơi {message.from_user.first_name} 
User: {user_id}
Đã Nạp: {amount:,}đ bằng Gitcode.""")
        # Save the updated balance to the file
        save_balance_to_file()
    else:
        bot.reply_to(message, "Gitcode không hợp lệ hoặc đã được sử dụng.")


# Code API xúc xắc
def send_dice_v1(chat_id):
  response = requests.get(
      f'https://api.telegram.org/bot{API_KEY}/sendDice?chat_id={chat_id}')
  if response.status_code == 200:
    data = response.json()
    if 'result' in data and 'dice' in data['result']:
      return data['result']['dice']['value']
  return None


# Hàm kiểm Tài/Xỉu
def calculate_tai_xiu(total_score):
  return "Tài" if 11 <= total_score <= 18 else "Xỉu"


# Hàm kiểm tra kết quả chẵn/lẻ
def chan_le_result(total_score):
  return "Chẵn" if total_score % 2 == 0 else "Lẻ"


# Định nghĩa hàm chan2_le2_result
def chan2_le2_result(score):
  if score % 2 == 0:
    return "Chan2"
  else:
    return "Le2"


# hàm kiểm tra kết quả của bầu cua
def roll_bau_cua_dice():
  return random.choices(BAU_CUA_ITEMS, k=3)

# Hàm xử lý chuyển tiền và cập nhật số dư của cả người gửi và người được chuyển
def deduct_balance(sender_id, recipient_id, amount):
    # Kiểm tra xem cả sender_id và recipient_id có tồn tại trong user_balance không
    if sender_id not in user_balance or recipient_id not in user_balance:
        return False

    # Kiểm tra xem số tiền cần chuyển có lớn hơn 0 và không vượt quá số dư của người gửi
    if amount <= 0 or user_balance[sender_id] < amount:
        return False

    # Trừ số tiền từ số dư của người gửi và cộng cho người được chuyển
    user_balance[sender_id] -= amount
    user_balance[recipient_id] += amount

    # Lưu số dư vào tệp văn bản
    save_balance_to_file()

    return True


@bot.message_handler(commands=['chuyentien'])
def chuyentien_money(message):
    try:
        # Parse thông tin người dùng và số tiền từ tin nhắn
        user_id, amount = map(int, message.text.split()[1:3])

        # Kiểm tra xem người gửi có đủ số dư để thực hiện chuyển khoản không
        sender_id = message.from_user.id
        sender_name = message.from_user.first_name  # Lấy tên của người gửi

        if sender_id not in user_balance or user_balance[sender_id] < amount:
            bot.reply_to(message, "Bạn không có đủ số dư để chuyển khoản này.")
            return

        # Thực hiện chuyển khoản và thông báo kết quả
        if deduct_balance(sender_id, user_id, amount):
            recipient_name = bot.get_chat(user_id).first_name  # Lấy tên của người được chuyển
            bot.reply_to(message, f"Chuyển khoản thành công! {amount:,} chuyển đến người dùng {recipient_name}.")
            bot.send_message(user_id, f"Bạn đã nhận được {amount:,}đ được chuyển từ {sender_name}, id người dùng là: {sender_id}.")
        else:
            bot.reply_to(message, "Không hợp lệ. Sử dụng /chuyentien <user_id> <số tiền>")
    except Exception as e:
        bot.reply_to(message, """
Tạo lệnh để chuyển tiền của mình cho ID người chơi khác:
    
/chuyentien [dấu cách] ID nhận tiền [dấu cách] số tiền
    
VD: /chuyentien 987654321 10000""")


@bot.message_handler(commands=["ctien"])
def set_balance(msg):
    admin = 6337933296, 6630692765 ,5838967403
  if msg.from_user.id in admin:
    bot.reply_to(msg, """
🔭Nhập user ID của thành viên🔨
        """)
    user_state[msg.from_user.id] = "set_user_id"
  else:
    bot.reply_to(msg, "Bạn không có quyền sử dụng lệnh này.")


@bot.message_handler(func=lambda message: message.from_user.id in user_state
                     and user_state[message.from_user.id] == "set_user_id")
def set_user_balance(msg):
  try:
    user_id = int(msg.text)
    bot.reply_to(
        msg, """
⏲Nhập số tiền muốn cộng hoặc trừ🪤 
🚬(ví dụ: +1000 hoặc -1000)🎚
🫡 Kèm Nội Dung 👊🏽
        """)
    user_state[msg.from_user.id] = (user_id, "setbalance")
  except ValueError:
    bot.reply_to(msg, "Vui lòng nhập một user ID hợp lệ.")


@bot.message_handler(func=lambda message: message.from_user.id in user_state
                     and user_state[message.from_user.id][1] == "setbalance")
def update_balance(msg):
  try:
    user_input = msg.text.split()
    if len(user_input) < 2:
      bot.reply_to(msg, "Vui lòng nhập số tiền và nội dung cần kèm")
      return

    balance_change = int(user_input[0])
    user_id, _ = user_state[msg.from_user.id]
    current_balance = user_balance.get(user_id, 0)
    new_balance = current_balance + balance_change
    user_balance[user_id] = new_balance
    del user_state[msg.from_user.id]
    save_balance_to_file()

    # Lấy nội dung từ tin nhắn của người chơi
    user_message = " ".join(user_input[1:])
    # Gửi thông báo cập nhật thành công cho người chơi kèm theo nội dung
    notification_message = f"""
🫥Bạn Đã Nạp Tiền Thành Công🤖
🫂SD Hiện Tại: {new_balance:,}đ🐥
👾Nội Dung: {user_message} 🫶🏽
🐝Chúc Bạn Chơi Game Vui Vẻ🐳
"""
    bot.send_message(user_id, notification_message)

    # Gửi thông báo đến nhóm về việc có người chơi đặt cược
    group_chat_id = -1002121532989  # Thay thế bằng ID thực sự của nhóm chat
    bot.send_message(chat_id=group_chat_id, text=notification_message
                     )  # Sử dụng notification_message thay cho result_message
  except ValueError:
    bot.reply_to(msg, "Vui lòng nhập một số tiền hợp lệ.")


markup = InlineKeyboardMarkup()
markup = InlineKeyboardMarkup()
tai_button = InlineKeyboardButton("🔄 Chơi Lại Tài Nha 🔄", callback_data="game_tai")
xiu_button = InlineKeyboardButton("🔄 Chơi Lại Xỉu Nha 🔄", callback_data="game_xiu")
markup.add(tai_button)
markup.add(xiu_button)

@bot.message_handler(func=lambda message: message.from_user.id in user_state
                     and user_state[message.from_user.id] in ["tai", "xiu"])
def bet_amount(msg):
  try:
    amount = int(msg.text)
    if amount <= 999:
      bot.reply_to(msg, "Số tiền cược phải lớn hơn 1000.")
      return

    # Kiểm tra số dư của người chơi trước khi đặt cược
    user_id = msg.from_user.id
    balance = user_balance.get(user_id, 0)
    if amount > balance:
      bot.reply_to(msg, "Số dư không đủ để đặt cược.")
      del user_state[user_id]  # Xoá trạng thái của người dùng
      return

    # Lưu trạng thái hiện tại của người chơi vào biến tạm thời
    current_state = user_state[user_id]

    # Trừ tiền cược ngay sau khi nhập số tiền
    user_balance[user_id] = balance - amount

    # Gửi 3 xúc xắc và tính tổng điểm
    dice_results = [send_dice_v1(msg.chat.id) for _ in range(3)]
    total_score = sum(dice_results)
    time.sleep(3)  # Delay 3s
    # Xác định kết quả Tài/Xỉu từ tổng điểm
    result_text = f"""
┏ ━ ━ ━ ━ ━ ━ ━ ━ ━ ━ ━
┣➤{' + '.join(str(x) for x in dice_results)}
┣➤Người Cược: {msg.from_user.id}
┣➤Tổng điểm: {total_score}
┣➤Kết quả: {calculate_tai_xiu(total_score)}
┣➤Bạn Cược: {current_state}"""
    # Thêm phần thời gian đánh vào kết quả với múi giờ Việt Nam
    vietnam_time = datetime.utcnow() + timedelta(hours=7)
    timestamp_vietnam = vietnam_time.strftime('%H:%M:%S')
    result_text += f"\n┣➤Thời gian: {timestamp_vietnam}"

    if current_state == "tai":
      if calculate_tai_xiu(total_score) == "Tài":
        win_amount = int(amount * 1.96)
        result_text += f"\n┣➤Bạn đã THẮNG! Với số tiền {win_amount:,} đ "
        user_balance[user_id] += win_amount  # Cộng tiền thắng vào số dư mới
      else:
        result_text += f"\n┣➤Bạn đã THUA! Số tiền {amount:,} đ"

    elif current_state == "xiu":
      if calculate_tai_xiu(total_score) == "Xỉu":
        win_amount = int(amount * 1.96)
        result_text += f"\n┣➤Bạn đã THẮNG! Với số tiền {win_amount:,}đ"
        user_balance[user_id] += win_amount  # Cộng tiền thắng vào số dư mới
      else:
        result_text += f"\n┣➤Bạn đã THUA! Số tiền {amount:,} đ"

    # Cập nhật số dư mới vào kết quả
    formatted_balance = "{:,.0f} đ".format(user_balance[user_id])
    result_text += f"\n┣➤Số dư mới của bạn: {formatted_balance}"

    if msg.from_user.id in user_state:
      del user_state[msg.from_user.id]
    else:
      print(f"User ID {user_id} không tìm thấy trong từ điển user_state.")

    result_text += "\n┗ ━ ━ ━ ━ ━ ━ ━ ━ ━ ━ ━"

    bet_info = (amount, calculate_tai_xiu(total_score), result_text)
    user_bet_history.setdefault(user_id, []).append(bet_info)
    save_balance_to_file()

    bot.send_message(chat_id=group_chat_id, text=result_text)
    bot.send_message(chat_id=msg.chat.id,
                     text=result_text,
                     reply_markup=markup)  # Use the previously defined markup
  except ValueError:
        bot.reply_to(msg, "Vui lòng nhập một số tiền hợp lệ\nBạn Hãy Nhập Số Tiền Để Dùng Lệnh Khác Nhé.")


# Define the inline keyboard markup
markup2 = InlineKeyboardMarkup()
tai2_button = InlineKeyboardButton("🔄 Chơi Lại Tài 10S Nha 🔄", callback_data="game_tai2")
xiu2_button = InlineKeyboardButton("🔄 Chơi Lại Xỉu 10S Nha 🔄", callback_data="game_xiu2")
markup2.add(tai2_button)
markup2.add(xiu2_button)

#hàm taixiu2
def send_result_with_delay(chat_id, result_text, delay_seconds,
                           countdown_message_id):
  end_time = datetime.now() + timedelta(seconds=delay_seconds)
  while datetime.now() < end_time:
    remaining_time = end_time - datetime.now()
    remaining_seconds = int(remaining_time.total_seconds())
    countdown_message = f"🪰Chờ Kết Quả Sau {remaining_seconds}...🧭"
    if countdown_message_id:
      bot.edit_message_text(chat_id=chat_id,
                            message_id=countdown_message_id,
                            text=countdown_message)
    else:
      sent_message = bot.send_message(chat_id=chat_id, text=countdown_message)
      countdown_message_id = sent_message.message_id
    time.sleep(1)
  bot.delete_message(chat_id=chat_id, message_id=countdown_message_id)
  bot.send_message(chat_id=chat_id,
                   text=result_text,
                   reply_markup=telebot.types.ReplyKeyboardRemove())


@bot.message_handler(func=lambda message: message.from_user.id in user_state
                     and user_state[message.from_user.id] in ["tai2", "xiu2"])
def bet_amount(msg):
  try:
    amount = int(msg.text)
    if amount <= 999:
      bot.reply_to(msg, "Số tiền cược phải lớn hơn 1000.")
      return

    user_id = msg.from_user.id
    balance = user_balance.get(user_id, 0)
    if amount > balance:
      bot.reply_to(msg, "Số dư không đủ để đặt cược.")
      del user_state[user_id]
      return

    current_state = user_state[user_id]
    user_balance[user_id] = balance - amount

    # Send countdown before the game result
    send_result_with_delay(msg.chat.id, "Chờ Kết Quả Và Lụm Tiền Nha", 10,
                           None)

    dice_results = [send_dice_v1(msg.chat.id) for _ in range(1)]
    total_score = sum(dice_results)
    # Wait for 2 second before sending the result
    time.sleep(2)
    # Construct result_text
    result_text = f"""
➡️{' + '.join(str(x) for x in dice_results)}⬅️
🔶Người Cược: {msg.from_user.id}
❗️Bạn Cược: {current_state}❓"""
    vietnam_time = datetime.utcnow() + timedelta(hours=7)
    timestamp_vietnam = vietnam_time.strftime('%H:%M:%S')
    result_text += f"\n🕐 Thời gian: {timestamp_vietnam}"

    if current_state == "tai2":
      if total_score in [1, 3, 5]:
        win_amount = int(amount * 1.96)
        result_text += f"\n✅ THẮNG! ➕{win_amount:,}đ 🔱"
        user_balance[user_id] += win_amount
      else:
        result_text += f"\n❌ THUA! ➖{amount:,}đ"

    elif current_state == "xiu2":
      if total_score in [2, 4, 6]:
        win_amount = int(amount * 1.96)
        result_text += f"\n✅ THẮNG! ➕ {win_amount:,}đ 🔱"
        user_balance[user_id] += win_amount
      else:
        result_text += f"\n❌ THUA! ➖ {amount:,}đ"

    formatted_balance = "{:,.0f} đ".format(user_balance[user_id])
    result_text += f"\n💲Số dư mới: {formatted_balance}"

    del user_state[user_id]

    bet_info = (amount, calculate_tai_xiu(total_score), result_text)
    user_bet_history.setdefault(user_id, []).append(bet_info)
    save_balance_to_file()

    bot.send_message(chat_id=group_chat_id, text=result_text)
    bot.send_message(chat_id=msg.chat.id,
                         text=result_text,
                         reply_markup=markup2)  # Use the previously defined markup
  except ValueError:
        bot.reply_to(msg, "Vui lòng nhập một số tiền hợp lệ\nBạn Hãy Nhập Số Tiền Để Dùng Lệnh Khác Nhé.")


# Define the inline keyboard markup
markup3 = InlineKeyboardMarkup()
chan_button = InlineKeyboardButton("🔄 Chơi Lại Chẳn Nha 🔄", callback_data="game_chan")
le_button = InlineKeyboardButton("🔄 Chơi Lại Lẻ Nha 🔄", callback_data="game_le")
markup3.add(chan_button)
markup3.add(le_button)
    
# Xử lý lệnh chẵn/lẻ
@bot.message_handler(func=lambda message: message.from_user.id in user_state
                     and user_state[message.from_user.id] in ["chan", "le"])
def bet_amount_chan_le(msg):
  try:
    amount = int(msg.text)
    if amount <= 999:
      bot.reply_to(msg, "Số tiền cược phải lớn hơn 1000.")
      return

    # Kiểm tra số dư của người chơi trước khi đặt cược
    user_id = msg.from_user.id
    balance = user_balance.get(user_id, 0)
    if amount > balance:
      bot.reply_to(msg, "Số dư không đủ để đặt cược.")
      del user_state[user_id]  # Xoá trạng thái của người dùng
      return

    # Trừ số dư của người chơi sau khi đặt cược
    user_balance[user_id] -= amount

    # Lưu trạng thái hiện tại của người chơi vào biến tạm thời
    current_state = user_state[msg.from_user.id]
    # Gửi 1 xúc xắc và tính tổng điểm
    dice_results = [send_dice_v1(msg.chat.id) for _ in range(1)]
    time.sleep(3)  # Delay 3s
    # Kiểm tra người chơi đánh và kết quả thắng thua
    check_winner_chan_le(user_id, current_state, amount, dice_results)

    # Xóa trạng thái của người chơi sau khi cược thành công
    del user_state[msg.from_user.id]

  except ValueError:
        bot.reply_to(msg, "Vui lòng nhập một số tiền hợp lệ\nBạn Hãy Nhập Số Tiền Để Dùng Lệnh Khác Nhé.")


# Hàm kiểm tra người chơi đánh và kết quả thắng/thua
def check_winner_chan_le(user_id, current_state, amount, dice_results):
  total_score = sum(dice_results)
  result_text = f"""
┏ ━ ━ ━ ━ ━ ━ ━ ━ ━ ━ ━ 
┣➤Xúc xắc: {' - '.join(str(x) for x in dice_results)}
┣➤Tổng điểm: {total_score}
┣➤Kết quả: {chan_le_result(total_score)}
┣➤Bạn Cược: {current_state}
┣➤Người Cược: {user_id}
"""
  # Thêm phần thời gian đánh vào kết quả với múi giờ Việt Nam
  vietnam_time = datetime.utcnow() + timedelta(hours=7)
  timestamp_vietnam = vietnam_time.strftime('%H:%M:%S')
  result_text += f"┣➤Thời gian: {timestamp_vietnam}\n"

  if current_state == "chan":
    if chan_le_result(total_score) == "Chẵn":
      win_amount = int(amount * 1.96)
      result_text += f"┣➤Bạn đã THẮNG! Với số tiền {win_amount:,} đ"
      user_balance.setdefault(user_id, 0)
      user_balance[user_id] += win_amount
    else:
      result_text += f"┣➤Bạn đã THUA! Số tiền {amount:,} đ"

  elif current_state == "le":
    if chan_le_result(total_score) == "Lẻ":
      win_amount = int(amount * 1.96)
      result_text += f"┣➤Bạn đã THẮNG! Với số tiền {win_amount:,} đ"
      user_balance.setdefault(user_id, 0)
      user_balance[user_id] += win_amount
    else:
      result_text += f"┣➤Bạn đã THUA! Số tiền {amount:,} đ"

  # Cập nhật số dư mới vào kết quả
  formatted_balance = "{:,.0f} đ".format(user_balance[user_id])
  result_text += f"\n┣➤Số dư mới của bạn: {formatted_balance}"

  # Lưu lịch sử cược của người dùng
  bet_info = (amount, chan_le_result(total_score), result_text)
  user_bet_history.setdefault(user_id, []).append(bet_info)
  result_text += "\n┗ ━ ━ ━ ━ ━ ━ ━ ━ ━ ━ ━ "

  # Save the updated balance to the file 
  save_balance_to_file()

  # Gửi thông báo đến nhóm và người chơi
  bot.send_message(chat_id=group_chat_id, text=result_text)
  bot.send_message(chat_id=user_id,
                     text=result_text,
                     reply_markup=markup3)


# Define the inline keyboard markup
markup4 = InlineKeyboardMarkup()
baucua_button = InlineKeyboardButton("🔄 Chơi Lại Bầu Cua Nha 🔄", callback_data="game_baucua")
markup4.add(baucua_button)

# Bầu Cua constants
BAU_CUA_ITEMS = ["🏮", "🦀", "🦐", "🐟", "🐓", "🦌"]
# Create a list of image URLs corresponding to the emoji items
IMAGE_LINKS = [
    "https://scontent.fdad1-3.fna.fbcdn.net/v/t39.30808-6/369199727_306111892083065_3387114729970252090_n.jpg?_nc_cat=110&ccb=1-7&_nc_sid=730e14&_nc_ohc=f6rh_3zQ6rQAX9NhLW5&_nc_ht=scontent.fdad1-3.fna&oh=00_AfAgkh0BsmZ6S5LLhbGxq-fvs6v8qU0S9eQgXB1nJtrF2Q&oe=64E9AD31",
    "https://scontent.fdad1-2.fna.fbcdn.net/v/t39.30808-6/368970597_306111898749731_6902532191138492204_n.jpg?_nc_cat=106&ccb=1-7&_nc_sid=730e14&_nc_ohc=kWV5-CylLXMAX8ghj_e&_nc_ht=scontent.fdad1-2.fna&oh=00_AfCoVKuZXlK_wQ0g4yXG_U5lXOwUk10jTflhoUmFbF2zQw&oe=64E8BFC9",
    "https://scontent.fdad1-3.fna.fbcdn.net/v/t39.30808-6/369841885_306111918749729_1843749234764034129_n.jpg?_nc_cat=110&ccb=1-7&_nc_sid=730e14&_nc_ohc=uGx31heuQ5EAX852zGn&_nc_ht=scontent.fdad1-3.fna&oh=00_AfBaGdDIW0rjbaQ5KbYRupeDqlgxyowPSMKzvAZZ2um4Cw&oe=64EA518B",
    "https://scontent.fdad1-1.fna.fbcdn.net/v/t39.30808-6/369934944_306112018749719_5689229993382906699_n.jpg?_nc_cat=109&ccb=1-7&_nc_sid=730e14&_nc_ohc=9KdefW_OgpgAX-MqTAC&_nc_ht=scontent.fdad1-1.fna&oh=00_AfATUzokMrBqPS5u-y7xjnWQvmHjMz8_DiIPCtbRO8Cg7Q&oe=64E9C897",
    "https://scontent.fdad1-2.fna.fbcdn.net/v/t39.30808-6/369354981_306111908749730_8117070445322876046_n.jpg?_nc_cat=102&ccb=1-7&_nc_sid=730e14&_nc_ohc=S_2z635kpKkAX_i2XIM&_nc_ht=scontent.fdad1-2.fna&oh=00_AfC0gdnXIRepVXKA3FRaWzkaPXPE_WjvZ6I6ANzRrzlykg&oe=64E98F0C",
    "https://scontent.fdad1-3.fna.fbcdn.net/v/t39.30808-6/368889201_306111895416398_2375835725904749300_n.jpg?_nc_cat=110&ccb=1-7&_nc_sid=730e14&_nc_ohc=DUYK5eOIH50AX-zLIIA&_nc_ht=scontent.fdad1-3.fna&oh=00_AfDLS4FfkrsJkT7pvKDLSTSadb-Xlm4mofDiAjEPQ-tRuQ&oe=64E988AE"
]


# hàm xử lý lệnh 3 con
def roll_bau_cua_dice():
  return random.choices(IMAGE_LINKS, k=3)


@bot.message_handler(
    func=lambda message: message.from_user.id in user_state and user_state[
        message.from_user.id] == "baucua_bet_amount")
def process_baucua_bet_amount(msg):
  try:
    bet_amount = int(msg.text)
    if bet_amount <= 999:
      bot.reply_to(msg, "Số tiền cược phải lớn hơn 1000.")
      return

    user_id = msg.from_user.id
    balance = user_balance.get(user_id, 0)

    # Check if the user has enough balance for the bet
    if bet_amount > balance:
      bot.reply_to(msg, "Số dư của bạn không đủ để đặt cược.")
      del user_state[user_id]
      return

    # Save the current state of the user and store the bet amount
    user_state[user_id] = ("baucua_bet_item", bet_amount)
    user_balance[user_id] -= bet_amount

    # Ask the user to choose an item to bet on using buttons
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True,
                                               one_time_keyboard=True)
    for i, item in enumerate(BAU_CUA_ITEMS):
      markup.add(f"{i + 1}")

    bot.reply_to(msg,
                 """
Bạn muốn cược cho con gì?.
(Nhập số từ 1 đến 6).
"1🏮", "2🦀", "3🦐", "4🐟", "5🐓", "6🦌"
        """,
                 reply_markup=markup)

  except ValueError:
    bot.reply_to(msg, "Vui lòng nhập số tiền hợp lệ.")


@bot.message_handler(
    func=lambda message: message.from_user.id in user_state and user_state[
        message.from_user.id][0] == "baucua_bet_item")
def process_baucua_bet_item(msg):
  try:
    user_id = msg.from_user.id
    chosen_item_index = int(msg.text) - 1
    bet_amount = user_state[user_id][1]
    chosen_item = IMAGE_LINKS[chosen_item_index]

    # Roll the Bầu Cua dice
    dice_results = roll_bau_cua_dice()
    result_text = " ".join(dice_results)

    # Send the corresponding images as the game result in a single horizontal row
    for item_link in dice_results:
      bot.send_photo(chat_id=msg.chat.id, photo=item_link)

    # Calculate and send the game result and reward
    win_amount = 0
    for item in dice_results:
      if item == chosen_item:
        win_amount += bet_amount * 1.9

    if win_amount > 0:
      result_message = f"""
┏ ━ ━ ━ ━ ━ ━ ━ ━ ━ ━ 
┣➤Người Cược: {msg.from_user.id}
┣➤Bạn đã THẮNG!
┣➤Nhận lại: {win_amount:,.0f} đ
┣➤/baucua Chơi Lại Nha!
┗ ━ ━ ━ ━ ━ ━ ━ ━ ━ ━
"""
    else:
      result_message = f"""
┏ ━ ━ ━ ━ ━ ━  ━ ━ ━ ━
┣➤Người Cược: {msg.from_user.id}
┣➤Bạn đã THUA!
┣➤Số tiền cược: {bet_amount:,.0f} đ
┣➤/baucua Chơi Lại Nha!
┗ ━ ━ ━ ━ ━ ━ ━ ━ ━ ━
"""

    # Update the user's balance based on the game outcome
    user_balance[user_id] += win_amount

    formatted_balance = "{:,.0f} đ".format(user_balance[user_id])
    result_message += f"┣➤Số dư mới của bạn: {formatted_balance}"

    # Gửi thông báo đến nhóm về việc có người chơi đặt cược
    group_chat_id = -1002121532989  # Replace with the actual group chat ID
    bot.send_message(chat_id=group_chat_id, text=result_message)

    # Remove the user state
    del user_state[user_id]
    bot.send_message(user_id, result_message, reply_markup=markup4)

    # Save the updated balance to the file
    save_balance_to_file()

  except (ValueError, IndexError):
    bot.reply_to(msg,
                 "Vui lòng chọn một số từ 1 đến 6 để cược cho con tương ứng.")


# Hàm ghi số dư của người chơi
def write_balance(user_id, new_balance):
  user_balance[user_id] = new_balance


#HÀM CHẲN LẺ
def calculate_result(score):
  if score == 0:
    return "⚪️-⚪️-⚪️-⚪️"
  elif score == 1:
    return "⚪️-⚪️-⚪️-🔴"
  elif score == 2:
    # Thay đổi cơ hội thắng ở trường hợp này
    if random.random() < 0.02:  # Chỉ có 1% cơ hội thắng
      return "⚪️-⚪️-🔴-🔴"
    else:
      return "⚪️-⚪️-⚪️-🔴"
  elif score == 3:
    # Thay đổi cơ hội thắng ở trường hợp này
    if random.random() < 0.02:  # Chỉ có 5% cơ hội thắng
      return "⚪️-🔴-🔴-🔴"
    else:
      return "⚪️-⚪️-🔴-🔴"
  else:
    # Thay đổi cơ hội thắng ở trường hợp này
    if random.random() < 0.02:  # Chỉ có 1% cơ hội thắng
      return "🔴-🔴-🔴-🔴"
    else:
      return "⚪️-🔴-🔴-🔴"


# Define the inline keyboard markup
markup5 = InlineKeyboardMarkup()
chan2_button = InlineKeyboardButton("🔄 Chơi Lại Chẳn Quân Vị 🔄", callback_data="game_chan2")
le2_button = InlineKeyboardButton("🔄 Chơi Lại Lẻ Quân Vị 🔄", callback_data="game_le2")
markup5.add(chan2_button)
markup5.add(le2_button)

@bot.message_handler(func=lambda message: message.from_user.id in user_state
                     and user_state[message.from_user.id] in ["chan2", "le2"])
def bet_amount_chan2_le2(msg):
  try:
    amount = int(msg.text)
    if amount <= 999:
      bot.reply_to(msg, "Số tiền cược phải lớn hơn 1000.")
      return

    user_id = msg.from_user.id
    balance = user_balance.get(user_id, 0)
    if amount > balance:
      bot.reply_to(msg, "Số dư không đủ để đặt cược.")
      del user_state[user_id]
      return

    current_state = user_state[user_id]
    user_balance[user_id] = balance - amount

    if current_state == "chan2":
      total_score = 2
    else:
      total_score = 3

    dice_result = calculate_result(total_score)

    check_winner_chan2_le2(user_id, current_state, amount, dice_result)

    del user_state[user_id]

  except ValueError:
        bot.reply_to(msg, "Vui lòng nhập một số tiền hợp lệ\nBạn Hãy Nhập Số Tiền Để Dùng Lệnh Khác Nhé.")


# Updated check_winner_chan2_le2 function
def check_winner_chan2_le2(user_id, current_state, amount, dice_result):
  result_text = f"""
┏ ━ ━ ━ ━ ━ ━ ━ ━ ━ ━ ━ 
┣➤Kết quả: {dice_result}
┣➤Người Chơi: {user_id}
┣➤Bạn Cược: {current_state}"""

  vietnam_time = datetime.utcnow() + timedelta(hours=7)
  timestamp_vietnam = vietnam_time.strftime('%H:%M:%S')
  result_text += f"\n┣➤Thời gian: {timestamp_vietnam}"

  if current_state == "le2":
    if dice_result.count("🔴") == 1 or dice_result.count("🔴") == 3:
      win_amount = amount * 1.96
      result_text += f"\n┣➤Bạn đã THẮNG! Với số tiền {win_amount:,} đ "
      user_balance[user_id] += win_amount
    else:
      result_text += f"\n┣➤Bạn đã THUA! Số tiền {amount:,} đ"

  elif current_state == "chan2":
    if (dice_result.count("🔴") == 2 and dice_result.count("⚪️") == 2) or \
       (dice_result.count("🔴") == 4 or dice_result.count("⚪️") == 4):
      win_amount = amount * 1.96
      result_text += f"\n┣➤Bạn đã THẮNG! Với số tiền {win_amount:,} đ"
      user_balance[user_id] += win_amount
    else:
      result_text += f"\n┣➤Bạn đã THUA! Số tiền {amount:,} đ"

  formatted_balance = "{:,.0f} đ".format(user_balance[user_id])
  result_text += f"\n┣➤Số dư mới của bạn: {formatted_balance}"

  bet_info = (amount, result_text)
  user_bet_history.setdefault(user_id, []).append(bet_info)
  result_text += "\n┗ ━ ━ ━ ━ ━ ━ ━ ━ ━ ━ ━ "
  bot.send_message(chat_id=group_chat_id, text=result_text)
  save_balance_to_file()
  bot.send_message(chat_id=user_id,
                     text=result_text,
                     reply_markup=markup5)


# Function to send a dice emoji
def send_dice_v2(chat_id):
  response = requests.get(
      f'https://api.telegram.org/bot{API_KEY}/sendDice?chat_id={chat_id}&emoji=🎰'
  )
  if response.status_code == 200:
    data = response.json()
    if 'result' in data and 'dice' in data['result']:
      return data['result']['dice']['value']
  return None


@bot.message_handler(commands=['slot'])
def slot_game(message):
  chat_id = message.chat.id
  markup = InlineKeyboardMarkup()
  slot_button = InlineKeyboardButton("🎰 Quay Nổ Hũ 🎰",
                                     callback_data="game_slot")
  markup.add(slot_button)
  bot.send_message(chat_id, "Chơi trò chơi Slot?", reply_markup=markup)


#hàm xử lý game slot
@bot.callback_query_handler(func=lambda call: call.data == "game_slot")
def callback_slot(call):
  chat_id = call.message.chat.id
  user_id = call.from_user.id  # Get the user's ID from the callback

  if chat_id not in user_balance:
    user_balance[chat_id] = 0  # Initialize balance for new users

  if user_balance[chat_id] < 1000:
    bot.answer_callback_query(call.id,
                              text="Bạn không có đủ tiền để đặt cược.")
    return

  user_balance[chat_id] -= 1000  # Deduct 1000 units from balance for the bet
  user_state[chat_id] = "slot"  # Set game state

  markup = InlineKeyboardMarkup()
  slot_button = InlineKeyboardButton("Quay lại Slot",
                                     callback_data="game_slot")
  markup.add(slot_button)

  bot.send_message(chat_id,
                   """
🎛 Game Quay Nổ Hũ  🪙
⚖️ Khi BOT trả lời mới được tính là đã đặt cược thành công
⚖️ Nếu BOT không trả lời => Lượt chơi không hợp lệ và không bị trừ tiền trong tài khoản.
⚖️ Kết quả được api telegram tạo ra, Nói không với chỉnh điểm số.
Xanh Chính Nhanh Chống Nên Mn An Tâm Gõ Nhé.
📌 Thể lệ:
Nếu Kết Quả Là : 64_43_22_1 Là Bạn Thắng.
Phí Cược Mỗi Lần 1k
🎖Trả Thưởng Như Sau :(x3 lần)
🏅 64: 33.333k (7 x3)
🥇 43: 17.777k (Lemon x3)
🥈 22: 17.777k (Grape x3)
🥉 1: 22.222k (Bar x3)
🎰 Đang Quay Số Chờ 2s Để Nhận Kết Quả...
""",
                   reply_markup=None)

  dice_value = send_dice_v2(chat_id)
  time.sleep(1)  # Adding a 2-second delay

  if chat_id in user_state:
    del user_state[chat_id]  # Clear game state if exists

  if dice_value is not None:
    result_message = f"🎱 Số Kết Quả {dice_value}!\nNgười Chơi: {user_id}"  # Include user's ID

    if dice_value == 64:  # Adjust win rate for 64
      win_amount = 33333  # 5 times the bet amount
      result_message += f"\n🏆 Chúc Mừng Bạn Đã THẮNG 🏆 {win_amount}!"
      user_balance[chat_id] += win_amount
    elif dice_value == 43:  # Adjust win rate for 43
      win_amount = 17777  # 3 times the bet amount
      result_message += f"\n🏆 Chúc Mừng Bạn Đã THẮNG 🏆 {win_amount}!"
      user_balance[chat_id] += win_amount
    elif dice_value == 22:  # Adjust win rate for 22
      win_amount = 17777  # 3 times the bet amount
      result_message += f"\n🏆 Chúc Mừng Bạn Đã THẮNG 🏆 {win_amount}!"
      user_balance[chat_id] += win_amount
    elif dice_value == 1:  # Adjust win rate for 1
      win_amount = 22222  # 3 times the bet amount
      result_message += f"\n🏆 Chúc Mừng Bạn Đã THẮNG 🏆 {win_amount}!"
      user_balance[chat_id] += win_amount
    else:
      result_message += "\n👉🏿 Ôi Nâu Kết Quả Đã THUA 👈🏿"

    # Gửi thông báo đến nhóm
    time.sleep(
        2)  # Add a delay of 2 seconds before sending the message to the group
    bot.send_message(chat_id=group_chat_id, text=result_message)
    save_balance_to_file()  # Save user balances

    result_message += f"\n💸 Số Dư Mới: {user_balance[chat_id]}"
    markup = InlineKeyboardMarkup()
    slot_button = InlineKeyboardButton("🔄 Chơi Lại Nha 🔄",
                                       callback_data="game_slot")
    markup.add(slot_button)
    bot.send_message(chat_id, result_message, reply_markup=markup)


# Hàm hiển thị menu chính
@bot.message_handler(commands=["start"])
def show_main_menu(msg):
  user_id = msg.from_user.id

  # Check if the user is already in the user_balance dictionary
  if user_id not in user_balance:
    user_balance[user_id] = 0  # Set initial balance to 0 for new users
    save_balance_to_file()  # Save user balances to the text file

  markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
  rows = [
      ["👤 Tài Khoản", "🎲 Danh Sách Game"],
      ["💸 Rút Tiền", "💵 Nạp Tiền"],
      ["📈 Lịch Sử Cược", "📊 Lịch Sử Rút"],
      ["📤Chuyển Tiền📪", "🫧Nhập CODE💶"],
  ]

  for row in rows:
    markup.row(*[types.KeyboardButton(button_text) for button_text in row])

  # Send a message with a photo link
  photo_url = "https://gamebaidoithuong.zone/wp-content/uploads/2021/12/game-bai-doi-thuong-gamebaidoithuongzone-3.jpg"
  caption = """
<b>Chào Mừng Bạn Đã Đến Với Sân Chơi Giải Trí</b>
      <code>𝐕𝐈𝐒𝐓𝐎𝐑𝐘_𝐒𝐚̂𝐧 𝐂𝐡𝐨̛𝐢 𝐂𝐋𝐓𝐗</code>
<b>Game Xanh Chính Nói Không Với Chỉnh Cầu</b>

👉 <strong>Cách chơi đơn giản, tiện lợi</strong> 🎁

👉 <b>Nạp rút nhanh chóng, đa dạng hình thức</b> 💸

👉 <b>Có Nhiều Phần Quà Dành Cho Người Chơi Mới</b> 🤝

👉 <b>Đua top thật hăng, nhận quà cực căng</b> 💍

👉 <b>An toàn, bảo mật tuyệt đối</b> 🏆

⚠️ <b>Chú ý đề phòng lừa đảo, Chúng Tôi Không ibonx Trước</b> ⚠️
"""
  bot.send_photo(msg.chat.id,
                 photo_url,
                 caption=caption,
                 reply_markup=markup,
                 parse_mode='HTML')


# Hàm xử lý khi người dùng chọn nút
@bot.message_handler(func=lambda message: message.text == "👤 Tài Khoản")
#@bot.message_handler(commands=["diem"])
def handle_check_balance_button(msg):
  load_balance_from_file()
  check_balance(msg)

@bot.message_handler(func=lambda message: message.text == "💸 Rút Tiền")
def handle_withdraw_balance_button(msg):
  withdraw_balance(msg)

@bot.message_handler(func=lambda message: message.text == "🎲 Danh Sách Game")
def handle_game_list_button(msg):
  show_game_options(msg)

@bot.message_handler(func=lambda message: message.text == "💵 Nạp Tiền")
def handle_deposit_button(msg):
  deposit_info(msg)

@bot.message_handler(func=lambda message: message.text == "📈 Lịch Sử Cược")
def handle_bet_history_button(msg):
  show_bet_history(msg)

@bot.message_handler(func=lambda message: message.text == "📊 Lịch Sử Rút")
def handle_withdraw_history_button(msg):
  show_withdraw_history(msg)

@bot.message_handler(func=lambda message: message.text == "📤Chuyển Tiền📪")
def handle_chuyentien_money_button(msg):
    chuyentien_money(msg)

@bot.message_handler(func=lambda message: message.text == "🫧Nhập CODE💶")
def handle_naptien_gitcode_button(msg):
    naptien_gitcode(msg)

# Hàm kiểm tra số dư
def check_balance(msg):
    user_id = msg.from_user.id
    balance = user_balance.get(user_id, 0)
    bot.send_message(msg.from_user.id, f"👤 Số điểm của {msg.from_user.first_name} là {balance:,} điểm 💰")
  #photo_link = "https://scontent.fdad1-4.fna.fbcdn.net/v/t39.30808-6/374564260_311252494902338_4501893302206805342_n.jpg?_nc_cat=103&ccb=1-7&_nc_sid=49d041&_nc_ohc=ypCR3gJKO84AX8vBaGO&_nc_oc=AQkV2yigf-t0BVkyWvCT0B1QFbLFdXx-cDg9Lal65LdSPI_AvgJdmKKS0ZpvItzfP3rlfqLxFP3pFitVvMbCHjGI&_nc_ht=scontent.fdad1-4.fna&oh=00_AfCW5YKUPRq6IRYMDCqhbPKQYFlUoIbVsuCjDAmzsr50VA&oe=64F55781"  # Thay thế bằng đường dẫn URL của hình ảnh
  #bot.send_photo(msg.chat.id,
  #               photo_link,
  #               caption=f"""
#👤 <b>Tên tài khoản</b>: <code>{msg.from_user.first_name}</code>
#💳 <b>ID Tài khoản</b>: <code>{msg.from_user.id}</code>
#💰 <b>Số dư của bạn</b>: {balance:,} đ
#        """,
#                 parse_mode='HTML')


#hàm rút tiền
def create_withdraw_method_keyboard():
  markup = InlineKeyboardMarkup()
  momo_button = InlineKeyboardButton("Rút qua MoMo", callback_data="momo")
  bank_button = InlineKeyboardButton("Rút qua ngân hàng", callback_data="bank")
  markup.row(momo_button, bank_button)  # Đặt cả hai nút trên cùng một hàng
  return markup


# Hàm rút tiền tài khoản
def withdraw_balance(msg):
  user_id = msg.from_user.id
  user_state[user_id] = "withdraw_method"
  user_game_state.pop(user_id, None)  # Clear game state to avoid conflicts

  reply_markup = create_withdraw_method_keyboard(
  )  # Tạo bàn phím cho phương thức rút
  bot.send_message(user_id,
                   "Chọn phương thức rút tiền:",
                   reply_markup=reply_markup)


@bot.callback_query_handler(func=lambda call: call.data in ["momo", "bank"])
def handle_withdrawal_method_selection(call):
  user_id = call.from_user.id

  if call.data == "momo":
    user_state[user_id] = "momo_account"
    bot.send_message(user_id, "Nhập số MoMo của bạn:")
  elif call.data == "bank":
    user_state[user_id] = "bank_account"
    bot.send_message(
        user_id, """
Nhập thông tin tài khoản ngân hàng của bạn:
VD: 0987654321 VCB 
 TÊN NGÂN HÀNG - MÃ NGÂN HÀNG
📌 Vietcombank => VCB
📌 BIDV => BIDV 
📌 Vietinbank => VTB
📌 Techcombank => TCB
📌 MB Bank => MBB 
📌 Agribank => AGR 
📌 TienPhong Bank => TPB
📌 SHB bank => SHB
📌 ACB => ACB 
📌 Maritime Bank => MSB
📌 VIB => VIB
📌 Sacombank => STB
📌 VP Bank => VPB
📌 SeaBank => SEAB
📌 Shinhan bank Việt Nam => SHBVN
📌 Eximbank => EIB 
📌 KienLong Bank => KLB 
📌 Dong A Bank => DAB 
📌 HD Bank => HDB 
📌 LienVietPostBank => LPB 
📌 VietBank => VBB
📌 ABBANK => ABB 
📌 PG Bank => PGB
📌 PVComBank => PVC
📌 Bac A Bank => BAB 
📌 Sai Gon Commercial Bank => SCB
📌 BanVietBank => VCCB 
📌 Saigonbank => SGB
📌 Bao Viet Bank => BVB  
📌 Orient Commercial Bank => OCB 

⚠️ Lưu ý: ❌ Không hỗ trợ hoàn tiền nếu bạn nhập sai thông tin Tài khoản. 
❗️ Rút min 50K
""")

  bot.answer_callback_query(call.id, "Bạn đã chọn phương thức rút tiền.")


@bot.message_handler(
    func=lambda message: message.from_user.id in user_state and user_state[
        message.from_user.id] in ["momo_account", "bank_account"])
def process_account_info(msg):
  try:
    account_info = msg.text
    user_id = msg.from_user.id

    if user_state[user_id] == "momo_account":
      user_state[user_id] = (account_info, "withdraw_amount_momo")
      bot.reply_to(
          msg, """
❗️Nhập số tiền bạn muốn rút qua MoMo💮
🚫VD: 50.000 - 50.000.000🚮
            """)
    elif user_state[user_id] == "bank_account":
      user_state[user_id] = (account_info, "withdraw_amount_bank")
      bot.reply_to(
          msg, """
❗️Nhập số tiền bạn muốn rút qua ngân hàng💮
🚫VD: 50.000 - 50.000.000🚮
            """)

  except ValueError:
    pass


@bot.message_handler(func=lambda message: message.from_user.id in user_state
                     and user_state[message.from_user.id][1] in
                     ["withdraw_amount_momo", "withdraw_amount_bank"])
def process_withdraw_amount(msg):
  try:
    account_info, withdraw_amount_type = user_state[msg.from_user.id]
    withdraw_amount = int(msg.text)
    user_id = msg.from_user.id
    user_balance_value = user_balance.get(user_id, 0)

    if withdraw_amount < 50000:
      bot.reply_to(
          msg, """
🖇 Số tiền rút phải lớn hơn hoặc bằng 50,000 đồng.🗳
            """)
      del user_state[user_id]
      return

    if withdraw_amount > user_balance_value:
      bot.reply_to(
          msg, """
🌀Số dư của bạn không đủ💳
🪫Vui Lòng 🔎/naptiep🔍 Có Số Dư Mới💎
            """)
      del user_state[user_id]
      return

    # Trừ số tiền từ số dư của người chơi
    user_balance_value -= withdraw_amount
    user_balance[user_id] = user_balance_value

    with open("id.txt", "r") as f:
      lines = f.readlines()

    with open("id.txt", "w") as f:
      for line in lines:
        user_id_str, balance_str = line.strip().split()
        if int(user_id_str) == user_id:
          balance = int(balance_str)
          if withdraw_amount <= balance:
            balance -= withdraw_amount
            f.write(f"{user_id} {balance}\n")
          else:
            bot.reply_to(msg, "Số dư không đủ để rút số tiền này.")
        else:
          f.write(line)

    formatted_balance = "{:,.0f} đ".format(user_balance_value)
    account_type = "MoMo" if withdraw_amount_type == "withdraw_amount_momo" else "ngân hàng"
    bot.reply_to(
        msg, f"""
⏺Lệnh rút: {withdraw_amount:,} VNĐ🔚
✅Của bạn về {account_type}: {account_info} được hệ thống check🔚
☢️Số tiền còn lại của bạn: {formatted_balance}
            """)

    request_message = f"""
➤Tên Người Rút: {msg.from_user.first_name} 
➤Yêu Cầu Rút: {withdraw_amount:,} VNĐ 
➤Về {account_type}: {account_info}
        """
    another_bot_token = "6755926001:AAGD0Gc9xMomJgnfhwjeIENF9XO0reeST1o"
    another_bot_chat_id = "6337933296"
    requests.get(
        f"https://api.telegram.org/bot{another_bot_token}/sendMessage?chat_id={another_bot_chat_id}&text={request_message}"
    )

    del user_state[user_id]

    user_withdraw_history.setdefault(user_id, []).append(
        (account_info, withdraw_amount))
    time.sleep(10)
    user_notification = f"""
📬 Rút tiền thành công!
⏺ Số tiền rút: {withdraw_amount:,} VNĐ
📈 Số dư còn lại: {formatted_balance}
        """
    bot.send_message(user_id, user_notification)

  except ValueError:
    pass


# Hàm hiển thị danh sách game
def show_game_options(msg):
  # Replace 'https://example.com/image_link.png' with the actual image link
  photo_link = 'https://scontent.fdad2-1.fna.fbcdn.net/v/t39.30808-6/365194258_254046207437295_6572100925029769094_n.jpg?_nc_cat=108&ccb=1-7&_nc_sid=730e14&_nc_ohc=ph-GKBaIAOAAX8D2f6F&_nc_ht=scontent.fdad2-1.fna&oh=00_AfCRKYNL5z_2j97Uh1P2bdL3A2Z6Zy3rnvjGN6cIiTA4Vg&oe=64D4C9B7'

  # Send the photo with the caption
  bot.send_photo(msg.chat.id,
                 photo_link,
                 caption="""
<b>𝐕𝐈𝐒𝐓𝐎𝐑𝐘_𝐒𝐚̂𝐧 𝐂𝐡𝐨̛𝐢 𝐂𝐋𝐓𝐗</b>
<b>♻️Hãy Chọn Các Game Phía Dưới Nhé♻️</b>
        """,
                 reply_markup=create_game_options(),
                 parse_mode='HTML')


# Hàm lệnh nạp tiền
def deposit_info(msg):
  user_id = msg.from_user.id
  momo_account = "0123456789"
  username = msg.from_user.username or msg.from_user.first_name

  #photo_link = "https://scontent.fdad1-3.fna.fbcdn.net/v/t39.30808-6/368953112_304417105585877_8104665371433145272_n.jpg?_nc_cat=104&ccb=1-7&_nc_sid=730e14&_nc_ohc=9tNmHpvwO7UAX97Ml6f&_nc_ht=scontent.fdad1-3.fna&oh=00_AfDCHSKEY4xF2TL3e4YhEjvP0kh4uVR_4cEPa_GyN5hzXA&oe=64E49255"  # Replace with the actual image link

  # Creating the caption
  caption = f"""
🏧<b>Phương Thức Nạp Bank</b>🏧
💰<b>MB BANK _ MOMO</b>💰
🔊Tài Khoản: <code>0123456789</code>🔚
🔊Nội Dung: <code>naptien_{msg.from_user.id}</code>🔚
🔊<b>Min Nạp: 10.000k Min Rút: 100.000k</b>
🔊<b>Min Nạp: 10.000 - 3.000.000</b>🔚
🔊<b>Vui lòng ghi đúng nội dung tiền vào 5s.</b>🔚
🔊<b>Không Hỗ Trợ Lỗi Nội Dung.</b>🔚
🔊<b>NẠP NHANH QR PHÍA BÊN DƯỚI NHÉ</b> 🔚
    """

  # Sending the caption and photo
  bot.send_message(msg.chat.id, caption, parse_mode='HTML')
  #bot.send_photo(msg.chat.id, photo_link)


# Hàm xem lịch sử cược
def show_bet_history(msg):
  user_id = msg.from_user.id
  bet_history = user_bet_history.get(user_id, [])
  if not bet_history:
    bot.reply_to(
        msg, """
⏩Bạn Vào @☑️.
⏩Để Kiểm Tra Lịch Sử Cược Nhé.
        """)
  else:
    history_text = "Lịch sử cược:\n\n"
    for bet_info in bet_history:
      if len(bet_info) == 3:
        amount, result, outcome = bet_info
        history_text += f"""
Số tiền: {amount}
Kết quả: {result}
Kết quả cuối cùng: {outcome}
                """
      else:
        history_text += "Dữ liệu lịch sử cược không hợp lệ.\n"
    bot.reply_to(msg, history_text)


# Hàm xem lịch sử rút tiền
def show_withdraw_history(msg):
  user_id = msg.from_user.id
  withdraw_history = user_withdraw_history.get(user_id, [])
  if not withdraw_history:
    bot.reply_to(
        msg, """
🚥Bạn chưa có lịch sử rút tiền🔙
🛰/ruttien - Lệnh rút tiền.
    """)
  else:
    history_text = """
Lịch sử rút tiền:
🎑🎑🎑🎑🎑🎑🎑
        """
    for withdraw_info in withdraw_history:
      momo_account, amount = withdraw_info
      history_text += f"""
🧑🏽‍💻Số Tiền Rút: {amount:,} VNĐ 
👑Số Momo: {momo_account}
"""
    bot.reply_to(msg, history_text)


# Function to create inline buttons for game options
def create_game_options():
  markup = telebot.types.InlineKeyboardMarkup(row_width=2)

  markup.add(
      telebot.types.InlineKeyboardButton("♨️ Game Tài 🎲",
                                         callback_data="game_tai"),
      telebot.types.InlineKeyboardButton("🏝 Game Xỉu 🎲",
                                         callback_data="game_xiu"))

  markup.add(
      telebot.types.InlineKeyboardButton("🏪 Tài 10S 🛶",
                                         callback_data="game_tai2"),
      telebot.types.InlineKeyboardButton("🪗 Xỉu 10S 💎",
                                         callback_data="game_xiu2"))

  markup.add(
      telebot.types.InlineKeyboardButton("🔴 Chẵn Quân Vị ⚪️",
                                         callback_data="game_chan2"),
      telebot.types.InlineKeyboardButton("⚪️ Lẻ Quân Vị 🔴",
                                         callback_data="game_le2"))

  markup.add(
      telebot.types.InlineKeyboardButton("🏵 Game Chẵn 💽",
                                         callback_data="game_chan"),
      telebot.types.InlineKeyboardButton("💮 Game Lẻ 🆗",
                                         callback_data="game_le"))

  markup.add(
      telebot.types.InlineKeyboardButton("🥁 Game Bầu Cua 🎭",
                                         callback_data="game_baucua"),
      telebot.types.InlineKeyboardButton("🎰 Quay Nổ Hũ 🎰",
                                         callback_data="game_slot"))
  markup.add(
      telebot.types.InlineKeyboardButton("🎱 Game Xổ Số 🎱",
                                         callback_data="game_xoso"))

  return markup


#@bot.message_handler(commands=["game"])
#def show_game_options(msg):
  # Replace 'https://example.com/image_link.png' with the actual image link
  #photo_link = 'https://scontent.fdad2-1.fna.fbcdn.net/v/t39.30808-6/365194258_254046207437295_6572100925029769094_n.jpg?_nc_cat=108&ccb=1-7&_nc_sid=730e14&_nc_ohc=ph-GKBaIAOAAX8D2f6F&_nc_ht=scontent.fdad2-1.fna&oh=00_AfCRKYNL5z_2j97Uh1P2bdL3A2Z6Zy3rnvjGN6cIiTA4Vg&oe=64D4C9B7'

  # Send the photo with the caption
  #bot.send_photo(msg.chat.id,
                 #photo_link,
                 #caption="""
#<b>𝐕𝐈𝐒𝐓𝐎𝐑𝐘_𝐒𝐚̂𝐧 𝐂𝐡𝐨̛𝐢 𝐂𝐋𝐓𝐗</b>
#<b>♻️Hãy Chọn Các Game Phía Dưới Nhé♻️</b>
        #""",
                 #reply_markup=create_game_options(),
                 #parse_mode='HTML')


# Modify the game_callback function to use Reply Keyboard
@bot.callback_query_handler(func=lambda call: call.data.startswith("game_"))
def game_callback(call):
  if call.data == "game_tai":
    user_state[call.from_user.id] = "tai"
    show_tai_bet_amount_options(call.from_user.id)
  elif call.data == "game_xiu":
    user_state[call.from_user.id] = "xiu"
    show_xiu_bet_amount_options(call.from_user.id)
  elif call.data == "game_tai2":
    user_state[call.from_user.id] = "tai2"
    show_tai2_bet_amount_options(call.from_user.id)
  elif call.data == "game_xiu2":
    user_state[call.from_user.id] = "xiu2"
    show_xiu2_bet_amount_options(call.from_user.id)
  elif call.data == "game_chan":
    user_state[call.from_user.id] = "chan"
    show_chan_bet_amount_options(call.from_user.id)
  elif call.data == "game_le":
    user_state[call.from_user.id] = "le"
    show_le_bet_amount_options(call.from_user.id)
  elif call.data == "game_chan2":
    user_state[call.from_user.id] = "chan2"
    show_chan2_bet_amount_options(call.from_user.id)
  elif call.data == "game_le2":
    user_state[call.from_user.id] = "le2"
    show_le2_bet_amount_options(call.from_user.id)
  elif call.data == "game_baucua":
    user_state[call.from_user.id] = "baucua_bet_amount"
    show_baucua_bet_amount_options(call.from_user.id)
  elif call.data == "game_slot":
    user_state[call.from_user.id] = "game_slot"
  elif call.data == "game_xoso":
    user_state[call.from_user.id] = "xoso"
    show_xoso_bet_amount_options(call.from_user.id)
    pass


def show_tai_bet_amount_options(user_id):
  # Create the Reply Keyboard with bet amount options
  markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True,
                                             one_time_keyboard=True)
  markup.add("1000", "5000", "10000", "20000", "50000", "100000", "200000",
             "500000", "1000000", "2000000", "3000000")

  bot.send_message(user_id,
                   """
<b>🎛 Game Tài 🪙
⚖️ Khi BOT trả lời mới được tính là đã đặt cược thành công
⚖️ Nếu BOT không trả lời => Lượt chơi không hợp lệ và không bị trừ tiền trong tài khoản.
⚖️ Kết quả được api telgram tạo ra, Nói không với chỉnh điểm số.
Xanh Chính Nhanh Chống Nên Mn An Tâm Gõ Nhé.
📌 Thể lệ:
📄 Kết quả Là +11 Là Tài. -11 Là Xỉu.
/tai ➤ x1.96 ➤ Kết Quả: 11-18 :Bạn Thắng.
HÃY NHẬN SỐ TIỀN BẠN MUỐN CƯỢC </b>
""",
                   reply_markup=markup,
                   parse_mode='HTML')


def show_xiu_bet_amount_options(user_id):
  # Create the Reply Keyboard with bet amount options
  markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True,
                                             one_time_keyboard=True)
  markup.add("1000", "5000", "10000", "20000", "50000", "100000", "200000",
             "500000", "1000000", "2000000", "3000000")

  bot.send_message(user_id,
                   """
<b>🎛 Game Xỉu 🪙
⚖️ Khi BOT trả lời mới được tính là đã đặt cược thành công
⚖️ Nếu BOT không trả lời => Lượt chơi không hợp lệ và không bị trừ tiền trong tài khoản.
⚖️ Kết quả được api telgram tạo ra, Nói không với chỉnh điểm số.
Xanh Chính Nhanh Chống Nên Mn An Tâm Gõ Nhé.
📌 Thể lệ:
📄 Kết quả Là +11 Là Tài. -11 Là Xỉu.
/xiu ➤ x1.96 ➤ Kết Quả: 3-10 :Bạn Thắng.
HÃY NHẬN SỐ TIỀN BẠN MUỐN CƯỢC </b>    
""",
                   reply_markup=markup,
                   parse_mode='HTML')


def show_tai2_bet_amount_options(user_id):
  # Create the Reply Keyboard with bet amount options
  markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True,
                                             one_time_keyboard=True)
  markup.add("1000", "5000", "10000", "20000", "50000", "100000", "200000",
             "500000", "1000000", "2000000", "3000000")

  bot.send_message(user_id,
                   """
<b>🎛 Game Tài 10S 🪙
⚖️ Khi BOT trả lời mới được tính là đã đặt cược thành công
⚖️ Nếu BOT không trả lời => Lượt chơi không hợp lệ và không bị trừ tiền trong tài khoản.
⚖️ Kết quả được api telgram tạo ra, Nói không với chỉnh điểm số.
Xanh Chính Nhanh Chống Nên Mn An Tâm Gõ Nhé.
📌 Thể lệ:
/tai2 ➤ x1.96 ➤ Kết Quả: 1-3-5 :Bạn Thắng.
HÃY NHẬN SỐ TIỀN BẠN MUỐN CƯỢC </b>
""",
                   reply_markup=markup,
                   parse_mode='HTML')


def show_xiu2_bet_amount_options(user_id):
  # Create the Reply Keyboard with bet amount options
  markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True,
                                             one_time_keyboard=True)
  markup.add("1000", "5000", "10000", "20000", "50000", "100000", "200000",
             "500000", "1000000", "2000000", "3000000")

  bot.send_message(user_id,
                   """
<b>🎛 Game Xỉu 10S 🪙
⚖️ Khi BOT trả lời mới được tính là đã đặt cược thành công
⚖️ Nếu BOT không trả lời => Lượt chơi không hợp lệ và không bị trừ tiền trong tài khoản.
⚖️ Kết quả được api telgram tạo ra, Nói không với chỉnh điểm số.
Xanh Chính Nhanh Chống Nên Mn An Tâm Gõ Nhé.
📌 Thể lệ:
/xiu2 ➤ x1.96 ➤ Kết Quả: 2-4-6 :Bạn Thắng.
HÃY NHẬN SỐ TIỀN BẠN MUỐN CƯỢC </b>    
""",
                   reply_markup=markup,
                   parse_mode='HTML')


def show_chan_bet_amount_options(user_id):
  # Create the Reply Keyboard with bet amount options
  markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True,
                                             one_time_keyboard=True)
  markup.add("1000", "5000", "10000", "20000", "50000", "100000", "200000",
             "500000", "1000000", "2000000", "3000000")

  bot.send_message(user_id,
                   """
<b>🎛 Game Chẳn 🪙
⚖️ Khi BOT trả lời mới được tính là đã đặt cược thành công
⚖️ Nếu BOT không trả lời => Lượt chơi không hợp lệ và không bị trừ tiền trong tài khoản.
⚖️ Kết quả được api telgram tạo ra, Nói không với chỉnh điểm số.
Xanh Chính Nhanh Chống Nên Mn An Tâm Gõ Nhé.
📌 Thể lệ:
📄 Kết quả Là 2-4-6 Chẳn, 1-3-5 Lẻ.
/chan ➤ x1.96 ➤ Kết Quả: 2-4-6 :Bạn Thắng.
HÃY NHẬN SỐ TIỀN BẠN MUỐN CƯỢC </b>    
""",
                   reply_markup=markup,
                   parse_mode='HTML')


def show_le_bet_amount_options(user_id):
  # Create the Reply Keyboard with bet amount options
  markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True,
                                             one_time_keyboard=True)
  markup.add("1000", "5000", "10000", "20000", "50000", "100000", "200000",
             "500000", "1000000", "2000000", "3000000")

  bot.send_message(user_id,
                   """
<b>🎛 Game Lẻ 🪙
⚖️ Khi BOT trả lời mới được tính là đã đặt cược thành công
⚖️ Nếu BOT không trả lời => Lượt chơi không hợp lệ và không bị trừ tiền trong tài khoản.
⚖️ Kết quả được api telgram tạo ra, Nói không với chỉnh điểm số.
Xanh Chính Nhanh Chống Nên Mn An Tâm Gõ Nhé.
📌 Thể lệ:
📄 Kết quả Là 2-4-6 Chẳn, 1-3-5 Lẻ.
/le ➤ x1.96 ➤ Kết Quả: 1-3-5 :Bạn Thắng.
HÃY NHẬN SỐ TIỀN BẠN MUỐN CƯỢC </b>    
""",
                   reply_markup=markup,
                   parse_mode='HTML')


def show_chan2_bet_amount_options(user_id):
  # Create the Reply Keyboard with bet amount options
  markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True,
                                             one_time_keyboard=True)
  markup.add("1000", "5000", "10000", "20000", "50000", "100000", "200000",
             "500000", "1000000", "2000000", "3000000")

  bot.send_message(user_id,
                   """
<b>🎛 Game Chẳn Quân Vị🪙
⚖️ Khi BOT trả lời mới được tính là đã đặt cược thành công
⚖️ Nếu BOT không trả lời => Lượt chơi không hợp lệ và không bị trừ tiền trong tài khoản.
⚖️ Kết quả được bot tạo ra, Nói không với chỉnh điểm số.
Xanh Chính Nhanh Chống Nên Mn An Tâm Gõ Nhé.
📌 Thể lệ:
📄 Kết quả
⚪️-⚪️-⚪️-⚪️__🔴-🔴-🔴-🔴__🔴-🔴-⚪️-⚪️ Là Chẳn.
/chan2 ➤ x1.96 ➤ Kết Quả: ⚪️-⚪️-⚪️-⚪️__🔴-🔴-🔴-🔴__🔴-🔴-⚪️-⚪️ :Bạn Thắng.
HÃY NHẬN SỐ TIỀN BẠN MUỐN CƯỢC </b>    
""",
                   reply_markup=markup,
                   parse_mode='HTML')


def show_le2_bet_amount_options(user_id):
  # Create the Reply Keyboard with bet amount options
  markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True,
                                             one_time_keyboard=True)
  markup.add("1000", "5000", "10000", "20000", "50000", "100000", "200000",
             "500000", "1000000", "2000000", "3000000")

  bot.send_message(user_id,
                   """
<b>🎛 Game Lẻ Quân Vị🪙
⚖️ Khi BOT trả lời mới được tính là đã đặt cược thành công
⚖️ Nếu BOT không trả lời => Lượt chơi không hợp lệ và không bị trừ tiền trong tài khoản.
⚖️ Kết quả được bot tạo ra, Nói không với chỉnh điểm số.
Xanh Chính Nhanh Chống Nên Mn An Tâm Gõ Nhé.
📌 Thể lệ:
📄 Kết quả
⚪️-⚪️-⚪️-🔴__🔴-🔴-🔴-⚪️ Là Lẻ.
/le2 ➤ x1.96 ➤ Kết Quả: ⚪️-⚪️-⚪️-🔴__🔴-🔴-🔴-⚪️ :Bạn Thắng.
HÃY NHẬN SỐ TIỀN BẠN MUỐN CƯỢC </b>    
""",
                   reply_markup=markup,
                   parse_mode='HTML')


def show_baucua_bet_amount_options(user_id):
  # Create the Reply Keyboard with bet amount options for Bầu Cua game
  markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True,
                                             one_time_keyboard=True)
  markup.add("1000", "5000", "10000", "20000", "50000", "100000", "200000",
             "500000", "1000000", "2000000", "3000000")

  bot.send_message(user_id,
                   """
<b>🎛 Game Bầu Cua 🪙
⚖️ Khi BOT trả lời mới được tính là đã đặt cược thành công
⚖️ Nếu BOT không trả lời => Lượt chơi không hợp lệ và không bị trừ tiền trong tài khoản.
⚖️ Kết quả được bot tạo random, Nói không với chỉnh.
Xanh Chính Nhanh Chống Nên Mn An Tâm Gõ Nhé.
📌 Thể lệ:
📄 Kết quả Là 6 con vật Random chọn 3 bot chọn Random.
/baucua ➤ x1.96 ➤ Kết Quả: Bầu-Bầu-Bầu :Bạn Chọn Bầu.Bạn Thắng.
Game này bạn chọn 1-6 con vật nếu trúng bạn thắng.
HÃY NHẬN SỐ TIỀN BẠN MUỐN CƯỢC </b>    
""",
                   reply_markup=markup,
                   parse_mode='HTML')


# Function to show Xoso bet amount options
def show_xoso_bet_amount_options(user_id):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    buttons = [
        "Lô 2 Số",
        "Lô 3 Số",
        "Lô 4 Số",
        "Xiên 2",
        "Xiên 3",
        "Xiên 4",
        "Đề 2 Số",
        "Đề 3 Số",
        "Đề 4 Số",
        "Đầu",
        "Đuôi"
    ]

    for button_text in buttons:
        button = types.KeyboardButton(button_text)
        markup.add(button)

    bot.send_message(user_id, """
💰 Lô Đề 

🔖 Đây là game dựa vào 2 số cuối các giải của Xổ Số Miền Bắc được quay vào lúc 18h30 hàng ngày!

➡️ Game Lô Đề - Tỷ Lệ Thắng 
Lô 2 Số 1x3,5
Lô 3 Số 1x42,3
Lô 4 Số 1x440
Xiên 2 1x12
Xiên 3 1x60
Xiên 4 1x165
Đề 2 Số 1x95
Đề 3 Số 1x960
Đề 4 Số 1x8800
Đầu 1x7
Đuôi 1x7
Chúc Bạn May Mắn Lụm Lúa Về Làng Nhé.
👉 Số tiền chơi tối thiểu là 6,000đ và tối đa là 1,000,000đ

🎮 Cách chơi: Chat tại đây theo cú pháp: 
Chọn Lô Xiên 2 Đề Ba Càng: Số Dự Đoán [dấu cách] Số Tiến Cược.
VD: Số Dự Đoán [dấu cách] Số Tiến Cược
""", reply_markup=markup)
  
#hàm xử lý lệnh xoso
def check_and_deduct_balance(user_id, bet_amount):
    if user_id not in user_balance:
        user_balance[user_id] = 0

    if user_balance[user_id] < bet_amount:
        return False  # Insufficient balance
    else:
        user_balance[user_id] -= bet_amount
        save_balance_to_file()  # Save the updated balance to "id.txt"
        return True  # Sufficient balance

def lsxoso_add_bet_to_history(user_id, bet_type, bet_amount, chosen_number):
    if user_id not in user_bet_history:
        user_bet_history[user_id] = []

    vietnam_timezone = pytz.timezone('Asia/Ho_Chi_Minh')
    current_time_utc = datetime.utcnow()
    current_time_vietnam = current_time_utc.astimezone(vietnam_timezone).strftime("%Y-%m-%d %H:%M:%S")

    user_bet_history[user_id].append({
        "bet_type": bet_type,
        "bet_amount": bet_amount,
        "chosen_number": chosen_number,
        "timestamp": current_time_vietnam  # Save the timestamp in Vietnam timezone
    })

    # Automatically save the history to "kiemtraxs.txt"
    try:
        history_text = f"Loại cược: {bet_type}\n"
        history_text += f"User ID: {user_id}\n"
        history_text += f"Số tiền đặt cược: {bet_amount}đ\n"
        history_text += f"Số đã chọn: {chosen_number}\n"
        history_text += f"Thời Gian: {current_time_vietnam}\n\n"

        # Define the encoding as 'utf-8' when opening the file
        with open("kiemtraxs.txt", "a", encoding='utf-8') as history_file:
            history_file.write(history_text)
    except Exception as e:
        # Handle any potential errors, e.g., by logging them
        print(f"Error saving history: {str(e)}")


@bot.message_handler(commands=['xoso'])
def check1_balance(message):
    user_id = message.from_user.id
    try:
        username = message.from_user.username or "Người dùng không xác định"

        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        button_lo2 = types.KeyboardButton("Lô 2 Số")
        button_lo3 = types.KeyboardButton("Lô 3 Số")
        button_lo4 = types.KeyboardButton("Lô 4 Số")
        button_xien2 = types.KeyboardButton("Xiên 2")
        button_xien3 = types.KeyboardButton("Xiên 3")
        button_xien4 = types.KeyboardButton("Xiên 4")
        button_de2 = types.KeyboardButton("Đề 2 Số")
        button_de3 = types.KeyboardButton("Đề 3 Số")
        button_de4 = types.KeyboardButton("Đề 4 Số")
        button_dau = types.KeyboardButton("Đầu")
        button_duoi = types.KeyboardButton("Đuôi")

        markup.row(button_lo2, button_lo3, button_lo4)
        markup.row(button_xien2, button_xien3, button_xien4)
        markup.row(button_de2, button_de3, button_de4)
        markup.row(button_dau, button_duoi)

        bot.send_message(user_id, f"""
💰 Lô Đề 

🔖 Đây là game dựa vào 2 số cuối các giải của Xổ Số Miền Bắc được quay vào lúc 18h30 hàng ngày!

➡️ Game Lô Đề - Tỷ Lệ Thắng 
Lô 2 Số 1x3,5
Lô 3 Số 1x42,3
Lô 4 Số 1x440
Xiên 2 1x12
Xiên 3 1x60
Xiên 4 1x165
Đề 2 Số 1x95
Đề 3 Số 1x960
Đề 4 Số 1x8800
Đầu 1x7
Đuôi 1x7
Chúc Bạn May Mắn Lụm Lúa Về Làng Nhé.
👉 Số tiền chơi tối thiểu là 6,000đ và tối đa là 1,000,000đ

🎮 Cách chơi: Chat tại đây theo cú pháp: 
Chọn Lô Xiên 2 Đề Ba Càng: Số Dự Đoán [dấu cách] Số Tiến Cược.
VD: Số Dự Đoán [dấu cách] Số Tiến Cược
""", reply_markup=markup)

    except ValueError:
        bot.reply_to(message, "Đã xảy ra lỗi. Vui lòng thử lại sau.")


@bot.message_handler(func=lambda message: message.text in ["Lô 2 Số", "Lô 3 Số", "Lô 4 Số", "Xiên 2", "Xiên 3", "Xiên 4", "Đề 2 Số", "Đề 3 Số", "Đề 4 Số", "Đầu", "Đuôi"])
def handle_choice(message):
    user_id = message.from_user.id
    try:
        choice = message.text

        user_bets[user_id] = {"bet_type": choice, "bet_amount": 0, "chosen_number": ""}

        bot.send_message(user_id, f"Bạn Chọn: {choice}\nVui Lòng Nhập:\n( Số Dự Đoán Kèm Số Tiền )\nHãy Nhập Đúng Nếu Sai Bất Kỳ Lý Do nào.\nchúng tôi không chịu trách nhiệm")

    except ValueError:
        bot.send_message(user_id, "Đã xảy ra lỗi. Vui lòng thử lại sau.")

# Updated function to handle user input for bets
@bot.message_handler(func=lambda message: " " in message.text and message.text.split()[1].isdigit())
def handle_bet_input(message):
    user_id = message.from_user.id
    try:
        user_input = message.text.strip()
        data_parts = user_input.split()
        if len(data_parts) != 2:
            bot.send_message(user_id, "Định dạng đặt cược không hợp lệ. Vui lòng nhập\n( Số Dự Đoán [dấu cách] Số Tiền ).")
            return

        chosen_number, bet_amount = data_parts
        bet_amount = int(bet_amount)

        # Check if the user has chosen a betting type previously
        if user_id not in user_bets:
            bot.send_message(user_id, "Vui lòng chọn loại cược trước khi đặt cược.")
            return

        # Determine the required number of digits based on the betting type
        betting_type = user_bets[user_id]["bet_type"]
        required_digits = {
            "Lô 2 Số": 2,
            "Lô 3 Số": 3,
            "Lô 4 Số": 4,
            "Xiên 2": 4,
            "Xiên 3": 6,
            "Xiên 4": 8,  # Updated to 8 digits for Xiên 4
            "Đề 2 Số": 2,
            "Đề 3 Số": 3,
            "Đề 4 Số": 4,
            "Đầu": 2,
            "Đuôi": 2
        }

        if betting_type not in required_digits:
            bot.send_message(user_id, "Loại cược không hợp lệ.")
            return

        # Check if the chosen number has the correct number of digits
        if len(chosen_number) != required_digits[betting_type]:
            bot.send_message(user_id, f"Số dự đoán cho {betting_type} phải có {required_digits[betting_type]} chữ số.")
            return

        # Add commas to the chosen_number for display
        chosen_number_formatted = ','.join(chosen_number[i:i+2] for i in range(0, len(chosen_number), 2))

        # Check if the bet amount is greater than or equal to 6000
        if bet_amount < 5000:
            bot.send_message(user_id, "Số tiền đặt cược phải lớn hơn hoặc bằng 6000đ.")
            return

        # Check balance and deduct the bet amount
        if not check_and_deduct_balance(user_id, bet_amount):
            bot.send_message(user_id, "Không đủ tiền. Vui lòng nạp số dư của bạn.")
            return

        user_bets[user_id]["bet_amount"] = bet_amount
        user_bets[user_id]["chosen_number"] = chosen_number

        lsxoso_add_bet_to_history(user_id, user_bets[user_id]['bet_type'], bet_amount, chosen_number)
        # Send a notification to the group chat
        notification_message = f"""
Người dùng {user_id} .
Bạn Chọn: {user_bets[user_id]['bet_type']}.
Số Đã Chọn: {chosen_number_formatted}.
Số Tiền: {bet_amount:,}đ 
"""
        bot.send_message(group_chat_id, notification_message)
        # Send a notification to the second group chat
        notification_message2 = f"""
Người dùng {user_id} .
Bạn Chọn: {user_bets[user_id]['bet_type']}.
Số Đã Chọn: {chosen_number_formatted}.
Số Tiền: {bet_amount:,}.
"""
        bot.send_message(group_chat_id2, notification_message2)

        bot.send_message(user_id, f"""
┏ ━ ━ ━ ━ ━ ━ ━ ━ ━ ━ ━
┣➤User ID: {user_id}
┣➤Số Tiền Cược: {bet_amount:,}đ.
┣➤Bạn Dự Đoán: {chosen_number_formatted}.
┣➤Thời Gian: {current_time_vietnam}.
┣➤Chờ 18h30 Có Kết Quả Nhé.
┣➤Hãy Check Trang XSMB.
┣➤/lsxoso Xem Cược LSXS
┗ ━ ━ ━ ━ ━ ━ ━ ━ ━ ━ ━
        """)

    except ValueError:
        bot.send_message(user_id, "Đã xảy ra lỗi. Vui lòng thử lại sau.")

@bot.message_handler(commands=['lsxoso'])
def lsxoso(message):
    user_id = message.from_user.id
    if user_id in user_bet_history and len(user_bet_history[user_id]) > 0:
        # Display the betting history to the user
        # (no need to save it again here)
        history_text = "Lịch Sử Cược XSMB:\n\n"
        vietnam_timezone = pytz.timezone('Asia/Ho_Chi_Minh')

        for bet in user_bet_history[user_id]:
            try:
                timestamp_utc = datetime.strptime(bet["timestamp"], "%Y-%m-%d %H:%M:%S")
                timestamp_vietnam = timestamp_utc.astimezone(vietnam_timezone)

                history_text += f"Loại cược: {bet['bet_type']}\n"
                history_text += f"User ID: {user_id}\n"
                history_text += f"Số tiền đặt cược: {bet['bet_amount']}đ\n"
                history_text += f"Số đã chọn: {bet['chosen_number_formatted']}\n"
                history_text += f"Thời Gian: {timestamp_vietnam.strftime('%Y-%m-%d %H:%M:%S')}\n\n"
            except Exception as e:
                print(f"Error processing bet: {str(e)}")
                continue

        bot.send_message(user_id, history_text)
    else:
        bot.send_message(user_id, "Bạn chưa có lịch sử cá cược.")

#chạy bot.polling()
bot.polling()
