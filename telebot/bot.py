import logging
import re

from telegram import Bot
from telegram import Update
from telegram import ParseMode
from telegram import InlineKeyboardButton
from telegram import InlineKeyboardMarkup
from telegram import KeyboardButton
from telegram import ReplyKeyboardMarkup
from telegram import ReplyKeyboardRemove
from telegram.ext import CallbackContext
from telegram.ext import Updater
from telegram.ext import Filters
from telegram.ext import MessageHandler
from telegram.ext import CommandHandler
from telegram.ext import ConversationHandler
from telegram.ext import CallbackQueryHandler
from telegram.utils.request import Request

from telebot.config import TG_TOKEN
from telebot.config import TG_API_URL
from telebot.config import ADMIN_IDS
from telebot.config import MAIN_ADMIN_ID
from telebot.config import TOKEN_REGISTRATION

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# states
(KEYBOARD_CONTROLLER, CHECK_TOKEN, CHECK_ANALYSIS, GET_POINTS) = map(chr, range(4))

# attributes of user data
(IS_AUTH) = map(chr, range(4, 5))

# token mask
TOKEN_MASK = re.compile('\w{8}-\w{4}-\w{4}-\w{4}-\w{12}')

# callback_data -- это то, что будет присылать TG при нажатии на каждую кнопку
# Поэтому каждый идентификатор должен быть уникальным
CALLBACK_BUTTON1_MAIN_MENU = "callback_button1_main_menu"
CALLBACK_BUTTON2_HELP = "callback_button2_help"
CALLBACK_BUTTON3_AUTH = "callback_button3_auth"
CALLBACK_BUTTON4_CHANGE_USER = "callback_button4_change_user"
CALLBACK_BUTTON5_GET_INFO = "callback_button5_get_info"
CALLBACK_BUTTON6_GET_POINTS = "callback_button6_get_points"
CALLBACK_BUTTON7_ANALYSIS = "callback_button7_analysis"

# callback выбора категории для получения баллов и для анализа
# CALLBACK_BUTTON8_CATEGORY_ANALYSIS = "callback_button8_category_analysis"
# CALLBACK_BUTTON9_CATEGORY_GET_POINTS = "callback_button9_category_get_points"

# callback выбора типа разметки
# CALLBACK_BUTTON10_TYPE_GET_POINTS = "callback_button10_type_get_points"

# callback выбор качества текста
CALLBACK_BUTTON11_GET_POINTS_TRUE = 'callaback_button11_get_points_true'
CALLBACK_BUTTON12_GET_POINTS_FALSE = 'callback_button12_get_points_false'

TITLES = {
    CALLBACK_BUTTON1_MAIN_MENU: "Главное меню",
    CALLBACK_BUTTON2_HELP: "Помощь",
    CALLBACK_BUTTON3_AUTH: "Вход",
    CALLBACK_BUTTON4_CHANGE_USER: "Сменить пользователя",
    CALLBACK_BUTTON5_GET_INFO: "Информация о пользователе",
    CALLBACK_BUTTON6_GET_POINTS: "Заработать баллы",
    CALLBACK_BUTTON7_ANALYSIS: "Получить анализ",
    # CALLBACK_BUTTON8_CATEGORY_ANALYSIS: "Одежда",
    # CALLBACK_BUTTON9_CATEGORY_GET_POINTS: "Одежда",
    # CALLBACK_BUTTON10_TYPE_GET_POINTS: "Бинарная разметка"
    CALLBACK_BUTTON11_GET_POINTS_TRUE: "Хороший",
    CALLBACK_BUTTON12_GET_POINTS_FALSE: "Плохой",
}


