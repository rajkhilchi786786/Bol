import logging
import random
import asyncio
import re
import os
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    ConversationHandler,
    filters
)
from playwright.async_api import async_playwright

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Registration steps
FIRST_NAME, LAST_NAME, EMAIL, PASSWORD = range(4)

class CloudwaysAutomator:
    def __init__(self):
        self.business_types = [
            "Freelancer", "Digital Agency", "Software House",
            "E-commerce Business", "Startup", "Enterprise"
        ]
        self.business_purposes = [
            "Web Application", "E-commerce Store", "CMS Website",
            "Custom Development", "Mobile App Backend", "API Services"
        ]
        self.timeout = 300000  # 5 minutes timeout
        self.mobile_user_agents = [
            "Mozilla/5.0 (iPhone; CPU iPhone OS 15_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0 Mobile/15E148 Safari/604.1",
            "Mozilla/5.0 (Linux; Android 10; SM-A205U) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.5615.47 Mobile Safari/537.36",
            "Mozilla/5.0 (Linux; Android 12; SM-S906N Build/QP1A.190711.020; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/80.0.3987.119 Mobile Safari/537.36"
        ]

    async def register_account(self, user_data):
        """Performs Cloudways registration through their official website"""
        async with async_playwright() as p:
            try:
                # Launch browser in HEADLESS mode for server compatibility
                browser = await p.chromium.launch(
                    headless=True,  # Changed from False to True
                    args=[
                        "--no-sandbox",
                        "--disable-dev-shm-usage",
                        "--disable-gpu",
                        "--disable-blink-features=AutomationControlled",
                        f"--user-agent={random.choice(self.mobile_user_agents)}"
                    ]
                )
            except Exception as e:
                logger.error(f"Browser launch failed: {e}")
                return False, f"❌ Browser initialization failed: {str(e)}"
            
            # Create fresh mobile context
            context = await browser.new_context(
                user_agent=random.choice(self.mobile_user_agents),
                locale="en-US",
                viewport={"width": 360, "height": 640},
                device_scale_factor=2.0,
                is_mobile=True,
                has_touch=True
            )
            await context.clear_cookies()
            
            page = await context.new_page()

            try:
                # Step 1: Load Cloudways registration page
                await page.goto("https://platform.cloudways.com/signup", timeout=self.timeout)
                await page.wait_for_load_state("networkidle")
                await asyncio.sleep(random.uniform(2, 4))

                # Debug: Save screenshot only if DEBUG environment variable is set
                if os.getenv('DEBUG', 'False').lower() == 'true':
                    await page.screenshot(path="debug1.png")

                # Step 2: Fill registration form
                await self._fill_field(page, 'input[name="first_name"], input[name="firstName"]', user_data['first_name'])
                await self._fill_field(page, 'input[name="last_name"], input[name="lastName"]', user_data['last_name'])
                await self._fill_field(page, 'input[name="email"], input[type="email"]', user_data['email'])
                await self._fill_field(page, 'input[name="password"], input[type="password"]', user_data['password'])
                await asyncio.sleep(random.uniform(1, 2))

                # Step 3: Select business information (updated selectors)
                await self._select_dropdown(page, 'div[role="button"]:first-of-type, div[aria-haspopup="listbox"]:first-of-type', random.choice(self.business_types))
                await asyncio.sleep(random.uniform(1, 2))
                await self._select_dropdown(page, 'div[role="button"]:nth-of-type(2), div[aria-haspopup="listbox"]:nth-of-type(2)', random.choice(self.business_purposes))
                await asyncio.sleep(random.uniform(1, 2))
                await self._select_dropdown(page, 'div[role="button"]:nth-of-type(3), div[aria-haspopup="listbox"]:nth-of-type(3)', "$0 to $50")
                await asyncio.sleep(random.uniform(1, 3))

                # Step 4: Accept terms and submit
                await page.click('input[name="terms"], input[type="checkbox"]', delay=random.randint(100, 300))
                await page.click('button[type="submit"], button:has-text("Sign Up")', delay=random.randint(200, 500))

                # Debug: Save screenshot after submission only if DEBUG is set
                if os.getenv('DEBUG', 'False').lower() == 'true':
                    await page.screenshot(path="debug2.png")

                # Step 5: Verify successful registration
                try:
                    await page.wait_for_selector(
                        'text=Your account has been created successfully, text=Verify your email',
                        timeout=60000
                    )
                    return True, "✅ Account created successfully! Check your email for verification."
                except Exception as e:
                    error = await self._get_error_message(page)
                    if os.getenv('DEBUG', 'False').lower() == 'true':
                        await page.screenshot(path="error.png")
                    return False, f"❌ Registration failed: {error or 'Unknown error'}"

            except Exception as e:
                logger.error(f"Registration error: {str(e)}", exc_info=True)
                return False, f"⚠️ System error: {str(e)}"
            finally:
                await context.close()
                await browser.close()

    async def _fill_field(self, page, selectors, value):
        """Human-like field filling with multiple selector options"""
        for selector in selectors.split(','):
            selector = selector.strip()
            if await page.query_selector(selector):
                await page.click(selector, delay=random.randint(100, 300))
                await asyncio.sleep(random.uniform(0.2, 0.5))
                await page.fill(selector, value, delay=random.randint(50, 150))
                return
        raise Exception(f"No matching field found for selectors: {selectors}")

    async def _select_dropdown(self, page, selectors, value):
        """Mobile-like dropdown selection with multiple selector options"""
        for selector in selectors.split(','):
            selector = selector.strip()
            if await page.query_selector(selector):
                await page.click(selector, delay=random.randint(200, 400))
                await asyncio.sleep(random.uniform(0.5, 1.5))
                option = await page.wait_for_selector(f'li[role="option"]:has-text("{value}"), div[role="option"]:has-text("{value}")', timeout=5000)
                await option.click(delay=random.randint(100, 300))
                return
        raise Exception(f"No matching dropdown found for selectors: {selectors}")

    async def _get_error_message(self, page):
        """Extracts error message if available"""
        for selector in ['.error-message', '.text-red-500', '[role="alert"]', '.alert-danger']:
            if element := await page.query_selector(selector):
                return await element.inner_text()
        return None

