import asyncio, logging, re

from aiogram import Bot, Dispatcher, types
from aiogram.filters.command import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

from datetime import datetime  # Buyurtma vaqtini aniqlaydi

from geopy.geocoders import Nominatim
from geopy.distance import geodesic

from random import randint
from branch import branch_info
from menu import menu   # Menyuni import qilish
# from sendsms import send_sms, get_eskiz  # Bu funksiyani oxirida yoqaman


TOKEN = "7793799628:AAH7OefE0pBzFv_PfPfseo3RDbMOqafKhOo"
channel_username = "@zayavka_uz"

logging.basicConfig(level=logging.INFO)

bot = Bot(token=TOKEN)
dp = Dispatcher()

# Geopy geocoderini yaratish
geolocator = Nominatim(user_agent="my_bot")

user_data = {}
user_orders = {}


email = "Your eskiz.uz email here"
password = "Your eskiz.uz password here"


@dp.message()
async def handle_message(message: types.Message):
    user_id = message.from_user.id
    if user_id not in user_data:
        await startup(message)
        return

    state = user_data[user_id]["state"]

    if state == "PHONE_NUMBER":
        await phone_number(message)
    elif state == "VERIFICATION":
        await check_verification(message)
    elif state == 'VERIFICATIONS':
        await process_verification(message)
    elif state == "ADDRESS":
        await address(message)
    elif state == "MAIN_MENU":
        # Bosh menyuda foydalanuvchi tanlovi
        if message.text == "📖 Buyurtmalar tarixi":
            await show_orders(message)
        elif message.text == "⚙️Sozlash ℹ️ Ma'lumotlar":
            await show_settings(message)
        elif message.text == "🔥 Aksiya":
            await show_discounts(message)
        elif message.text == "🙋🏻‍♂️ Jamoamizga qo'shiling":
            await join_command(message)
        else:
            await process_main_menu(message)
    elif state == "ORDER_MENU":
        # Buyurtma menyusida foydalanuvchi tanlovi
        await process_order_menu(message)
    elif state == "DELIVERY_MENU":
        # Yetkazib berish menyusida foydalanuvchi tanlovi
        await process_delivery_menu(message)
    elif state == "TAKEAWAY_MENU":
        # Olib ketish menyusida foydalanuvchi tanlovi
        await process_takeaway_menu(message)
    elif state == "DISCOUNTS":
        # Aksiya menyusida foydalanuvchi tanlovi
        await process_main_menu(message)
    elif state == "FOOD_MENU":
        # Taom menyusida foydalanuvchi tanlovi
        await process_food_menu(message)
    elif state == "ITEM_SELECTION":
        # Buyurtma uchun item tanlash
        await process_item_selection(message)
    elif state == "BASKET":
        # Savatni ko'rsatish
        await process_show_basket(message)
    elif state == 'CALL_MENU':
        # Qo'ng'iroq menyusida foydalanuvchi tanlovi
        await process_call(message)
    elif state == 'SELECT_BRANCH_MENU':
        # Filial tanlash
        await process_select_branch(message)
    elif state == 'SETTINGS':
        # Sozlash menyusida foydalanuvchi tanlovi
        await process_settings(message)
    elif state == 'BRANCH':
        # Filial tanlash
        await process_branch(message)
    elif state == 'WAITING_FOR_NAME':
        # Ismni kiritish
        await process_change(message)
    elif state == 'WAITING_FOR_PHONE':
        # Telefon raqamini kiritish
        await process_change(message)
    elif state == 'NEAR_BRANCH_MENU':
        # Eng yaqin filialni tanlash
        await show_nearest_branch(message)
    elif state == 'CHANGE_LANGUAGE':
        # Tilni o'zgartirish
        await change_language(message)


@dp.message(Command("start"))
async def startup(message: types.Message):
    user_id = message.from_user.id    
    user_data[user_id] = {"state": "PHONE_NUMBER"}
    await message.answer("Assalomu Aleykum! Les Ailesga hush kelibsiz!\nIltimos 📲 Raqam Jo'natish tugmasini bosing yoki raqaminggizni kiriting.",
                        reply_markup=ReplyKeyboardMarkup(
                            keyboard=[[KeyboardButton(text="📲 Raqam Jo'natish", request_contact=True)]],
                            resize_keyboard=True
                        ))
    
# Telefon raqami tekshiruvi
def is_valid_uzbek_phone_number(phone):
    # Telefon raqami +998 bilan boshlanishi va 13 ta belgidan iborat bo'lishi kerak
    pattern = r"^\+998\d{9}$"
    return re.match(pattern, phone) is not None


