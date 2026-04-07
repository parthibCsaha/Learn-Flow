import logging

from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings

logger = logging.getLogger(__name__)

@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_enrollment_email(self, user_id, course_id):
    """Send welcome email when a student enrolls in a course."""

    logger.debug('Preparing to send enrollment email: user_id=%s course_id=%s', user_id, course_id)

    try:
        from apps.users.models import User
        from apps.courses.models import Course

        user = User.objects.get(pk=user_id)
        course = Course.objects.get(pk=course_id)

        send_mail(
            subject=f'Welcome to {course.title}!',
            message=(
                f'Hi {user.username},\n\n'
                f'You have successfully enrolled in "{course.title}".\n'
                f'Start learning at your own pace.\n\n'
                f'Good luck!\n'
                f'The LearnFlow Team'
            ),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=False,
        )
    except Exception as exc:
        raise self.retry(exc=exc)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_completion_email(self, user_id, course_id):
    """Send congratulations email when a student completes a course."""
    try:
        from apps.users.models import User
        from apps.courses.models import Course

        user = User.objects.get(pk=user_id)
        course = Course.objects.get(pk=course_id)

        send_mail(
            subject=f'Congratulations! You completed {course.title}',
            message=(
                f'Hi {user.username},\n\n'
                f'You have completed "{course.title}" — great work!\n\n'
                f'Keep learning and growing.\n\n'
                f'The LearnFlow Team'
            ),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=False,
        )
    except Exception as exc:
        raise self.retry(exc=exc)
    