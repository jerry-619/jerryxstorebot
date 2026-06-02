import os
from telegram import Update
from telegram.ext import ContextTypes, ApplicationHandlerStop

async def private_chat_interceptor(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Intercepts all private messages and stops further processing."""
    if update.effective_chat.type == 'private':
        await update.message.reply_text("⛔ This bot is exclusively for private use in @jerryxxstore. It cannot be used here.")
        raise ApplicationHandlerStop

async def greet_new_members(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Greets new members if they join the specific topic."""
    message = update.message
    
    # Check if this is a group/supergroup and there are new members
    if message and message.new_chat_members:
        # Get the target topic ID and chat ID from environment variables
        target_topic_id = os.getenv("GREETING_TOPIC_ID")
        target_chat_id = os.getenv("TARGET_CHAT_ID")
        
        # Verify chat ID if it's set
        if target_chat_id:
            try:
                target_chat_id = int(target_chat_id)
                if message.chat_id != target_chat_id:
                    return
            except ValueError:
                print("Error: TARGET_CHAT_ID must be an integer.")
                
        # Check if a target topic ID is configured
        if target_topic_id:
            try:
                target_topic_id = int(target_topic_id)
            except ValueError:
                print("Error: GREETING_TOPIC_ID must be an integer.")
                return

            for new_member in message.new_chat_members:
                # Ignore the bot itself joining
                if new_member.id != context.bot.id:
                    user_name = new_member.first_name
                    # Check if premium emojis are enabled
                    use_premium = os.getenv("USE_PREMIUM_EMOJIS", "False").lower() == "true"
                    
                    if use_premium:
                        # Replace the emoji IDs below with your actual premium emoji IDs
                        greeting = (
                            f"<tg-emoji emoji-id='5224607267797606837'>⚡</tg-emoji> <b>𝙅𝙀𝙍𝙍𝙔 𝙓 𝙎𝙏𝙊𝙍𝙀</b> <tg-emoji emoji-id='5224607267797606837'>⚡</tg-emoji>\n"
                            f"───────────────────\n\n"
                            f"<tg-emoji emoji-id='5431499171045581032'>🛒</tg-emoji> <b>𝗕𝗨𝗬𝗘𝗥</b> ➛ <a href='tg://user?id={new_member.id}'><b>{user_name}</b></a>\n\n"
                            f"<tg-emoji emoji-id='4927154609018897632'>🪐</tg-emoji> <b>𝗠𝗔𝗥𝗞𝗘𝗧</b> ➛ Exclusive Drops Available\n\n"
                            f"<tg-emoji emoji-id='6176773544198806516'>📦</tg-emoji> <b>𝗧𝗔𝗥𝗚𝗘𝗧</b> ➛ Elevate your style\n\n"
                            f"───────────────────\n"
                            f"<tg-emoji emoji-id='5271604874419647061'>🔗</tg-emoji> <i>Explore the exclusive.</i>\n"
                        )
                    else:
                        greeting = (
                            f"⚡ <b>𝙅𝙀𝙍𝙍𝙔 𝙓 𝙎𝙏𝙊𝙍𝙀</b> ⚡\n"
                            f"───────────────────\n\n"
                            f"🛒 <b>𝗕𝗨𝗬𝗘𝗥</b> ➛ <a href='tg://user?id={new_member.id}'><b>{user_name}</b></a>\n"
                            f"🪐 <b>𝗠𝗔𝗥𝗞𝗘𝗧</b> ➛ Exclusive Drops Available 💬\n"
                            f"📦 <b>𝗧𝗔𝗥𝗚𝗘𝗧</b> ➛ Elevate your style\n\n"
                            f"───────────────────\n"
                            f"🔗 <i>Explore the exclusive.</i>\n"
                        )
                    
                    try:
                        # Try to send with the image (needs to be saved as welcome.jpg)
                        with open('welcome.jpg', 'rb') as photo:
                            await context.bot.send_photo(
                                chat_id=message.chat_id,
                                photo=photo,
                                caption=greeting,
                                parse_mode='HTML',
                                message_thread_id=target_topic_id
                            )
                    except FileNotFoundError:
                        # Fallback if image isn't found
                        await context.bot.send_message(
                            chat_id=message.chat_id,
                            text=greeting,
                            parse_mode='HTML',
                            message_thread_id=target_topic_id
                        )
