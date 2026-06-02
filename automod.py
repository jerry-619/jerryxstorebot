import os
import json
from telegram import Update, ChatPermissions
from telegram.ext import ContextTypes
from telegram.error import BadRequest
from admin_commands import is_admin

DATA_FILE = "filters.json"

# Default structure
data = {
    "banned_words": [],
    "filter_links": False,
    "user_strikes": {}  # user_id: strike_count
}

def load_data():
    global data
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r") as f:
                loaded = json.load(f)
                data["banned_words"] = loaded.get("banned_words", [])
                data["filter_links"] = loaded.get("filter_links", False)
                data["user_strikes"] = loaded.get("user_strikes", {})
        except Exception:
            pass

def save_data():
    with open(DATA_FILE, "w") as f:
        json.dump(data, f)

# Load immediately on import
load_data()

async def addfilter_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context, True): return
    if not context.args:
        await update.message.reply_text("Usage: /addfilter <word>")
        return
        
    word = " ".join(context.args).lower()
    if word in data["banned_words"]:
        await update.message.reply_text(f"'{word}' is already filtered.")
    else:
        data["banned_words"].append(word)
        save_data()
        await update.message.reply_text(f"✅ Added '{word}' to the filter list.")

async def rmfilter_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context, True): return
    if not context.args:
        await update.message.reply_text("Usage: /rmfilter <word>")
        return
        
    word = " ".join(context.args).lower()
    if word in data["banned_words"]:
        data["banned_words"].remove(word)
        save_data()
        await update.message.reply_text(f"✅ Removed '{word}' from the filter list.")
    else:
        await update.message.reply_text(f"'{word}' is not in the filter list.")

async def filters_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context, True): return
    
    words = data["banned_words"]
    if not words:
        await update.message.reply_text("No words are currently filtered.")
        return
        
    text = "🛑 <b>Filtered Words:</b>\n" + "\n".join([f"- {w}" for w in words])
    await update.message.reply_text(text, parse_mode='HTML')

async def filterlinks_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context, True): return
    if not context.args:
        state = "ON" if data["filter_links"] else "OFF"
        await update.message.reply_text(f"Link filtering is currently {state}.\nUsage: /filterlinks on OR /filterlinks off")
        return
        
    arg = context.args[0].lower()
    if arg == "on":
        data["filter_links"] = True
        save_data()
        await update.message.reply_text("✅ Link filtering turned ON.")
    elif arg == "off":
        data["filter_links"] = False
        save_data()
        await update.message.reply_text("✅ Link filtering turned OFF.")
    else:
        await update.message.reply_text("Invalid option. Use 'on' or 'off'.")

async def rmwarn_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context, True): return
    if not update.message.reply_to_message:
        await update.message.reply_text("Reply to a user's message to clear their warnings.")
        return
        
    user_id = str(update.message.reply_to_message.from_user.id)
    user_name = update.message.reply_to_message.from_user.first_name
    
    if user_id in data["user_strikes"] and data["user_strikes"][user_id] > 0:
        data["user_strikes"][user_id] = 0
        save_data()
        await update.message.reply_text(f"✅ Cleared all warnings for <b>{user_name}</b>.", parse_mode='HTML')
    else:
        await update.message.reply_text(f"<b>{user_name}</b> currently has 0 warnings.", parse_mode='HTML')

# --- GLOBAL AUTOMOD HANDLER ---

async def automod_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Only process text messages in groups
    if not update.message or not update.message.text:
        return
    if update.effective_chat.type not in ['group', 'supergroup']:
        return
        
    # Check if target chat matches
    target_chat_id = os.getenv("TARGET_CHAT_ID")
    if target_chat_id and str(update.effective_chat.id) != target_chat_id:
        return
        
    # Ignore admins
    if await is_admin(update, context):
        return

    text = update.message.text.lower()
    violation = False
    reason = ""

    # Check for links
    if data["filter_links"]:
        entities = update.message.parse_entities(["url", "text_link"])
        if entities:
            violation = True
            reason = "posting a link"

    # Check for banned words
    if not violation:
        for word in data["banned_words"]:
            if word in text:
                violation = True
                reason = "using a filtered word"
                break

    if violation:
        user_id = str(update.effective_user.id)
        user_name = update.effective_user.first_name
        
        # Delete the message
        try:
            await update.message.delete()
        except BadRequest:
            pass
            
        # Manage strikes
        strikes = data["user_strikes"].get(user_id, 0) + 1
        data["user_strikes"][user_id] = strikes
        save_data()
        
        if strikes >= 10:
            # Mute the user
            permissions = ChatPermissions(can_send_messages=False)
            try:
                await context.bot.restrict_chat_member(update.effective_chat.id, update.effective_user.id, permissions)
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text=f"🛑 <b>{user_name}</b> has been muted for reaching 10 warnings (Reason: {reason}).",
                    parse_mode='HTML',
                    message_thread_id=update.message.message_thread_id
                )
                # Reset strikes
                data["user_strikes"][user_id] = 0
                save_data()
            except BadRequest:
                pass
        else:
            # Warn the user
            msg = await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=f"⚠️ <b>{user_name}</b>, your message was deleted for {reason}. Warning {strikes}/10.",
                parse_mode='HTML',
                message_thread_id=update.message.message_thread_id
            )
            # Delete warning after 5 seconds to keep chat clean
            import asyncio
            context.application.create_task(delete_later(msg, 5))

async def delete_later(message, delay):
    import asyncio
    await asyncio.sleep(delay)
    try:
        await message.delete()
    except BadRequest:
        pass