# Telefon raqamini kiritish
async def phone_number(message: types.Message):
    user_id = message.from_user.id

    user_name = message.from_user.username or "None"
    name = message.from_user.first_name
    user_data[user_id]["username"] = user_name
    user_data[user_id]["name"] = name

    if message.contact is not None:
        phone = message.contact.phone_number
    else:
        phone = message.text

    if is_valid_uzbek_phone_number(phone):
        user_data[user_id]['phone'] = phone
        verification_code = randint(1000, 9999)
        user_data[user_id]['verification_code'] = verification_code
        
        # token = await get_eskiz(email, password)
        # await send_sms(phone, token)                  #BU ikkisini ham oxirida yoqish kere

        user_data[user_id]["state"] = "VERIFICATION"
        await message.answer(f"Tasdiqlash raqamini kiriting: {verification_code}")
    else:
        await message.answer(f"Raqam mavjud emas! Boshqatan urunib ko'ring:")

    print(user_data)

# Tasdiqlash kodi tekshirish
async def check_verification(message: types.Message):
    user_id = message.from_user.id
    if message.text == str(user_data[user_id]['verification_code']):
        user_data[user_id]["state"] = "ADDRESS"
        await message.answer("Ajoyib! Endi manzil kiriting yoki 📍 Manzil Jo'natish tugmasini bosing.",
                            reply_markup=ReplyKeyboardMarkup(
                                keyboard=[[KeyboardButton(text="📍Manzil Jo'natish", request_location=True)]],
                                resize_keyboard=True
                            ))
    else:
        await message.reply("Tasdiqlash kodi xato. Iltimos qaytadan urunib ko'ring.")

# Manzilni kiritish
async def address(message: types.Message):
    user_id = message.from_user.id
    if message.location:
        latitude = message.location.latitude
        longitude = message.location.longitude

        # Geolokatsiyani manzilga aylantirish
        location = geolocator.reverse((latitude, longitude), language='uz', timeout=10)
        
        if location:
            full_address = location.address
            formatted_address = format_address(full_address)  # Formatlash
            user_data[user_id]["address"] = formatted_address
            user_data[user_id]["state"] = "MAIN_MENU"
            await message.answer(f"Manzilingiz:\n{formatted_address}")
            await show_main_menu(message)
        else:
            await message.answer("Manzilni aniqlashda xatolik yuz berdi.")
    else:
        user_data[user_id]["address"] = message.text
        user_data[user_id]["state"] = "MAIN_MENU"
        await show_main_menu(message)


# Manzildan kerakli qismlarni ajratib olish
def format_address(address: str) -> str:
    parts = address.split(", ")
    
    # Manzildan kerakli qismlarni olish
    try:
        country = parts[-1]
        district = parts[-3]
        street = parts[1]
        house = parts[0]

        # Formatlangan manzilni qaytarish
        return f"{country}, {district}, {street}, {house}"
    except IndexError:
        return "Manzilni aniqlashda xatolik yuz berdi."
    

# Bosh menyuni ko'rsatish
async def show_main_menu(message: types.Message):
    keyboard = [
        [KeyboardButton(text="🛍 Buyurtma berish")],
        [KeyboardButton(text="📖 Buyurtmalar tarixi")],
        [KeyboardButton(text="⚙️ Sozlash ℹ️ Ma'lumotlar"), KeyboardButton(text="🔥 Aksiya")],
        [KeyboardButton(text="🙋🏻‍♂️ Jamoamizga qo'shiling"), KeyboardButton(text="☎️ Les Ailes bilan aloqa")]
    ]
    
    await message.answer("Bosh menyu:", reply_markup=ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True
    ))

    print(user_data)

# Bosh menyudagi tugmalarni qayta ishlash
async def process_main_menu(message: types.Message):
    user_id = message.from_user.id

    if message.text == "🛍 Buyurtma berish":
        await show_order_menu(message)
    elif message.text == "📖 Buyurtmalar tarixi":
        await show_orders(message)
    elif message.text == "⚙️ Sozlash ℹ️ Ma'lumotlar":
        await show_settings(message)
    elif message.text == "🔥 Aksiya":
        await show_discounts(message)
    elif message.text == "🙋🏻‍♂️ Jamoamizga qo'shiling ":
        await join_command(message)
    elif message.text == "☎️ Les Ailes bilan aloqa":
        await call_command(message)

    print(user_data)

async def show_order_menu(message: types.Message):
    user_id = message.from_user.id
    user_data[user_id]["state"] = "ORDER_MENU"
    keyboard = [
            [KeyboardButton(text="🏃 Olib ketish"), KeyboardButton(text="🚙 Yetkazib berish")],
            [KeyboardButton(text="⬅️ Orqaga")],
        ]
    await message.answer("Buyurtmani o'zingiz 🙋‍♂️ olib keting yoki Yetkazib berishni 🚙 tanlang", reply_markup=ReplyKeyboardMarkup(
            keyboard=keyboard,
            resize_keyboard=True
            ))

