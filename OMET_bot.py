from const import TOKEN, my_chat_id, max_chat_id, di_chat_id, email_sender, password_sender, recipient_email
from flask import Flask, request
import json
import telebot
from telebot import types
import sqlite3 as sq
import datetime
import re
import os
import requests
import functools
import time
import schedule
from tabulate import tabulate
import threading


app = Flask(__name__)

bot = telebot.TeleBot(TOKEN, parse_mode=None)

#Create a route for your webhook:
@app.route('/bot', methods=['POST']) #allows only HttpPost requests ro be sent to '/bot'
def handle_updates():
    update = json.loads(request.data)  # it accesses incoming request's data and parses in Py dictionary

    if 'message' in update:
        message = types.Message.de_json(update['message']) #calls the de_json() method from the telebot.types.
        # Message class to convert the JSON data from the update['message'] into a Message object,
        # which can be processed by the TeleBot library. The Message
        bot.process_new_messages([message]) 

    return 'OK', 200

# create an empty dictionary to store user data
user_data = {}

# create date: 05.03.2023 and time: 12:00
date_1 = datetime.date(2023, 3, 5)
time_1 = datetime.time(12,0)

table_name = f"tour_at_{date_1.strftime('%d_%m_%Y')}_{time_1.strftime('%H_%M')}"#.replace('-', '_')
#SQL doesn`t allow '-', so i have to replace it

# open file with database
with sq.connect('mus_schedule.db', check_same_thread=False) as connect:
  cursor = connect.cursor()

"""cursor.execute(...): This method executes an SQL query using the cursor object, which is typically created from an active
SQLite connection.
The SQL query inside the execute method is an f-string, which is a formatted string literal in Python that allows you to embed
expressions inside string literals. The expressions are enclosed in curly braces {} and are replaced with their values when the
string is created.
.fetchone(): This method retrieves the first row of the result set returned by the SQL query. If the table with the specified
name exists in the database, fetchone() will return a tuple containing the table's name. If the table doesn't exist, fetchone()
will return None."""
if cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}';").fetchone():
  cursor.execute(f"SELECT SUM(quantity) FROM {table_name}")
  total_quantity = cursor.fetchone()[0] # return tuple with 'Sum'
  if total_quantity is not None and total_quantity > 50:
  # create new table's parameters with group for the next hour
    datetime_1 = datetime.datetime.combine(date_1, time_1) + datetime.timedelta(hours=1) #combine to convert in 'date' object 
    time_1 = datetime_1.time() #cause adding hours is forbidden
  

table_name = f"tour_at_{date_1.strftime('%d_%m_%Y')}_{time_1.strftime('%H_%M')}"

cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS {table_name} (
            name STRING,
            quantity INTEGER,
            contact STRING UNIQUE
            );   """)
connect.commit()




@bot.message_handler(commands=['omet','start']) # comands that responded
#@bot.message_handler(content_types=['text','sticker'])
def start_respond(message):
  
# photo_mus = types.InputMediaPhoto('https://scontent-ams2-1.xx.fbcdn.net/v/t1.6435-9/193684250_1184653448716244_1549048136683557681_n.jpg?
# _nc_cat=108&ccb=1-7&_nc_sid=8bfeb9&_nc_ohc=7yIjZg512oIAX-92GYU&_nc_ht=scontent-ams2-1.xx&oh=00_AfAudupE6CtYIyfwv4wymPOXc7HrylZBNvlL-KIs7B_Q3Q&oe=643A8642')
    
  text_menu=f"<i>{message.from_user.first_name}</i>.,виберіть та натисніть одну з кнопок нижче\n\
          <strong>1.Зареєструватись на найближчу екскурсію.</strong>\n\
          <strong>2.Відвідати наші соціальні мережі.</strong>\n\
          <strong>3.Залишити відгук відносно роботи електротранспорту.</strong>"
  # markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=False)
  markup=types.InlineKeyboardMarkup(row_width=1) #, resize_keyboard=True)
    
  button_1=types.InlineKeyboardButton(f"1.Екскурсія\
    {date_1.strftime ('%d-%m-%Y')} о {time_1}",callback_data='schedule')
     #photo = photo.read(),\
      #photo = photo_mus)
  with open('photo_2023-03-13_10-20-36.jpg', 'rb') as photo:
    bot.send_photo(message.chat.id, photo, reply_markup=markup)
    
  button_2=types.InlineKeyboardButton("2.Відвідати соц.мережі КП 'OMET'", callback_data='site')

  button_3=types.InlineKeyboardButton("3.Залишити відгук.", callback_data='respond')
  markup.add(button_1,button_2,button_3)
    
  bot.send_message(message.chat.id, text_menu, reply_markup=markup, parse_mode='html') #,resize_keybord=True)


@bot.message_handler(commands=['links'])
def duplicate_links(message):
    send_social_links(message) # The send_social_links function is responsible for sending a message with inline buttons containing
    # social media links or other relevant URLs. It does not register any next step handlers for the bot.
    # bot.register_next_step_handler(message, send_social_links) - This causes the bot to wait for the user's response before executing the send_social_links function. 

def send_social_links(message):
  markup = types.InlineKeyboardMarkup(row_width=1)
  
  site_button = types.InlineKeyboardButton("Сайт 'ОМЕТ'", url="https://oget.od.ua")
  facebook_button = types.InlineKeyboardButton("Facebook 'ОМЕТ'", url="https://www.facebook.com/kp.oget")
  instagram_button = types.InlineKeyboardButton("Instagram 'ОМЕТ'", url="https://instagram.com/kp_oget_staff_?igshid=YmMyMTA2M2Y=")
  link_1_button = types.InlineKeyboardButton("Facebook 'Музей'", url="https://www.facebook.com/museumoget?eav=Afbt3KtbE2zmGEaQqXN-5Y5dk-HZz96Qb4Tr-i44q0nSTsb1bPYiXdpFpx5kj3coJHY&paipv=0&_rdr")
  link_2_button = types.InlineKeyboardButton("Instagram 'Музей'", url="https://www.instagram.com/museum_kp_omet/?igshid=YmMyMTA2M2Y%3D")

  markup.add(site_button, facebook_button, instagram_button, link_1_button, link_2_button)

# variable 'message' - contains info about current msg, 'chat.id' - note the indeficator of chat, where is conversation with bot
  bot.send_message(message.chat.id, "Оберіть соціальну мережу або посилання:\n\
    Для повернення до головного меню натисніть - надрукуйте '/start' або '/omet'\n\
    Також ви завжди можете зв'язатись з нашим інформаційним центром за номером 717 54 54 або 788 688 6", reply_markup=markup)


def respond_buttons(message):
  markup = types.InlineKeyboardMarkup(row_width=3)

  text_button = types.InlineKeyboardButton("Текст", callback_data='text_respond')
  audio_button = types.InlineKeyboardButton("Аудіо", callback_data='audio_respond')
  video_button = types.InlineKeyboardButton("Відео", callback_data='video_respond')

  markup.add(text_button, audio_button, video_button)
    
  bot.send_message(message.chat.id, "Оберіть форму вашого звернення:", reply_markup=markup)


def skip_button(message):
  keyboard = types.InlineKeyboardMarkup()
  skip_button = types.InlineKeyboardButton("Без фото", callback_data='skip_image')
  keyboard.add(skip_button)


@bot.callback_query_handler(func=lambda call: True)
def callback(call):
  if call.message:  # check if button pushed
    if call.data == 'schedule':
      bot.send_message(call.message.chat.id, "Напишіть цифрами кількість людей,\
            які планують відвідати музей КП 'ОМЕТ'\n\
            (наприклад:'12' - бот ідентифікує лише цифрову складову у цьому повідомленні)")
      bot.register_next_step_handler(call.message, save_quantity) #When you register a next
      # step handler, it remains active until a new message from the user is received or another next step handler is registered.
      
    elif call.data == 'respond':
      respond_buttons(call.message) # call.message is likely an attribute of the call object that contains
      # information about the specific message or event that triggered the button response.
      
    elif call.data == 'site':
      send_social_links(call.message)
      
    elif call.data == 'text_respond':
      bot.register_next_step_handler(call.message, save_text_respond)
      bot.send_message(call.message.chat.id, "Введіть текстовий відгук.\n\
            у ньому вкажіть дату, час, адресу, номер транспортного засобу (якщо потрібно) та коротко опишіть ситуацію.\
            <b>(нагадуємо, що в повідомленні телеграма може вміститись близько 4000 символів)</b>", parse_mode='html')
          
    elif call.data == 'audio_respond':
      bot.register_next_step_handler(call.message, save_audio_respond)
      bot.send_message(call.message.chat.id, "Надішліть голосове повідомлення чи аудіо відгук тривалістю <b>до 1 хвилини</b>\n\
            у ньому озвучте дату, час, адресу, номер транспортного засобу (якщо потрібно) та коротко опишіть ситуацію.", parse_mode='html')
    
    elif call.data == 'video_respond':
      bot.register_next_step_handler(call.message, save_video_respond)
      bot.send_message(call.message.chat.id, ("Надішліть відео відгук чи відео повідомлення тривалістю <b>до 30 секунд</b>\n\
          у ньому озвучте дату, час, адресу, номер транспортного засобу (якщо потрібно) та коротко опишіть ситуацію.\n\
          <b>(завантаження відео на сервер може зайняти декілька секунда, тож дайте машині трохи часу;)</b>"), parse_mode='html')
          #"Відео-відгуки знаходяться у стадії розробки.\
          #Для повернення до головного меню натисніть - надрукуйте '/start' або '/omet'")
                           
    elif call.data == 'skip_image':
      #bot.register_next_step_handler(call.message, start_respond)
      bot.send_message(call.message.chat.id, "Повідомлення успішно збережене без зображення!\n\
        Для повернення до головного меню натисніть - надрукуйте '/start' або '/omet'")



@bot.message_handler(commands=['tour'])
def duplicate_tour(message):
  bot.send_message(message.chat.id, "Напишіть цифрами кількість людей,\
            які планують відвідати музей КП 'ОМЕТ'\n\
            (наприклад:'12' - бот ідентифікує лише цифрову складову у цьому повідомленні)")
      # save_quantity(call.message, initial_call=True)
  bot.register_next_step_handler(message, save_quantity)

def save_quantity(message, initial_call=False):
  
  """bot.register_next_step_handler(message, handle_quantity_input)

