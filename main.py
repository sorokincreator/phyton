import telebot
from config import API_KEY
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

admin_chat_id = '1807821919'
bot = telebot.TeleBot(API_KEY)

application_counter = 0

translations = {
    'ru': {
        'help_text': "\n/start - запуск бота\n/help - доступные команды\n/about - информация о боте",
        'about_text': "Программист и разработчик, СОРОКИН А.С. сделал этого бота. Техническая поддержка по номеру: 89831254221.",
        'choose_language': "Выберите язык:",
        'welcome': "Здравствуйте! Я помогу создать заявку на ремонт принтера.",
        'choose_manufacturer': "Выберите производителя принтера:",
        'invalid_manufacturer': "Пожалуйста, выберите производителя из предложенных вариантов.",
        'describe_problem': "Опишите проблему с принтером:",
        'enter_phone': "Введите ваш номер телефона (11 цифр):",
        'invalid_phone': "Неверный формат номера. Пожалуйста, введите 11 цифр:",
        'attach_photo': "Прикрепите фотографию принтера (обязательно):",
        'skip': "Пропустить",
        'invalid_photo': "Пожалуйста, отправьте фото.",
        'enter_address': "Введите адрес (Улица и Дом):",
        'application_created': "Заявка №{} создана и отправлена. Вам перезвонят в ближайшее время. Спасибо!",
        'start_help': "Пожалуйста, начните с команды /start",
        'cancel': "Отмена",
        'cancelled': "Заявка отменена. Начинаем новую заявку..."
    },
    'en': {
        'help_text': "\n/start - start the bot\n/help - available commands\n/about - bot information",
        'about_text': "Programmer and developer, SOROKIN A.S. made this bot. Technical support by phone: 89831254221.",
        'choose_language': "Choose language:",
        'welcome': "Hello! I will help you create a printer repair request.",
        'choose_manufacturer': "Choose printer manufacturer:",
        'invalid_manufacturer': "Please choose a manufacturer from the suggested options.",
        'describe_problem': "Describe the problem with the printer:",
        'enter_phone': "Enter your phone number (11 digits):",
        'invalid_phone': "Invalid phone format. Please enter 11 digits:",
        'attach_photo': "Attach a photo of the printer:",
        'skip': "Skip",
        'invalid_photo': "Please send a photo.",
        'enter_address': "Enter address (Street and House):",
        'application_created': "Request №{} created and sent. We will call you back soon. Thank you!",
        'start_help': "Please start with /start command",
        'cancel': "Cancel",
        'cancelled': "Application cancelled. Starting new application..."
    }
}

manufacturers = ["HP", "Canon", "Epson", "Brother", "Samsung", "Lexmark",
                 "Xerox", "Ricoh", "Dell", "Kodak", "Pantum"]

user_data = {}
user_languages = {}
# Словарь для отслеживания текущих шагов пользователей
user_current_step = {}


@bot.message_handler(commands=["help"])
def help_command(message):
    user_language = get_user_language(message.chat.id)
    bot.send_message(message.chat.id, text=translations[user_language]['help_text'])


@bot.message_handler(commands=["about"])
def about(message):
    user_language = get_user_language(message.chat.id)
    bot.send_message(message.chat.id, translations[user_language]['about_text'])


def get_user_language(chat_id):
    return user_languages.get(chat_id, 'ru')


def set_user_language(chat_id, language):
    user_languages[chat_id] = language


def language_keyboard():
    markup = InlineKeyboardMarkup()
    markup.row(
        InlineKeyboardButton('🇷🇺 Русский', callback_data='lang_ru'),
        InlineKeyboardButton('🇺🇸 English', callback_data='lang_en')
    )
    return markup


def manufacturers_keyboard():
    markup = InlineKeyboardMarkup()
    buttons = []
    for manufacturer in manufacturers:
        buttons.append(InlineKeyboardButton(manufacturer, callback_data=f'manufacturer_{manufacturer}'))

    for i in range(0, len(buttons), 2):
        if i + 1 < len(buttons):
            markup.row(buttons[i], buttons[i + 1])
        else:
            markup.row(buttons[i])

    markup.row(InlineKeyboardButton("❌ Отмена / Cancel", callback_data='cancel'))
    return markup


def cancel_keyboard(language):
    markup = InlineKeyboardMarkup()
    markup.row(InlineKeyboardButton("❌ " + translations[language]['cancel'], callback_data='cancel'))
    return markup


@bot.message_handler(commands=['start'])
def start(message):
    # Очищаем текущий шаг при новом старте
    if message.chat.id in user_current_step:
        del user_current_step[message.chat.id]

    bot.send_message(message.chat.id,
                     translations['ru']['choose_language'],
                     reply_markup=language_keyboard())