# Buyurtma berish tugmasi
async def process_order_menu(message: types.Message):
    user_id = message.from_user.id
    if message.text == "🏃 Olib ketish":
        user_data[user_id]["state"] = "TAKEAWAY_MENU"  # State ni yangilash
        await show_takeaway_menu(message)
    elif message.text == "🚙 Yetkazib berish":
        user_data[user_id]["state"] = "DELIVERY_MENU"  # State ni yangilash
        await show_delivery_menu(message)
    elif message.text == "⬅️ Orqaga":
        user_data[user_id]["state"] = "MAIN_MENU"  # State ni yangilash
        await show_main_menu(message)


# Olib ketish menyusini ko'rsatish
async def show_takeaway_menu(message: types.Message):
    keyboard = [
            [KeyboardButton(text="⬅️ Orqaga"), KeyboardButton(text="📍 Eng yaqin filialni aniqlash")],
            [KeyboardButton(text="🌐 Bu yerda buyurtma berish"), KeyboardButton(text="📍 Filialni tanlang")],
        ]
    await message.answer("Olib ketish", reply_markup=ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True
    ))

# Yetkazib berish menyusini ko'rsatish
async def show_delivery_menu(message: types.Message):
    user_id = message.from_user.id
    # user_id[user_data]["state"] = "DELIVERY_MENU"
    keyboard = [
            [KeyboardButton(text="📍 Eng yaqin filialni aniqlash")],
            [KeyboardButton(text="⬅️ Orqaga"), KeyboardButton(text="🗺 Mening manzillarim")],
        ]
    await message.answer("Yetkazib berish", reply_markup=ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True
    ))

# Olib ketish menyusida foydalanuvchi tanlovini qabul qilish
async def process_takeaway_menu(message: types.Message):
    user_id = message.from_user.id
    if message.text == "🌐 Bu yerda buyurtma berish":

        inline_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="O'tish", url="https://lesailes.uz/")]
        ])
        # Xabarni yuborish
        await message.answer("O'z joylashuvingiz bilan buyurtma bering - https://lesailes.uz/", reply_markup=inline_keyboard)

        user_data[user_id]["state"] = "TAKEAWAY_MENU"  # State ni yangilash

    elif message.text == "📍 Filialni tanlang":
        user_data[user_id]["state"] = "SELECT_BRANCH_MENU"  # State ni yangilash
        await show_select_branch(message)

    elif message.text == "📍 Eng yaqin filialni aniqlash":
        user_data[user_id]["state"] = "NEAR_BRANCH_MENU"  # State ni yangilash
        await show_nearest_branch(message)

    elif message.text == "⬅️ Orqaga":
        user_data[user_id]["state"] = "ORDER_MENU"  # State ni yangilash
        await show_order_menu(message)


# Yetkazib berish menyusida foydalanuvchi tanlovini qabul qilish
async def process_delivery_menu(message: types.Message):
    user_id = message.from_user.id
    if message.text == "🗺 Mening manzillarim":
        await message.answer("Sizning Manzilingiz: "+ user_data[user_id]["address"])
        user_data[user_id]["state"] = "FOOD_MENU"  # State ni yangilash
        await show_food_menu(message)
    elif message.text == "📍 Eng yaqin filialni aniqlash":
        user_data[user_id]["state"] = "NEAR_BRANCH_MENU"  # State ni yangilash
        await show_nearest_branch(message)
    elif message.text == "⬅️ Orqaga":
        user_data[user_id]["state"] = "ORDER_MENU"  # State ni yangilash
        await show_order_menu(message)


async def show_select_branch(message: types.Message):
    user_id = message.from_user.id
    user_data[user_id]["state"] = "SELECT_BRANCH_MENU"
    keyboard = [
            [KeyboardButton(text="Bochka"), KeyboardButton(text="Samarqand Darvoza")],
            [KeyboardButton(text="Atlas"), KeyboardButton(text="Chilonzor")],
            [KeyboardButton(text="Oybek"), KeyboardButton(text="M-5")],
            [KeyboardButton(text="Zenit"), KeyboardButton(text="Sergeli")],
            [KeyboardButton(text="S. Rahimov"), KeyboardButton(text="Farhod")],
            [KeyboardButton(text="Yunusobot"), KeyboardButton(text="Buyuk ipak yo'li")],
            [KeyboardButton(text="Parus"), KeyboardButton(text="Ko'kcha")],
            [KeyboardButton(text="Asia Nukus"), KeyboardButton(text="Next")],

            [KeyboardButton(text="⬅️ Orqaga")],
        ]
    await message.answer("📍 Filialni tanlang", reply_markup=ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True
    ))


