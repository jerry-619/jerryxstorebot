import os
import asyncio
import time
import random
from datetime import timedelta
from telegram import Update, ChatPermissions, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from telegram.error import BadRequest

# In-memory storage for active giveaways
active_giveaways = {}

async def is_admin(update: Update, context: ContextTypes.DEFAULT_TYPE, send_warning: bool = False) -> bool:
    """Checks if the user sending the command is an admin or creator."""
    chat = update.effective_chat
    user = update.effective_user
    
    # Check if target chat matches
    target_chat_id = os.getenv("TARGET_CHAT_ID")
    if target_chat_id and str(chat.id) != target_chat_id:
        return False

    member = await chat.get_member(user.id)
    is_adm = member.status in ['administrator', 'creator']
    
    if not is_adm and send_warning:
        msg = await update.message.reply_text("<tg-emoji emoji-id='6267000941547885720'>⛔</tg-emoji> This command is only for Admins.")
        context.application.create_task(delete_later(msg, 3))
        
    return is_adm

async def ban_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context, True): return
    if not update.message.reply_to_message:
        await update.message.reply_text("Reply to a user's message to ban them.")
        return
        
    user_to_ban = update.message.reply_to_message.from_user
    try:
        await context.bot.ban_chat_member(update.effective_chat.id, user_to_ban.id)
        await update.message.reply_text(f"🔨 {user_to_ban.first_name} has been banned.")
    except BadRequest as e:
        await update.message.reply_text(f"Error banning user: {e}")

async def unban_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context, True): return
    if not context.args:
        await update.message.reply_text("Please provide a user ID to unban.")
        return
        
    try:
        user_id = int(context.args[0])
        await context.bot.unban_chat_member(update.effective_chat.id, user_id, only_if_banned=True)
        await update.message.reply_text(f"<tg-emoji emoji-id='5364035134725043602'>✅</tg-emoji> User ID {user_id} has been unbanned.")
    except (ValueError, BadRequest) as e:
        await update.message.reply_text(f"Error unbanning user: {e}")

async def kick_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context, True): return
    if not update.message.reply_to_message:
        await update.message.reply_text("Reply to a user's message to kick them.")
        return
        
    user_to_kick = update.message.reply_to_message.from_user
    try:
        await context.bot.ban_chat_member(update.effective_chat.id, user_to_kick.id)
        await context.bot.unban_chat_member(update.effective_chat.id, user_to_kick.id)
        await update.message.reply_text(f"👢 {user_to_kick.first_name} has been kicked.")
    except BadRequest as e:
        await update.message.reply_text(f"Error kicking user: {e}")

async def mute_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context, True): return
    if not update.message.reply_to_message:
        await update.message.reply_text("Reply to a user's message to mute them.")
        return
        
    user_to_mute = update.message.reply_to_message.from_user
    permissions = ChatPermissions(can_send_messages=False)
    try:
        await context.bot.restrict_chat_member(update.effective_chat.id, user_to_mute.id, permissions)
        await update.message.reply_text(f"🔇 {user_to_mute.first_name} has been muted.")
    except BadRequest as e:
        await update.message.reply_text(f"Error muting user: {e}")

async def unmute_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context, True): return
    if not update.message.reply_to_message:
        await update.message.reply_text("Reply to a user's message to unmute them.")
        return
        
    user_to_unmute = update.message.reply_to_message.from_user
    permissions = ChatPermissions(
        can_send_messages=True,
        can_send_audios=True,
        can_send_documents=True,
        can_send_photos=True,
        can_send_videos=True,
        can_send_video_notes=True,
        can_send_voice_notes=True,
        can_send_polls=True,
        can_send_other_messages=True,
        can_add_web_page_previews=True
    )
    try:
        await context.bot.restrict_chat_member(update.effective_chat.id, user_to_unmute.id, permissions)
        await update.message.reply_text(f"🔊 {user_to_unmute.first_name} has been unmuted.")
    except BadRequest as e:
        await update.message.reply_text(f"Error unmuting user: {e}")

