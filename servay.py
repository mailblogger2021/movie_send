import os
import json
from telegram import Update,Bot
from telegram.ext import Application, PollAnswerHandler, CallbackContext

# Load questions from the JSON file
with open('survey_questions.json', 'r') as file:
    survey_data = json.load(file)

# Telegram bot token
bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
bot_token = "7910154011:AAFlqDOHHS_K-5zhmSpLJxlfM_NWJaoXpss"
bot = Bot(token=bot_token)


# Store the current poll question index for each user
user_poll_state = {}

# Function to send the next poll
async def send_next_poll(chat_id, question_index, context: CallbackContext):
    if question_index < len(survey_data['questions']):
        question_data = survey_data['questions'][question_index]
        await context.bot.send_poll(
            chat_id=chat_id,
            question=question_data['question'],
            options=question_data['options'],
            is_anonymous=False,
            allows_multiple_answers=False
        )
        user_poll_state[chat_id] = question_index + 1
    else:
        await context.bot.send_message(chat_id=chat_id, text="Thank you for completing the survey!")

# Function to handle poll answers
async def handle_poll_answer(update: Update, context: CallbackContext):
    poll_answer = update.poll_answer
    chat_id = poll_answer.user.id

    # Check if the user has more questions to answer
    if chat_id in user_poll_state:
        next_question_index = user_poll_state[chat_id]
        await send_next_poll(chat_id, next_question_index, context)
    else:
        # Start with the first question if the user is new
        await send_next_poll(chat_id, 0, context)

# Main function to run the bot
async def main():
    # Set up the bot with the Application builder
    application = Application.builder().token(bot_token).build()

    # Handle poll answers
    application.add_handler(PollAnswerHandler(handle_poll_answer))

    # Start the bot by polling for updates
    await application.start_polling()

    # Block until the application is stopped
    await application.wait_until_stopped()

if __name__ == '__main__':
    import asyncio
    asyncio.run(main())