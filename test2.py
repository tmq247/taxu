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


API_KEY = '6757521267:AAE5IHnHoESuOPViTNOJsxrYMlit6jtgbwQ'
bot = telebot.TeleBot(API_KEY, parse_mode=None)

#luu ket qua
#luu_cau = {}

# Dictionary to store user bets
user_bets = {}

# Dictionary to store user balances
user_balance = {}

# Variable to store the group chat ID
group_chat_id = -1002121532989

# Winning coefficient
winning_coefficient = 1.98

# Function to send a dice and get its value
def send_dice(chat_id):
    response = requests.get(f'https://api.telegram.org/bot{API_KEY}/sendDice?chat_id={chat_id}')
    if response.status_code == 200:
        data = response.json()
        if 'result' in data and 'dice' in data['result']:
            return data['result']['dice']['value']
    return None

# Hàm kiểm Tài/Xỉu
def calculate_tai_xiu(total_score):
  return "Tài" if 11 <= total_score <= 18 else "Xỉu"

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


# Function to confirm the bet and check user balance
def confirm_bet(user_id, bet_type, bet_amount, ten_ncuoc):
    if bet_type == 'T':
        cua_cuoc = '🔵Tài'
    else:
        cua_cuoc = '🔴Xỉu'
    bot.send_message(group_chat_id, f"{ten_ncuoc} đã cược {cua_cuoc} {bet_amount} điểm")
    
    # Check if the user_id is present in user_balance dictionary
    if user_id in user_balance:
        # Check user balance
        if user_balance[user_id] >= bet_amount:
            user_bets[user_id] = {'T': 0, 'X': 0}  # Initialize the user's bets if not already present
            user_bets[user_id][bet_type] += bet_amount
            user_balance[user_id] -= bet_amount
            bot.send_message(group_chat_id, f"Cược đã được chấp nhận.")
        else:
            bot.send_message(group_chat_id, "Không đủ điểm để đặt cược. Vui lòng kiểm tra lại số điểm của bạn.")
    else:
        bot.send_message(group_chat_id, "Hãy nhắn tin cho bot @testtaixiu1bot và đặt cược lại.")

# Function to start the dice game
def start_game():
    total_bet_T = sum([user_bets[user_id]['T'] for user_id in user_bets])
    total_bet_X = sum([user_bets[user_id]['X'] for user_id in user_bets])

    #bot.send_message(group_chat_id, f"🔵 Tổng cược bên TÀI: {total_bet_T}đ")
    #bot.send_message(group_chat_id, f"🔴 Tổng cược bên XỈU: {total_bet_X}đ")
    bot.send_message(group_chat_id, f"""
┏ ━ ━ ━ ━ ━ ━ ━ ━ ━ ━ ━
┣➤🔵Tổng cược bên TÀI: {total_bet_T}đ
┣➤🔴Tổng cược bên XỈU: {total_bet_X}đ
┗ ━ ━ ━ ━ ━ ━ ━ ━ ━ ━ ━
""")
    bot.send_message(group_chat_id, "💥 Bắt đầu tung XX 💥")

    time.sleep(3)  # Simulating dice rolling

    result = [send_dice(group_chat_id) for _ in range(3)]
    total_score = sum(result)
    luu_cau = f"➤KẾT QUẢ XX: {' + '.join(str(x) for x in result)} = {total_score} điểm {calculate_tai_xiu(total_score)}"
    #bot.send_message(group_chat_id, f"➤KẾT QUẢ XX: {' + '.join(str(x) for x in result)} = {total_score} điểm {calculate_tai_xiu(total_score)}")
    bot.send_message(group_chat_id, f"{luu_cau}")

    # Determine the winner and calculate total winnings
    total_win = 0
    for user_id in user_bets:
        if sum(result) >= 4 and user_bets[user_id]['T'] > 0:
            total_win += user_bets[user_id]['T'] * winning_coefficient
        elif sum(result) < 4 and user_bets[user_id]['X'] > 0:
            total_win += user_bets[user_id]['X'] * winning_coefficient

    # Update user balances based on the game result
    for user_id in user_bets:
        if sum(result) >= 4 and user_bets[user_id]['T'] > 0:
            user_balance[user_id] += total_win
        elif sum(result) < 4 and user_bets[user_id]['X'] > 0:
            user_balance[user_id] += total_win

    # Clear user bets
    user_bets.clear()

    #luu cau
    #luucau()
    # Save updated balances to the file
    save_balance_to_file()

    bot.send_message(group_chat_id, f"""
Tổng thắng: {total_win}đ
Tổng thua: {total_bet_T + total_bet_X}đ
""")
    #bot.send_message(group_chat_id, f"Tổng thua: {total_bet_T + total_bet_X}đ")
    return