async def delete_later(message, delay):
    import asyncio
    await asyncio.sleep(delay)
    try:
        await message.delete()
    except BadRequest:
        pass

async def del_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context, True): return
    
    # If an amount is specified (e.g., /del 10)
    if context.args:
        try:
            amt = int(context.args[0])
            if amt <= 0 or amt > 100:
                await update.message.reply_text("Please provide a number between 1 and 100.")
                return
                
            current_id = update.message.message_id
            
            # Delete the command message itself
            try:
                await update.message.delete()
            except BadRequest:
                pass
                
            # Loop backwards and delete
            deleted_count = 0
            for i in range(1, amt + 1):
                try:
                    await context.bot.delete_message(chat_id=update.effective_chat.id, message_id=current_id - i)
                    deleted_count += 1
                except BadRequest:
                    # Message might not exist or we don't have permission for that specific message
                    pass
            
            confirm_msg = await context.bot.send_message(
                chat_id=update.effective_chat.id, 
                text=f"🗑️ Purged {deleted_count} messages.",
                message_thread_id=update.message.message_thread_id
            )
            # Delete confirmation after 3 seconds
            context.application.create_task(delete_later(confirm_msg, 3))
            return
            
        except ValueError:
            await update.message.reply_text("Please provide a valid number. Example: /del 10")
            return

    # Fallback to single message reply deletion
    if not update.message.reply_to_message:
        await update.message.reply_text("Reply to a message to delete it, or provide an amount (e.g., /del 10).")
        return
        
    try:
        await update.message.reply_to_message.delete()
        await update.message.delete()
    except BadRequest:
        pass

async def announce_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context, True): return
    if not context.args:
        await update.message.reply_text("Usage: /announce <your message>")
        return
        
    # Extract the raw text after the command to preserve line breaks and HTML tags
    command_text = update.message.text.split()[0]
    announcement = update.message.text[len(command_text):].strip()
    
    text = f"<tg-emoji emoji-id='5215668805199473901'>📢</tg-emoji> <b>ANNOUNCEMENT</b>\n\n{announcement}"
    
    msg = await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=text,
        parse_mode='HTML',
        message_thread_id=update.message.message_thread_id
    )
    try:
        await msg.pin()
    except BadRequest:
        pass

async def pin_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context, True): return
    if not update.message.reply_to_message:
        await update.message.reply_text("Reply to a message to pin it.")
        return
    try:
        await update.message.reply_to_message.pin()
    except BadRequest as e:
        await update.message.reply_text(f"Error pinning: {e}")

async def unpin_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context, True): return
    if not update.message.reply_to_message:
        await update.message.reply_text("Reply to a message to unpin it.")
        return
    try:
        await update.message.reply_to_message.unpin()
    except BadRequest as e:
        await update.message.reply_text(f"Error unpinning: {e}")

# --- GIVEAWAY LOGIC ---

