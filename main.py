import telebot
from config import API_KEY

bot = telebot.TeleBot(API_KEY)

@bot.message_handler(commands = ["start"])
def start(message):
    bot.send_message(message.chat.id, "Hello World")

@bot.message_handler(commands = ["help"])
def start(message):
    bot.send_message(message.chat.id, text= "\n start - запуск бота. \n help - доступные команды. \n about - информация о боте." )


@bot.message_handler(commands = ["about"])
def about(message):
    bot.send_message(message.chat.id, "Программист и разработчик СОРОКИН А.С. сделал этого бота")

bot.polling()