def handle_quantity_input(message):
    save_quantity(message)"""
  
  # bot.send_message(message.chat.id, "Напишіть цифрами кількість людей,\
  # які планують відвідати музей КП 'ОМЕТ'\n\
  # (наприклад:'12' - бот ідентифікує лише цифрову складову у цьому повідомленні)", parse_mode='html')
  quantity = message.text.strip()  # remove extra spaces from text 
  
  user_data['name'] = message.from_user.first_name
    
  # check if quantity is real number
  if not quantity.isdigit(): #isdigit() return True if integer
    bot.send_message(message.chat.id, "Невірно введена кількість")
    bot.register_next_step_handler(message, save_quantity)  # waiting for next message
    return
  
  # check if quantity more than 50
  if int(quantity) > 50:
    bot.send_message(message.chat.id, "Зв'яжіться із директором музею за телефоном 050 399 42 11 для обговорення окремої\
      екскурсії для такої великої кількості людей.\n\
      Якщо хочете повернутись в головне меню напишіть команду '/start' або '/omet'.")
    return
  
  # separate the numerical part from the text, if there is one
  digits_str = ''.join(re.findall('\d+', quantity))
  digits_int = int(digits_str) if digits_str else None
  
  user_data['quantity'] = digits_int
  
  bot.send_message(message.chat.id, f"Кількість відвідувачів {digits_int} збережено")
  
  bot.send_message(message.chat.id, "Надішліть будь ласка ваш номер телефону для зв'язку з вами,\n\
    наприклад: 0661234567 або 7562598 , без пробілів та інших символів крім цифр")
  
  bot.register_next_step_handler(message, lambda m: None)  # Add this line to clear the next step handler
  bot.register_next_step_handler(message, ask_phone_tour)
                   

def ask_phone_tour(message):
  global table_name
  phone_number = message.text.strip()  # remove extra spaces from text
  
  # check if phone number is valid
  #if not phone_number.isdigit() or not 6 <= len(phone_number) <= 13:
  if not re.match(r'^\+?\d{6,13}$', phone_number) or not phone_number.isdigit():
    # '^' - begin of str; '\+?' - '+' could be included or not; '\d' - indicate any number, '{6,13} - quantity'; '$' - end of a str.
    bot.send_message(message.chat.id, "В номері невідповідна кількість цифр або він містить недопустимі символи")
    bot.register_next_step_handler(message, ask_phone_tour)  # waiting for next message
    return
  
  int_phone = int(''.join(re.findall('\d+', phone_number)))
  
  with sq.connect('mus_schedule.db', check_same_thread=False) as connect:
    cursor = connect.cursor()
  
  # check if phone number and name is unique
    cursor.execute(f"SELECT COUNT(*) FROM {table_name} WHERE contact =? Or name =?", (int_phone, user_data['name']))
    count = cursor.fetchone()[0]
    if count > 0:
      bot.send_message(message.chat.id, "Номер телефону або користувача вже зареєстрований на цю екскурсію.\n\
        Для повернення до головного меню натисніть - надрукуйте '/start' або '/omet'\n\
        Також ви завжди можете зв'язатись з нашим інформаційним центром за номером 717 54 54 або 788 688 6")
      return
  
  user_data['phone'] = int_phone
  
  cursor.execute(f"Insert Or Replace Into {table_name} (name, quantity, contact) VALUES (?, ?, ?)",\
    (user_data['name'], user_data['quantity'], user_data['phone']))
  connect.commit()
  
  connect.close()

  bot.send_message(message.chat.id, f"Ваш контакт збережено. Будемо раді бачити вас у музеї, гарного дня!\
    Якщо хочете повернутись в головне меню натисніть-напишіть команду '/start' або '/omet'")






waiting_for_image = False # Anchor for "save_image_respond" function

text_from_user = None
first_name = None
date_text = None
int_phone_respond = None


@bot.message_handler(commands=['text'])
def duplicate_text(message):
  bot.send_message(message.chat.id, "Введіть текстовий відгук.\n\
            у ньому вкажіть дату, час, адресу, номер транспортного засобу (якщо потрібно) та коротко опишіть ситуацію.\
            <b>(нагадуємо, що в повідомленні телеграма може вміститись близько 4000 символів)</b>", parse_mode='html')
  bot.register_next_step_handler(message, save_text_respond)
  
def save_text_respond(message):
  
  # Збереження текстового відгука
  global text_from_user
  text_from_user = message.text
  
  content_type = message.content_type
  if content_type != 'text':
      bot.send_message(message.chat.id, "Будь ласка, надішліть текстове повідомлення.")
      bot.register_next_step_handler(message, save_text_respond)
  
  bot.send_message(message.chat.id, "Тепер надішліть ваш номер телефону для зв'язку з вами,\n\
    наприклад: 0661234567 або 7562598 , без пробілів та інших символів крім цифр")
  
  bot.register_next_step_handler(message, ask_phone_text)
  
  
def ask_phone_text(message):
  global text_from_user, first_name, date_text, int_phone_respond, waiting_for_image, email_sender, password_sender
  
   #конвертація дати повідомлення з формату Unix-часу в рядок виду "дд_мм_рррр"
  date_text = datetime.datetime.fromtimestamp(message.date).strftime('%d_%m_%Y') 

  # Отримання імені користувача та його номера відвідувача (ви можете змінити номер відвідувача, якщо у вас є спосіб отримання його)
  first_name = message.from_user.first_name
  last_name = message.from_user.last_name #отримання прізвища користувача, який надіслав повідомлення.
    
  phone_number_respond = message.text.strip()  # remove extra spaces from text
  
  # check if phone number is valid
  #if not phone_number.isdigit() or not 6 <= len(phone_number) <= 13:
  if not re.match(r'^\+?\d{6,13}$', phone_number_respond) or not phone_number_respond.isdigit():
    # '^' - begin of str; '\+?' - '+' could be included or not; '\d' - indicate any number, '{6,13} - quantity'; '$' - end of a str.
    bot.send_message(message.chat.id, "В номері невідповідна кількість цифр або він містить недопустимі символи")
    bot.register_next_step_handler(message, ask_phone_text)  # waiting for next message
    return
  
  int_phone_respond = int(''.join(re.findall('\d+', phone_number_respond)))

  # Створення назви файлу та шляху до папки для збереження
  local_filename = f"{int_phone_respond}_{first_name}_{date_text}_.txt"
  folder_path = "C:\IDE\Testing_new\Telegram responds"  # Змініть на потрібний шлях до папки
  full_file_path = os.path.join(folder_path, local_filename)

  # Запис текстового відгука у файл
  with open(full_file_path, 'w', encoding='utf-8') as f:
      f.write(text_from_user)
      
  keyboard = types.InlineKeyboardMarkup()
  skip_button = types.InlineKeyboardButton("Без фото", callback_data='skip_image')
  keyboard.add(skip_button)
  
  bot.send_message(message.chat.id, "Надішліть зображення (якщо хочете) або використайте кнопку 'Без фото' для пропуску цього кроку.",
                   reply_markup=keyboard)
  waiting_for_image = True
  bot.register_next_step_handler(message, save_image_text_respond)



@bot.message_handler(content_types=['photo'], func=lambda message: waiting_for_image)
def save_image_text_respond(message):
    global waiting_for_image, first_name, date_text, int_phone_respond, email_sender, password_sender
    waiting_for_image = False
    
  
    if message.content_type == 'photo':
        # Отримання ідентифікатора файлу (file_id) зображення
        file_id = message.photo[-1].file_id

        # Отримання додаткової інформації про файл
        file_info = bot.get_file(file_id)

        # Завантаження вмісту файлу з серверів Telegram
        file_content = bot.download_file(file_info.file_path)

        # Формування назви файлу зображення та шляху до папки для збереження
        local_image_filename = f"{int_phone_respond}_{first_name}_{date_text}_image_review.jpg"
        full_image_file_path = os.path.join("C:\IDE\Testing_new\Telegram responds", local_image_filename)

        # Збереження зображення
        
        with open(full_image_file_path, 'wb') as f:
          f.write(file_content)

      # Відправка відповіді користувачеві
        bot.reply_to(message, "Повідомлення та зображення успішно збережені!\n\
        Для повернення до головного меню натисніть - надрукуйте '/start' або '/omet'")

    else:
      bot.reply_to(message, "Це не зображення. Будь ласка, надішліть фото або використайте кнопку 'Без фото' для пропуску цього кроку.")
      waiting_for_image = True
      bot.register_next_step_handler(message, save_image_text_respond)
            
# @bot.callback_query_handler(func=lambda call: call.data == 'skip_image')
# def process_callback_skip_image(call):
#   global waiting_for_image
#   waiting_for_image = False
#   keyboard = types.InlineKeyboardMarkup()
#   skip_button = types.InlineKeyboardButton("Без фото", callback_data='skip_image')
#   keyboard.add(skip_button)
#   bot.send_message(call.message.chat.id, "Фото не буде додано. Відгук збережено!\n\
#   Для повернення до головного меню натисніть - надрукуйте '/start' або '/omet'")
#   bot.answer_callback_query(call.id)

"""Номер інформаційного центру 717 54 54 або 788 688 6, info@oget.od.ua"""

# How to make a function that will send telegram message via mail?






# обробка аудіо повідомлень
@bot.message_handler(commands=['/audio'])
def duplicate_audio(message):
  bot.send_message(message.chat.id, "Будь ласка, надішліть голосове або аудіо повідомлення.")
  bot.register_next_step_handler(message, save_audio_respond)
@bot.message_handler(content_types=['voice', 'audio']) #декоратор, який вказує, що ця функція буде обробляти голосові повідомлення.
def save_audio_respond(message): #визначення функції handle_voice, яка приймає об'єкт message
  content_type = message.content_type
  if content_type not in ['voice', 'audio']:
      bot.send_message(message.chat.id, "Будь ласка, надішліть голосове або аудіо повідомлення.")
      bot.register_next_step_handler(message, save_audio_respond)
        
  if 'voice' in message.content_type:
        duration = message.voice.duration
        file_id = message.voice.file_id
  elif 'audio' in message.content_type:
        duration = message.audio.duration
        file_id = message.audio.file_id
  else:
    return

  if duration > 60:
    bot.send_message(message.chat.id, "Будь ласка, надішліть аудіо тривалістю не більше 1 хвилини.")
    return
  # отримання ідентифікатора файлу (file_id) аудіофайлу з голосового повідомлення. file_id є унікальним ідентифікатором файлу на серверах Telegram,
  # який потрібен для подальшого доступу до цього файлу.
  file_id = message.voice.file_id

    # отримання додаткової інформації про файл, такої як шлях файлу (file_path) на серверах Telegram.
    # Ця інформація потрібна, щоб завантажити файл з серверів Telegram.
  file_info = bot.get_file(file_id)

    # завантаження вмісту файлу з серверів Telegram. Після цього кроку ви отримуєте бінарні дані аудіофайлу у змінній file_content,
    # які ви можете зберегти на локальному диску або використовувати за потреби.
  file_content = bot.download_file(file_info.file_path)
  
  bot.send_message(message.chat.id, "Тепер надішліть ваш номер телефону для зв'язку з вами,\n\
    наприклад: 0661234567 або 7562598 , без пробілів та інших символів крім цифр")
  
  #це функція з модуля functools, яка дозволяє фіксувати аргументи для функції, створюючи нову функцію з частково застосованими
  # аргументами. У цьому випадку, ми фіксуємо аргумент file_info для функції ask_phone_voice.
  bot.register_next_step_handler(message, ask_phone_voice, file_info)  #functools.partial(ask_phone_voice, file_info=file_info))


def ask_phone_voice(message,file_info):
    global first_name
    global date_text 
    global int_phone_respond 
    global waiting_for_image
   
    phone_number_respond = message.text.strip()  # remove extra spaces from text
  
  # check if phone number is valid
  #if not phone_number.isdigit() or not 6 <= len(phone_number) <= 13:
    if not re.match(r'^\+?\d{6,13}$', phone_number_respond) or not phone_number_respond.isdigit():
    # '^' - begin of str; '\+?' - '+' could be included or not; '\d' - indicate any number, '{6,13} - quantity'; '$' - end of a str.
      bot.send_message(message.chat.id, "В номері невідповідна кількість цифр або він містить недопустимі символи")
      bot.register_next_step_handler(message, functools.partial(ask_phone_voice, file_info=file_info))
  # waiting for next message
      return

    int_phone_respond = int(''.join(re.findall('\d+', phone_number_respond)))

    # отримання дати та імені користувача
    date_voice = datetime.datetime.fromtimestamp(message.date).strftime('%d_%m_%Y') #конвертація дати повідомлення з формату Unix-часу в рядок виду "дд_мм_рррр"
    first_name = message.from_user.first_name #отримання імені користувача, який надіслав повідомлення.
    last_name = message.from_user.last_name #отримання прізвища користувача, який надіслав повідомлення.

    # завантаження аудіо файлу
    file_url = f'https://api.telegram.org/file/bot{TOKEN}/{file_info.file_path}' #формування посилання на файл для завантаження.
    response = requests.get(file_url) #завантаження файлу з використанням бібліотеки requests
      
    #forming the name
    local_filename = os.path.join('C:\IDE\Testing_new\Telegram responds', f'{date_voice} від {first_name} {last_name}_{int_phone_respond}.ogg') 
    #формування шляху та імені локального файлу з використанням зазначеного шляху, дати та імені користувача.
    with open(local_filename, 'wb') as f: #відкриття файлу у бінарному режимі для запису.
        f.write(response.content) #записування вмісту відповіді в локальний файл.
        
    keyboard = types.InlineKeyboardMarkup()
    skip_button = types.InlineKeyboardButton("Без фото", callback_data='skip_image')
    keyboard.add(skip_button)
    
    waiting_for_image = True

    bot.send_message(message.chat.id, "Надішліть зображення (якщо хочете) або використайте кнопку 'Без фото' для пропуску цього кроку.",
                    reply_markup=keyboard, parse_mode='HTML')
    bot.register_next_step_handler(message, save_image_audio_respond)


@bot.message_handler(content_types=['photo'], func=lambda message: waiting_for_image)
def save_image_audio_respond(message):
    global waiting_for_image
    waiting_for_image = False
    global first_name
    global date_text 
    global int_phone_respond
  
    if message.content_type == 'photo':
        # Отримання ідентифікатора файлу (file_id) зображення
        file_id = message.photo[-1].file_id

        # Отримання додаткової інформації про файл
        file_info = bot.get_file(file_id)

        # Завантаження вмісту файлу з серверів Telegram
        file_content = bot.download_file(file_info.file_path)

        # Формування назви файлу зображення та шляху до папки для збереження
        local_image_filename = f"{int_phone_respond}_{first_name}_{date_text}_image_review.jpg"
        full_image_file_path = os.path.join("C:\IDE\Testing_new\Telegram responds", local_image_filename)

        # Збереження зображення
        with open(full_image_file_path, 'wb') as f:
            f.write(file_content)
        
        
      # відправка відповіді користувачеві
        bot.reply_to(message, "Повідомлення успішно збережене!\n\
        Для повернення до головного меню натисніть - надрукуйте '/start' або '/omet'")



# обробка відео повідомлень
@bot.message_handler(commands=['/video'])
def duplicate_video(message):
  bot.send_message(message.chat.id, "Будь ласка, надішліть відео або відеонотаток.")
  bot.register_next_step_handler(message, save_video_respond)
@bot.message_handler(content_types=['video', 'video_note'])
def save_video_respond(message):
  content_type = message.content_type
  
  if content_type == 'video':
        file_id = message.video.file_id
        duration = message.video.duration

  elif content_type == 'video_note':
        file_id = message.video_note.file_id
        duration = message.video_note.duration

  else:
        bot.send_message(message.chat.id, "Будь ласка, надішліть відео або відеонотаток.")
        bot.register_next_step_handler(message, save_video_respond)
  

  if duration > 30:
        bot.send_message(message.chat.id, "Будь ласка, надішліть відео тривалістю не більше 30 секунд.")
        return
  
  # отримання додаткової інформації про файл, такої як шлях файлу (file_path) на серверах Telegram.
    # Ця інформація потрібна, щоб завантажити файл з серверів Telegram.
  file_info = bot.get_file(file_id)

    # завантаження вмісту файлу з серверів Telegram. Після цього кроку ви отримуєте бінарні дані аудіофайлу у змінній file_content,
    # які ви можете зберегти на локальному диску або використовувати за потреби.
  file_content = bot.download_file(file_info.file_path)
  
  bot.send_message(message.chat.id, "Тепер надішліть ваш номер телефону для зв'язку з вами,\n\
    наприклад: 0661234567 або 7562598 , без пробілів та інших символів крім цифр")
  
  bot.register_next_step_handler(message, ask_phone_video, file_info)
  
def ask_phone_video(message,file_info):
  global first_name
  global date_text 
  global int_phone_respond
  
  phone_number_respond = message.text.strip()  # remove extra spaces from text
  
  # check if phone number is valid
  #if not phone_number.isdigit() or not 6 <= len(phone_number) <= 13:
  if not re.match(r'^\+?\d{6,13}$', phone_number_respond) or not phone_number_respond.isdigit():
    # '^' - begin of str; '\+?' - '+' could be included or not; '\d' - indicate any number, '{6,13} - quantity'; '$' - end of a str.
    bot.send_message(message.chat.id, "В номері невідповідна кількість цифр або він містить недопустимі символи")
    bot.register_next_step_handler(message, ask_phone_video, file_info)  # waiting for next message
    return

  int_phone_respond = int(''.join(re.findall('\d+', phone_number_respond)))
  
  # отримання дати та імені користувача
  date_video = datetime.datetime.fromtimestamp(message.date).strftime('%d_%m_%Y') #конвертація дати повідомлення з формату Unix-часу в рядок виду "дд_мм_рррр"
  first_name = message.from_user.first_name #отримання імені користувача, який надіслав повідомлення.
  last_name = message.from_user.last_name #отримання прізвища користувача, який надіслав повідомлення.

  # завантаження аудіо файлу
  file_url = f'https://api.telegram.org/file/bot{TOKEN}/{file_info.file_path}' #формування посилання на файл для завантаження.
  response = requests.get(file_url) #завантаження файлу з використанням бібліотеки requests
    
  #forming the name
  local_filename = os.path.join('C:\IDE\Testing_new\Telegram responds', f'{date_video} від {first_name} {last_name}_{int_phone_respond}.mp4') 
  #формування шляху та імені локального файлу з використанням зазначеного шляху, дати та імені користувача.
  with open(local_filename, 'wb') as f: #відкриття файлу у бінарному режимі для запису.
      f.write(response.content) #записування вмісту відповіді в локальний файл.

  # відправка відповіді користувачеві
  bot.reply_to(message, "Повідомлення успішно збережене!\n\
    Для повернення до головного меню натисніть - надрукуйте '/start' або '/omet'") 
  #відправка відповіді користувачу про успішне збереження повідомлення."""
  

