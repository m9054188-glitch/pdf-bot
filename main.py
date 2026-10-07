import os
import fitz  # PyMuPDF
import arabic_reshaper
from bidi.algorithm import get_display
from deep_translator import GoogleTranslator
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, FSInputFile
from aiogram.fsm.storage.memory import MemoryStorage
import asyncio

BOT_TOKEN = os.getenv("BOT_TOKEN")
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

user_settings = {}

def get_user_config(user_id):
    if user_id not in user_settings:
        user_settings[user_id] = {
            "color": (0.8, 0, 0),       # أحمر
            "font_size": 6.5,
            "y_offset": 2.5,
            "highlight_color": None
        }
    return user_settings[user_id]

def main_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="لون الخط 🎨", callback_data="menu_color"),
         InlineKeyboardButton(text="حجم الخط 📏", callback_data="menu_size")],
        [InlineKeyboardButton(text="موضع النص (رفع/خفض) ↕️", callback_data="menu_pos"),
         InlineKeyboardButton(text="تظليل النصوص (هايلايت) 🖍️", callback_data="menu_hl")]
    ])

@dp.message(Command("start"))
async def start_handler(message: types.Message):
    await message.answer("أهلاً بك! دزلي ملف PDF حتى اترجمه فوك السطر الأصلي، أو اضبط إعداداتك من جوة:", reply_markup=main_keyboard())

@dp.callback_query(F.data == "menu_color")
async def color_menu(call: types.CallbackQuery):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="أحمر 🔴", callback_data="c_red"), InlineKeyboardButton(text="أزرق 🔵", callback_data="c_blue")],
        [InlineKeyboardButton(text="أسود ⚫", callback_data="c_black"), InlineKeyboardButton(text="أخضر 🟢", callback_data="c_green")],
        [InlineKeyboardButton(text="رجوع 🔙", callback_data="menu_back")]
    ])
    await call.message.edit_text("اختر لون خط الترجمة:", reply_markup=kb)

@dp.callback_query(F.data.startswith("c_"))
async def set_color(call: types.CallbackQuery):
    cfg = get_user_config(call.from_user.id)
    colors = {
        "c_red": (0.8, 0, 0),
        "c_blue": (0, 0.2, 0.8),
        "c_black": (0, 0, 0),
        "c_green": (0, 0.6, 0)
    }
    cfg["color"] = colors.get(call.data, (0.8, 0, 0))
    await call.message.edit_text("تم حفظ اللون!", reply_markup=main_keyboard())

@dp.callback_query(F.data == "menu_size")
async def size_menu(call: types.CallbackQuery):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="تكبير ➕", callback_data="sz_up"), InlineKeyboardButton(text="تصغير ➖", callback_data="sz_down")],
        [InlineKeyboardButton(text="رجوع 🔙", callback_data="menu_back")]
    ])
    await call.message.edit_text("تحكم بحجم الخط:", reply_markup=kb)

@dp.callback_query(F.data.startswith("sz_"))
async def adjust_size(call: types.CallbackQuery):
    cfg = get_user_config(call.from_user.id)
    if call.data == "sz_up":
        cfg["font_size"] = min(cfg["font_size"] + 0.5, 12.0)
    else:
        cfg["font_size"] = max(cfg["font_size"] - 0.5, 4.0)
    await call.answer(f"الحجم الحالي: {cfg['font_size']} pt")

@dp.callback_query(F.data == "menu_pos")
async def pos_menu(call: types.CallbackQuery):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="رفع للأعلى 🔺", callback_data="pos_up"), InlineKeyboardButton(text="خفض للأسفل 🔻", callback_data="pos_down")],
        [InlineKeyboardButton(text="رجوع 🔙", callback_data="menu_back")]
    ])
    await call.message.edit_text("تحكم بموضع النص فوق السطر:", reply_markup=kb)

