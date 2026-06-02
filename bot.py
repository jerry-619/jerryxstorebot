import os
import logging
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, MessageHandler, CommandHandler, CallbackQueryHandler, filters

from handlers import greet_new_members, private_chat_interceptor
from commands import start_command, commands_callback, back_callback
from admin_commands import (
    ban_command, unban_command, kick_command, mute_command, unmute_command,
    del_command, announce_command, pin_command, unpin_command, gw_command, join_gw_callback,
    cid_command, ping_command
)
from automod import (
    addfilter_command, rmfilter_command, filters_command, filterlinks_command, rmwarn_command, automod_handler
)

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

def main():
    """Start the bot."""
    # Load environment variables
    load_dotenv()
    
    bot_token = os.getenv("BOT_TOKEN")
    if not bot_token:
        logger.error("BOT_TOKEN not found in environment variables.")
        return

    # Create the Application and pass it your bot's token.
    application = Application.builder().token(bot_token).build()

    # Intercept all private messages before any commands are processed
    application.add_handler(MessageHandler(filters.ChatType.PRIVATE, private_chat_interceptor), group=-1)
    
    # Register handlers
    # We use filters.StatusUpdate.NEW_CHAT_MEMBERS to trigger only on new member joins
    application.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, greet_new_members))
    
    # Command handlers
    application.add_handler(CommandHandler("start", start_command))
    
    # Admin Command handlers
    application.add_handler(CommandHandler("ban", ban_command))
    application.add_handler(CommandHandler("unban", unban_command))
    application.add_handler(CommandHandler("kick", kick_command))
    application.add_handler(CommandHandler("mute", mute_command))
    application.add_handler(CommandHandler("unmute", unmute_command))
    application.add_handler(CommandHandler("del", del_command))
    application.add_handler(CommandHandler("delete", del_command))
    application.add_handler(CommandHandler("purge", del_command))  # Simplified purge logic mapped to del for now
    application.add_handler(CommandHandler("announce", announce_command))
    application.add_handler(CommandHandler("pin", pin_command))
    application.add_handler(CommandHandler("unpin", unpin_command))
    application.add_handler(CommandHandler("gw", gw_command))
    application.add_handler(CommandHandler("giveaway", gw_command))
    application.add_handler(CommandHandler("cid", cid_command))
    application.add_handler(CommandHandler("ping", ping_command))
    
    # Automod Commands
    application.add_handler(CommandHandler("addfilter", addfilter_command))
    application.add_handler(CommandHandler("rmfilter", rmfilter_command))
    application.add_handler(CommandHandler("filters", filters_command))
    application.add_handler(CommandHandler("filterlinks", filterlinks_command))
    application.add_handler(CommandHandler("rmwarn", rmwarn_command))
    
    # Global Message Handler for Automod (Group 1 to run alongside other handlers)
    application.add_handler(MessageHandler(filters.TEXT | filters.Entity("url") | filters.Entity("text_link"), automod_handler), group=1)
    
    # Callback Handlers
    application.add_handler(CallbackQueryHandler(join_gw_callback, pattern="^join_gw$"))
    application.add_handler(CallbackQueryHandler(commands_callback, pattern="^cmd_commands$"))
    application.add_handler(CallbackQueryHandler(back_callback, pattern="^cmd_back$"))

    # Run the bot until the user presses Ctrl-C
    logger.info("Bot is starting...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