@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    chat_id = call.message.chat.id
    message_id = call.message.message_id

    if call.data.startswith('lang_'):
        language = call.data.split('_')[1]
        set_user_language(chat_id, language)
        user_language = get_user_language(chat_id)

        bot.edit_message_text(
            chat_id=chat_id,
            message_id=message_id,
            text=translations[user_language]['choose_language'] + "\n✅ " + (
                "Выбран русский" if language == 'ru' else "Selected English")
        )

        start_application(chat_id, user_language)

    elif call.data.startswith('manufacturer_'):
        manufacturer = call.data.split('_', 1)[1]
        user_language = get_user_language(chat_id)

        if chat_id not in user_data:
            user_data[chat_id] = {}

        user_data[chat_id]['manufacturer'] = manufacturer
        user_current_step[chat_id] = 'describe_problem'

        bot.edit_message_text(
            chat_id=chat_id,
            message_id=message_id,
            text=f"✅ {translations[user_language]['choose_manufacturer']}\n{manufacturer}"
        )

        bot.send_message(chat_id, translations[user_language]['describe_problem'],
                         reply_markup=cancel_keyboard(user_language))
        bot.register_next_step_handler(call.message, get_problem_description)

    elif call.data == 'cancel':
        user_language = get_user_language(chat_id)

        # Очищаем данные текущей заявки и текущий шаг
        if chat_id in user_data:
            del user_data[chat_id]
        if chat_id in user_current_step:
            del user_current_step[chat_id]

        bot.edit_message_text(
            chat_id=chat_id,
            message_id=message_id,
            text="❌ " + translations[user_language]['cancelled']
        )

        # Сразу начинаем новую заявку
        start_application(chat_id, user_language)


def start_application(chat_id, user_language):
    global application_counter
    application_counter += 1
    current_number = application_counter

    if chat_id not in user_data:
        user_data[chat_id] = {}

    user_data[chat_id]['application_number'] = current_number
    user_current_step[chat_id] = 'choose_manufacturer'

    welcome_text = translations[user_language]['welcome']
    choose_manufacturer_text = translations[user_language]['choose_manufacturer']

    bot.send_message(chat_id,
                     f"{welcome_text}\n{choose_manufacturer_text}",
                     reply_markup=manufacturers_keyboard())


def get_problem_description(message):
    # Проверяем, не отменена ли заявка
    if message.chat.id not in user_current_step or user_current_step.get(message.chat.id) != 'describe_problem':
        return

    user_language = get_user_language(message.chat.id)
    description = message.text.strip()

    if message.chat.id not in user_data:
        user_data[message.chat.id] = {}

    user_data[message.chat.id]['description'] = description
    user_current_step[message.chat.id] = 'enter_phone'

    bot.send_message(message.chat.id, translations[user_language]['enter_phone'],
                     reply_markup=cancel_keyboard(user_language))
    bot.register_next_step_handler(message, get_phone_number)


def get_phone_number(message):
    # Проверяем, не отменена ли заявка
    if message.chat.id not in user_current_step or user_current_step.get(message.chat.id) != 'enter_phone':
        return

    user_language = get_user_language(message.chat.id)
    phone = message.text.strip()

    if not (phone.isdigit() and len(phone) == 11):
        bot.send_message(message.chat.id, translations[user_language]['invalid_phone'],
                         reply_markup=cancel_keyboard(user_language))
        bot.register_next_step_handler(message, get_phone_number)
        return

    user_data[message.chat.id]['phone'] = phone
    user_current_step[message.chat.id] = 'attach_photo'

    bot.send_message(message.chat.id,
                     translations[user_language]['attach_photo'],
                     reply_markup=cancel_keyboard(user_language))
    bot.register_next_step_handler(message, get_photo)


def get_photo(message):
    # Проверяем, не отменена ли заявка
    if message.chat.id not in user_current_step or user_current_step.get(message.chat.id) != 'attach_photo':
        return

    user_language = get_user_language(message.chat.id)

    if message.photo:
        photo_file_id = message.photo[-1].file_id
        user_data[message.chat.id]['photo'] = photo_file_id
        user_current_step[message.chat.id] = 'enter_address'

        bot.send_message(message.chat.id, "✅ " + ("Фото получено" if user_language == 'ru' else "Photo received"))
        ask_address(message)
    else:
        bot.send_message(message.chat.id, translations[user_language]['invalid_photo'],
                         reply_markup=cancel_keyboard(user_language))
        bot.register_next_step_handler(message, get_photo)


def ask_address(message):
    user_language = get_user_language(message.chat.id)
    user_current_step[message.chat.id] = 'enter_address'

    bot.send_message(message.chat.id, translations[user_language]['enter_address'],
                     reply_markup=cancel_keyboard(user_language))
    bot.register_next_step_handler(message, get_address)


def get_address(message):
    # Проверяем, не отменена ли заявка
    if message.chat.id not in user_current_step or user_current_step.get(message.chat.id) != 'enter_address':
        return

    user_language = get_user_language(message.chat.id)
    address = message.text.strip()

    if not isinstance(address, str):
        address = str(address)

    user_data[message.chat.id]['address'] = address

    data = user_data[message.chat.id]

    report = f"Заявка №{data['application_number']}:\n" \
             f"Производитель: {data['manufacturer']}\n" \
             f"Проблема: {data['description']}\n" \
             f"Телефон: {data['phone']}\n" \
             f"Адрес: {data['address']}\n" \
             f"Язык: {'Русский' if user_language == 'ru' else 'Английский'}"

    bot.send_message(int(admin_chat_id), report)
    if data.get('photo'):
        bot.send_photo(chat_id=int(admin_chat_id), photo=data['photo'])

    bot.send_message(message.chat.id,
                     translations[user_language]['application_created'].format(data['application_number']))

    # Очищаем данные после успешного завершения
    if message.chat.id in user_data:
        del user_data[message.chat.id]
    if message.chat.id in user_current_step:
        del user_current_step[message.chat.id]


@bot.message_handler(func=lambda message: True)
def handle_unknown(message):
    user_language = get_user_language(message.chat.id)
    bot.send_message(message.chat.id, translations[user_language]['start_help'])


if __name__ == "__main__":
    print("Бот запускается...")
    try:
        bot.polling(none_stop=True)
    except Exception as e:
        print(f"Ошибка: {e}")