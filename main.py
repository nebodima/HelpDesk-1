import aiogram
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram import executor
from app import sql
import config

import asyncio
loop = asyncio.get_event_loop()
import logging
logging.basicConfig(level=logging.INFO)


bot = Bot(token=config.BOT_TOKEN)
dp = Dispatcher(bot)
dp.middleware.setup(LoggingMiddleware())
# Создание таблиц в базе данных SQLite
sql.create_tables()



@dp.message_handler(commands=['start'])
async def send_start(message: types.Message):
    user_id = message.from_user.id
    data_reg = message.date
    user = sql.get_user_by_id(user_id)
    
    if not user:
        # Если пользователь отсутствует, добавляем его
        user_info = {
            'tg_id': user_id,
            'pos': 'main_menu',
            'data_reg': data_reg, 
            'profile': {"organization": "Нет данных", "organization_adress": "Нет данных", "organization_inn": "Нет данных", "organization_phone": "Нет данных", "history_ticket": "", "data_ticket": "", "user_name": ""}
        }
        sql.add_user(**user_info)
        text_no_user = f"Добро пожаловать в HelpDesk компании <b>ЭниКей</b>! Для работы в сервисе необходимо заполнить данные."
        keyboard = InlineKeyboardMarkup()
        keyboard.add(InlineKeyboardButton(text="🏢 Моя компания", callback_data="my_company"))
        await message.answer(text_no_user, reply_markup=keyboard, parse_mode="HTML")
        
    else:
        # Проверка открытых\закрытых тикетов 
        open_ticket = sql.get_total_tickets_by_status_for_user(user_id, "В работе")
        closed_ticket = sql.get_total_tickets_by_status_for_user(user_id, "Завершена")
        # Чтение профиля
        profile = sql.read_profile(user_id)
        sql.update_pos('main_menu', 'tg_id', user_id)
        organization = profile.get("organization", "Нет данных")
        organization_phone = profile.get("organization_phone", "Нет данных")
        
        text_user =  (f"<b>🧑‍💻 Главное меню</b> \n\n" 
                f"<b>📋 Компания: </b> {organization}\n"
                f"<b>☎️ Контактный номер:</b> {organization_phone}\n\n"
                
                f"<b>📬Открытых заявок:</b> {open_ticket}\n" 
                f"<b>📭Закрытых заявок:</b> {closed_ticket}\n" 
                f"\nВыберите интересующее действие ⬇️"
        )
        keyboard = InlineKeyboardMarkup()
        keyboard.add(InlineKeyboardButton(text="🏢 Моя компания", callback_data="my_company"),
                    InlineKeyboardButton(text="📥 Мои заявки", callback_data="my_ticket"))
        keyboard.add(InlineKeyboardButton(text="📤 Новая заявка", callback_data="new_ticket"))
                
        # Проверяем, является ли пользователь администратором
        if user_id == config.ADMIN_USER:
            send_media_button = types.InlineKeyboardButton("🤘Админ меню", callback_data="admin_panel")
            keyboard.add(send_media_button)
        
        await message.answer(text_user, reply_markup=keyboard, parse_mode="HTML")
       
    
# Главное меню пользователя мимикрия под /start
def main_menu(tg_id):
    sql.update_pos('main_menu', 'tg_id', tg_id)
    user_id = tg_id
    open_ticket = sql.get_total_tickets_by_status_for_user(tg_id, "В работе")
    closed_ticket = sql.get_total_tickets_by_status_for_user(tg_id, "Завершена")
    profile = sql.read_profile(tg_id)
    organization = profile.get("organization", "Нет данных")
    organization_phone = profile.get("organization_phone", "Нет данных")
    
    text =  (f"<b>🧑‍💻 Главное меню</b> \n\n" 
            f"<b>📋 Компания: </b> {organization}\n"
            f"<b>☎️ Контактный номер:</b> {organization_phone}\n\n"
            
            f"<b>📬Открытых заявок:</b> {open_ticket}\n" 
            f"<b>📭Закрытых заявок:</b> {closed_ticket}\n" 
            f"\nВыберите интересующее действие ⬇️"
    )
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton(text="🏢 Моя компания", callback_data="my_company"),
                 InlineKeyboardButton(text="📥 Мои заявки", callback_data="my_ticket"))
    keyboard.add(InlineKeyboardButton(text="📤 Новая заявка", callback_data="new_ticket"))
    
    # Проверяем, является ли пользователь администратором
    if user_id == config.ADMIN_USER:
        send_media_button = types.InlineKeyboardButton("🤘Админ меню🫰", callback_data="admin_panel")
        keyboard.add(send_media_button)
    
    return text, keyboard
    
    
