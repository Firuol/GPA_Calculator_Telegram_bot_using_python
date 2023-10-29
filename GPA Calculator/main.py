import logging
from telegram import Bot, Update
from telegram.ext import CommandHandler, MessageHandler, Filters, ConversationHandler, CallbackContext, Dispatcher

import configparser

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Read bot credentials from the configuration file
config = configparser.ConfigParser()
config.read('config.ini')

# Extract bot token and username
bot_token = config.get('Telegram', 'bot_token')
bot_username = config.get('Telegram', 'bot_username')

# Define states for the conversation
SELECTING, NUM_COURSES, COURSES, GPA = range(4)

# Store user data
user_data = {}

# Create a bot instance
bot = Bot(token=bot_token)

# Create a dispatcher
dp = Dispatcher(bot, None, workers=0, use_context=True)

# Start command to initiate the conversation
def start(update: Update, context: CallbackContext) -> int:
    update.message.reply_text("Welcome to GPA Calculator Bot! I can help you calculate your GPA.\n"
                              "Please enter the number of courses you've taken.")
    return NUM_COURSES

# Function to save the number of courses
def set_num_courses(update: Update, context: CallbackContext) -> int:
    user_data['num_courses'] = int(update.message.text)
    update.message.reply_text(f"Great! You've taken {user_data['num_courses']} courses.\n"
                              "Now, please enter your course details one by one.")
    user_data['courses'] = []
    user_data['total_credit_hours'] = 0
    user_data['cumulative_points'] = 0
    user_data['current_course'] = 0
    return COURSES

# Function to save course details
def set_course_details(update: Update, context: CallbackContext) -> int:
    course_details = update.message.text.split(',')
    if len(course_details) != 2:
        update.message.reply_text("Please enter course details in the format 'Grade,Credit Hours', e.g., 'A,3'.")
        return COURSES

    grade, credit_hours = course_details
    grade = grade.strip().upper()
    credit_hours = int(credit_hours.strip())

    if grade not in ['A', 'B', 'C', 'D', 'F']:
        update.message.reply_text("Invalid grade. Please enter a valid grade (A, B, C, D, F).")
        return COURSES

    user_data['courses'].append((grade, credit_hours))
    user_data['total_credit_hours'] += credit_hours
    user_data['cumulative_points'] += grade_to_points(grade) * credit_hours

    user_data['current_course'] += 1

    if user_data['current_course'] < user_data['num_courses']:
        update.message.reply_text(f"Course {user_data['current_course'] + 1} details saved. Please enter the next course details.")
        return COURSES
    else:
        gpa = user_data['cumulative_points'] / user_data['total_credit_hours']
        update.message.reply_text(f"Your GPA is: {gpa:.2f}")
        return ConversationHandler.END

# Function to convert grade to points
def grade_to_points(grade):
    grade_points = {'A': 4.0, 'B': 3.0, 'C': 2.0, 'D': 1.0, 'F': 0.0}
    return grade_points.get(grade, 0.0)

# Function to cancel the conversation
def cancel(update: Update, context: CallbackContext) -> int:
    update.message.reply_text("The conversation has been canceled.")
    return ConversationHandler.END

# Set up handlers for the dispatcher
dp.add_handler(CommandHandler('start', start))
dp.add_handler(MessageHandler(Filters.text & ~Filters.command, set_num_courses))
dp.add_handler(MessageHandler(Filters.text & ~Filters.command, set_course_details))

if __name__ == '__main__':
    bot.start_polling()
    dp.run_polling()
