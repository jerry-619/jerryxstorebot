import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

# Aesthetic welcome text and keyboard
def get_main_menu(user_name):
    welcome_text = (
        f"❖ <b>JERRY X STORE</b> ❖\n\n"
        f"Welcome to the central hub, <b>{user_name}</b>.\n"
        f"Select an option below to navigate the realm. ⚡\n\n"
        f"<i>— Stay sharp, stay elite.</i>"
    )
    
    owner_id = os.getenv("OWNER_ID", "1420742289")
    
    # Note: Telegram does not support colored 'style' parameters for Inline Buttons.
    keyboard = [
        [
            InlineKeyboardButton("🛒 Shop", callback_data="cmd_shop" , style='primary'),
            InlineKeyboardButton("⚙️ Commands", callback_data="cmd_commands", style='danger'),
        ],
        [
           
            InlineKeyboardButton("👑 Owner", url=f"tg://user?id={owner_id}", style='success'),
        ]
    ]
    return welcome_text, InlineKeyboardMarkup(keyboard)

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles the /start command and displays a modern inline menu."""
    user_name = update.effective_user.first_name
    welcome_text, reply_markup = get_main_menu(user_name)

    await update.message.reply_text(
        text=welcome_text,
        reply_markup=reply_markup,
        parse_mode='HTML'
    )

async def commands_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles the 'Commands' button click."""
    query = update.callback_query
    await query.answer()
    
    commands_text = (
        f"<b><i><tg-emoji emoji-id='5224607267797606837'>⚡</tg-emoji>JERRY X STORE COMMANDS</i></b>\n\n"
        f"<b><tg-emoji emoji-id='5215392879320505675'>🔨</tg-emoji> Moderation:</b>\n"
        f"<tg-emoji emoji-id='5215392879320505675'>🔨</tg-emoji> /ban - Ban a user\n"
        f"<tg-emoji emoji-id='5364035134725043602'>✅</tg-emoji> /unban &lt;id&gt; - Unban a user\n"
        f"<tg-emoji emoji-id='5390851106634997669'>👢</tg-emoji> /kick - Kick a user\n"
        f"<tg-emoji emoji-id='5462990730253319917'>🔇</tg-emoji> /mute - Mute a user\n"
        f"<tg-emoji emoji-id='5253997827788385948'>🔊</tg-emoji> /unmute - Unmute a user\n"
        f"<tg-emoji emoji-id='5372825386591732174'>🗑️</tg-emoji> /del [amt] - Delete msg(s)\n"
        f"<tg-emoji emoji-id='5397782960512444700'>📌</tg-emoji> /pin - Pin a message\n"
        f"<tg-emoji emoji-id='5330088116944380969'>📍</tg-emoji> /unpin - Unpin a message\n"
        f"<tg-emoji emoji-id='5298609030321691620'>📢</tg-emoji> /announce &lt;msg&gt; - Announcement\n"
        f"<tg-emoji emoji-id='5235695112419303615'>🎁</tg-emoji> /gw &lt;secs&gt; &lt;prize&gt; - Giveaway\n"
        f"<tg-emoji emoji-id='5231200819986047254'>📊</tg-emoji> /cid - Get IDs\n"
        f"<tg-emoji emoji-id='5386367538735104399'>🏓</tg-emoji> /ping - Check Bot Status\n\n"
        f"<tg-emoji emoji-id='5251203410396458957'>🛡️</tg-emoji> <b>Automod Filters:</b>\n"
        f"<tg-emoji emoji-id='5393194986252542669'>➕</tg-emoji> /addfilter &lt;word&gt; - Block a word\n"
        f"<tg-emoji emoji-id='5382261056078881010'>➖</tg-emoji> /rmfilter &lt;word&gt; - Unblock a word\n"
        f"<tg-emoji emoji-id='5226512880362332956'>📋</tg-emoji> /filters - List blocked words\n"
        f"<tg-emoji emoji-id='5375129357373165375'>🔗</tg-emoji> /filterlinks on/off - Block URLs\n"
        f"<tg-emoji emoji-id='5382261056078881010'>➖</tg-emoji> /rmwarn - Clear user warnings\n\n"
    )
    
    keyboard = [[InlineKeyboardButton("🔙 Back to Main Menu", callback_data="cmd_back", style='danger')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        text=commands_text,
        reply_markup=reply_markup,
        parse_mode='HTML'
    )

async def back_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles the 'Back' button click to return to the main menu."""
    query = update.callback_query
    await query.answer()
    
    user_name = query.from_user.first_name
    welcome_text, reply_markup = get_main_menu(user_name)
    
    await query.edit_message_text(
        text=welcome_text,
        reply_markup=reply_markup,
        parse_mode='HTML'
    )
