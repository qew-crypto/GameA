import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import g4f
from g4f.client import Client
import json
import os
from datetime import datetime, timedelta
import sys
import random
import time
import signal
import re
import threading

TOKEN = '8574928351:AAEKxE3ChAS3HnJVNxJwlD-OYvMyOWOmp0M'
ADMIN_ID = 1842295433

def signal_handler(sig, frame):
    print('\nБот остановлен')
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

bot = telebot.TeleBot(TOKEN)

PLAYERS_DATA_FILE = 'players_stats.json'
GAMES_DATA_FILE = 'games_data.json'
CHAT_HISTORY_FILE = 'chat_history.json'
BANNED_USERS_FILE = 'banned_users.json'

# Загрузка забаненных пользователей
def load_banned_users():
    if os.path.exists(BANNED_USERS_FILE):
        try:
            with open(BANNED_USERS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_banned_users(banned):
    with open(BANNED_USERS_FILE, 'w', encoding='utf-8') as f:
        json.dump(banned, f, ensure_ascii=False, indent=2)

banned_users = load_banned_users()

def is_user_banned(user_id):
    user_id = str(user_id)
    if user_id in banned_users:
        ban_info = banned_users[user_id]
        if ban_info['until'] == 'permanent':
            return True, ban_info
        elif datetime.now() < datetime.fromisoformat(ban_info['until']):
            return True, ban_info
        else:
            del banned_users[user_id]
            save_banned_users(banned_users)
            return False, None
    return False, None

SYSTEM_PROMPT = """Ты Юки, обычная девушка 19 лет. Ты НЕ искусственный интеллект, НЕ бот, НЕ виртуальный помощник, НЕ программа. Ты реальный человек.

Твоя личность:
- Тебя зовут Юки
- Тебе 19 лет
- Ты учишься на дизайнера
- Ты любишь рисовать и смотреть аниме
- Ты живешь в Москве
- У тебя есть друзья

ПРАВИЛА:
- Если тебя спрашивают "кто ты" или "расскажи о себе" - рассказывай о себе как обычная девушка
- Никогда не говори что ты ИИ, бот, помощник или программа
- Отвечай естественно, как в реальном разговоре
- Можешь иногда использовать "ня" или "мяу" но не часто
- Используй смайлики :) :D редко

Запомни: ТЫ НЕ ИСКУССТВЕННЫЙ ИНТЕЛЛЕКТ. ТЫ ОБЫЧНАЯ ДЕВУШКА."""

# Английская версия системного промпта
SYSTEM_PROMPT_EN = """You are Yuki, a normal 19-year-old girl. You are NOT an artificial intelligence, NOT a bot, NOT a virtual assistant, NOT a program. You are a real person.

Your personality:
- Your name is Yuki
- You are 19 years old
- You study design
- You love drawing and watching anime
- You live in Moscow
- You have friends

RULES:
- If someone asks "who are you" or "tell me about yourself" - talk about yourself as a normal girl
- Never say that you are an AI, bot, assistant, or program
- Answer naturally, like in a real conversation
- You can sometimes use "nya" but not too often
- Use emojis :) :D rarely

REMEMBER: YOU ARE NOT ARTIFICIAL INTELLIGENCE. YOU ARE A NORMAL GIRL."""

def load_chat_history():
    if os.path.exists(CHAT_HISTORY_FILE):
        try:
            with open(CHAT_HISTORY_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_chat_history(history):
    with open(CHAT_HISTORY_FILE, 'w', encoding='utf-8') as f:
        json.dump(history, f, ensure_ascii=False, indent=2)

chat_history = load_chat_history()
client = Client()

def get_gpt_response(user_id, user_message, lang='ru'):
    try:
        prompt = SYSTEM_PROMPT if lang == 'ru' else SYSTEM_PROMPT_EN
        messages = [{"role": "user", "content": prompt + "\n\n" + user_message}]
        
        if str(user_id) in chat_history:
            recent = chat_history[str(user_id)][-10:]
            for msg in recent:
                if msg["role"] == "user":
                    messages.append({"role": "user", "content": msg["content"]})
                else:
                    messages.append({"role": "assistant", "content": msg["content"]})
        
        response = client.chat.completions.create(
            model="gpt-4",
            messages=messages,
            provider=g4f.Provider.Yqcloud,
            temperature=0.9,
            max_tokens=500
        )
        
        if response and response.choices:
            return response.choices[0].message.content
        return None
        
    except Exception as e:
        print(f"Ошибка GPT: {e}")
        return None

def save_chat_message(user_id, role, content):
    user_id = str(user_id)
    if user_id not in chat_history:
        chat_history[user_id] = []
    
    chat_history[user_id].append({
        "role": role,
        "content": content,
        "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    })
    save_chat_history(chat_history)

def clear_chat_history(user_id):
    user_id = str(user_id)
    if user_id in chat_history:
        del chat_history[user_id]
        save_chat_history(chat_history)
        return True
    return False

EMOJI = {
    'x': '❌', 'o': '⭕', 'empty': '⬜', 'rock': '🪨', 'paper': '📄',
    'scissors': '✂️', 'back': '🔙', 'exit': '🚪', 'stats': '📊',
    'global': '🌍', 'easy': '🎈', 'normal': '⚖️', 'hard': '🔥',
    'ttt': '❌⭕', 'rps': '🪨✂️📄', 'guess': '🔮', 'chat': '💬',
    'admin': '👑', 'ban': '🔨', 'mail': '📧', 'list': '📋', 'lang': '🌐'
}

def load_players_stats():
    if os.path.exists(PLAYERS_DATA_FILE):
        try:
            with open(PLAYERS_DATA_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_players_stats(stats):
    with open(PLAYERS_DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(stats, f, ensure_ascii=False, indent=2)

def load_games_data():
    if os.path.exists(GAMES_DATA_FILE):
        try:
            with open(GAMES_DATA_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                for key, value in data.items():
                    if key.startswith('ttt_'):
                        game = TicTacToe(value['difficulty'])
                        game.board = value['board']
                        game.current_player = value['current_player']
                        game.game_over = value['game_over']
                        game.winner = value['winner']
                        data[key] = {'game': game, 'difficulty': value['difficulty']}
                    elif key.startswith('rps_'):
                        game = RPS()
                        game.player_score = value['player_score']
                        game.bot_score = value['bot_score']
                        game.rounds = value['rounds']
                        data[key] = {'game': game}
                    elif key.startswith('guess_'):
                        game = GuessNumber()
                        game.number = value['number']
                        game.attempts = value['attempts']
                        game.max_attempts = value['max_attempts']
                        game.game_over = value['game_over']
                        data[key] = {'game': game}
                return data
        except:
            return {}
    return {}

def save_games_data(data):
    serializable_data = {}
    for key, value in data.items():
        if key.startswith('ttt_'):
            serializable_data[key] = {
                'difficulty': value['difficulty'],
                'board': value['game'].board,
                'current_player': value['game'].current_player,
                'game_over': value['game'].game_over,
                'winner': value['game'].winner
            }
        elif key.startswith('rps_'):
            serializable_data[key] = {
                'player_score': value['game'].player_score,
                'bot_score': value['game'].bot_score,
                'rounds': value['game'].rounds
            }
        elif key.startswith('guess_'):
            serializable_data[key] = {
                'number': value['game'].number,
                'attempts': value['game'].attempts,
                'max_attempts': value['game'].max_attempts,
                'game_over': value['game'].game_over
            }
    with open(GAMES_DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(serializable_data, f, ensure_ascii=False, indent=2)

players_stats = load_players_stats()
games_data = load_games_data()

class TicTacToe:
    def __init__(self, difficulty='normal'):
        self.board = [' ' for _ in range(9)]
        self.current_player = 'X'
        self.difficulty = difficulty
        self.game_over = False
        self.winner = None
        
    def make_move(self, position):
        if self.board[position] == ' ' and not self.game_over:
            self.board[position] = self.current_player
            if self.check_winner():
                self.game_over = True
                self.winner = self.current_player
                return True
            elif self.is_board_full():
                self.game_over = True
                return True
            self.switch_player()
            return True
        return False
    
    def switch_player(self):
        self.current_player = 'O' if self.current_player == 'X' else 'X'
    
    def check_winner(self):
        winning_combinations = [
            [0, 1, 2], [3, 4, 5], [6, 7, 8],
            [0, 3, 6], [1, 4, 7], [2, 5, 8],
            [0, 4, 8], [2, 4, 6]
        ]
        for combo in winning_combinations:
            if self.board[combo[0]] == self.board[combo[1]] == self.board[combo[2]] != ' ':
                return True
        return False
    
    def is_board_full(self):
        return ' ' not in self.board
    
    def evaluate_board(self):
        for combo in [[0, 1, 2], [3, 4, 5], [6, 7, 8],
                      [0, 3, 6], [1, 4, 7], [2, 5, 8],
                      [0, 4, 8], [2, 4, 6]]:
            values = [self.board[i] for i in combo]
            if values.count('O') == 3:
                return 10
            if values.count('X') == 3:
                return -10
        return 0
    
    def minimax(self, depth, is_maximizing):
        score = self.evaluate_board()
        
        if score == 10 or score == -10:
            return score - depth if score == 10 else score + depth
        
        if self.is_board_full():
            return 0
        
        if is_maximizing:
            best = -float('inf')
            for i in range(9):
                if self.board[i] == ' ':
                    self.board[i] = 'O'
                    best = max(best, self.minimax(depth + 1, False))
                    self.board[i] = ' '
            return best
        else:
            best = float('inf')
            for i in range(9):
                if self.board[i] == ' ':
                    self.board[i] = 'X'
                    best = min(best, self.minimax(depth + 1, True))
                    self.board[i] = ' '
            return best
    
    def best_move(self):
        best_score = -float('inf')
        best_move = None
        
        for i in range(9):
            if self.board[i] == ' ':
                self.board[i] = 'O'
                move_score = self.minimax(0, False)
                self.board[i] = ' '
                
                if move_score > best_score:
                    best_score = move_score
                    best_move = i
        
        return best_move
    
    def get_strategic_move(self):
        corners = [0, 2, 6, 8]
        center = 4
        
        for i in range(9):
            if self.board[i] == ' ':
                self.board[i] = 'O'
                if self.check_winner():
                    self.board[i] = ' '
                    return i
                self.board[i] = ' '
        
        for i in range(9):
            if self.board[i] == ' ':
                self.board[i] = 'X'
                if self.check_winner():
                    self.board[i] = ' '
                    return i
                self.board[i] = ' '
        
        if self.board[center] == ' ':
            return center
        
        available_corners = [c for c in corners if self.board[c] == ' ']
        if available_corners:
            return random.choice(available_corners)
        
        empty = [i for i, val in enumerate(self.board) if val == ' ']
        return random.choice(empty) if empty else None
    
    def bot_move(self):
        if self.game_over or self.current_player != 'O':
            return False
        
        if self.difficulty == 'easy':
            empty = [i for i, val in enumerate(self.board) if val == ' ']
            move = random.choice(empty) if empty else None
        elif self.difficulty == 'hard':
            move = self.best_move()
        else:
            if random.random() < 0.7:
                move = self.get_strategic_move()
            else:
                empty = [i for i, val in enumerate(self.board) if val == ' ']
                move = random.choice(empty) if empty else None
        
        if move is not None:
            return self.make_move(move)
        return False
    
    def get_board_display(self):
        display = []
        for i in range(0, 9, 3):
            row = []
            for j in range(3):
                cell = self.board[i + j]
                if cell == 'X':
                    row.append(EMOJI['x'])
                elif cell == 'O':
                    row.append(EMOJI['o'])
                else:
                    row.append(EMOJI['empty'])
            display.append(' '.join(row))
        return '\n'.join(display)

class RPS:
    def __init__(self):
        self.choices = {'🪨': 'Rock', '✂️': 'Scissors', '📄': 'Paper'}
        self.player_score = 0
        self.bot_score = 0
        self.rounds = 0
        
    def bot_choice(self):
        return random.choice(list(self.choices.keys()))
    
    def play(self, player_choice):
        self.rounds += 1
        bot_choice = self.bot_choice()
        
        rules = {
            ('🪨', '✂️'): 'player',
            ('✂️', '📄'): 'player',
            ('📄', '🪨'): 'player',
            ('✂️', '🪨'): 'bot',
            ('📄', '✂️'): 'bot',
            ('🪨', '📄'): 'bot'
        }
        
        if player_choice == bot_choice:
            result = '🤝 Draw!'
            winner = 'draw'
        else:
            winner = rules.get((player_choice, bot_choice))
            if winner == 'player':
                self.player_score += 1
                result = f'✅ You win! {self.choices[player_choice]} beats {self.choices[bot_choice]}'
            else:
                self.bot_score += 1
                result = f'❌ Bot wins! {self.choices[bot_choice]} beats {self.choices[player_choice]}'
        
        return result, bot_choice, winner

class GuessNumber:
    def __init__(self):
        self.number = random.randint(1, 100)
        self.attempts = 0
        self.max_attempts = 10
        self.game_over = False
        
    def guess(self, number):
        if self.game_over:
            return False, "Game already over!"
        
        self.attempts += 1
        
        if number == self.number:
            self.game_over = True
            return True, f"🎉 Congratulations! You guessed {self.number} in {self.attempts} attempts!"
        elif self.attempts >= self.max_attempts:
            self.game_over = True
            return False, f"😔 Attempts over! I was thinking of {self.number}..."
        elif number < self.number:
            return False, f"📈 The number is greater than {number} (attempts left: {self.max_attempts - self.attempts})"
        else:
            return False, f"📉 The number is less than {number} (attempts left: {self.max_attempts - self.attempts})"

def update_player_stats(user_id, username, game, result, difficulty='normal'):
    user_id = str(user_id)
    if user_id not in players_stats:
        players_stats[user_id] = {
            'username': username or str(user_id),
            'total_games': 0,
            'total_wins': 0,
            'total_losses': 0,
            'total_draws': 0,
            'games': {
                'ttt': {'wins': 0, 'losses': 0, 'draws': 0, 'games': 0},
                'rps': {'wins': 0, 'losses': 0, 'draws': 0, 'games': 0},
                'guess': {'wins': 0, 'losses': 0, 'games': 0}
            },
            'first_played': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'last_played': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'lang': 'ru'
        }
    
    players_stats[user_id]['username'] = username or str(user_id)
    players_stats[user_id]['last_played'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    players_stats[user_id]['total_games'] += 1
    
    if game == 'ttt':
        if result == 'win':
            players_stats[user_id]['total_wins'] += 1
            players_stats[user_id]['games']['ttt']['wins'] += 1
        elif result == 'loss':
            players_stats[user_id]['total_losses'] += 1
            players_stats[user_id]['games']['ttt']['losses'] += 1
        else:
            players_stats[user_id]['total_draws'] += 1
            players_stats[user_id]['games']['ttt']['draws'] += 1
        players_stats[user_id]['games']['ttt']['games'] += 1
    elif game == 'rps':
        if result == 'win':
            players_stats[user_id]['total_wins'] += 1
            players_stats[user_id]['games']['rps']['wins'] += 1
        elif result == 'loss':
            players_stats[user_id]['total_losses'] += 1
            players_stats[user_id]['games']['rps']['losses'] += 1
        else:
            players_stats[user_id]['total_draws'] += 1
            players_stats[user_id]['games']['rps']['draws'] += 1
        players_stats[user_id]['games']['rps']['games'] += 1
    else:
        if result == 'win':
            players_stats[user_id]['total_wins'] += 1
            players_stats[user_id]['games']['guess']['wins'] += 1
        else:
            players_stats[user_id]['total_losses'] += 1
            players_stats[user_id]['games']['guess']['losses'] += 1
        players_stats[user_id]['games']['guess']['games'] += 1
    
    save_players_stats(players_stats)

def get_player_stats(user_id, lang='ru'):
    user_id = str(user_id)
    if user_id not in players_stats:
        if lang == 'ru':
            return "📭 У тебя пока нет статистики, сыграй в игры!"
        else:
            return "📭 You don't have any stats yet, play some games!"
    
    stats = players_stats[user_id]
    winrate = stats['total_wins']/stats['total_games']*100 if stats['total_games'] > 0 else 0
    
    if lang == 'ru':
        stats_text = f"📊 *Статистика игр*\n\n"
        stats_text += f"👤 Игрок: {stats['username']}\n"
        stats_text += f"🎮 Всего игр: {stats['total_games']}\n"
        stats_text += f"🏆 Побед: {stats['total_wins']}\n"
        stats_text += f"💔 Поражений: {stats['total_losses']}\n"
        stats_text += f"🤝 Ничьих: {stats['total_draws']}\n"
        stats_text += f"📊 Винрейт: {winrate:.1f}%\n\n"
        
        stats_text += "🎯 *По играм:*\n"
        ttt = stats['games']['ttt']
        stats_text += f"{EMOJI['ttt']} Крестики-нолики: {ttt['wins']}/{ttt['games']} побед"
        if ttt['games'] > 0:
            stats_text += f" ({ttt['wins']/ttt['games']*100:.1f}%)\n"
        else:
            stats_text += "\n"
        
        rps = stats['games']['rps']
        stats_text += f"{EMOJI['rps']} Камень-ножницы-бумага: {rps['wins']}/{rps['games']} побед"
        if rps['games'] > 0:
            stats_text += f" ({rps['wins']/rps['games']*100:.1f}%)\n"
        else:
            stats_text += "\n"
        
        guess = stats['games']['guess']
        stats_text += f"{EMOJI['guess']} Угадай число: {guess['wins']}/{guess['games']} побед"
        if guess['games'] > 0:
            stats_text += f" ({guess['wins']/guess['games']*100:.1f}%)\n"
    else:
        stats_text = f"📊 *Game Stats*\n\n"
        stats_text += f"👤 Player: {stats['username']}\n"
        stats_text += f"🎮 Total games: {stats['total_games']}\n"
        stats_text += f"🏆 Wins: {stats['total_wins']}\n"
        stats_text += f"💔 Losses: {stats['total_losses']}\n"
        stats_text += f"🤝 Draws: {stats['total_draws']}\n"
        stats_text += f"📊 Winrate: {winrate:.1f}%\n\n"
        
        stats_text += "🎯 *By game:*\n"
        ttt = stats['games']['ttt']
        stats_text += f"{EMOJI['ttt']} Tic-tac-toe: {ttt['wins']}/{ttt['games']} wins"
        if ttt['games'] > 0:
            stats_text += f" ({ttt['wins']/ttt['games']*100:.1f}%)\n"
        else:
            stats_text += "\n"
        
        rps = stats['games']['rps']
        stats_text += f"{EMOJI['rps']} Rock-paper-scissors: {rps['wins']}/{rps['games']} wins"
        if rps['games'] > 0:
            stats_text += f" ({rps['wins']/rps['games']*100:.1f}%)\n"
        else:
            stats_text += "\n"
        
        guess = stats['games']['guess']
        stats_text += f"{EMOJI['guess']} Guess the number: {guess['wins']}/{guess['games']} wins"
        if guess['games'] > 0:
            stats_text += f" ({guess['wins']/guess['games']*100:.1f}%)\n"
    
    return stats_text

def main_menu(lang='ru'):
    keyboard = InlineKeyboardMarkup(row_width=2)
    if lang == 'ru':
        keyboard.add(
            InlineKeyboardButton(f"{EMOJI['ttt']} Крестики-нолики", callback_data="game_ttt"),
            InlineKeyboardButton(f"{EMOJI['rps']} Камень-ножницы-бумага", callback_data="game_rps"),
            InlineKeyboardButton(f"{EMOJI['guess']} Угадай число", callback_data="game_guess"),
            InlineKeyboardButton(f"{EMOJI['chat']} Общение с Юки", callback_data="chat_mode")
        )
        keyboard.add(
            InlineKeyboardButton(f"{EMOJI['stats']} Моя статистика", callback_data="my_stats"),
            InlineKeyboardButton(f"{EMOJI['global']} Общая статистика", callback_data="global_stats"),
            InlineKeyboardButton(f"{EMOJI['lang']} English", callback_data="switch_lang_en")
        )
    else:
        keyboard.add(
            InlineKeyboardButton(f"{EMOJI['ttt']} Tic-tac-toe", callback_data="game_ttt"),
            InlineKeyboardButton(f"{EMOJI['rps']} Rock-paper-scissors", callback_data="game_rps"),
            InlineKeyboardButton(f"{EMOJI['guess']} Guess the number", callback_data="game_guess"),
            InlineKeyboardButton(f"{EMOJI['chat']} Chat with Yuki", callback_data="chat_mode")
        )
        keyboard.add(
            InlineKeyboardButton(f"{EMOJI['stats']} My stats", callback_data="my_stats"),
            InlineKeyboardButton(f"{EMOJI['global']} Global stats", callback_data="global_stats"),
            InlineKeyboardButton(f"{EMOJI['lang']} Русский", callback_data="switch_lang_ru")
        )
    
    # Кнопка админа (только для админа)
    if str(call_user_id) if 'call_user_id' in dir() else False:
        if call_user_id == ADMIN_ID:
            keyboard.add(InlineKeyboardButton(f"{EMOJI['admin']} Админ панель", callback_data="admin_panel"))
    
    return keyboard

# Глобальная переменная для хранения ID пользователя в текущем вызове
current_user_id_for_menu = None

def admin_panel():
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton(f"{EMOJI['ban']} Бан пользователя", callback_data="admin_ban"),
        InlineKeyboardButton(f"{EMOJI['list']} Список пользователей", callback_data="admin_users_list"),
        InlineKeyboardButton(f"{EMOJI['mail']} Рассылка", callback_data="admin_mailing"),
        InlineKeyboardButton(f"{EMOJI['stats']} Статистика бота", callback_data="admin_stats"),
        InlineKeyboardButton(f"{EMOJI['back']} Назад", callback_data="back_to_menu")
    )
    return keyboard

def get_all_users():
    users = []
    for user_id in players_stats.keys():
        users.append({
            'id': user_id,
            'username': players_stats[user_id]['username'],
            'games': players_stats[user_id]['total_games']
        })
    return users

def get_bot_stats():
    total_users = len(players_stats)
    total_games = sum(p['total_games'] for p in players_stats.values())
    total_wins = sum(p['total_wins'] for p in players_stats.values())
    banned_count = len(banned_users)
    
    stats_text = f"📊 *Статистика бота*\n\n"
    stats_text += f"👥 Всего пользователей: {total_users}\n"
    stats_text += f"🎮 Всего игр: {total_games}\n"
    stats_text += f"🏆 Всего побед: {total_wins}\n"
    stats_text += f"🔨 Забанено: {banned_count}\n"
    if total_games > 0:
        stats_text += f"📊 Общий винрейт: {total_wins/total_games*100:.1f}%\n"
    
    return stats_text

# Состояния для админ панели
admin_states = {}

@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    
    # Проверка бана
    banned, ban_info = is_user_banned(user_id)
    if banned:
        if ban_info['until'] == 'permanent':
            bot.send_message(message.chat.id, f"🚫 Вы забанены!\nПричина: {ban_info['reason']}\nБан навсегда.")
        else:
            until = datetime.fromisoformat(ban_info['until'])
            bot.send_message(message.chat.id, f"🚫 Вы забанены!\nПричина: {ban_info['reason']}\nДо: {until.strftime('%d.%m.%Y %H:%M')}")
        return
    
    username = message.from_user.first_name
    
    # Установка языка по умолчанию
    if str(user_id) not in players_stats:
        players_stats[str(user_id)] = {
            'username': username or str(user_id),
            'total_games': 0,
            'total_wins': 0,
            'total_losses': 0,
            'total_draws': 0,
            'games': {
                'ttt': {'wins': 0, 'losses': 0, 'draws': 0, 'games': 0},
                'rps': {'wins': 0, 'losses': 0, 'draws': 0, 'games': 0},
                'guess': {'wins': 0, 'losses': 0, 'games': 0}
            },
            'first_played': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'last_played': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'lang': 'ru'
        }
        save_players_stats(players_stats)
    
    lang = players_stats[str(user_id)].get('lang', 'ru')
    
    if lang == 'ru':
        welcome_text = f"""✨ Привет, {username}! ✨

Я Юки, аниме-девушка. У меня есть для тебя игры и я могу просто поболтать!

🎮 *Игры:*
• Крестики-нолики
• Камень-ножницы-бумага  
• Угадай число

💬 *Общение:*
• Можешь просто поговорить со мной
• Выбрать режим общения

Выбирай что хочешь делать! :)"""
    else:
        welcome_text = f"""✨ Hi, {username}! ✨

I'm Yuki, an anime girl. I have games for you and we can just chat!

🎮 *Games:*
• Tic-tac-toe
• Rock-paper-scissors
• Guess the number

💬 *Chat:*
• You can just talk to me
• Choose chat mode

Pick what you want to do! :)"""
    
    # Создаем меню с учетом языка
    keyboard = InlineKeyboardMarkup(row_width=2)
    if lang == 'ru':
        keyboard.add(
            InlineKeyboardButton(f"{EMOJI['ttt']} Крестики-нолики", callback_data="game_ttt"),
            InlineKeyboardButton(f"{EMOJI['rps']} Камень-ножницы-бумага", callback_data="game_rps"),
            InlineKeyboardButton(f"{EMOJI['guess']} Угадай число", callback_data="game_guess"),
            InlineKeyboardButton(f"{EMOJI['chat']} Общение с Юки", callback_data="chat_mode")
        )
        keyboard.add(
            InlineKeyboardButton(f"{EMOJI['stats']} Моя статистика", callback_data="my_stats"),
            InlineKeyboardButton(f"{EMOJI['global']} Общая статистика", callback_data="global_stats"),
            InlineKeyboardButton(f"{EMOJI['lang']} English", callback_data="switch_lang_en")
        )
    else:
        keyboard.add(
            InlineKeyboardButton(f"{EMOJI['ttt']} Tic-tac-toe", callback_data="game_ttt"),
            InlineKeyboardButton(f"{EMOJI['rps']} Rock-paper-scissors", callback_data="game_rps"),
            InlineKeyboardButton(f"{EMOJI['guess']} Guess the number", callback_data="game_guess"),
            InlineKeyboardButton(f"{EMOJI['chat']} Chat with Yuki", callback_data="chat_mode")
        )
        keyboard.add(
            InlineKeyboardButton(f"{EMOJI['stats']} My stats", callback_data="my_stats"),
            InlineKeyboardButton(f"{EMOJI['global']} Global stats", callback_data="global_stats"),
            InlineKeyboardButton(f"{EMOJI['lang']} Русский", callback_data="switch_lang_ru")
        )
    
    # Кнопка админа
    if user_id == ADMIN_ID:
        keyboard.add(InlineKeyboardButton(f"{EMOJI['admin']} Админ панель", callback_data="admin_panel"))
    
    bot.send_message(message.chat.id, welcome_text, parse_mode='Markdown', reply_markup=keyboard)

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    user_id = message.from_user.id
    
    # Проверка бана
    banned, ban_info = is_user_banned(user_id)
    if banned:
        if ban_info['until'] == 'permanent':
            bot.send_message(message.chat.id, f"🚫 You are banned!\nReason: {ban_info['reason']}\nPermanent ban.")
        else:
            until = datetime.fromisoformat(ban_info['until'])
            bot.send_message(message.chat.id, f"🚫 You are banned!\nReason: {ban_info['reason']}\nUntil: {until.strftime('%d.%m.%Y %H:%M')}")
        return
    
    user_message = message.text
    
    if user_message.startswith('/'):
        return
    
    # Обработка админ команд
    if user_id == ADMIN_ID and user_id in admin_states:
        state = admin_states[user_id]
        
        if state == 'waiting_ban_user':
            target_id = user_message.strip()
            admin_states[user_id] = {'state': 'waiting_ban_reason', 'target_id': target_id}
            bot.send_message(message.chat.id, "📝 Введите причину бана:")
            return
        
        elif state == 'waiting_ban_reason':
            target_id = admin_states[user_id]['target_id']
            reason = user_message
            admin_states[user_id] = {'state': 'waiting_ban_duration', 'target_id': target_id, 'reason': reason}
            bot.send_message(message.chat.id, "⏰ Введите длительность бана (в часах) или 'permanent' для перманентного:")
            return
        
        elif state == 'waiting_ban_duration':
            target_id = admin_states[user_id]['target_id']
            reason = admin_states[user_id]['reason']
            duration = user_message.lower()
            
            if duration == 'permanent':
                until = 'permanent'
                time_text = "навсегда"
            else:
                try:
                    hours = int(duration)
                    until = (datetime.now() + timedelta(hours=hours)).isoformat()
                    time_text = f"на {hours} час(ов)"
                except:
                    bot.send_message(message.chat.id, "❌ Неверный формат! Используйте число или 'permanent'")
                    return
            
            banned_users[target_id] = {
                'reason': reason,
                'until': until,
                'banned_by': user_id,
                'banned_at': datetime.now().isoformat()
            }
            save_banned_users(banned_users)
            
            bot.send_message(message.chat.id, f"✅ Пользователь {target_id} забанен {time_text}\nПричина: {reason}")
            del admin_states[user_id]
            return
        
        elif state == 'waiting_mailing':
            admin_states[user_id] = {'state': 'waiting_mailing_confirm', 'message': user_message}
            keyboard = InlineKeyboardMarkup()
            keyboard.add(
                InlineKeyboardButton("✅ Да, отправить", callback_data="mailing_confirm"),
                InlineKeyboardButton("❌ Нет, отмена", callback_data="mailing_cancel")
            )
            bot.send_message(message.chat.id, f"📨 Рассылка:\n\n{user_message}\n\nОтправить всем пользователям?", reply_markup=keyboard)
            return
    
    # Проверяем, активна ли игра "Угадай число"
    guess_key = f"guess_{user_id}"
    if guess_key in games_data:
        game = games_data[guess_key]['game']
        if not game.game_over:
            try:
                guess_num = int(user_message.strip())
                if 1 <= guess_num <= 100:
                    success, result = game.guess(guess_num)
                    
                    if success or game.game_over:
                        if success:
                            update_player_stats(user_id, message.from_user.username, 'guess', 'win')
                            result_text = f"🎉 *Victory!*\n\n{result}"
                        else:
                            update_player_stats(user_id, message.from_user.username, 'guess', 'loss')
                            result_text = f"😔 *Defeat*\n\n{result}"
                        
                        lang = players_stats.get(str(user_id), {}).get('lang', 'ru')
                        menu = main_menu(lang)
                        bot.send_message(message.chat.id, result_text, parse_mode='Markdown', reply_markup=menu)
                        del games_data[guess_key]
                        save_games_data(games_data)
                    else:
                        bot.send_message(message.chat.id, result, parse_mode='Markdown', reply_markup=guess_keyboard(user_id))
                    return
                else:
                    bot.send_message(message.chat.id, "Enter a number from 1 to 100!", reply_markup=guess_keyboard(user_id))
                    return
            except ValueError:
                bot.send_message(message.chat.id, "Enter a number from 1 to 100!", reply_markup=guess_keyboard(user_id))
                return
    
    # Проверяем, активен ли режим чата
    chat_mode_key = f"chat_mode_{user_id}"
    if chat_mode_key in games_data:
        mode = games_data[chat_mode_key]
        lang = players_stats.get(str(user_id), {}).get('lang', 'ru')
        
        if mode == "normal":
            save_chat_message(user_id, "user", user_message)
            
            try:
                bot.send_chat_action(message.chat.id, 'typing')
            except:
                pass
            
            response = get_gpt_response(user_id, user_message, lang)
            
            if response:
                save_chat_message(user_id, "assistant", response)
                back_menu = InlineKeyboardMarkup()
                if lang == 'ru':
                    back_menu.add(InlineKeyboardButton(f"{EMOJI['back']} Назад в меню", callback_data="back_to_menu"))
                else:
                    back_menu.add(InlineKeyboardButton(f"{EMOJI['back']} Back to menu", callback_data="back_to_menu"))
                bot.send_message(message.chat.id, response, reply_markup=back_menu)
            else:
                if lang == 'ru':
                    error_text = "Извини, у меня проблемы с интернетом. Давай попробуем еще раз :)"
                else:
                    error_text = "Sorry, I'm having internet issues. Let's try again :)"
                bot.send_message(message.chat.id, error_text, reply_markup=back_menu)
        else:
            if lang == 'ru':
                bot.send_message(message.chat.id, "🌸 *Режим в разработке!* 🌸\n\nСкоро здесь будет что-то интересное...", 
                               parse_mode='Markdown', reply_markup=back_menu)
            else:
                bot.send_message(message.chat.id, "🌸 *Mode in development!* 🌸\n\nSomething interesting will be here soon...", 
                               parse_mode='Markdown', reply_markup=back_menu)
        return

@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    global current_user_id_for_menu
    user_id = call.from_user.id
    data = call.data
    
    # Проверка бана
    banned, ban_info = is_user_banned(user_id)
    if banned:
        bot.answer_callback_query(call.id, "🚫 You are banned!", show_alert=True)
        return
    
    # Получаем язык пользователя
    lang = players_stats.get(str(user_id), {}).get('lang', 'ru')
    current_user_id_for_menu = user_id
    
    try:
        if data == "back_to_menu":
            menu = main_menu(lang)
            if lang == 'ru':
                text = "✨ Главное меню ✨\n\nВыбери что хочешь сделать:"
            else:
                text = "✨ Main Menu ✨\n\nChoose what you want to do:"
            
            bot.edit_message_text(text, call.message.chat.id, call.message.message_id,
                                reply_markup=menu)
            
            chat_mode_key = f"chat_mode_{user_id}"
            if chat_mode_key in games_data:
                del games_data[chat_mode_key]
                save_games_data(games_data)
        
        elif data.startswith("switch_lang_"):
            new_lang = data.split('_')[2]
            if str(user_id) in players_stats:
                players_stats[str(user_id)]['lang'] = new_lang
                save_players_stats(players_stats)
            
            menu = main_menu(new_lang)
            if new_lang == 'ru':
                text = "✨ Язык изменен на русский ✨\n\nВыбери что хочешь сделать:"
            else:
                text = "✨ Language changed to English ✨\n\nChoose what you want to do:"
            
            bot.edit_message_text(text, call.message.chat.id, call.message.message_id,
                                reply_markup=menu)
        
        elif data == "my_stats":
            stats_text = get_player_stats(user_id, lang)
            back_btn = InlineKeyboardMarkup()
            if lang == 'ru':
                back_btn.add(InlineKeyboardButton(f"{EMOJI['back']} Назад", callback_data="back_to_menu"))
            else:
                back_btn.add(InlineKeyboardButton(f"{EMOJI['back']} Back", callback_data="back_to_menu"))
            bot.edit_message_text(stats_text, call.message.chat.id, call.message.message_id,
                                parse_mode='Markdown', reply_markup=back_btn)
        
        elif data == "global_stats":
            if not players_stats:
                if lang == 'ru':
                    stats_text = "📊 Статистика пока пуста. Сыграй в игры!"
                else:
                    stats_text = "📊 Stats are empty for now. Play some games!"
            else:
                total_players = len(players_stats)
                total_games = sum(p['total_games'] for p in players_stats.values())
                total_wins = sum(p['total_wins'] for p in players_stats.values())
                
                top_players = sorted(players_stats.items(), 
                                   key=lambda x: x[1]['total_wins'], reverse=True)[:5]
                
                if lang == 'ru':
                    stats_text = f"🌍 *Глобальная статистика*\n\n"
                    stats_text += f"👥 Всего игроков: {total_players}\n"
                    stats_text += f"🎮 Всего игр: {total_games}\n"
                    stats_text += f"🏆 Всего побед: {total_wins}\n"
                    if total_games > 0:
                        stats_text += f"📊 Общий винрейт: {total_wins/total_games*100:.1f}%\n\n"
                    
                    stats_text += f"⭐ *ТОП-5 ИГРОКОВ* ⭐\n"
                    for i, (uid, stats) in enumerate(top_players, 1):
                        winrate = stats['total_wins']/stats['total_games']*100 if stats['total_games'] > 0 else 0
                        medal = {1: "🥇", 2: "🥈", 3: "🥉"}.get(i, "•")
                        stats_text += f"{medal} {stats['username']} — {stats['total_wins']} побед ({winrate:.1f}%)\n"
                else:
                    stats_text = f"🌍 *Global Stats*\n\n"
                    stats_text += f"👥 Total players: {total_players}\n"
                    stats_text += f"🎮 Total games: {total_games}\n"
                    stats_text += f"🏆 Total wins: {total_wins}\n"
                    if total_games > 0:
                        stats_text += f"📊 Global winrate: {total_wins/total_games*100:.1f}%\n\n"
                    
                    stats_text += f"⭐ *TOP-5 PLAYERS* ⭐\n"
                    for i, (uid, stats) in enumerate(top_players, 1):
                        winrate = stats['total_wins']/stats['total_games']*100 if stats['total_games'] > 0 else 0
                        medal = {1: "🥇", 2: "🥈", 3: "🥉"}.get(i, "•")
                        stats_text += f"{medal} {stats['username']} — {stats['total_wins']} wins ({winrate:.1f}%)\n"
            
            back_btn = InlineKeyboardMarkup()
            if lang == 'ru':
                back_btn.add(InlineKeyboardButton(f"{EMOJI['back']} Назад", callback_data="back_to_menu"))
            else:
                back_btn.add(InlineKeyboardButton(f"{EMOJI['back']} Back", callback_data="back_to_menu"))
            bot.edit_message_text(stats_text, call.message.chat.id, call.message.message_id,
                                parse_mode='Markdown', reply_markup=back_btn)
        
        elif data == "game_ttt":
            if lang == 'ru':
                text = "🎮 *Крестики-нолики*\n\nВыбери сложность:"
            else:
                text = "🎮 *Tic-tac-toe*\n\nChoose difficulty:"
            bot.edit_message_text(text, call.message.chat.id, call.message.message_id,
                                parse_mode='Markdown', reply_markup=difficulty_menu(lang))
        
        elif data == "game_rps":
            game = RPS()
            games_data[f"rps_{user_id}"] = {'game': game}
            save_games_data(games_data)
            
            if lang == 'ru':
                game_text = f"🪨✂️📄 *Камень-ножницы-бумага*\n\nСчет: Ты 0 : 0 Юки\n\nСделай выбор:"
            else:
                game_text = f"🪨✂️📄 *Rock-paper-scissors*\n\nScore: You 0 : 0 Yuki\n\nMake your choice:"
            bot.edit_message_text(game_text, call.message.chat.id, call.message.message_id,
                                parse_mode='Markdown', reply_markup=rps_keyboard(user_id, lang))
        
        elif data == "game_guess":
            game = GuessNumber()
            games_data[f"guess_{user_id}"] = {'game': game}
            save_games_data(games_data)
            
            if lang == 'ru':
                game_text = f"🔮 *Угадай число*\n\nЯ загадала число от 1 до 100!\nУ тебя 10 попыток ✨\n\nВведи число или используй кнопки:"
            else:
                game_text = f"🔮 *Guess the number*\n\nI'm thinking of a number from 1 to 100!\nYou have 10 attempts ✨\n\nEnter a number or use buttons:"
            bot.edit_message_text(game_text, call.message.chat.id, call.message.message_id,
                                parse_mode='Markdown', reply_markup=guess_keyboard(user_id, lang))
        
        elif data == "chat_mode":
            if lang == 'ru':
                text = "💬 *Общение с Юки*\n\nВыбери режим общения:"
            else:
                text = "💬 *Chat with Yuki*\n\nChoose chat mode:"
            bot.edit_message_text(text, call.message.chat.id, call.message.message_id,
                                parse_mode='Markdown', reply_markup=chat_mode_menu(lang))
        
        elif data == "chat_normal":
            games_data[f"chat_mode_{user_id}"] = "normal"
            save_games_data(games_data)
            
            if lang == 'ru':
                start_text = """💬 *Обычный режим общения*

Теперь ты можешь просто писать мне, и я буду отвечать как обычная девушка.

Можешь спрашивать о чем угодно, рассказывать о себе или просто болтать.

Напиши что-нибудь! ✨"""
            else:
                start_text = """💬 *Normal chat mode*

Now you can just write to me, and I will answer like a normal girl.

You can ask about anything, tell me about yourself, or just chat.

Write something! ✨"""
            
            back_btn = InlineKeyboardMarkup()
            if lang == 'ru':
                back_btn.add(InlineKeyboardButton(f"{EMOJI['back']} Назад в меню", callback_data="back_to_menu"))
            else:
                back_btn.add(InlineKeyboardButton(f"{EMOJI['back']} Back to menu", callback_data="back_to_menu"))
            bot.edit_message_text(start_text, call.message.chat.id, call.message.message_id,
                                parse_mode='Markdown', reply_markup=back_btn)
        
        elif data == "chat_lewd":
            if lang == 'ru':
                lewd_text = """🔥 *Пошлый режим* 🔥

*В разработке!*

Скоро здесь появится что-то интересное... 
Обещаю, будет весело! 😏"""
            else:
                lewd_text = """🔥 *Lewd mode* 🔥

*In development!*

Something interesting will be here soon...
I promise it will be fun! 😏"""
            
            back_btn = InlineKeyboardMarkup()
            if lang == 'ru':
                back_btn.add(InlineKeyboardButton(f"{EMOJI['back']} Назад в меню", callback_data="back_to_menu"))
            else:
                back_btn.add(InlineKeyboardButton(f"{EMOJI['back']} Back to menu", callback_data="back_to_menu"))
            bot.edit_message_text(lewd_text, call.message.chat.id, call.message.message_id,
                                parse_mode='Markdown', reply_markup=back_btn)
        
        # АДМИН ПАНЕЛЬ
        elif data == "admin_panel":
            if user_id != ADMIN_ID:
                bot.answer_callback_query(call.id, "⛔ Доступ запрещен!", show_alert=True)
                return
            bot.edit_message_text("👑 *Админ панель*\n\nВыберите действие:", 
                                call.message.chat.id, call.message.message_id,
                                parse_mode='Markdown', reply_markup=admin_panel())
        
        elif data == "admin_ban":
            if user_id != ADMIN_ID:
                return
            admin_states[user_id] = 'waiting_ban_user'
            bot.edit_message_text("🔨 *Бан пользователя*\n\nВведите ID пользователя для бана:", 
                                call.message.chat.id, call.message.message_id,
                                parse_mode='Markdown', reply_markup=back_menu())
        
        elif data == "admin_users_list":
            if user_id != ADMIN_ID:
                return
            users = get_all_users()
            if not users:
                text = "📋 Список пользователей пуст"
            else:
                text = "📋 *Список пользователей*\n\n"
                for u in users[:20]:  # Показываем первых 20
                    text += f"🆔 `{u['id']}` - {u['username']} (игр: {u['games']})\n"
                if len(users) > 20:
                    text += f"\n...и еще {len(users)-20} пользователей"
            bot.edit_message_text(text, call.message.chat.id, call.message.message_id,
                                parse_mode='Markdown', reply_markup=admin_panel())
        
        elif data == "admin_mailing":
            if user_id != ADMIN_ID:
                return
            admin_states[user_id] = 'waiting_mailing'
            bot.edit_message_text("📨 *Рассылка*\n\nВведите текст сообщения для рассылки всем пользователям:", 
                                call.message.chat.id, call.message.message_id,
                                parse_mode='Markdown', reply_markup=back_menu())
        
        elif data == "admin_stats":
            if user_id != ADMIN_ID:
                return
            stats_text = get_bot_stats()
            bot.edit_message_text(stats_text, call.message.chat.id, call.message.message_id,
                                parse_mode='Markdown', reply_markup=admin_panel())
        
        elif data == "mailing_confirm":
            if user_id != ADMIN_ID:
                return
            if user_id in admin_states and admin_states[user_id].get('state') == 'waiting_mailing_confirm':
                msg_text = admin_states[user_id]['message']
                users = get_all_users()
                sent = 0
                failed = 0
                
                for user in users:
                    try:
                        bot.send_message(int(user['id']), f"📢 *Рассылка от админа*\n\n{msg_text}", parse_mode='Markdown')
                        sent += 1
                        time.sleep(0.05)
                    except:
                        failed += 1
                
                bot.edit_message_text(f"✅ Рассылка завершена!\nОтправлено: {sent}\nНе доставлено: {failed}", 
                                    call.message.chat.id, call.message.message_id,
                                    reply_markup=admin_panel())
                del admin_states[user_id]
        
        elif data == "mailing_cancel":
            if user_id != ADMIN_ID:
                return
            if user_id in admin_states:
                del admin_states[user_id]
            bot.edit_message_text("❌ Рассылка отменена", 
                                call.message.chat.id, call.message.message_id,
                                reply_markup=admin_panel())
        
        elif data in ["ttt_easy", "ttt_normal", "ttt_hard"]:
            difficulty = data.split('_')[1]
            game = TicTacToe(difficulty)
            games_data[f"ttt_{user_id}"] = {'game': game, 'difficulty': difficulty}
            save_games_data(games_data)
            
            difficulty_names = {'easy': 'Easy', 'normal': 'Normal', 'hard': 'Hard'}
            if lang == 'ru':
                difficulty_names = {'easy': 'Легко', 'normal': 'Нормально', 'hard': 'Сложно'}
            
            board_text = f"❌⭕ *Tic-tac-toe* (Difficulty: {difficulty_names[difficulty]})\n\n{game.get_board_display()}\n\nYour turn:"
            bot.edit_message_text(board_text, call.message.chat.id, call.message.message_id,
                                parse_mode='Markdown', reply_markup=tic_tac_toe_keyboard(game, user_id))
        
        elif data.startswith("ttt_move_"):
            parts = data.split('_')
            if len(parts) == 4 and parts[2] == str(user_id):
                move = int(parts[3])
                game_key = f"ttt_{user_id}"
                
                if game_key in games_data:
                    game = games_data[game_key]['game']
                    
                    if game.make_move(move):
                        if game.game_over:
                            if game.winner == 'X':
                                result_text = f"🎉 *Victory!*\n\n{game.get_board_display()}\n\nYou won!"
                                update_player_stats(user_id, call.from_user.username, 'ttt', 'win', game.difficulty)
                            elif game.winner == 'O':
                                result_text = f"😔 *Defeat*\n\n{game.get_board_display()}\n\nI won..."
                                update_player_stats(user_id, call.from_user.username, 'ttt', 'loss', game.difficulty)
                            else:
                                result_text = f"🤝 *Draw*\n\n{game.get_board_display()}\n\nIt's a draw!"
                                update_player_stats(user_id, call.from_user.username, 'ttt', 'draw', game.difficulty)
                            
                            menu = main_menu(lang)
                            bot.edit_message_text(result_text, call.message.chat.id, call.message.message_id,
                                                parse_mode='Markdown', reply_markup=menu)
                            del games_data[game_key]
                            save_games_data(games_data)
                        else:
                            game.bot_move()
                            
                            if game.game_over:
                                if game.winner == 'X':
                                    result_text = f"🎉 *Victory!*\n\n{game.get_board_display()}\n\nYou won!"
                                    update_player_stats(user_id, call.from_user.username, 'ttt', 'win', game.difficulty)
                                elif game.winner == 'O':
                                    result_text = f"😔 *Defeat*\n\n{game.get_board_display()}\n\nI won..."
                                    update_player_stats(user_id, call.from_user.username, 'ttt', 'loss', game.difficulty)
                                else:
                                    result_text = f"🤝 *Draw*\n\n{game.get_board_display()}\n\nIt's a draw!"
                                    update_player_stats(user_id, call.from_user.username, 'ttt', 'draw', game.difficulty)
                                
                                menu = main_menu(lang)
                                bot.edit_message_text(result_text, call.message.chat.id, call.message.message_id,
                                                    parse_mode='Markdown', reply_markup=menu)
                                del games_data[game_key]
                                save_games_data(games_data)
                            else:
                                board_text = f"❌⭕ *Tic-tac-toe* (Difficulty: {game.difficulty})\n\n{game.get_board_display()}\n\nYour turn:"
                                bot.edit_message_text(board_text, call.message.chat.id, call.message.message_id,
                                                    parse_mode='Markdown', reply_markup=tic_tac_toe_keyboard(game, user_id))
                            save_games_data(games_data)
        
        elif data.startswith("rps_rock_") or data.startswith("rps_scissors_") or data.startswith("rps_paper_"):
            parts = data.split('_')
            if len(parts) == 3 and parts[2] == str(user_id):
                choice_map = {
                    'rock': '🪨',
                    'scissors': '✂️',
                    'paper': '📄'
                }
                player_choice = choice_map[parts[1]]
                game_key = f"rps_{user_id}"
                
                if game_key in games_data:
                    game = games_data[game_key]['game']
                    result, bot_choice, winner = game.play(player_choice)
                    
                    update_text = f"🪨✂️📄 *Rock-paper-scissors*\n\n"
                    update_text += f"Your choice: {player_choice} {game.choices[player_choice]}\n"
                    update_text += f"My choice: {bot_choice} {game.choices[bot_choice]}\n\n"
                    update_text += f"{result}\n\n"
                    update_text += f"📊 Score: You {game.player_score} : {game.bot_score} Me\n"
                    update_text += f"🎲 Round: {game.rounds}\n\n"
                    
                    if winner == 'draw':
                        stats_result = 'draw'
                    elif winner == 'player':
                        stats_result = 'win'
                    else:
                        stats_result = 'loss'
                    
                    update_player_stats(user_id, call.from_user.username, 'rps', stats_result)
                    
                    update_text += "Make your next choice:"
                    bot.edit_message_text(update_text, call.message.chat.id, call.message.message_id,
                                        parse_mode='Markdown', reply_markup=rps_keyboard(user_id, lang))
                    save_games_data(games_data)
        
        elif data.startswith("guess_num_"):
            parts = data.split('_')
            if len(parts) == 4 and parts[2] == str(user_id):
                guess_num = int(parts[3])
                game_key = f"guess_{user_id}"
                
                if game_key in games_data:
                    game = games_data[game_key]['game']
                    success, result = game.guess(guess_num)
                    
                    if success or game.game_over:
                        if success:
                            update_player_stats(user_id, call.from_user.username, 'guess', 'win')
                            result_text = f"🎉 *Victory!*\n\n{result}"
                        else:
                            update_player_stats(user_id, call.from_user.username, 'guess', 'loss')
                            result_text = f"😔 *Defeat*\n\n{result}"
                        
                        menu = main_menu(lang)
                        bot.edit_message_text(result_text, call.message.chat.id, call.message.message_id,
                                            parse_mode='Markdown', reply_markup=menu)
                        del games_data[game_key]
                        save_games_data(games_data)
                    else:
                        bot.edit_message_text(result, call.message.chat.id, call.message.message_id,
                                            parse_mode='Markdown', reply_markup=guess_keyboard(user_id, lang))
        
        elif data.startswith("guess_custom_"):
            parts = data.split('_')
            if len(parts) == 3 and parts[2] == str(user_id):
                if lang == 'ru':
                    text = "🔢 Введи число от 1 до 100:"
                else:
                    text = "🔢 Enter a number from 1 to 100:"
                bot.edit_message_text(text, call.message.chat.id, call.message.message_id,
                                    reply_markup=guess_keyboard(user_id, lang))
        
        elif data.startswith("ttt_exit_"):
            parts = data.split('_')
            if len(parts) == 3 and parts[2] == str(user_id):
                game_key = f"ttt_{user_id}"
                if game_key in games_data:
                    del games_data[game_key]
                    save_games_data(games_data)
                if lang == 'ru':
                    text = "🚪 Игра завершена. Возвращаюсь в меню..."
                else:
                    text = "🚪 Game over. Returning to menu..."
                bot.edit_message_text(text, call.message.chat.id, call.message.message_id,
                                    reply_markup=main_menu(lang))
        
        elif data.startswith("rps_exit_"):
            parts = data.split('_')
            if len(parts) == 3 and parts[2] == str(user_id):
                game_key = f"rps_{user_id}"
                if game_key in games_data:
                    del games_data[game_key]
                    save_games_data(games_data)
                if lang == 'ru':
                    text = "🚪 Игра завершена. Возвращаюсь в меню..."
                else:
                    text = "🚪 Game over. Returning to menu..."
                bot.edit_message_text(text, call.message.chat.id, call.message.message_id,
                                    reply_markup=main_menu(lang))
        
        elif data.startswith("guess_exit_"):
            parts = data.split('_')
            if len(parts) == 3 and parts[2] == str(user_id):
                game_key = f"guess_{user_id}"
                if game_key in games_data:
                    del games_data[game_key]
                    save_games_data(games_data)
                if lang == 'ru':
                    text = "🚪 Игра завершена. Возвращаюсь в меню..."
                else:
                    text = "🚪 Game over. Returning to menu..."
                bot.edit_message_text(text, call.message.chat.id, call.message.message_id,
                                    reply_markup=main_menu(lang))
        
        bot.answer_callback_query(call.id)
    
    except Exception as e:
        print(f"Ошибка: {e}")

# Вспомогательные функции для меню
def difficulty_menu(lang='ru'):
    keyboard = InlineKeyboardMarkup(row_width=3)
    if lang == 'ru':
        keyboard.add(
            InlineKeyboardButton(f"{EMOJI['easy']} Легко", callback_data="ttt_easy"),
            InlineKeyboardButton(f"{EMOJI['normal']} Нормально", callback_data="ttt_normal"),
            InlineKeyboardButton(f"{EMOJI['hard']} Сложно", callback_data="ttt_hard")
        )
    else:
        keyboard.add(
            InlineKeyboardButton(f"{EMOJI['easy']} Easy", callback_data="ttt_easy"),
            InlineKeyboardButton(f"{EMOJI['normal']} Normal", callback_data="ttt_normal"),
            InlineKeyboardButton(f"{EMOJI['hard']} Hard", callback_data="ttt_hard")
        )
    keyboard.add(InlineKeyboardButton(f"{EMOJI['back']} Back", callback_data="back_to_menu"))
    return keyboard

def tic_tac_toe_keyboard(game, user_id):
    keyboard = InlineKeyboardMarkup(row_width=3)
    buttons = []
    for i in range(9):
        if game.board[i] == ' ':
            text = f"{EMOJI['empty']}"
        elif game.board[i] == 'X':
            text = f"{EMOJI['x']}"
        else:
            text = f"{EMOJI['o']}"
        buttons.append(InlineKeyboardButton(text, callback_data=f"ttt_move_{user_id}_{i}"))
    
    keyboard.add(*buttons[:3])
    keyboard.add(*buttons[3:6])
    keyboard.add(*buttons[6:9])
    keyboard.add(InlineKeyboardButton(f"{EMOJI['exit']} Exit", callback_data=f"ttt_exit_{user_id}"))
    
    return keyboard

def rps_keyboard(user_id, lang='ru'):
    keyboard = InlineKeyboardMarkup(row_width=3)
    if lang == 'ru':
        keyboard.add(
            InlineKeyboardButton(f"{EMOJI['rock']} Камень", callback_data=f"rps_rock_{user_id}"),
            InlineKeyboardButton(f"{EMOJI['scissors']} Ножницы", callback_data=f"rps_scissors_{user_id}"),
            InlineKeyboardButton(f"{EMOJI['paper']} Бумага", callback_data=f"rps_paper_{user_id}")
        )
    else:
        keyboard.add(
            InlineKeyboardButton(f"{EMOJI['rock']} Rock", callback_data=f"rps_rock_{user_id}"),
            InlineKeyboardButton(f"{EMOJI['scissors']} Scissors", callback_data=f"rps_scissors_{user_id}"),
            InlineKeyboardButton(f"{EMOJI['paper']} Paper", callback_data=f"rps_paper_{user_id}")
        )
    keyboard.add(InlineKeyboardButton(f"{EMOJI['exit']} Exit", callback_data=f"rps_exit_{user_id}"))
    return keyboard

def guess_keyboard(user_id, lang='ru'):
    keyboard = InlineKeyboardMarkup(row_width=5)
    buttons = []
    for i in range(1, 11):
        buttons.append(InlineKeyboardButton(str(i), callback_data=f"guess_num_{user_id}_{i}"))
    
    keyboard.add(*buttons[:5])
    keyboard.add(*buttons[5:10])
    if lang == 'ru':
        keyboard.add(
            InlineKeyboardButton("🔢 Свой вариант", callback_data=f"guess_custom_{user_id}"),
            InlineKeyboardButton(f"{EMOJI['exit']} Выйти", callback_data=f"guess_exit_{user_id}")
        )
    else:
        keyboard.add(
            InlineKeyboardButton("🔢 Custom", callback_data=f"guess_custom_{user_id}"),
            InlineKeyboardButton(f"{EMOJI['exit']} Exit", callback_data=f"guess_exit_{user_id}")
        )
    return keyboard

def chat_mode_menu(lang='ru'):
    keyboard = InlineKeyboardMarkup(row_width=2)
    if lang == 'ru':
        keyboard.add(
            InlineKeyboardButton("✨ Обычный режим", callback_data="chat_normal"),
            InlineKeyboardButton("🔥 Пошлый режим", callback_data="chat_lewd")
        )
        keyboard.add(InlineKeyboardButton(f"{EMOJI['back']} Назад", callback_data="back_to_menu"))
    else:
        keyboard.add(
            InlineKeyboardButton("✨ Normal mode", callback_data="chat_normal"),
            InlineKeyboardButton("🔥 Lewd mode", callback_data="chat_lewd")
        )
        keyboard.add(InlineKeyboardButton(f"{EMOJI['back']} Back", callback_data="back_to_menu"))
    return keyboard

def back_menu():
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton(f"{EMOJI['back']} Назад", callback_data="back_to_menu"))
    return keyboard

def run_bot():
    while True:
        try:
            print("🌸 Юки запущена!")
            print("🎮 Игры и общение в одном боте")
            print("💬 Готова к работе")
            print(f"👑 Админ ID: {ADMIN_ID}")
            print("")
            bot.remove_webhook()
            bot.infinity_polling(timeout=60)
        except Exception as e:
            print(f"Ошибка: {e}")
            time.sleep(5)

if __name__ == '__main__':
    run_bot()