async def gw_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context, True): return
    if len(context.args) < 2:
        await update.message.reply_text("Usage: /gw <seconds> <prize>\nExample: /gw 60 Spotify Premium")
        return
        
    try:
        duration_secs = int(context.args[0])
    except ValueError:
        await update.message.reply_text("Duration must be an integer (in seconds).")
        return
        
    prize = " ".join(context.args[1:])
    
    keyboard = [[InlineKeyboardButton("🎉 Join Giveaway", callback_data="join_gw")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    msg_text = (
        f"<tg-emoji emoji-id='6276134137963222688'>🎁</tg-emoji> <b>GIVEAWAY STARTED!</b> <tg-emoji emoji-id='6276134137963222688'>🎁</tg-emoji>\n\n"
        f"<b>Prize:</b> {prize}\n"
        f"<b>Time:</b> {duration_secs} seconds\n\n"
        f"Click the button below to enter!"
    )
    
    gw_msg = await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=msg_text,
        reply_markup=reply_markup,
        parse_mode='HTML',
        message_thread_id=update.message.message_thread_id
    )
    
    # Store giveaway state
    active_giveaways[gw_msg.message_id] = {
        'participants': set(),
        'prize': prize
    }
    
    # Schedule the end of the giveaway
    context.application.create_task(
        end_giveaway(context, update.effective_chat.id, gw_msg.message_id, update.message.message_thread_id, duration_secs)
    )

async def join_gw_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    msg_id = query.message.message_id
    user = query.from_user
    
    if msg_id in active_giveaways:
        if user.id in active_giveaways[msg_id]['participants']:
            await query.answer("You have already joined this giveaway!", show_alert=True)
        else:
            active_giveaways[msg_id]['participants'].add(user.id)
            count = len(active_giveaways[msg_id]['participants'])
            await query.answer(f"Successfully joined! Total participants: {count}")
    else:
        await query.answer("This giveaway has ended or is invalid.", show_alert=True)

async def end_giveaway(context: ContextTypes.DEFAULT_TYPE, chat_id: int, message_id: int, thread_id: int, delay: int):
    await asyncio.sleep(delay)
    
    if message_id not in active_giveaways:
        return
        
    gw_data = active_giveaways.pop(message_id)
    participants = list(gw_data['participants'])
    prize = gw_data['prize']
    
    # Remove the join button
    try:
        await context.bot.edit_message_reply_markup(
            chat_id=chat_id,
            message_id=message_id,
            reply_markup=None
        )
    except Exception:
        pass
        
    if not participants:
        await context.bot.send_message(
            chat_id=chat_id,
            text=f"<tg-emoji emoji-id='6276134137963222688'>🎁</tg-emoji> The giveaway for <b>{prize}</b> has ended.\n\nSadly, no one joined!",
            parse_mode='HTML',
            message_thread_id=thread_id
        )
        return
        
    winner_id = random.choice(participants)
    
    # Try to get winner info
    try:
        winner = await context.bot.get_chat(winner_id)
        winner_name = winner.first_name
        winner_mention = f"<a href='tg://user?id={winner_id}'>{winner_name}</a>"
    except Exception:
        winner_mention = f"<a href='tg://user?id={winner_id}'>User {winner_id}</a>"
        
    await context.bot.send_message(
        chat_id=chat_id,
        text=f"<tg-emoji emoji-id='5238078046174456159'>🎉</tg-emoji> <b>GIVEAWAY ENDED!</b> <tg-emoji emoji-id='5238078046174456159'>🎉</tg-emoji>\n\nPrize: <b>{prize}</b>\nWinner: {winner_mention}\n\nCongratulations! Please contact an admin to claim your prize.",
        parse_mode='HTML',
        message_thread_id=thread_id
    )

async def cid_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context, True): return
    
    chat_id = update.effective_chat.id
    topic_id = update.message.message_thread_id
    user_id = update.effective_user.id
    
    msg = (
        f"<tg-emoji emoji-id='5231200819986047254'>📊</tg-emoji> <b>ID Information</b>\n\n"
        f"<b>Chat ID:</b> <code>{chat_id}</code>\n"
        f"<b>Topic ID:</b> <code>{topic_id if topic_id else 'None'}</code>\n"
        f"<b>Your User ID:</b> <code>{user_id}</code>"
    )
    await update.message.reply_text(msg, parse_mode='HTML')

async def ping_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context, True): return
    
    start_time = time.time()
    msg = await update.message.reply_text("<tg-emoji emoji-id='5386367538735104399'>🏓</tg-emoji> <i>Pinging...</i>", parse_mode='HTML')
    end_time = time.time()
    
    ping_ms = round((end_time - start_time) * 1000)
    
    await msg.edit_text(f"<tg-emoji emoji-id='5386367538735104399'>🏓</tg-emoji> <b>Pong!</b>\nLatency: <code>{ping_ms}ms</code>", parse_mode='HTML')