# Function to handle the game timing
def game_timer():
    #while True:
        bot.send_message(group_chat_id, "Bắt đầu cược! Có 45s để đặt cược.")
        time.sleep(45)  # Wait for 120 seconds

        bot.send_message(group_chat_id, "Hết thời gian cược. Kết quả sẽ được công bố ngay sau đây.")
        start_game()

# Function to handle user messages
@bot.message_handler(commands=["t", "x"])
def handle_message(message, 
                   total_bet_T = sum([user_bets[user_id]['T'] for user_id in user_bets]), 
                   total_bet_X = sum([user_bets[user_id]['X'] for user_id in user_bets])
                   ):
    chat_id = message.chat.id
    ten_ncuoc = message.from_user.first_name

    # Check if the message is from the group chat
    if chat_id == group_chat_id:
        # Check if the message is a valid bet
        if message.text and message.text.upper() in ['/T ALL', '/X ALL'] or (message.text and message.text.upper()[1] in ['T', 'X'] and message.text[3:].isdigit()):
            user_id = message.from_user.id
            bet_type = message.text.upper()[1]
            if message.text.upper() == '/T ALL' or message.text.upper() == '/X ALL':
                bet_amount = user_balance.get(user_id, 0)  # Use the entire balance
            else:
                bet_amount = int(message.text[3:])

            # Confirm the bet and check user balance
            confirm_bet(user_id, bet_type, bet_amount)
            
        else:
            bot.send_message(chat_id, "Lệnh không hợp lệ. Vui lòng tuân thủ theo quy tắc cược.")
        #bot.send_message(group_chat_id, f"""
#┏ ━ ━ ━ ━ ━ ━ ━ ━ ━ ━ ━
#┣➤🔵Tổng cược bên TÀI: {total_bet_T}đ
#┣➤🔴Tổng cược bên XỈU: {total_bet_X}đ
#┗ ━ ━ ━ ━ ━ ━ ━ ━ ━ ━ ━
#""")

# Load user balances from the file
load_balance_from_file()

def check_balance(msg):
  user_id = msg.from_user.id
  balance = user_balance.get(user_id, 0)
  photo_link = "https://scontent.fdad1-4.fna.fbcdn.net/v/t39.30808-6/374564260_311252494902338_4501893302206805342_n.jpg?_nc_cat=103&ccb=1-7&_nc_sid=49d041&_nc_ohc=ypCR3gJKO84AX8vBaGO&_nc_oc=AQkV2yigf-t0BVkyWvCT0B1QFbLFdXx-cDg9Lal65LdSPI_AvgJdmKKS0ZpvItzfP3rlfqLxFP3pFitVvMbCHjGI&_nc_ht=scontent.fdad1-4.fna&oh=00_AfCW5YKUPRq6IRYMDCqhbPKQYFlUoIbVsuCjDAmzsr50VA&oe=64F55781"  # Thay thế bằng đường dẫn URL của hình ảnh
  bot.send_photo(msg.chat.id,
                 photo_link,
                 caption=f"""
👤 <b>Số điểm của</b>: <code>{msg.from_user.first_name} là >💰{balance:,} điểm</code>
        """,
                 parse_mode='HTML')
  
@bot.message_handler(commands=["diem"])
def handle_check_balance_button(msg):
    load_balance_from_file()
    check_balance(msg)

@bot.message_handler(commands=["tx"])
def start_taixiu(message):
    chat_id = message.chat.id
    bot.send_message(chat_id, "Bắt đầu game.")
    game_timer()
    return
    #timer_thread = threading.Thread(target=game_timer)
    #timer_thread.start()

#def luucau():
  #with open("luucau.txt", "w") as f:
    #for user_id, balance in user_balance.items():
        #f.write(f"{user_id} {balance}\n")
    #for result, total_score in luu_cau():
        #f.write(f"➤{' + '.join(str(x) for x in result)} = {total_score} điểm {calculate_tai_xiu(total_score)}\n")

#@bot.message_handler(commands=["sc"])
#def check_cau(message):
    #kqsoi_cau = luucau.get(result, total_score)
    #bot.send_message(f"{kqsoi_cau}")

# Adding a small delay
#time.sleep(1)

# Run the bot
bot.polling()
