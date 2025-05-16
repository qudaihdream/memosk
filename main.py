import logging
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.filters import Command

# استبدل التوكن بتوكن البوت الخاص بك
API_TOKEN = "7917264932:AAHkuA9hrMAiFu5WvqZZTfDSdUh4O8oPcLc"

# إعداد السجل
logging.basicConfig(level=logging.INFO)

# إنشاء كائنات البوت والموزع
bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# إنشاء لوحة أزرار داخلية
inline_kb = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="اقسام المسشتفى", callback_data="info")],
    [InlineKeyboardButton(text="الدخول والخروج", callback_data="hello")],
    [InlineKeyboardButton(text="التقارير الطبية", callback_data="exit")]
])

# عند تنفيذ الأمر /start
@dp.message(Command("menu"))
async def start_handler(message: types.Message):
    await message.answer("مستشفى الرعاية المديدة بالظهران يرحب بكم ..فضلا اختر الخدمة من القائمة ", reply_markup=inline_kb)

# التعامل مع الضغط على الأزرار
@dp.callback_query()
async def handle_callback(callback: types.CallbackQuery):
    if callback.data == "hello":
        await callback.message.answer("هنا سوف يكون مشروع الدخول والخروج")
    elif callback.data == "info":
        await callback.message.answer("هنا سوف يكون مشروع التقارير الطبية")
    elif callback.data == "exit":
        await callback.message.answer("هنا سوف يكون مشروع التقارير الطبية")
    await callback.answer()  # لتأكيد الضغط

# تشغيل البوت
async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