async def find_nearest_branch(user_id):
    # Foydalanuvchining joylashuvi
    if "address" not in user_data[user_id]:
        return None, None

    user_location = user_data[user_id]["address"]  # Foydalanuvchining geolokatsiyasi (lat, lon)

    if isinstance(user_location, str):  # Agar manzil string bo'lsa, geolokatsiya qilishimiz kerak
        location = geolocator.geocode(user_location)
        if location:
            user_location = (location.latitude, location.longitude)
        else:
            return None, None  # Manzilni aniqlashda xatolik

    # Eng yaqin filialni aniqlash
    nearest_branch = None
    min_distance = float('inf')  # Boshlang'ichda eng kichik masofani o'rnatamiz

    for branch_name, branch in branch_info.items():
        branch_location = branch["location"]  # Filialning koordinatalari
        # Haversine yordamida masofani hisoblash
        distance = geodesic(user_location, branch_location).kilometers

        if distance < min_distance:
            min_distance = distance
            nearest_branch = branch_name

    return nearest_branch, min_distance

async def show_nearest_branch(message: types.Message):
    user_id = message.from_user.id

    # Agar foydalanuvchi manzilini hali yubormagan bo'lsa
    if "address" not in user_data[user_id]:
        await message.answer("Iltimos, avval manzilingizni yuboring.")
        return

    # Foydalanuvchining joylashuvini olish va eng yaqin filialni aniqlash
    nearest_branch, distance = await find_nearest_branch(user_id)

    # Eng yaqin filialni foydalanuvchiga yuborish
    if nearest_branch:
        branch = branch_info[nearest_branch]
        address = branch["address"]
        location = branch["location"]

        await message.answer(f"Eng yaqin filial:\n{address}\nMasofa: {distance:.2f} km.")
        await message.answer_location(latitude=location[0], longitude=location[1])

        # Foydalanuvchi uchun Food Menu ni ko'rsatish
        user_data[user_id]["state"] = "FOOD_MENU"
        await show_food_menu(message)
    else:
        await message.answer("Filiallar bilan bog'lanishda xatolik yuz berdi.")


async def process_select_branch(message: types.Message):
    user_id = message.from_user.id
    
    if message.text == "⬅️ Orqaga":
        user_data[user_id]["state"] = "ORDER_MENU"  # State ni yangilash
        await show_order_menu(message)  # Orqaga qaytish

    elif message.text in branch_info:
        # Tanlangan filial haqida ma'lumot yuborish
        user_data[user_id]["branch"] = message.text
        branch = branch_info[message.text]
        address = branch["address"]
        location = branch["location"]

        # Manzilni yuborish
        await message.answer(address)

        # Geografik joylashuvni yuborish
        await message.answer_location(latitude=location[0], longitude=location[1])

        # Foydalanuvchining holatini yangilash va ovqat menyusini ko'rsatish
        user_data[user_id]["state"] = "FOOD_MENU"
        await show_food_menu(message)



# Les Ailes bilan aloqaga chiqish
async def call_command(message: types.Message):
    user_id = message.from_user.id
    if message.text == '☎️ Les Ailes bilan aloqa':
        user_data[user_id]["state"] = "CALL_MENU"
        keyboard = [
        [KeyboardButton(text="💬 Biz bilan aloqaga chiqing"),
        KeyboardButton(text="⬅️ Orqaga")], 
        ]   
        await message.answer("Agar siz bizga yozsangiz yoki sharh qoldirmoqchi bo'lsangiz, xursand bo'lamiz.", reply_markup=ReplyKeyboardMarkup(      
            keyboard=keyboard,
            resize_keyboard=True
        ))

        print(user_data)

# Biz bilan aloqaga chiqish tugmasiga bosilganida
async def process_call(message: types.Message):
    user_id = message.from_user.id
    if message.text == "💬 Biz bilan aloqaga chiqing":
        
        inline_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💬 Biz bilan aloqaga chiqing", url="https://t.me/lesaileshelpbot")]
        ])

        await message.answer("Agar biron-bir savol yoki taklif bo'lsa, bizga aloqaga chiqing.",
                            reply_markup=inline_keyboard)
    
    elif message.text == "⬅️ Orqaga":
        user_data[user_id]["state"] = "MAIN_MENU"
        await show_main_menu(message)

        print(user_data)
        

