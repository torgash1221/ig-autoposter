# handlers/keyboards.py
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def gallery_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🦪 УстриЦО",
                    callback_data="gallery:ustritso"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🍣 My Thai",
                    callback_data="gallery:mythai"
                )
            ]
        ]
    )


def publish_keyboard(business: str, content_id: int):
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="📲 Опубликовать",
                callback_data=f"published:{business}"
            ),
            InlineKeyboardButton(
                text="🔁 Заменить",
                callback_data=f"replace:{business}"
            )
        ],
        [
            InlineKeyboardButton(
                text="🗑 Удалить",
                callback_data=f"delete:{content_id}"
            )
        ]
    ])
