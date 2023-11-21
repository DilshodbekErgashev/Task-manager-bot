
import telebot
from telebot import types
import psycopg2

token = '5785935703:AAFHBmB5TGi9zxQZvOTEokQzifbBfJIKGWA'
bot = telebot.TeleBot(token)

def make_conn():
    conn = psycopg2.connect(
        database="task_manager",
        user="postgres",
        password="111200209",
        host="localhost"
    )
    return conn

def create_table(user_id):
    conn = make_conn()
    curr = conn.cursor()

    query = f"""
    CREATE TABLE IF NOT EXISTS tasks_{user_id} (
        id SERIAL PRIMARY KEY,
        title VARCHAR(25),
        due_date DATE,
        priority INTEGER
    );
    """
    curr.execute(query)
    conn.commit()

    curr.close()
    conn.close()

def add_task_to_db(user_id, task_description, deadline, priority):
    conn = make_conn()
    curr = conn.cursor()

    query = f"""
    INSERT INTO tasks_{user_id} (title, due_date, priority)
    VALUES (%s, %s, %s);
    """
    curr.execute(query, (task_description, deadline, priority))
    conn.commit()

    curr.close()
    conn.close()

def get_tasks_from_db(user_id):
    conn = make_conn()
    curr = conn.cursor()

    query = f"SELECT * FROM tasks_{user_id} ORDER BY due_date;"
    curr.execute(query)
    tasks = curr.fetchall()

    curr.close()
    conn.close()

    return tasks

def delete_task_from_db(user_id, task_id):
    conn = make_conn()
    curr = conn.cursor()

    query = f"DELETE FROM tasks_{user_id} WHERE id = %s;"
    curr.execute(query, (task_id,))
    conn.commit()

    curr.close()
    conn.close()

@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    create_table(user_id)
    keyboard = types.ReplyKeyboardMarkup(True)
    keyboard.row('✅ Добавить задачу', '📋 Показать задачи')
    keyboard.row('⏰ Сортировка по времени', '⭐️ Сортировка по приоритету')
    keyboard.row('❌ Удалить задачу')
    
    bot.send_message(message.chat.id, f'Привет, {message.from_user.first_name}! 😊 Я бот-менеджер задач. Чем могу помочь?', reply_markup=keyboard)

@bot.message_handler(commands=['help'])
def help(message):
    bot.send_message(message.chat.id, '⏰ Добавляйте напоминания, чтобы не забыть важные вещи')

@bot.message_handler(func=lambda message: message.text == '✅ Добавить задачу')
def add_task(message):
    bot.send_message(message.chat.id, 'Пожалуйста, введите задачу, которую вы хотите добавить:')
    bot.register_next_step_handler(message, add_task_description)

def add_task_description(message):
    task_description = message.text
    bot.send_message(message.chat.id, 'Пожалуйста, введите срок выполнения этой задачи (ГГГГ-ММ-ДД):')
    bot.register_next_step_handler(message, add_task_deadline, task_description)

def add_task_deadline(message, task_description):
    deadline = message.text.strip()
    bot.send_message(message.chat.id, 'Пожалуйста, введите приоритет задачи (от 1 до 5):')
    bot.register_next_step_handler(message, add_task_priority, task_description, deadline)

def add_task_priority(message, task_description, deadline):
    priority = message.text.strip()
    user_id = message.from_user.id
    add_task_to_db(user_id, task_description, deadline, priority)
    bot.send_message(message.chat.id, 'Задача успешно добавлена!✅')

@bot.message_handler(func=lambda message: message.text == '📋 Показать задачи')
def show_tasks(message):
    user_id = message.from_user.id
    tasks = get_tasks_from_db(user_id)
    if len(tasks) > 0:
        response = 'Ваши задачи:\n'
        for index, task in enumerate(tasks):
            response += f'{index+1}. Описание: {task[1]}, Срок: {task[2]}, Приоритет: {task[3]}\n'
        bot.send_message(message.chat.id, response)
    else:
        bot.send_message(message.chat.id, 'У вас нет задач на данный момент.')

@bot.message_handler(func=lambda message: message.text == '⏰ Сортировка по времени')
def sort_by_time(message):
    user_id = message.from_user.id
    tasks = get_tasks_from_db(user_id)
    if len(tasks) > 0:
        sorted_tasks = sorted(tasks, key=lambda x: x[2])
        response = 'Задачи отсортированы по времени:\n'
        for index, task in enumerate(sorted_tasks):
            response += f'{index+1}. Описание: {task[1]}, Срок: {task[2]}, Приоритет: {task[3]}\n'
        bot.send_message(message.chat.id, response)
    else:
        bot.send_message(message.chat.id, 'У вас нет задач на данный момент.')

@bot.message_handler(func=lambda message: message.text == '⭐️ Сортировка по приоритету')
def sort_by_priority(message):
    user_id = message.from_user.id
    tasks = get_tasks_from_db(user_id)
    if len(tasks) > 0:
        sorted_tasks = sorted(tasks, key=lambda x: x[3])
        response = 'Задачи отсортированы по приоритету:\n'
        for index, task in enumerate(sorted_tasks):
            response += f'{index+1}. Описание: {task[1]}, Срок: {task[2]}, Приоритет: {task[3]}\n'
        bot.send_message(message.chat.id, response)
    else:
        bot.send_message(message.chat.id, 'У вас нет задач на данный момент.😶')
        
@bot.message_handler(func=lambda message: message.text.startswith('❌ Удалить задачу'))
def delete_task(message):
    user_id = message.from_user.id
    tasks = get_tasks_from_db(user_id)
    if len(tasks) > 0:
        response = 'Выберите задачу для удаления (введите ID):\n'
        for task in tasks:
            response += f'ID: {task[0]}, Описание: {task[1]}, Срок: {task[2]}, Приоритет: {task[3]}\n'
        bot.send_message(message.chat.id, response)
        bot.register_next_step_handler(message, delete_task_confirm)
    else:
        bot.send_message(message.chat.id, 'У вас нет задач на данный момент.')

def delete_task_confirm(message):
    task_id_text = message.text.strip()
    if task_id_text:
        try:
            task_id = int(task_id_text)
            user_id = message.from_user.id
            delete_task_from_db(user_id, task_id)
            bot.reply_to(message, 'Задача успешно удалена!')
        except ValueError:
            bot.reply_to(message, 'Неверный формат ID задачи.')
    else:
        bot.reply_to(message, 'Необходимо указать ID задачи.')
        
@bot.message_handler(func=lambda message: True)
def handle_all_other_messages(message):
    if message.text.startswith('/') and not message.text.startswith('/start') and not message.text.startswith('/help'):
        bot.send_message(message.chat.id, 'Извините, я не понимаю эту команду.☹️')
    else:
        bot.send_message(message.chat.id, 'Извините, я не понимаю эту команду.☹️')

bot.polling(none_stop=True)