# Jamoaga qo'shilish
async def join_command(message: types.Message):
    user_id = message.from_user.id

    # Inline tugmalarni yaratish
    inline_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="O'tish", url="https://t.me/HavoqandJamoa_Bot")]
    ])

    await message.answer(
        "Ahil jamoamizda ishlashga taklif qilamiz! Telegramdan chiqmay, shu yerning o'zida anketani to'ldirish uchun quyidagi tugmani bosing.",
        reply_markup=inline_keyboard
    )

    user_data[user_id]["state"] = "MAIN_MENU"

    print(user_data)


async def show_settings(message: types.Message):
    user_id = message.from_user.id
    user_data[user_id]["state"] = "SETTINGS"

    keyboard = [
        [KeyboardButton(text="Ismni o'zgartirish"), KeyboardButton(text="📱 Raqamni o'zgartirish")],
        [KeyboardButton(text="🏙 Shaharni o'zgartirish"), KeyboardButton(text="🇺🇿 Tilni o'zgartirish")],
        [KeyboardButton(text="ℹ️ Filallar haqida ma'lumotlar"), KeyboardButton(text="📄 Ommaviy taklif")],
        [KeyboardButton(text="⬅️ Orqaga")],
    ]
    await message.answer("Harakatni tanlang:", reply_markup=ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True
    ))

    print(user_data)


async def process_settings(message: types.Message):
    user_id = message.from_user.id
    if message.text == "Ismni o'zgartirish":
        user_data[user_id]["state"] = "CHANGE_NAME"
        await change_settings(message)

    elif message.text == "📱 Raqamni o'zgartirish":
        user_data[user_id]["state"] = "CHANGE_PHONE"
        await change_settings(message)

    elif message.text == "🏙 Shaharni o'zgartirish":
        user_data[user_id]["state"] = "CHANGE_CITY"
        await change_settings(message)

    elif message.text == "🇺🇿 Tilni o'zgartirish":
        user_data[user_id]["state"] = "CHANGE_LANGUAGE"
        keyboard = [
            [KeyboardButton(text="🇷🇺 Русский"), KeyboardButton(text="🇺🇿 O'zbekcha"), KeyboardButton(text="🇺🇸 English")],
            [KeyboardButton(text="⬅️ Orqaga")],
        ]
        await message.answer("Tilni tanlang:", reply_markup=ReplyKeyboardMarkup(
            keyboard=keyboard,
            resize_keyboard=True
        ))

    elif message.text == "ℹ️ Filallar haqida ma'lumotlar":
        await show_branch(message)

    elif message.text == "📄 Ommaviy taklif":
        await message.answer("https://telegra.ph/Publichnaya-oferta-Chopar-Pizza-05-21")
        user_data[user_id]["state"] = "SETTINGS"

    elif message.text == "⬅️ Orqaga":
        user_data[user_id]["state"] = "MAIN_MENU"
        await show_main_menu(message)

    print(user_data)


async def change_settings(message: types.Message):
    user_id = message.from_user.id

    if user_data[user_id]["state"] == "CHANGE_NAME":
        await message.answer("Ismingizni kiriting:")
        user_data[user_id]["state"] = "WAITING_FOR_NAME"  # Holatni o'zgartiramiz

    elif user_data[user_id]["state"] == "CHANGE_PHONE":
        await message.answer("Raqamingizni kiriting: (+998xx xxx xx xx)")
        user_data[user_id]["state"] = "WAITING_FOR_PHONE"  # Holatni o'zgartiramiz

    elif user_data[user_id]["state"] == "CHANGE_CITY":
        await message.answer("Hozirgi kunda faqat Toshkent shahridagi filiallar mavjud!")
        user_data[user_id]["state"] = "SETTINGS"
        await show_settings(message)

    elif user_data[user_id]["state"] == "CHANGE_LANGUAGE":
        await change_language(message)

    elif message.text == "⬅️ Orqaga":
        user_data[user_id]["state"] = "SETTINGS"
        await show_settings(message)


async def change_language(message: types.Message):
    user_id = message.from_user.id
    if message.text == "🇺🇿 O'zbekcha":
        await message.answer("✅ Tayyor")
        user_data[user_id]["state"] = "SETTINGS"
        await show_settings(message)

    elif message.text == "🇺🇸 English":
        await message.answer("Hozirgi kunda faqat O'zbek tili mavjud")
        user_data[user_id]["state"] = "SETTINGS"
        await show_settings(message)

    elif message.text == "🇷🇺 Русский":
        await message.answer("Hozirgi kunda faqat O'zbek tili mavjud")
        user_data[user_id]["state"] = "SETTINGS"
        await show_settings(message)

    elif message.text == "⬅️ Orqaga":
        user_data[user_id]["state"] = "SETTINGS"
        await show_settings(message)