# if __name__ == '__main__':
#     while True:
#         try:
#             bot.polling(none_stop=True) #  The none_stop=True argument ensures that the bot keeps running even if an error occurs while handling updates.

#         except Exception as e: # catch all exceptions
          
#             print(f"Error: {e}")
#             time.sleep(15)  # Wait for 15 seconds before attempting to reconnect



"""def send_table():
    # Read data from the table
    cursor.execute(f"SELECT * FROM {table_name}")
    table_data = cursor.fetchall() #all rows from sql table

    # Fetch column names
    column_names = [description[0] for description in cursor.description]

    # Format table data using tabulate
    formatted_table = tabulate(table_data, headers=column_names, tablefmt="pretty") # make excel table

    # Send the formatted table to your Telegram chat
    chat_id = my_chat_id  # Replace with your chat ID
    bot.send_message(chat_id, f"Таблиця '{table_name}' містить наступні дані:\n\n{formatted_table}")

# Schedule the function to run every day at a specific time (e.g., 12:00)
# schedule.every().day.at("12:00").do(send_table)


# Keep the script running to execute the scheduled task
def scheduler():
    while True:
        schedule.run_pending()
        time.sleep(30)

# Schedule the function to run every day at a specific time (e.g., 12:00)
# schedule.every().day.at("12:00").do(send_table)
schedule.every(1).minutes.do(send_table)

# Start a separate thread for the scheduler
scheduler_thread = threading.Thread(target=scheduler)
scheduler_thread.start()"""

bot.infinity_polling()