@dp.callback_query(F.data.startswith("pos_"))
async def adjust_pos(call: types.CallbackQuery):
    cfg = get_user_config(call.from_user.id)
    if call.data == "pos_up":
        cfg["y_offset"] += 0.5
    else:
        cfg["y_offset"] = max(cfg["y_offset"] - 0.5, 0.0)
    await call.answer(f"الإزاحة الحالية: {cfg['y_offset']} pt")

@dp.callback_query(F.data == "menu_hl")
async def hl_menu(call: types.CallbackQuery):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="أصفر 🟡", callback_data="hl_yellow"), InlineKeyboardButton(text="أخضر 🟢", callback_data="hl_green")],
        [InlineKeyboardButton(text="وردي 🌸", callback_data="hl_pink"), InlineKeyboardButton(text="أزرق 🔵", callback_data="hl_blue")],
        [InlineKeyboardButton(text="إلغاء التظليل ❌", callback_data="hl_none")],
        [InlineKeyboardButton(text="رجوع 🔙", callback_data="menu_back")]
    ])
    await call.message.edit_text("اختر لون الهايلايت:", reply_markup=kb)

@dp.callback_query(F.data.startswith("hl_"))
async def set_highlight(call: types.CallbackQuery):
    cfg = get_user_config(call.from_user.id)
    hl_colors = {
        "hl_yellow": (1, 1, 0),
        "hl_green": (0.6, 1, 0.6),
        "hl_pink": (1, 0.7, 0.8),
        "hl_blue": (0.7, 0.9, 1),
        "hl_none": None
    }
    cfg["highlight_color"] = hl_colors.get(call.data)
    await call.message.edit_text("تم ضبط التظليل!", reply_markup=main_keyboard())

@dp.callback_query(F.data == "menu_back")
async def back_to_main(call: types.CallbackQuery):
    await call.message.edit_text("القائمة الرئيسية - اضبط إعداداتك:", reply_markup=main_keyboard())

def reshape_arabic(text: str) -> str:
    reshaped = arabic_reshaper.reshape(text)
    return get_display(reshaped)

def process_pdf(input_path: str, output_path: str, cfg: dict):
    doc = fitz.open(input_path)
    translator = GoogleTranslator(source="en", target="ar")

    for page in doc:
        blocks = page.get_text("blocks")
        for b in blocks:
            text = b[4].strip()
            if not text or len(text) < 2:
                continue

            if cfg["highlight_color"] and (len(text.split()) < 5 or text.isupper()):
                rect = fitz.Rect(b[0], b[1], b[2], b[3])
                annot = page.add_highlight_annot(rect)
                annot.set_colors(stroke=cfg["highlight_color"])
                annot.update()

            try:
                translated = translator.translate(text[:400])
                if not translated:
                    continue

                arabic_text = reshape_arabic(translated)
                x = b[0]
                y = max(b[1] - cfg["y_offset"], 10)

                page.insert_text(
                    fitz.Point(x, y),
                    arabic_text,
                    fontsize=cfg["font_size"],
                    color=cfg["color"]
                )
            except Exception:
                continue

    doc.save(output_path)
    doc.close()

@dp.message(F.document)
async def handle_document(message: types.Message):
    doc = message.document
    if not doc.file_name.lower().endswith(".pdf"):
        await message.reply("يرجى إرسال ملف بصيغة PDF فقط.")
        return

    status_msg = await message.reply("جاري تنزيل الملف وترجمته... انتظر ثواني ⏳")
    file_id = doc.file_id
    file = await bot.get_file(file_id)

    input_file = f"in_{doc.file_name}"
    output_file = f"translated_{doc.file_name}"

    await bot.download_file(file.file_path, input_file)

    cfg = get_user_config(message.from_user.id)
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, process_pdf, input_file, output_file, cfg)

    await message.reply_document(
        FSInputFile(output_file),
        caption="تمت الترجمة فوق السطر بنجاح! ✅"
    )

    await status_msg.delete()
    if os.path.exists(input_file):
        os.remove(input_file)
    if os.path.exists(output_file):
        os.remove(output_file)

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