async def process_change(message: types.Message):
    user_id = message.from_user.id

    if user_data[user_id]["state"] == "WAITING_FOR_NAME":
        user_data[user_id]["name"] = message.text
        await message.answer("✅ Saqlandi")
        user_data[user_id]["state"] = "SETTINGS"
        await show_settings(message)

    elif user_data[user_id]["state"] == "WAITING_FOR_PHONE":
        user_id = message.from_user.id
        phone = message.text

        if is_valid_uzbek_phone_number(phone):
            user_data[user_id]['phone'] = message.text
            verification_code = randint(1000, 9999)
            user_data[user_id]['verification_code'] = verification_code
        
            # token = await get_eskiz(email, password)
            # await send_sms(phone, token)                  #BU ikkisini ham oxirida yoqish kere

            user_data[user_id]["state"] = "VERIFICATIONS"
            await message.answer(f"Tasdiqlash raqamini kiriting: {verification_code}")
        else:
            await message.answer(f"Raqam mavjud emas! Boshqatan urunib ko'ring:")

        # user_data[user_id]["state"] = "SETTINGS"
        # await show_settings(message)

async def process_verification(message: types.Message):
    user_id = message.from_user.id
    if message.text == str(user_data[user_id]['verification_code']):
        await message.answer("✅ Saqlandi")
        user_data[user_id]["state"] = "SETTINGS"
        await show_settings(message)
    else:
        await message.answer("Raqam noto'g'ri kiritildi. Boshqatan urunib ko'ring:")


async def show_branch(message: types.Message):
    user_id = message.from_user.id
    user_data[user_id]["state"] = "BRANCH"
    keyboard = [
        [KeyboardButton(text="Bochka"), KeyboardButton(text="Samarqand Darvoza")],
        [KeyboardButton(text="Atlas"), KeyboardButton(text="Chilonzor")],
        [KeyboardButton(text="Oybek"), KeyboardButton(text="M-5")],
        [KeyboardButton(text="Zenit"), KeyboardButton(text="Sergeli")],
        [KeyboardButton(text="S. Rahimov"), KeyboardButton(text="Farhod")],
        [KeyboardButton(text="Yunusobot"), KeyboardButton(text="Buyuk ipak yo'li")],
        [KeyboardButton(text="Parus"), KeyboardButton(text="Ko'kcha")],
        [KeyboardButton(text="Asia Nukus"), KeyboardButton(text="Next")],
        [KeyboardButton(text="⬅️ Orqaga")], 
    ]
    await message.answer("Sizni qaysi filial qiziqtiryapti ?", reply_markup=ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True
    ))


# Foydalanuvchi filialni tanlaganidan so'ng uni qayta ishlash
async def process_branch(message: types.Message):
    user_id = message.from_user.id

    # Foydalanuvchi tanlagan filialni tekshirish
    if message.text == "⬅️ Orqaga":
        user_data[user_id]["state"] = "SETTINGS"
        await show_settings(message)

    elif message.text in branch_info:
        # Tanlangan filial haqida ma'lumot yuborish
        user_data[user_id]["branch"] = message.text
        branch = branch_info[message.text]
        address = branch["address"]
        location = branch["location"]

        # Manzilni yuborish
        await message.answer(address)

        # Geografik joylashuvni yuborish
        await message.answer_location(latitude=location[0], longitude=location[1])

        user_data[user_id]["state"] = "BRANCH"  # State ni yangilash
    else:
        await message.answer("Noma'lum filial tanlandi. Iltimos, ro'yxatdan biror bir filialni tanlang.")


# Aksiya borligini tekshirish
async def show_discounts(message: types.Message):
    user_id = message.from_user.id
    user_data[user_id]["state"] = "DISCOUNTS"
    await message.answer("Sizning shahringizda aksiya mavjud emas") 

    print(user_data)


# Menyuni ko'rsatish
async def show_food_menu(message: types.Message):
    keyboard = [[KeyboardButton(text="⬅️ Orqaga"), KeyboardButton(text="📥 Savat")]]
    categories = list(menu.keys())
    for i in range(0, len(categories), 2):
        row = [KeyboardButton(text=categories[i])]
        if i + 1 < len(categories):
            row.append(KeyboardButton(text=categories[i + 1]))
        keyboard.append(row)

    await message.answer("Nimalarni tanladingiz?", reply_markup=ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True
    ))

    print(user_data)


async def process_food_menu(message: types.Message):
    user_id = message.from_user.id
    if message.text in menu:
        category = message.text
        user_data[user_id]['cur_category'] = category
        await show_items(message, category)
    elif message.text == "📥 Savat":
        await show_basket(message)
        user_data[user_id]["state"] = "BASKET"
    elif message.text == "⬅️ Orqaga":
        user_data[user_id]["state"] = "ORDER_MENU"
        await show_order_menu(message)
    else:
        await message.reply(f"Bunday taom mavjud emas\n Iltimos menyudan tanlang")

    print(user_data)