def new_ticket(tg_id):
    text = (f"<b>📤 Создание новой заявки</b>\n\n" 
            f" - 📝 Опишите вашу проблему.\n"
            f" - 🧩 Пожалуйста, опишите вашу проблему и укажите как можно больше деталей.\n\n"
            f"<b>Пример оформления заявки:</b> \n<i>Не работает принтер на 4 ПК, необходимо проверить подключение.</i>")

    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton(text="⬅️ Назад", callback_data="main_menu"))
    return text, keyboard 


def my_ticket(tg_id):
    profile = sql.read_profile(tg_id)
    user_tickets_in_progress = sql.get_tickets_in_progress_by_user_id(tg_id)
    total_user_tickets_in_progress = len(user_tickets_in_progress)
    open_ticket = str(total_user_tickets_in_progress) if total_user_tickets_in_progress else "0"
    organization = profile.get("organization")
    organization_address = profile.get("organization_adress")
    
    if user_tickets_in_progress:
        text = (f"<b>📥 Мои заявки </b>\n\n"
                     f"<b>Компания:</b> {organization}\n"
                     f"<b>Адрес заявки:</b> {organization_address}\n" 
                     f"<b>Заявок в работе:</b> {open_ticket}\n\n"
                     )     
        for ticket in user_tickets_in_progress:
            # Использование индексов для доступа к данным кортежа           
            text += (f"<b>Номер заявки:</b> <code>#{ticket[0]} </code>\n"
                     f"<b>Описание:</b> {ticket[4]}\n"
                     f"<b>Дата: </b>{ticket[5]}\n\n"
                    #f"<b>Статус:</b> {ticket[6]}\n\n"
                     )
    else:
        text = '<b>📥 Мои заявки </b>\n\nУ вас пока нет заявок в работе..  🤷‍♂️ \n- <i>Что бы оставить заявку воспользуйтесь меню </i><b>"📤 Новая заявка"</b>'

    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton(text="⬅️ Назад", callback_data="main_menu"))
    return text, keyboard


def my_company(tg_id):
    profile = sql.read_profile(tg_id)
    organization = profile.get("organization", "Нет данных")
    organization_address = profile.get("organization_adress", "Нет данных")
    organization_inn = profile.get("organization_inn", "Нет данных")
    organization_phone = profile.get("organization_phone", "Нет данных")
    
    # Формирование текста для отображения данных о компании
    text = (f"<b>🏢 Информация о компании</b>\n\n" 
           f"<b>📋 Компания:</b> {organization}\n" 
           f"<b>📍 Адрес:</b> {organization_address}\n" 
           f"<b>📑 ИНН:</b> {organization_inn}\n" 
           f"<b>☎️ Контактный номер:</b> <i>{organization_phone}</i>\n\n" 
           f"<b>ЗАПОЛНИТЬ ДАННЫЕ О КОМПАНИИ ⬇️ </b>" )  
    
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton(text=f"{'✅' if organization != 'Нет данных' else '❌'} Наименование компании", callback_data="edit_company_name"))
    keyboard.add(InlineKeyboardButton(text=f"{'✅' if organization_address != 'Нет данных' else '❌'} Фактический адрес", callback_data="edit_company_adress"))
    keyboard.add(InlineKeyboardButton(text=f"{'✅' if organization_inn != 'Нет данных' else '❌'} ИНН", callback_data="edit_company_inn"))
    keyboard.add(InlineKeyboardButton(text=f"{'✅' if organization_phone != 'Нет данных' else '❌'} Контактный номер", callback_data="edit_company_phone"))
    keyboard.add(InlineKeyboardButton(text="⬅️ В меню", callback_data="main_menu"))
    return text, keyboard


def edit_company_name(tg_id):
    text = f"📋 Введите наименование организации. \nПример: <code> ООО РОГА И КОПЫТА </code>"
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton(text="⬅️ Назад", callback_data="my_company"))
    return text, keyboard

def edit_company_adress(tg_id):
    text = f"📍Введите фактический адрес организации. \nПример: <code> г. Иваново, ул. Варенцовой, д. 33 оф. 1 </code>"
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton(text="⬅️ Назад", callback_data="my_company"))
    return text, keyboard
    
def edit_company_inn(tg_id):
    text = f"📑 Введите ИНН организации. \nПример: <code> 3700010101 </code>"
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton(text="⬅️ Назад", callback_data="my_company"))
    return text, keyboard

def edit_company_phone(tg_id):
    text = f"☎️ Введите контактный номер телефона. \nПример: <code> +79109998188 </code>"
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton(text="⬅️ Назад", callback_data="my_company"))
    return text, keyboard
      
def done_ticket(tg_id):
    last_ticket_number = sql.get_last_ticket_number()   
    text = f'🎉🥳 Успех, ваша заявка зарегестрирована! \nНомер заявки <code>{last_ticket_number}</code>. \n\n<i>PS: Отслеживайте статус поставленных задач в разделе</i> <b>"📥 Мои заявки"</b>'
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton(text="⬅️  В меню", parse_mode="HTML", callback_data="main_menu"))
    return text, keyboard

