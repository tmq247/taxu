import telebot
import requests
import random
import threading
import time
import os
from multiprocessing import Process

API_KEY = '6732861232:AAEqfUxoJnkxUSeFQOD_KjlDlYBCUXUICzA'
bot = telebot.TeleBot(API_KEY, parse_mode=None)

# Dictionary to store user bets
user_bets = {}

# Dictionary to store user balances
user_balance = {}

# Variable to store the group chat ID
group_chat_id = -1002043487044

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
def confirm_bet(user_id, bet_type, bet_amount):
    bot.send_message(group_chat_id, f"Đã nhận cược từ {user_id}: {bet_type} {bet_amount}đ")

    # Check if the user_id is present in user_balance dictionary
    if user_id in user_balance:
        # Check user balance
        if user_balance[user_id] >= bet_amount:
            user_bets[user_id] = {'T': 0, 'X': 0}  # Initialize the user's bets if not already present
            user_bets[user_id][bet_type] += bet_amount
            user_balance[user_id] -= bet_amount
            bot.send_message(group_chat_id, f"Cược đã được chấp nhận.")
        else:
            bot.send_message(group_chat_id, "Không đủ số dư để đặt cược. Vui lòng kiểm tra lại số dư của bạn.")
    else:
        bot.send_message(group_chat_id, "Người chơi không có trong danh sách. Hãy thử lại.")

# Function to start the dice game
def start_game():
    total_bet_T = sum([user_bets[user_id]['T'] for user_id in user_bets])
    total_bet_X = sum([user_bets[user_id]['X'] for user_id in user_bets])

    bot.send_message(group_chat_id, f"🔵 Tổng cược bên TÀI: {total_bet_T}đ")
    bot.send_message(group_chat_id, f"🔴 Tổng cược bên XỈU: {total_bet_X}đ")
    bot.send_message(group_chat_id, "💥 Bắt đầu tung XX 💥")

    time.sleep(3)  # Simulating dice rolling

    result = [send_dice(group_chat_id) for _ in range(3)]

    bot.send_message(group_chat_id, f"KẾT QUẢ XX: {result}")

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

    # Save updated balances to the file
    save_balance_to_file()

    bot.send_message(group_chat_id, f"Tổng thắng: {total_win}đ")
    bot.send_message(group_chat_id, f"Tổng thua: {total_bet_T + total_bet_X}đ")

# Function to handle the game timing
def game_timer():
    while True:
        bot.send_message(group_chat_id, "Bắt đầu cược! Có 120s để đặt cược.")
        time.sleep(120)  # Wait for 120 seconds

        bot.send_message(group_chat_id, "Hết thời gian cược. Kết quả sẽ được công bố ngay sau đây.")
        start_game()

# Function to handle user messages
@bot.message_handler(func=lambda message: True)
def handle_message(message):
    chat_id = message.chat.id

    # Check if the message is from the group chat
    if chat_id == group_chat_id:
        # Check if the message is a valid bet
        if message.text and message.text.upper() in ['T MAX', 'X MAX'] or (message.text and message.text[0] in ['T', 'X'] and message.text[1:].isdigit()):
            user_id = message.from_user.id
            bet_type = message.text[0]
            if message.text.upper() == 'T MAX' or message.text.upper() == 'X MAX':
                bet_amount = user_balance.get(user_id, 0)  # Use the entire balance
            else:
                bet_amount = int(message.text[2:])

            # Confirm the bet and check user balance
            confirm_bet(user_id, bet_type, bet_amount)

        else:
            bot.send_message(chat_id, "Lệnh không hợp lệ. Vui lòng tuân thủ theo quy tắc cược.")

# Load user balances from the file
load_balance_from_file()

# Start the game timer in a separate process
timer_process = Process(target=game_timer)
timer_process.start()

# Adding a small delay
time.sleep(1)

# Run the bot
bot.polling()
