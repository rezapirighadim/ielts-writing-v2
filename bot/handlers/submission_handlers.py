"""
IELTS text submission handlers for writing evaluation.
"""

import logging
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CommandHandler, MessageHandler, filters, CallbackQueryHandler
from session.session_utils import (
    get_user_session_from_update,
    set_user_conversation_step,
    reset_user_conversation,
    get_user_conversation_step
)
from session.conversation_state import ConversationStep
from limits.usage_limiter import check_submission_limits
from limits.limit_utils import get_user_limit_info_from_update, format_limit_message
from database.submission_operations import SubmissionOperations
from handlers.text_validators import validate_submission_text, TextValidationError
from messages.persian_messages import PersianMessages

logger = logging.getLogger(__name__)


async def submit_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle /submit command - start text submission process.

    Python Concept: This is the main entry point for text submission.
    It guides users through the submission process step by step.
    """
    try:
        # Get user session
        session = get_user_session_from_update(update)
        if not session:
            await update.message.reply_text("لطفاً ابتدا از دستور /start استفاده کنید")
            return

        # Check submission limits
        limit_result = check_submission_limits(session.telegram_id)

        if not limit_result.get("can_submit", False):
            # Show limit exceeded message with options
            limit_info = get_user_limit_info_from_update(update)
            limit_message = format_limit_message(limit_info)

            keyboard = [
                [InlineKeyboardButton("📢 دریافت درخواست رایگان", callback_data="get_bonus_requests")],
                [InlineKeyboardButton("💎 ارتقاء اکانت", callback_data="upgrade_account")],
                [InlineKeyboardButton("📊 مشاهده آمار", callback_data="view_stats")]
            ]

            reply_markup = InlineKeyboardMarkup(keyboard)

            await update.message.reply_text(
                f"{limit_message}\n\n💡 گزینه‌های شما:",
                reply_markup=reply_markup
            )
            return

        # Set conversation state to waiting for task type selection
        set_user_conversation_step(update, ConversationStep.SUBMISSION_TASK_TYPE)

        # Show task type selection
        await show_task_type_selection(update, context)

        logger.info(f"Submit command started by user {session.telegram_id}")

    except Exception as e:
        logger.error(f"Error in submit_command: {e}")
        await update.message.reply_text(PersianMessages.ERROR_GENERAL)
        reset_user_conversation(update)


async def show_task_type_selection(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Show IELTS task type selection to user.

    Python Concept: This function creates an interactive interface
    for users to select between Task 1 and Task 2.
    """
    try:
        welcome_message = """📝 ارسال متن برای بررسی آیلتس

لطفاً نوع تسک آیلتس خود را انتخاب کنید:

📊 **Task 1**: گراف، جدول، نمودار یا فرآیند (حداقل 150 کلمه)
📝 **Task 2**: مقاله نظری یا بحثی (حداقل 250 کلمه)

💡 پس از انتخاب، متن خود را ارسال کنید."""

        keyboard = [
            [
                InlineKeyboardButton("📊 Task 1 (150+ کلمه)", callback_data="select_task:task1"),
                InlineKeyboardButton("📝 Task 2 (250+ کلمه)", callback_data="select_task:task2")
            ],
            [InlineKeyboardButton("❌ انصراف", callback_data="cancel_submission")]
        ]

        reply_markup = InlineKeyboardMarkup(keyboard)

        if update.callback_query:
            await update.callback_query.edit_message_text(
                welcome_message,
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
        else:
            await update.message.reply_text(
                welcome_message,
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )

    except Exception as e:
        logger.error(f"Error in show_task_type_selection: {e}")
        await update.message.reply_text("خطا در نمایش انتخاب تسک")


async def handle_task_selection(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle task type selection callback.

    Python Concept: This processes the user's task type selection
    and prepares for text input.
    """
    try:
        query = update.callback_query
        await query.answer()

        callback_data = query.data
        session = get_user_session_from_update(update)

        if not session:
            await query.edit_message_text("جلسه منقضی شده. لطفاً دوباره /submit را اجرا کنید.")
            return

        if callback_data.startswith("select_task:"):
            task_type = callback_data.split(":", 1)[1]

            # Store task type in session context
            context.user_data['selected_task_type'] = task_type

            # Set conversation state to waiting for text
            set_user_conversation_step(update, ConversationStep.SUBMISSION_TEXT_INPUT)

            # Show text input instructions
            await show_text_input_instructions(update, context, task_type)

        elif callback_data == "cancel_submission":
            await query.edit_message_text(
                "❌ ارسال متن لغو شد.\n\n💡 برای شروع مجدد از /submit استفاده کنید."
            )
            reset_user_conversation(update)

    except Exception as e:
        logger.error(f"Error in handle_task_selection: {e}")
        await update.callback_query.edit_message_text("خطا در انتخاب تسک")


async def show_text_input_instructions(update: Update, context: ContextTypes.DEFAULT_TYPE, task_type: str) -> None:
    """
    Show instructions for text input based on selected task type.
    """
    try:
        task_info = {
            'task1': {
                'name': 'Task 1',
                'min_words': 150,
                'description': 'گراف، جدول، نمودار یا فرآیند',
                'tips': '• توضیح داده‌های کلیدی\n• مقایسه و تضاد\n• استفاده از زبان تحلیلی'
            },
            'task2': {
                'name': 'Task 2',
                'min_words': 250,
                'description': 'مقاله نظری یا بحثی',
                'tips': '• ارائه نظر شخصی\n• استدلال منطقی\n• نتیجه‌گیری قوی'
            }
        }

        task_info_data = task_info.get(task_type, task_info['task2'])

        instructions = f"""📝 **{task_info_data['name']}** انتخاب شد

📋 **نوع**: {task_info_data['description']}
📏 **حداقل کلمات**: {task_info_data['min_words']} کلمه

💡 **نکات مهم**:
{task_info_data['tips']}

✏️ **اکنون متن خود را ارسال کنید**:
• متن را در یک پیام بنویسید
• از copy/paste هم می‌توانید استفاده کنید
• دقت کنید تعداد کلمات کافی باشد

⏱️ **زمان**: حداکثر 10 دقیقه برای ارسال"""

        keyboard = [
            [InlineKeyboardButton("🔄 تغییر نوع تسک", callback_data="change_task_type")],
            [InlineKeyboardButton("❌ انصراف", callback_data="cancel_submission")]
        ]

        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.callback_query.edit_message_text(
            instructions,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )

    except Exception as e:
        logger.error(f"Error in show_text_input_instructions: {e}")


async def handle_text_submission(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle actual text submission from user.

    Python Concept: This is the core function that processes submitted text,
    validates it, and prepares it for AI evaluation.
    """
    try:
        # Check if user is in correct conversation state
        current_step = get_user_conversation_step(update)
        if current_step != ConversationStep.SUBMISSION_TEXT_INPUT:
            return  # Ignore messages when not expecting text

        session = get_user_session_from_update(update)
        if not session:
            await update.message.reply_text("جلسه منقضی شده. لطفاً دوباره /submit را اجرا کنید.")
            return

        # Get selected task type
        task_type = context.user_data.get('selected_task_type', 'task2')
        submitted_text = update.message.text

        # Validate the text
        try:
            validation_result = validate_submission_text(submitted_text, task_type)
        except TextValidationError as e:
            # Show validation error with retry option
            await show_validation_error(update, context, str(e), task_type)
            return

        # Show processing message
        processing_message = await update.message.reply_text(
            "🔄 متن شما دریافت شد!\n\n⏳ در حال آماده‌سازی برای بررسی...\nلطفاً چند لحظه صبر کنید."
        )

        # Set processing state
        set_user_conversation_step(update, ConversationStep.SUBMISSION_PROCESSING)

        # Store submission in database
        try:
            submission_data = {
                'user_id': session.user_id,
                'telegram_id': session.telegram_id,
                'submission_text': submitted_text,
                'task_type': task_type,
                'word_count': validation_result['word_count'],
                'submission_date': datetime.utcnow(),
                'status': 'pending'
            }

            submission_id = SubmissionOperations.create_submission(submission_data)

            if not submission_id:
                raise Exception("Failed to create submission record")

            # Store submission ID for later use
            context.user_data['current_submission_id'] = submission_id

            # Update processing message
            await processing_message.edit_text(
                f"✅ متن ذخیره شد (شناسه: {submission_id})\n\n🤖 ارسال به سیستم ارزیابی...\n⏱️ زمان تقریبی: 30-60 ثانیه"
            )

            # TODO: In next step, we'll add AI evaluation here
            # For now, just show confirmation
            await show_submission_confirmation(update, context, submission_id, validation_result)

        except Exception as e:
            logger.error(f"Error storing submission: {e}")
            await processing_message.edit_text(
                "❌ خطا در ذخیره متن. لطفاً دوباره تلاش کنید."
            )
            reset_user_conversation(update)

    except Exception as e:
        logger.error(f"Error in handle_text_submission: {e}")
        await update.message.reply_text("خطا در پردازش متن ارسالی")
        reset_user_conversation(update)


async def show_validation_error(update: Update, context: ContextTypes.DEFAULT_TYPE,
                                error_message: str, task_type: str) -> None:
    """
    Show validation error with retry options.
    """
    try:
        task_names = {'task1': 'Task 1', 'task2': 'Task 2'}
        task_name = task_names.get(task_type, 'Task 2')

        error_text = f"""❌ **خطا در متن ارسالی**

🔍 **مشکل**: {error_message}

📝 **تسک انتخابی**: {task_name}

💡 **راهنما**:
• متن را بررسی و اصلاح کنید
• تعداد کلمات را چک کنید
• از زبان انگلیسی استفاده کنید
• دوباره ارسال کنید

✏️ **متن اصلاح شده را ارسال کنید:**"""

        keyboard = [
            [InlineKeyboardButton("🔄 تغییر نوع تسک", callback_data="change_task_type")],
            [InlineKeyboardButton("❌ انصراف", callback_data="cancel_submission")]
        ]

        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_text(
            error_text,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )

    except Exception as e:
        logger.error(f"Error showing validation error: {e}")


async def show_submission_confirmation(update: Update, context: ContextTypes.DEFAULT_TYPE,
                                       submission_id: int, validation_result: dict) -> None:
    """
    Show submission confirmation and next steps.
    """
    try:
        task_type = context.user_data.get('selected_task_type', 'task2')
        task_names = {'task1': 'Task 1', 'task2': 'Task 2'}
        task_name = task_names.get(task_type, 'Task 2')

        confirmation_text = f"""✅ **متن با موفقیت ارسال شد!**

📋 **جزئیات ارسال**:
• شناسه: {submission_id}
• نوع تسک: {task_name}
• تعداد کلمات: {validation_result['word_count']}
• زمان ارسال: {datetime.now().strftime('%H:%M')}

🤖 **مرحله بعدی**:
در ادامه، سیستم ارزیابی AI متن شما را بر اساس معیارهای آیلتس بررسی خواهد کرد.

⏱️ **زمان تقریبی**: 30-60 ثانیه

📊 **معیارهای ارزیابی**:
• Task Achievement
• Coherence & Cohesion  
• Lexical Resource
• Grammatical Range & Accuracy"""

        keyboard = [
            [InlineKeyboardButton("📊 مشاهده آمار", callback_data="view_stats")],
            [InlineKeyboardButton("📝 ارسال متن جدید", callback_data="new_submission")],
            [InlineKeyboardButton("🏠 منوی اصلی", callback_data="main_menu")]
        ]

        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_text(
            confirmation_text,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )

        # Reset conversation state
        reset_user_conversation(update)

        # Log successful submission
        logger.info(f"Submission {submission_id} confirmed for user {update.effective_user.id}")

    except Exception as e:
        logger.error(f"Error showing submission confirmation: {e}")


async def handle_submission_callbacks(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle callback queries related to submissions.
    """
    try:
        query = update.callback_query
        await query.answer()

        callback_data = query.data

        if callback_data == "change_task_type":
            await show_task_type_selection(update, context)

        elif callback_data == "cancel_submission":
            await query.edit_message_text(
                "❌ ارسال متن لغو شد.\n\n💡 برای شروع مجدد از /submit استفاده کنید."
            )
            reset_user_conversation(update)

        elif callback_data == "new_submission":
            await query.delete_message()
            # Restart submission process
            fake_update = update
            fake_update.message = query.message
            await submit_command(fake_update, context)

        elif callback_data == "main_menu":
            await query.edit_message_text(
                "🏠 منوی اصلی\n\n" +
                "📝 /submit - ارسال متن جدید\n" +
                "📊 /stats - مشاهده آمار\n" +
                "📢 /channels - کانال‌ها برای درخواست رایگان\n" +
                "❓ /help - راهنما"
            )

        elif callback_data == "get_bonus_requests":
            await query.edit_message_text(
                "📢 برای دریافت درخواست رایگان اضافی از دستور /channels استفاده کنید."
            )

    except Exception as e:
        logger.error(f"Error in handle_submission_callbacks: {e}")


def register_submission_handlers(application) -> None:
    """
    Register submission-related handlers with the application.

    Args:
        application: Telegram Application instance
    """
    try:
        # Command handlers
        application.add_handler(CommandHandler("submit", submit_command))

        # Callback query handlers
        application.add_handler(CallbackQueryHandler(
            handle_task_selection,
            pattern="^(select_task:|cancel_submission).*"
        ))

        application.add_handler(CallbackQueryHandler(
            handle_submission_callbacks,
            pattern="^(change_task_type|new_submission|main_menu|get_bonus_requests)$"
        ))

        # Text message handler (for actual submissions)
        application.add_handler(MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            handle_text_submission
        ))

        logger.info("✅ Submission handlers registered successfully")

    except Exception as e:
        logger.error(f"❌ Failed to register submission handlers: {e}")
        raise