# Административный раздел
def admin_panel():
    total_open_tickets = sql.get_total_tickets_by_status_admin("В работе")  # Получаем общее количество заявок "В работе"
    total_closed_tickets = sql.get_total_tickets_by_status_admin("Завершена")  # Получаем общее количество завершенных заявок

    text = f"<b>🤘Админ меню</b>\n\n"
    text += f"<b>🔥Заявок в работе:</b> {total_open_tickets}\n"
    text += f"<b>👍Завершенных заявок:</b> {total_closed_tickets}\n\n"
    text += f"<b>⚠️ Внимание!</b> <i>Закрытые задачи не могут быть возвращены в работу. Пожалуйста, будьте внимательны при их закрытии!</i>"
    
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton(text="📋 Список задач в работе", callback_data="show_all_tickets_in_progress"))
    keyboard.add(InlineKeyboardButton(text="⬅️ Назад", callback_data="main_menu"))
    return text, keyboard
    

def show_all_tickets_in_progress():
    all_tickets_in_progress = sql.get_all_tickets_in_progress()
    keyboard = InlineKeyboardMarkup()
    text = f"<b>💪 Список заявок в работе: </b>\n\n <b>⚠️ Внимание!</b> <i>Закрытые задачи не могут быть возвращены в работу. Пожалуйста, будьте внимательны при их закрытии!</i>"
    for ticket in all_tickets_in_progress:
        ticket_info = f"Заявка #{ticket[0]} - {ticket[5]}" # Номер и описание заявки
        keyboard.add(InlineKeyboardButton(text=ticket_info, callback_data=f"ticket_{ticket[0]}"))
    keyboard.add(InlineKeyboardButton(text="⬅️ Назад", callback_data="admin_panel"))
    return text, keyboard


@dp.callback_query_handler(lambda query: query.data.startswith('ticket_'))
async def show_ticket_info(query: types.CallbackQuery):
    ticket_id = query.data.split('_')[1]
    ticket_info = sql.get_ticket_info(ticket_id)
    
    text = f"<b>Детали заявки:</b> <code>#{ticket_info[0]}\n\n</code>" \
           f"<b>Пользователь ID:</b> <a href='tg://user?id={ticket_info[1]}'>{ticket_info[1]}</a>\n" \
           f"<b>Организация:</b> {ticket_info[2]}\n" \
           f"<b>Адрес:</b> {ticket_info[3]}\n" \
           f"<b>Сообщение:</b> {ticket_info[4]}\n" \
           f"<b>Время создания:</b> {ticket_info[5]}\n" \
           f"<b>Статус:</b> {ticket_info[6]}\n"

    keyboard = types.InlineKeyboardMarkup()
    complete_button = types.InlineKeyboardButton("✅ Выполнить", callback_data=f"complete_{ticket_info[0]}")
    back_button = types.InlineKeyboardButton("⬅️ Назад", callback_data="show_all_tickets_in_progress")
    keyboard.add(complete_button, back_button)
    await query.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")



