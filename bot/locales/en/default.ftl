# Welcome
welcome =
    Hello, { $name }! 👋

    I'm a Telegram bot template with multi-language support.

    Use /menu to open the main menu
    or /help for assistance.

# Profile
profile =
    👤 <b>Your Profile</b>

    🆔 ID: <code>{ $user_id }</code>
    👤 Name: { $first_name }
    📛 Username: @{ $username }
    🌐 Language: { $language }

no-username = none

# Settings
settings-menu = ⚙️ Bot Settings
settings-language = 🌐 Change Language

# Language
select-language = Select language:
language-changed = ✅ Language changed successfully!
language-error = ❌ Error changing language

# Help
help-text =
    ❓ <b>Help</b>

    Available commands:
    /start — start using the bot
    /menu — open main menu
    /profile — show your profile
    /help — show this help

    Bot created based on template using:
    • aiogram 3.x
    • PostgreSQL + Tortoise ORM
    • Redis
    • Docker

help-text-chat = 
    🤖 <b>Bot Commands in the Group</b>

    /help — show this help message
    /stats — group statistics (for admins only)

    The bot automatically processes chat events.

# Stats
chat-stats = 
    📊 <b>Chat Statistics</b>

    👥 Members: { $member_count }
    💬 Chat: { $chat_title }
    🆔 Chat ID: <code>{ $chat_id }</code>