# Telegram Bot Handlers
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🌟 Cloudways Auto-Registration Bot 🌟\n\n"
        "This performs REAL registration through Cloudways' official website.\n"
        "Use /new to start a fresh registration."
    )

async def new(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text("📝 Enter First Name:")
    return FIRST_NAME

async def get_first_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(update.message.text) < 2:
        await update.message.reply_text("❌ Name too short. Please enter valid first name:")
        return FIRST_NAME
    context.user_data['first_name'] = update.message.text
    await update.message.reply_text("📝 Enter Last Name:")
    return LAST_NAME

async def get_last_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(update.message.text) < 2:
        await update.message.reply_text("❌ Name too short. Please enter valid last name:")
        return LAST_NAME
    context.user_data['last_name'] = update.message.text
    await update.message.reply_text("📧 Enter Email Address:")
    return EMAIL

async def get_email(update: Update, context: ContextTypes.DEFAULT_TYPE):
    email = update.message.text.lower()
    if not re.match(r"^[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}$", email):
        await update.message.reply_text("❌ Invalid email format. Please enter a valid email:")
        return EMAIL
    if any(domain in email for domain in ["tempmail", "mailinator", "10minutemail"]):
        await update.message.reply_text("❌ Temporary emails not allowed. Please use a real email:")
        return EMAIL
    context.user_data['email'] = email
    await update.message.reply_text("🔑 Create Password (min 8 characters with mix of letters and numbers):")
    return PASSWORD

async def get_password(update: Update, context: ContextTypes.DEFAULT_TYPE):
    password = update.message.text
    if len(password) < 8 or not re.search(r"[0-9]", password) or not re.search(r"[a-zA-Z]", password):
        await update.message.reply_text("❌ Weak password. Minimum 8 chars with letters and numbers:")
        return PASSWORD
    
    context.user_data['password'] = password
    msg = await update.message.reply_text("⏳ Processing registration with Cloudways...")
    
    automator = CloudwaysAutomator()
    success, result = await automator.register_account(context.user_data)
    
    if success:
        await context.bot.edit_message_text(
            chat_id=msg.chat_id,
            message_id=msg.message_id,
            text=(
                "🎉 REGISTRATION SUCCESSFUL!\n\n"
                "Your Cloudways account details:\n"
                f"👤 Name: {context.user_data['first_name']} {context.user_data['last_name']}\n"
                f"📧 Email: {context.user_data['email']}\n"
                f"🔑 Password: {'*' * len(context.user_data['password'])}\n\n"
                "📩 Check your email for verification link\n"
                "🔗 Login at: https://platform.cloudways.com/login"
            )
        )
    else:
        await context.bot.edit_message_text(
            chat_id=msg.chat_id,
            message_id=msg.message_id,
            text=f"❌ REGISTRATION FAILED\n\n{result}\n\nTry again with /new"
        )
    
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ Registration cancelled")
    return ConversationHandler.END

def main():
    # Get Telegram token from environment variable
    token = '8483930476:AAHoDKyxgQXCTbK0oPK1RDpZPBO0reevhZk'
    if not token:
        raise ValueError("Please set TELEGRAM_BOT_TOKEN environment variable")
    
    # Create application
    application = Application.builder().token(token).build()

    # Setup conversation handler
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('new', new)],
        states={
            FIRST_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_first_name)],
            LAST_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_last_name)],
            EMAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_email)],
            PASSWORD: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_password)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
        allow_reentry=True
    )

    # Add handlers
    application.add_handler(CommandHandler('start', start))
    application.add_handler(conv_handler)
    
    # Start bot
    logger.info("Bot is running and ready for registrations...")
    application.run_polling()

if __name__ == '__main__':
    main()