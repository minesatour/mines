OTP Verification and Telegram Integration Script

This project allows you to automate OTP calls using Twilio and manage them via a Telegram bot. The script is highly customizable and includes features like prompt configuration, spoofed number setup, and language selection.

Features
Automated OTP call handling via Twilio.
Telegram bot integration for remote command execution.
Interactive menu for easy configuration.
Customizable prompts and language settings.
Logging for debugging and usage tracking.
Folder Structure
plaintext
Copy code
project-repo/

Prerequisites
Python 3.8 or higher.
Twilio account with verified credentials.
Telegram bot token (from the BotFather on Telegram).
Ngrok (or a public server) to expose your Flask app for Twilio callbacks.

Setup Instructions

Step 1: Clone the Repository
bash
Copy code
git clone https://github.com/your-repo/project-repo.git
cd project-repo

Step 2: Install Dependencies
Install the required Python libraries listed in requirements.txt:

bash
Copy code
pip install -r requirements/requirements.txt

Step 3: Configure the Project
Navigate to the config/ directory.
Edit the config.json file with your credentials and settings:
json
Copy code

{
  "TWILIO_SID": "your_twilio_sid",
  "TWILIO_AUTH_TOKEN": "your_twilio_auth_token",
  "TWILIO_PHONE_NUMBER": "your_twilio_phone_number",
  "TELEGRAM_BOT_TOKEN": "your_telegram_bot_token",
  "CALLBACK_URL": "http://your-ngrok-url",
  "otp_length": 6,
  "language": "en",
  "ai_enabled": false,
  "log_level": "INFO",
  "call_timeout": 30,
  "retry_attempts": 3,
  "schedule_enabled": false,
  "ai_prompt": "Please enter the OTP you have received.",
  "company_name": "Your Company Name",
  "spoof_number": "your_spoof_number",
  "prompts": {}
}
Step 4: Run the Flask App
Start the Flask app for Twilio callbacks:

bash
Copy code
python app/main.py
Expose the Flask app to the internet using Ngrok:

bash
Copy code
ngrok http 5000
Update the CALLBACK_URL in config.json with the Ngrok URL.

Step 5: Start the Telegram Bot
Run the Telegram bot to handle commands:

bash
Copy code
python bot/bot.py
Usage Instructions
Interactive Menu
Run the script to access the interactive menu for configuration:

bash
Copy code
python app/main.py
You can configure settings such as:

Twilio credentials.
Telegram bot token.
OTP length, language, and prompts.
Enable/disable AI features.
Telegram Bot Commands
Trigger OTP Call:

Use the /custom command in the Telegram bot to trigger an OTP call.

Syntax:

php
Copy code
/custom <victim_number> <company_name> <spoof_number> <full_name> <prompt_key>
Example:

bash
Copy code
/custom +1234567890 MyCompany +0987654321 JohnDoe prompt1
Available Prompts: Ensure that prompt_key exists in your prompts configuration.

Testing
Run the test scripts to ensure the app and bot are functioning as expected:

bash
Copy code
pytest tests/
Troubleshooting
Invalid Phone Number Error: Ensure the numbers are in E.164 format (e.g., +1234567890).

Twilio Call Fails:

Verify your Twilio SID, Auth Token, and phone number.
Ensure the Ngrok URL is correctly set in config.json.
Telegram Bot Not Responding:

Check the bot token.
Verify internet connectivity.
Logs: Refer to logs/app.log for detailed error messages.

Future Improvements
Add scheduling for OTP calls.
Enhance AI integration for custom call handling.
Improve multi-language support.
License
This project is licensed under the MIT License. See the LICENSE file for details.