# Группа колбеков на батоны
@dp.callback_query_handler()
async def inline_kb_answer_callback_handler(query: types.CallbackQuery):
    user_id = query.from_user.id
    tg_id = user_id

    if query.data == 'admin_panel':
        # Обновление ячейки 'pos' в базе данных
        sql.update_pos('admin_panel', 'tg_id', user_id)
        text, keyboard = admin_panel()
        await query.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
        
    if query.data == 'show_all_tickets_in_progress':
        # Обновление ячейки 'pos' в базе данных
        sql.update_pos('show_all_tickets_in_progress', 'tg_id', user_id)
        text, keyboard = show_all_tickets_in_progress()
        await query.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
        
    if query.data.startswith('complete_'):   
        ticket_id = query.data.split('_')[1]
        # Обновление ячейки 'pos' в базе данных
        sql.update_pos('complete_', 'tg_id', user_id)
        sql.update_ticket_status(ticket_id, "Завершена")
        
        # Отправка сообщения пользователю о завершении задачи
        ticket_info = sql.get_ticket_info(ticket_id)
        user_id = ticket_info[1]  # ID пользователя, поставившего задачу
        completion_message = f"🎉 Задача <code>#{ticket_id}</code> выполнена! \n\n⚠️ Пожалуйста, проверьте корректность исполнения задачи."
        
        await bot.send_message(user_id, completion_message, parse_mode="HTML")
        await bot.send_message(query.from_user.id, completion_message, parse_mode="HTML")        
        
    if query.data == 'main_menu':
        # Обновление ячейки 'pos' в базе данных
        sql.update_pos('main_menu', 'tg_id', user_id)
        text, keyboard = main_menu(tg_id)
        await query.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    
    if query.data == 'my_company':
        # Обновление ячейки 'pos' в базе данных
        sql.update_pos('my_company', 'tg_id', user_id)
        text, keyboard = my_company(tg_id)
        await query.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
       
    if query.data == 'edit_company_name':
        # Обновление ячейки 'pos' в базе данных
        sql.update_pos('edit_company_name', 'tg_id', user_id)
        text, keyboard = edit_company_name(tg_id)
        await query.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
        
    if query.data == 'edit_company_adress':
        # Обновление ячейки 'pos' в базе данных
        sql.update_pos('edit_company_adress', 'tg_id', user_id)
        text, keyboard = edit_company_adress(tg_id)
        await query.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")     

    if query.data == 'edit_company_inn':
        # Обновление ячейки 'pos' в базе данных
        sql.update_pos('edit_company_inn', 'tg_id', user_id)
        text, keyboard = edit_company_inn(tg_id)
        await query.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
 
    if query.data == 'edit_company_phone':
        # Обновление ячейки 'pos' в базе данных
        sql.update_pos('edit_company_phone', 'tg_id', user_id)
        text, keyboard = edit_company_phone(tg_id)
        await query.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
             
    if query.data == 'new_ticket':
        # Обновление ячейки 'pos' в базе данных
        sql.update_pos('new_ticket', 'tg_id', user_id)
        text, keyboard = new_ticket(tg_id)
        await query.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
        
    if query.data == 'my_ticket':
        # Обновление ячейки 'pos' в базе данных
        sql.update_pos('my_ticket', 'tg_id', user_id)
        text, keyboard = my_ticket(tg_id)
        await query.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")      

        
# Обратотка текстовых сообщений
@dp.message_handler()
async def handle_text_input(message: types.Message):
    user_id = message.from_user.id
    username = message.from_user.username
    profile = sql.read_profile(user_id)  
    organization_name = profile.get("organization", "")
    organization_address = profile.get("organization_adress", "") 
    organization_phone = profile.get("organization_phone", "Нет данных")
    user_position = sql.read_cell('pos', 'tg_id', user_id)

    if user_position == 'edit_company_name':
        sql.update_profile_data(user_id, 'organization', message.text)
        text, keyboard = my_company(user_id)
        await message.reply(text, reply_markup=keyboard, parse_mode="HTML")

    if user_position == 'edit_company_adress':
        sql.update_profile_data(user_id, 'organization_adress', message.text)
        text, keyboard = my_company(user_id)
        await message.reply(text, reply_markup=keyboard, parse_mode="HTML")

    if user_position == 'edit_company_inn':
        sql.update_profile_data(user_id, 'organization_inn', message.text)
        text, keyboard = my_company(user_id)
        await message.reply(text, reply_markup=keyboard, parse_mode="HTML")
        
    if user_position == 'edit_company_phone':
        sql.update_profile_data(user_id, 'organization_phone', message.text)
        text, keyboard = my_company(user_id)
        await message.reply(text, reply_markup=keyboard, parse_mode="HTML")
        
    if user_position == 'new_ticket':
        user_ticket = user_id
        organization = organization_name
        addres_ticket = organization_address
        message_ticket = message.text
        time_ticket = message.date
        state_ticket = "В работе"

        # Добавляем новую заявку в базу данных
        sql.add_ticket(user_ticket, organization, addres_ticket, message_ticket, time_ticket, state_ticket)
        # Получаем номер последней добавленной заявки
        last_ticket_number = sql.get_last_ticket_number()

        if last_ticket_number:
            # Обновляем профиль пользователя с номером последней добавленной заявки
            sql.update_profile_data(user_id, 'history_ticket', str(last_ticket_number))
            sql.update_profile_data(user_id, 'data_ticket', str(time_ticket))
            sql.update_profile_data(user_id, 'user_name', str(username))
            # Меню благодарочки
            text, keyboard = done_ticket(user_id)
            await message.reply(text, reply_markup=keyboard, parse_mode="HTML")
            
            # Отправка сообщения администратору
            admin_text = (f"📬❗️Пользователь @{username} создал новую заявку с номером <code>{last_ticket_number}</code>."
                          f"\n\n<b>Сообщение от пользователя:</b>\n - {message_ticket}"
                          f"\n\n<b>Телефон:</b> {organization_phone}\n"
                          f"<b>Компания:</b> {organization}\n"
                          f"<b>Адрес:</b> {addres_ticket}\n"
            )
            await bot.send_message(config.ADMIN_USER, admin_text, parse_mode="HTML")
        else:
            await message.reply("Ошибка при получении заявки.")
            

if __name__ == '__main__':
    executor = aiogram.executor.Executor(dp, loop=loop, skip_updates=True)
    executor.start_polling()
