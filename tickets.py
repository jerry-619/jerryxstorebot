import os
import json
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from telegram.error import BadRequest
from admin_commands import is_admin

STATE_FILE = "ticket_state.json"
state = {
    "active_users": [],
    "msg_map": {}
}

def load_state():
    global state
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, "r") as f:
                loaded = json.load(f)
                if "active_users" in loaded and "msg_map" in loaded:
                    state = loaded
        except Exception:
            pass

def save_state():
    with open(STATE_FILE, "w") as f:
        json.dump(state, f)

load_state()

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
    user_id_str = str(user.id)
    
    # If this is a new ticket conversation, send the Info Panel to the owner
    if user_id_str not in state["active_users"]:
        state["active_users"].append(user_id_str)
        
        keyboard = [[InlineKeyboardButton("<tg-emoji emoji-id='5429405838345265327'>🔒</tg-emoji> Close Ticket", callback_data=f"close_ticket_{user.id}")]]
        info_text = (
            f"<tg-emoji emoji-id='5377599075237502153'>🎫</tg-emoji> <b>NEW TICKET OPENED</b>\n"
            f"───────────────────\n"
            f"<tg-emoji emoji-id='5373012449597335010'>👤</tg-emoji> <b>User:</b> <a href='tg://user?id={user.id}'>{user.first_name}</a>\n"
            f"<tg-emoji emoji-id='5909054643362598630'>🆔</tg-emoji> <b>ID:</b> <code>{user.id}</code>\n"
            f"───────────────────\n"
            f"<i>Reply to any of their messages below to respond.</i>"
        )
        try:
            await context.bot.send_message(
                chat_id=int(owner_id),
                text=info_text,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode='HTML'
            )
        except Exception:
            pass

    # Copy the actual message to the owner
    try:
        copied_msg = await context.bot.copy_message(
            chat_id=int(owner_id),
            from_chat_id=update.effective_chat.id,
            message_id=update.message.message_id
        )
        
        # Save mapping so owner can reply to THIS exact copied message
        state["msg_map"][str(copied_msg.message_id)] = user.id
        save_state()
        
    except Exception as e:
        await update.message.reply_text(f"Failed to send message to support: {e}")

async def process_owner_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Called from handlers.py when the Owner replies to a ticket in their DM."""
    reply_to_id = str(update.message.reply_to_message.message_id)
    
    if reply_to_id in state["msg_map"]:
        target_user_id = state["msg_map"][reply_to_id]
        try:
            await context.bot.copy_message(
                chat_id=target_user_id,
                from_chat_id=update.effective_chat.id,
                message_id=update.message.message_id
            )
            await update.message.reply_text("<tg-emoji emoji-id='5364035134725043602'>✅</tg-emoji> <i>Sent to user.</i>", parse_mode='HTML')
        except BadRequest as e:
            await update.message.reply_text(f"Failed to send: {e}")
    else:
        await update.message.reply_text("⚠️ Could not find the user for this ticket. (The mapping might be lost or this is not a ticket message).")

async def close_ticket_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles the 'Close Ticket' button click by the owner."""
    query = update.callback_query
    owner_id = os.getenv("OWNER_ID")
    
    # Security check: only owner can close it
    if str(query.from_user.id) != str(owner_id):
        await query.answer("You are not authorized to close tickets.", show_alert=True)
        return
        
    # Extract target user_id from callback_data (format: close_ticket_{user_id})
    data_parts = query.data.split('_')
    if len(data_parts) != 3:
        await query.answer("Invalid data.")
        return
        
    target_user_id = data_parts[2]
    
    # Remove from active users
    if target_user_id in state["active_users"]:
        state["active_users"].remove(target_user_id)
        save_state()
        
        # Notify the user that their ticket was closed
        try:
            await context.bot.send_message(
                chat_id=int(target_user_id),
                text="<tg-emoji emoji-id='5429405838345265327'>🔒</tg-emoji> <b>Your support ticket has been closed by the staff.</b>\n\nIf you need further assistance, simply send another message to open a new ticket.",
                parse_mode='HTML'
            )
        except BadRequest:
            pass # User might have blocked the bot
            
        # Edit the owner's info panel to show it's closed
        await query.edit_message_text(
            text=query.message.text.replace("NEW TICKET OPENED", "TICKET CLOSED") + "\n\n<tg-emoji emoji-id='5429405838345265327'>🔒</tg-emoji> <i>Ticket has been closed.</i>",
            parse_mode='HTML',
            reply_markup=None # Removes the button
        )
        await query.answer("Ticket closed successfully!")
    else:
        # Already closed or not found
        await query.edit_message_reply_markup(reply_markup=None)
        await query.answer("This ticket is already closed.", show_alert=True)
