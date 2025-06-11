"""
Persian language messages for the IELTS Telegram Bot.
This module contains all user-facing messages in Persian.
"""

from typing import Dict, Any
from shared.constants import TaskType, SubscriptionType


class PersianMessages:
    """
    Persian messages class containing all bot messages in Persian.

    Python Concept: Using a class to organize related messages makes
    them easier to maintain and allows for dynamic message generation.
    """

    # Welcome and help messages
    WELCOME = """🎯 به ربات تمرین رایتینگ آیلتس خوش آمدید!

این ربات به شما کمک می‌کند تا مهارت نوشتن خود را برای آزمون آیلتس بهبود دهید.

📝 امکانات ربات:
✅ بررسی و نمره‌دهی متون آیلتس توسط هوش مصنوعی
✅ بازخورد تفصیلی بر اساس معیارهای رسمی آیلتس
✅ پیگیری پیشرفت و آمار شخصی
✅ درخواست‌های رایگان اضافی از طریق عضویت در کانال‌ها

برای شروع، از دستور /help استفاده کنید."""

    HELP = """📚 راهنمای استفاده از ربات آیلتس

🔹 دستورات اصلی:
📝 /submit - ارسال متن برای بررسی و نمره‌دهی
📊 /stats - مشاهده آمار و نمرات شخصی
💎 /upgrade - ارتقاء اکانت به نسخه پریمیوم
📚 /examples - مشاهده نمونه سوالات آیلتس
📢 /channels - کانال‌ها برای درخواست رایگان اضافی

🔹 نحوه استفاده:
1️⃣ روی /submit کلیک کنید
2️⃣ نوع تسک (Task 1 یا Task 2) را انتخاب کنید
3️⃣ متن خود را بفرستید
4️⃣ نتیجه و بازخورد را دریافت کنید

📊 معیارهای نمره‌دهی آیلتس:
- Task Achievement (انجام وظیفه)
- Coherence & Cohesion (انسجام و پیوستگی)
- Lexical Resource (دامنه واژگان)
- Grammatical Range & Accuracy (دستور زبان)

💡 نکته: اکانت رایگان ماهانه ۱۰ درخواست، پریمیوم ۱۰۰ درخواست دارد."""

    # Command responses
    START_REGISTERED = """🎉 خوش برگشتید!

شما قبلاً ثبت‌نام کرده‌اید. برای مشاهده امکانات ربات از /help استفاده کنید.

📊 وضعیت اکانت شما:
- نوع اشتراک: {subscription_type}
- درخواست‌های استفاده شده این ماه: {used_submissions}/{monthly_limit}
- درخواست‌های اضافی: {bonus_requests}"""

    START_NEW_USER = """🎉 ثبت‌نام شما با موفقیت انجام شد!

اکانت رایگان شما فعال است و ماهانه ۱۰ درخواست بررسی متن دارید.

برای شروع، از دستور /help استفاده کنید یا مستقیماً /submit بزنید."""

    # Submission process messages
    SUBMIT_START = """📝 ارسال متن برای بررسی

لطفاً نوع تسک آیلتس را انتخاب کنید:

🔸 Task 1: نوشتن گزارش، نامه یا توضیح نمودار
   (حداقل ۱۵۰ کلمه)

🔸 Task 2: مقاله نظری در پاسخ به سوال
   (حداقل ۲۵۰ کلمه)"""

    SUBMIT_TASK_SELECTED = """✅ نوع تسک: {task_type}

حالا متن خود را بفرستید.

📏 حداقل تعداد کلمات: {min_words}
⏰ زمان پردازش: ۳۰ ثانیه تا ۲ دقیقه

💡 نکته: متن خود را در یک پیام ارسال کنید."""

    PROCESSING = """⏳ در حال بررسی متن شما...

🔄 متن شما توسط هوش مصنوعی تحلیل می‌شود
📊 نمره‌دهی بر اساس معیارهای رسمی آیلتس
✍️ تولید بازخورد تفصیلی

لطفاً چند لحظه صبر کنید..."""

    PROCESSING_COMPLETE = """✅ بررسی متن شما تکمیل شد!

📊 نتایج نمره‌دهی آیلتس:

🎯 Task Achievement: {task_achievement}/9
🔗 Coherence & Cohesion: {coherence_cohesion}/9
📚 Lexical Resource: {lexical_resource}/9
📝 Grammar & Accuracy: {grammatical_accuracy}/9

🏆 نمره کل: {overall_score}/9 ({score_band})

📊 تعداد کلمات: {word_count}"""

    FEEDBACK_SECTION = """💬 بازخورد تفصیلی:

{feedback_text}

📈 پیشنهادات بهبود:
- بر روی نقاط ضعف شناسایی شده تمرکز کنید
- واژگان متنوع‌تری استفاده کنید
- ساختار جملات را بهبود دهید
- انسجام متن را افزایش دهید"""

    # Limit and subscription messages
    MONTHLY_LIMIT_REACHED = """📊 محدودیت ماهانه شما به پایان رسیده است

🔸 استفاده شده: {used_submissions}/{monthly_limit}
🔸 درخواست‌های اضافی: {bonus_requests}

💎 برای ادامه استفاده:
- /upgrade - ارتقاء به اکانت پریمیوم (۱۰۰ درخواست ماهانه)
- /channels - عضویت در کانال‌ها برای درخواست رایگان اضافی

📅 تاریخ بازنشانی: اول ماه آینده"""

    UPGRADE_INFO = """💎 ارتقاء به اکانت پریمیوم

🔸 اکانت فعلی: رایگان (۱۰ درخواست ماهانه)
🔸 اکانت پریمیوم: ۱۰۰ درخواست ماهانه

✨ امکانات پریمیوم:
- ۱۰ برابر درخواست بیشتر
- پردازش سریع‌تر
- بازخورد تفصیلی‌تر
- دسترسی به ویژگی‌های ویژه

📞 برای ارتقاء با پشتیبانی تماس بگیرید:
@support_username"""

    # Channel membership messages
    CHANNELS_LIST = """📢 کانال‌ها برای درخواست رایگان اضافی

با عضویت در هر کانال، {bonus_per_channel} درخواست رایگان اضافی دریافت می‌کنید:

{channels_list}

📝 نحوه دریافت درخواست اضافی:
1️⃣ در کانال عضو شوید
2️⃣ روی "بررسی عضویت" کلیک کنید
3️⃣ درخواست‌های اضافی به اکانت شما افزوده می‌شود

⚠️ حداکثر {max_bonus} درخواست اضافی قابل جمع‌آوری است."""

    CHANNEL_MEMBERSHIP_BONUS = """🎉 تبریک!

با عضویت در کانال {channel_title}، {bonus_amount} درخواست رایگان اضافی دریافت کردید!

📊 وضعیت فعلی:
- درخواست‌های اضافی: {total_bonus}
- مجموع درخواست‌های در دسترس: {available_submissions}"""

    CHANNEL_NOT_MEMBER = """❌ عضویت تأیید نشد

شما هنوز در کانال {channel_title} عضو نیستید.

لطفاً:
1️⃣ ابتدا در کانال عضو شوید: {channel_url}
2️⃣ سپس مجدد روی "بررسی عضویت" کلیک کنید"""

    CHECK_MEMBERSHIP = """🔄 در حال بررسی عضویت شما...

لطفاً چند لحظه صبر کنید..."""

    # Statistics messages
    STATS_HEADER = """📊 آمار شخصی شما

👤 نام کاربری: @{username}
🗓️ تاریخ عضویت: {registration_date}
💎 نوع اشتراک: {subscription_type}"""

    STATS_USAGE = """📈 آمار استفاده:
- کل ارسال‌ها: {total_submissions}
- ارسال‌های ماه جاری: {monthly_submissions}/{monthly_limit}
- درخواست‌های اضافی: {bonus_requests}
- آخرین فعالیت: {last_activity}"""

    STATS_SCORES = """🏆 نمرات اخیر:
{recent_scores}

📊 میانگین نمرات:
- Task Achievement: {avg_task_achievement}
- Coherence & Cohesion: {avg_coherence}
- Lexical Resource: {avg_lexical}
- Grammar & Accuracy: {avg_grammar}
- نمره کل میانگین: {avg_overall}"""

    NO_SUBMISSIONS_YET = """📝 هنوز متنی ارسال نکرده‌اید

برای شروع، از دستور /submit استفاده کنید و اولین متن خود را برای بررسی ارسال کنید."""

    # Error messages
    ERROR_GENERAL = """❌ متأسفانه خطایی رخ داده است

لطفاً مجدد تلاش کنید. اگر مشکل ادامه داشت، با پشتیبانی تماس بگیرید.

🔄 دستور /start - شروع مجدد
📞 پشتیبانی: @support_username"""

    ERROR_WORD_COUNT_LOW = """📏 تعداد کلمات کافی نیست

متن شما {word_count} کلمه دارد، ولی حداقل {min_required} کلمه لازم است.

لطفاً متن کامل‌تری ارسال کنید."""

    ERROR_WORD_COUNT_HIGH = """📏 متن شما خیلی طولانی است

متن شما {word_count} کلمه دارد، ولی حداکثر {max_allowed} کلمه مجاز است.

لطفاً متن کوتاه‌تری ارسال کنید."""

    ERROR_INVALID_TASK_TYPE = """❌ نوع تسک نامعتبر

لطفاً یکی از گزینه‌های Task 1 یا Task 2 را انتخاب کنید."""

    ERROR_NO_TEXT = """📝 متنی دریافت نشد

لطفاً متن خود را بنویسید و ارسال کنید."""

    ERROR_PROCESSING_FAILED = """❌ خطا در پردازش متن

متأسفانه در پردازش متن شما مشکلی پیش آمد. لطفاً مجدد تلاش کنید.

اگر مشکل ادامه داشت، با پشتیبانی تماس بگیرید."""

    # Examples
    EXAMPLES_INTRO = """📚 نمونه سوالات آیلتس

در زیر نمونه‌هایی از سوالات Task 1 و Task 2 آیلتس آورده شده:"""

    TASK1_EXAMPLES = """📊 نمونه سوالات Task 1:

🔸 نمونه ۱ - نمودار:
"The chart below shows the percentage of households in owned and rented accommodation in England and Wales between 1918 and 2011. Summarise the information by selecting and reporting the main features..."

🔸 نمونه ۲ - نامه:
"You recently bought a piece of equipment for your kitchen but it did not work. You phoned the shop but no action was taken. Write a letter to the shop manager..."

🔸 نمونه ۳ - فرآیند:
"The diagrams below show the life cycle of a species of large fish called the salmon. Summarise the information by selecting and reporting the main features..."

✅ نکات مهم Task 1:
- حداقل ۱۵۰ کلمه
- توصیف داده‌ها، نه تفسیر
- استفاده از زمان مناسب"""

    TASK2_EXAMPLES = """✍️ نمونه سوالات Task 2:

🔸 نمونه ۱ - نظر شخصی:
"Some people think that universities should provide graduates with the knowledge and skills needed in the workplace. Others think that the true function of a university should be to give access to knowledge for its own sake. Discuss both views and give your own opinion."

🔸 نمونه ۲ - مشکل و راه‌حل:
"In many countries, the amount of crime is increasing. What do you think are the main causes of crime? How can we deal with those causes?"

🔸 نمونه ۳ - موافق یا مخالف:
"Today, the high sales of popular consumer goods reflect the power of advertising and not the real needs of the society in which they are sold. To what extent do you agree or disagree?"

✅ نکات مهم Task 2:
- حداقل ۲۵۰ کلمه
- پاسخ کامل به سوال
- ساختار منطقی
- مثال‌های مناسب"""

    # Button texts
    BUTTON_TASK1 = "📊 Task 1"
    BUTTON_TASK2 = "✍️ Task 2"
    BUTTON_CHECK_MEMBERSHIP = "بررسی عضویت"
    BUTTON_CANCEL = "❌ انصراف"
    BUTTON_BACK = "🔙 بازگشت"

    @classmethod
    def format_welcome_returning_user(cls, user_data: Dict[str, Any]) -> str:
        """Format welcome message for returning users."""
        subscription_type = "پریمیوم" if user_data.get('is_premium') else "رایگان"

        return cls.START_REGISTERED.format(
            subscription_type=subscription_type,
            used_submissions=user_data.get('monthly_submissions', 0),
            monthly_limit=user_data.get('monthly_limit', 10),
            bonus_requests=user_data.get('bonus_requests', 0)
        )

    @classmethod
    def format_processing_complete(cls, submission_data: Dict[str, Any]) -> str:
        """Format the completion message with scores."""
        from shared.utils import get_score_band_description

        overall_score = submission_data.get('overall_score', 0)
        score_band = get_score_band_description(float(overall_score))

        return cls.PROCESSING_COMPLETE.format(
            task_achievement=submission_data.get('task_achievement_score', 0),
            coherence_cohesion=submission_data.get('coherence_cohesion_score', 0),
            lexical_resource=submission_data.get('lexical_resource_score', 0),
            grammatical_accuracy=submission_data.get('grammatical_accuracy_score', 0),
            overall_score=overall_score,
            score_band=score_band,
            word_count=submission_data.get('word_count', 0)
        )

    @classmethod
    def format_task_selected(cls, task_type: TaskType) -> str:
        """Format task selection confirmation message."""
        task_name = "Task 1" if task_type == TaskType.TASK1 else "Task 2"
        min_words = 150 if task_type == TaskType.TASK1 else 250

        return cls.SUBMIT_TASK_SELECTED.format(
            task_type=task_name,
            min_words=min_words
        )

    @classmethod
    def format_monthly_limit_reached(cls, user_data: Dict[str, Any]) -> str:
        """Format monthly limit reached message."""
        return cls.MONTHLY_LIMIT_REACHED.format(
            used_submissions=user_data.get('monthly_submissions', 0),
            monthly_limit=user_data.get('monthly_limit', 10),
            bonus_requests=user_data.get('bonus_requests', 0)
        )

    @classmethod
    def format_channel_bonus(cls, channel_title: str, bonus_amount: int,
                             total_bonus: int, available_submissions: int) -> str:
        """Format channel membership bonus message."""
        return cls.CHANNEL_MEMBERSHIP_BONUS.format(
            channel_title=channel_title,
            bonus_amount=bonus_amount,
            total_bonus=total_bonus,
            available_submissions=available_submissions
        )


def get_message(message_key: str, **kwargs) -> str:
    """
    Get a message by key with optional formatting.

    Args:
        message_key: The message key (attribute name in PersianMessages)
        **kwargs: Formatting arguments

    Returns:
        str: Formatted message
    """
    message = getattr(PersianMessages, message_key.upper(), None)
    if message is None:
        return f"Message not found: {message_key}"

    if kwargs:
        try:
            return message.format(**kwargs)
        except KeyError as e:
            return f"Message formatting error: {e}"

    return message