async def show_items(message: types.Message, category: str):
    user_id = message.from_user.id
    keyboard = [[KeyboardButton(text="⬅️ Orqaga"), KeyboardButton(text="📥 Savat")]]
    
    items = list(menu[category].keys())
    for i in range(0, len(items), 2):
        row = [KeyboardButton(text=items[i])]
        if i + 1 < len(items):
            row.append(KeyboardButton(text=items[i + 1]))
        keyboard.append(row)
    
    user_data[user_id]["state"] = "ITEM_SELECTION"
    await message.answer(f"Menyu: {category}", reply_markup=ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True
    ))

    print(user_data)



async def process_item_selection(message: types.Message):
    user_id = message.from_user.id
    category = user_data[user_id]["cur_category"]
    if message.text in menu[category]:
        item = message.text
        price = menu[category][item]["price"]
        description = menu[category][item].get("description", "Tavsif mavjud emas.")  # Tavsifni olish

        user_data[user_id]["cur_item"] = item
        count_key = f"{user_id}_{item}_count"

        # Инициализируем количество, если его еще нет
        current_count = user_data.get(count_key, 0)

        # Рассчитываем общую цену на основе количества
        total_price = price * current_count
        keyboard = [
            [
                InlineKeyboardButton(text="➖", callback_data=f"decrease_{item}"),
                InlineKeyboardButton(text=str(current_count), callback_data=f"count_{item}"),
                InlineKeyboardButton(text="➕", callback_data=f"increase_{item}")
            ],
            [InlineKeyboardButton(text="📥 Savatga qoshish ✅", callback_data="add_to_basket")]
        ]

        await message.reply_photo(
            photo=menu[category][item]["image"],
            caption=(
                f"{item}\n"
                f"{description}\n"  # Tavsifni qo'shish
                f"Narxi: {price} so'm\n"
            ),
            reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
        )
    elif message.text == "⬅️ Orqaga":
        user_data[user_id]["state"] = "FOOD_MENU"
        await show_food_menu(message)
    
    elif message.text == "📥 Savat":
        await show_basket(message)
        user_data[user_id]["state"] = "BASKET"

    print(user_data)


