import os
import json
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from telegram.error import BadRequest
from admin_commands import is_admin

MAPPINGS_FILE = "ticket_mappings.json"
mappings = {}

def load_mappings():
    global mappings
    if os.path.exists(MAPPINGS_FILE):
        try:
            with open(MAPPINGS_FILE, "r") as f:
                mappings = json.load(f)
        except Exception:
            pass

def save_mappings():
    with open(MAPPINGS_FILE, "w") as f:
        json.dump(mappings, f)

load_mappings()

async def ticketpanel_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Sends the static ticket creation panel to the current chat/topic."""
    if not await is_admin(update, context, True): return
    
    bot_username = context.bot.username
    url = f"https://t.me/{bot_username}?start=ticket"
    
    keyboard = [[InlineKeyboardButton("📩 Create Ticket", url=url, style='success')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    text = (
        f"<tg-emoji emoji-id='5224607267797606837'>⚡</tg-emoji> <b>𝙉𝙀𝙀𝘿 𝘼𝙎𝙎𝙄𝙎𝙏𝘼𝙉𝘾𝙀?</b> <tg-emoji emoji-id='5224607267797606837'>⚡</tg-emoji>\n"
        f"────────────────────\n\n"
        f"<tg-emoji emoji-id='5395804191769763641'>🛰️</tg-emoji> <b>𝗦𝗨𝗣𝗣𝗢𝗥𝗧</b> ➛ Private Ticket System\n\n"
        f"<tg-emoji emoji-id='5123270130083563228'>💬</tg-emoji> <b>𝗦𝗧𝗔𝗙𝗙</b> ➛ Active & Ready\n\n"
        f"────────────────────\n"
        f"<tg-emoji emoji-id='5377599075237502153'>🎫</tg-emoji> <i>Click the button below to open a private ticket with our staff team.</i>\n"
        f"<tg-emoji emoji-id='5096218811145651199'>💀</tg-emoji> <b><i>— Stay sharp.</i></b>"
    )
    
    await update.message.reply_text(
        text,
        reply_markup=reply_markup,
        parse_mode='HTML'
    )
    
    # Delete the admin's command message to keep it clean
    try:
        await update.message.delete()
    except BadRequest:
        pass

async def process_user_ticket_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Called from handlers.py when a normal user sends a message in DM."""
    owner_id = os.getenv("OWNER_ID")
    if not owner_id:
        await update.message.reply_text("The ticket system is currently unavailable (Owner ID not set).")
        return
        
    user = update.effective_user
    
    # Notify owner who it's from before copying the message (if it's the start of a convo)
    # We'll just copy the message directly and map it.
    try:
        copied_msg = await context.bot.copy_message(
            chat_id=int(owner_id),
            from_chat_id=update.effective_chat.id,
            message_id=update.message.message_id
        )
        
        # Save mapping so owner can reply to THIS exact copied message
        mappings[str(copied_msg.message_id)] = user.id
        save_mappings()
        
    except Exception as e:
        await update.message.reply_text(f"Failed to send message to support: {e}")

async def process_owner_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Called from handlers.py when the Owner replies to a ticket in their DM."""
    reply_to_id = str(update.message.reply_to_message.message_id)
    
    if reply_to_id in mappings:
        target_user_id = mappings[reply_to_id]
        try:
            await context.bot.copy_message(
                chat_id=target_user_id,
                from_chat_id=update.effective_chat.id,
                message_id=update.message.message_id
            )
            # Add a small reaction or confirmation to owner
            await update.message.reply_text("<tg-emoji emoji-id='5364035134725043602'>✅</tg-emoji> <i>Sent to user.</i>", parse_mode='HTML')
        except BadRequest as e:
            await update.message.reply_text(f"Failed to send: {e}")
    else:
        await update.message.reply_text("<tg-emoji emoji-id='6089079808187174973'>✅</tg-emoji> Could not find the user for this ticket. (The mapping might be lost or this is not a ticket message).")