# decorators
def log_error(f):
    def inner(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except Exception as e:
            error_message = f'[ADMIN] Произошла ошибка {e}'
            logger.error(error_message)

            update = args[0]
            if update and hasattr(update, 'message'):
                for admin in MAIN_ADMIN_ID:
                    update.message.bot.send_message(
                        chat_id=admin,
                        text=error_message,
                    )
            raise e

    return inner


def user_access(f):
    def inner(*args, **kwargs):
        update = args[0]
        context = args[1]
        if context:
            # 492618436
            if context.user_data.get(IS_AUTH):
                logger.info(f"Доступ разрешен по id: {update.callback_query.message.chat.id}")
                return f(*args, **kwargs)
            else:
                logger.info(f"Доступ запрещен по id: {update.callback_query.message.chat.id}")
                # update.inline_query.answer(
                #     text='Доступ запрещен!'
                # )
                update.callback_query.answer()
                update.callback_query.edit_message_text(
                    text="Доступ запрещен! Сначала авторизуйтесь!",
                    reply_markup=get_keyboard_main_menu(context.user_data.get(IS_AUTH))
                )
                return KEYBOARD_CONTROLLER
        else:
            logger.warning("Нет аргумента context")

    return inner


# helps functions
def is_auth(id: int):
    return id in ADMIN_IDS


# keyboards
def get_keyboard_base_part():
    """Get base part of keyboard
    return: list
    """
    return [
        [
            InlineKeyboardButton(TITLES[CALLBACK_BUTTON2_HELP], callback_data=CALLBACK_BUTTON2_HELP),
        ],
        [
            InlineKeyboardButton(TITLES[CALLBACK_BUTTON1_MAIN_MENU], callback_data=CALLBACK_BUTTON1_MAIN_MENU),
        ]
    ]


def get_keyboard_main_menu(is_auth: bool):
    """Get keyboard main menu
    return: InlineKeyboardMarkup
    """
    if not is_auth:
        keyboard = [
            [
                InlineKeyboardButton(TITLES[CALLBACK_BUTTON3_AUTH], callback_data=CALLBACK_BUTTON3_AUTH)
            ]
        ]
    else:
        keyboard = [
            [
                InlineKeyboardButton(TITLES[CALLBACK_BUTTON4_CHANGE_USER], callback_data=CALLBACK_BUTTON4_CHANGE_USER)
            ]
        ]
    keyboard.extend([
        [
            InlineKeyboardButton(TITLES[CALLBACK_BUTTON5_GET_INFO], callback_data=CALLBACK_BUTTON5_GET_INFO)
        ],
        [
            InlineKeyboardButton(TITLES[CALLBACK_BUTTON6_GET_POINTS], callback_data=CALLBACK_BUTTON6_GET_POINTS)
        ],
        [
            InlineKeyboardButton(TITLES[CALLBACK_BUTTON7_ANALYSIS], callback_data=CALLBACK_BUTTON7_ANALYSIS)
        ]
    ])
    keyboard.extend([
        [
            InlineKeyboardButton(TITLES[CALLBACK_BUTTON2_HELP], callback_data=CALLBACK_BUTTON2_HELP),
        ],
    ])
    return InlineKeyboardMarkup(keyboard)


# start handler
def start(update: Update, context: CallbackContext):
    context.user_data[IS_AUTH] = is_auth(update.message.chat.id)

    update.message.reply_text('Привет! Это Deku bot!')
    update.message.reply_text(
        text='Выбери интересующую Вас функцию:',
        reply_markup=get_keyboard_main_menu(context.user_data.get(IS_AUTH))
    )
    return KEYBOARD_CONTROLLER


def show_main_menu(update: Update, context: CallbackContext):
    update.callback_query.answer()
    update.callback_query.edit_message_text(
        'Выбери интересующую Вас функцию:',
        reply_markup=get_keyboard_main_menu(context.user_data.get(IS_AUTH))
    )


# help handler
def help_handler(update: Update, context: CallbackContext):
    keyboard = [
        [
            InlineKeyboardButton(TITLES[CALLBACK_BUTTON1_MAIN_MENU], callback_data=CALLBACK_BUTTON1_MAIN_MENU)
        ]
    ]
    keyboard = InlineKeyboardMarkup(keyboard)
    update.callback_query.answer()
    update.callback_query.edit_message_text(
        text='Это Помощь!',
        reply_markup=keyboard
    )


# auth handler
def get_auth(update: Update, context: CallbackContext):
    update.callback_query.message.reply_text(
        text='Введите ваш токен, либо введите комманду \'/cancel\' для отмены',
    )


def check_token(update: Update, context: CallbackContext):
    tm = TOKEN_MASK.search(update.message.text)
    if tm is None:
        update.message.reply_text(
            text='Токен не верного формата, попробуйте снова',
            reply_markup=InlineKeyboardMarkup(get_keyboard_base_part())
        )
        return KEYBOARD_CONTROLLER

    if update.message.text in TOKEN_REGISTRATION:
        update.message.reply_text(
            text='Токен успешно установлен!',
            reply_markup=InlineKeyboardMarkup(get_keyboard_base_part())
        )
    else:
        update.message.reply_text(
            text='Ошибка установления токена. Попробуйте снова.',
            reply_markup=InlineKeyboardMarkup(get_keyboard_base_part())
        )
    context.user_data[IS_AUTH] = is_auth(update.message.chat.id)
    return KEYBOARD_CONTROLLER


# analysis handler
@user_access
def get_analysis(update: Update, context: CallbackContext):
    # TODO: Check number of points

    update.callback_query.answer()
    update.callback_query.message.reply_text(
        text='Введите ваш текст, либо введите комманду \'/cancel\' для отмены',
    )


def check_analysis(update: Update, context: CallbackContext):
    # TODO: Использование модели и получение анализа
    quality = True

    if quality:
        update.message.reply_text(
            text='Поздравляем! Ваш текст успешен!',
            reply_markup=InlineKeyboardMarkup(get_keyboard_base_part())
        )
    else:
        update.message.reply_text(
            text='Текст имеет низкие показатели. Настоятельно рекомендуем его улучшить перед демонстрацией!',
            reply_markup=InlineKeyboardMarkup(get_keyboard_base_part())
        )
    return KEYBOARD_CONTROLLER


# handler get user info
@user_access
def get_info(update: Update, context: CallbackContext):
    # TODO: Получение информации о пользователе
    user = {
        'name': 'Alexander',
        'token': TOKEN_REGISTRATION[0],
        'points': 1235
    }

    update.callback_query.answer()
    update.callback_query.edit_message_text(
        text=f'<b>Имя:</b> {user["name"]}\n<b>Токен:</b> {user["token"]}\n<b>Число баллов:</b> {user["points"]}',
        parse_mode='html',
        reply_markup=InlineKeyboardMarkup(get_keyboard_base_part())
    )


# get points handler
@user_access
def get_points(update: Update, context: CallbackContext):
    keyboard = [
        [
            InlineKeyboardButton(
                TITLES[CALLBACK_BUTTON11_GET_POINTS_TRUE], callback_data=CALLBACK_BUTTON11_GET_POINTS_TRUE
            ),
            InlineKeyboardButton(
                TITLES[CALLBACK_BUTTON12_GET_POINTS_FALSE], callback_data=CALLBACK_BUTTON12_GET_POINTS_FALSE
            )
        ]
    ]
    keyboard = InlineKeyboardMarkup(keyboard)
    update.callback_query.answer()
    update.callback_query.edit_message_text(
        text='К какому типу относится следующий текст:\nЭто очень классный текст!',
        reply_markup=keyboard
    )


def get_points_get_result(update: Update, context: CallbackContext):
    data = update.callback_query.data
    if data == CALLBACK_BUTTON11_GET_POINTS_TRUE:
        logger.info(True)
    elif data == CALLBACK_BUTTON12_GET_POINTS_FALSE:
        logger.info(False)
    else:
        logger.warning("Error")
    update.callback_query.answer()
    update.callback_query.edit_message_text(
        text='Спасибо! Вам начислены баллы!',
        reply_markup=InlineKeyboardMarkup(get_keyboard_base_part())
    )

    return KEYBOARD_CONTROLLER


# fallback for Conversations
def cancel(update: Update, context: CallbackContext):
    update.message.reply_text(
        text='Выбери интересующую Вас функцию:',
        reply_markup=get_keyboard_main_menu(context.user_data.get(IS_AUTH))
    )
    return KEYBOARD_CONTROLLER


def stop(update: Update, context: CallbackContext):
    return ConversationHandler.END


# keyboard controller handler
def keyboard_controller(update: Update, context: CallbackContext):
    query = update.callback_query
    data = query.data

    if data == CALLBACK_BUTTON1_MAIN_MENU:
        show_main_menu(update, context)
        return KEYBOARD_CONTROLLER
    elif data == CALLBACK_BUTTON2_HELP:
        help_handler(update, context)
        return KEYBOARD_CONTROLLER
    elif data == CALLBACK_BUTTON3_AUTH or data == CALLBACK_BUTTON4_CHANGE_USER:
        get_auth(update, context)
        return CHECK_TOKEN
    elif data == CALLBACK_BUTTON5_GET_INFO:
        get_info(update, context)
        return KEYBOARD_CONTROLLER
    elif data == CALLBACK_BUTTON6_GET_POINTS:
        get_points(update, context)
        return GET_POINTS
    elif data == CALLBACK_BUTTON7_ANALYSIS:
        get_analysis(update, context)
        return CHECK_ANALYSIS
    else:
        query.answer()
        query.edit_message_text(
            text='Неизвестная команда! Попробуйте позже',
            reply_markup=InlineKeyboardMarkup(get_keyboard_base_part())
        )
        return KEYBOARD_CONTROLLER


def main():
    req = Request(
        connect_timeout=1,
    )
    bot = Bot(
        request=req,
        token=TG_TOKEN,
        base_url=TG_API_URL,
    )
    updater = Updater(
        bot=bot,
        use_context=True,
    )
    logger.info(updater.bot.get_me())

    menu_handler = ConversationHandler(
        entry_points=[
            CommandHandler('start', start),
        ],

        states={
            KEYBOARD_CONTROLLER: [CallbackQueryHandler(keyboard_controller)],
            CHECK_TOKEN: [MessageHandler(Filters.regex('^[^/]'), check_token),
                          CommandHandler('cancel', cancel)],
            GET_POINTS: [CallbackQueryHandler(get_points_get_result),
                         CommandHandler('cancel', cancel)],
            CHECK_ANALYSIS: [MessageHandler(Filters.regex('^[^/]'), check_analysis),
                             CommandHandler('cancel', cancel)],
        },

        fallbacks=[CommandHandler('stop', stop)]
    )
    updater.dispatcher.add_handler(menu_handler)

    updater.start_polling()
    updater.idle()


if __name__ == "__main__":
    main()