@dp.callback_query()
async def process_item_callback(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    current_item = user_data[user_id]["cur_item"]
    count_key = f"{user_id}_{current_item}_count"

    # Ustunliklarni oshirish yoki kamaytirish
    if "increase" in callback_query.data:
        user_data[count_key] = user_data.get(count_key, 0) + 1
    elif "decrease" in callback_query.data and user_data.get(count_key, 0) > 1:
        user_data[count_key] -= 1
    elif callback_query.data == "add_to_basket":
        # Savatga qo'shish
        user_data[user_id].setdefault("basket", {})
        current_count = user_data.get(count_key, 0)
        if current_count >= 1:
            user_data[user_id]["basket"][current_item] = user_data[user_id]["basket"].get(current_item, 0) + current_count
            await callback_query.answer("Savatga qo'shildi ✅")
            return
        elif current_count == 0:
            await callback_query.answer("Iltimos, miqdorni tanlang! ❌")
            return

    current_count = user_data.get(count_key, 0)
    price = menu[user_data[user_id]["cur_category"]][current_item]["price"]
    description = menu[user_data[user_id]["cur_category"]][current_item].get("description", "Tavsif mavjud emas.")  # Tavsifni olish
    total_price = price * current_count

    # Yangilangan xabarni yuboring
    keyboard = [
        [
            InlineKeyboardButton(text="➖", callback_data=f"decrease_{current_item}"),
            InlineKeyboardButton(text=str(current_count), callback_data=f"count_{current_item}"),
            InlineKeyboardButton(text="➕", callback_data=f"increase_{current_item}")
        ],
        [InlineKeyboardButton(text="📥 Savatga qoshish ✅", callback_data="add_to_basket")]
    ]

    # Обновляем подпись и инлайн-клавиатуру с новым количеством
    await callback_query.message.edit_caption(
        caption=(
                f"{current_item}\n"
                f"{description}\n"  # Tavsifni qo'shish
                f"Narxi: {total_price} so'm\n"
            ),
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
    )
    await callback_query.answer()

    print(user_data)


async def show_basket(message: types.Message):
    user_id = message.from_user.id
    user_data[user_id]["state"] = "BASKET"  # Savat holatini o'rnating
    basket = user_data[user_id].get("basket", {})

    if not basket:
        await message.reply("Sizning savatingiz bo'sh")
    else:
        basket_text = ""
        total_sum = 0

        for item, count in basket.items():
            # Har bir item uchun category'ni topish
            category_found = None
            for category in menu:
                if item in menu[category]:
                    category_found = category
                    break
            
            if category_found is None:
                continue  # Agar category topilmasa, o'tkazib yuborish

            price = menu[category_found][item]["price"]
            item_total = price * count
            total_sum += item_total
            basket_text += f"{item} x {count} dona. = {item_total} so'm\n"

        basket_text += f"\nTo'lov uchun: {total_sum} so'м"

        keyboard = [
            [KeyboardButton(text="⬅️ Orqaga"), KeyboardButton(text="✅ Zakazni yopish")],
            [KeyboardButton(text="🔄 Tozalash")]
        ]

        await message.reply(f"Sizning savatingizda:\n{basket_text}", reply_markup=ReplyKeyboardMarkup(
            keyboard=keyboard,
            resize_keyboard=True
        ))

        print(user_data)


async def process_show_basket(message: types.Message):
    user_id = message.from_user.id
    user_data[user_id]["state"] = "SHOW_BASKET"


    if message.text == "⬅️ Orqaga":
        user_data[user_id]["state"] = "FOOD_MENU"
        await show_food_menu(message)
    elif message.text == "✅ Zakazni yopish":
        user_data[user_id]["state"] = "MAIN_MENU"
        await finish_order(message)
    elif message.text == "🔄 Tozalash":
        user_data[user_id]["basket"] = {}
        await message.answer("To'liq tozalangan 🔄, uni tezda to'ldirish kerak ☺️")
        user_data[user_id]["state"] = "FOOD_MENU"
        await show_food_menu(message)

    print(user_data)


async def finish_order(message: types.Message):
    user_id = message.from_user.id
    basket = user_data[user_id].get('basket', {})

    if not basket:
        await message.reply("Sizning savatingiz bo'sh. Iltimos, buyurtma qiling.")
        return

    total = sum(menu[category][item]['price'] * quantity
                for category in menu
                for item, quantity in basket.items()
                if item in menu[category])

    now = datetime.now()
    formatted_time = now.strftime("%Y-%m-%d %H:%M")

    order_summary = "Sizning buyurtmangiz:\n\n" + "\n".join(f"{item}: {quantity} dona." for item, quantity in basket.items())
    await message.reply(f"{order_summary}\n\nTo'lovga: {total} so'm\n\nBuyurtma beruvchi ismi: {user_data[user_id]['name']}\n\nBuyurtma berilgan vaqti: {formatted_time}\n\n🎉 Xaridingiz uchun raxmat 🥰\n🕒 Buyurtmangiz 15 daqiqada tayyor bo'ladi!")

    # Buyurtmani saqlash
    user_orders.setdefault(user_id, []).append({
        "summary": order_summary,
        "total": total,
        "address": user_data[user_id].get("address", "Mavjud emas"),
        "name": user_data[user_id].get("name", "Mavjud emas"),
        "time": formatted_time
    })

    await bot.send_message(channel_username, f"{order_summary}\n\nTo'lovga: {total} so'm\n\nBuyurtma beruvchi ismi: {user_data[user_id]['name']}\n\nBuyurtma berilgan vaqti: {formatted_time}\n\nBuyurtma berivchi raqami: {user_data[user_id]['phone']}\n")

    # Foydalanuvchi ma'lumotlarini tozalash
    user_data[user_id]["basket"] = {}  # Savatni tozalash
    user_data[user_id]["cur_item"] = None  # Tanlangan itemni tozalash
    user_data[user_id]["cur_category"] = None  # Tanlangan kategoriya
    user_data[user_id]["state"] = "MAIN_MENU"
    
    # Foydalanuvchiga bosh menyuni ko'rsatish
    await show_main_menu(message)


async def show_orders(message: types.Message):
    user_id = message.from_user.id
    orders = user_orders.get(user_id, [])

    if not orders:
        await message.reply("Sizning buyurtma tarixingiz bo'sh.")
    else:
        order_history = ""
        for order in orders:
            order_history += f"{order['summary']}\n\nTo'lov: {order['total']} so'm\nManzil: {order['address']}\nBuyurtma beruvchi ismi: {order['name']}\nBuyurtma berilgan vaqti: {order['time']}\n\n"
        
        await message.reply(f"Sizning buyurtma tarixingiz:\n\n{order_history}")

    user_data[user_id]["state"] = "MAIN_MENU"

async def main():
    await dp.start_polling(bot)

print('The bot is running...')

if __name__ == "__main__":
    asyncio.run(main())