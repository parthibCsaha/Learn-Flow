import json
import logging
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

logger = logging.getLogger(__name__)


class GroqAPIError(Exception):
    pass


def chat_completion(messages):
    if not settings.GROQ_API_KEY:
        raise ImproperlyConfigured('GROQ_API_KEY is not configured.')

    payload = {
        'model': settings.GROQ_MODEL,
        'messages': messages,
        'temperature': 0.2,
    }

    request = Request(
        url=settings.GROQ_API_URL,
        data=json.dumps(payload).encode('utf-8'),
        headers={
            'Authorization': f'Bearer {settings.GROQ_API_KEY}',
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'User-Agent': 'LearnFlow-LMS/1.0 (+https://learnflow.local)',
        },
        method='POST',
    )

    try:
        with urlopen(request, timeout=settings.GROQ_TIMEOUT_SECONDS) as response:
            raw_body = response.read().decode('utf-8')
    except HTTPError as exc:
        error_body = exc.read().decode('utf-8', errors='ignore')
        logger.warning('Groq HTTP error: status=%s body=%s', exc.code, error_body)
        raise GroqAPIError(f'Groq API returned HTTP {exc.code}.') from exc
    except URLError as exc:
        logger.warning('Groq network error: %s', exc)
        raise GroqAPIError('Could not connect to Groq API.') from exc

    try:
        data = json.loads(raw_body)
        content = data['choices'][0]['message']['content']
    except (ValueError, KeyError, IndexError, TypeError) as exc:
        logger.warning('Invalid Groq response: %s', raw_body)
        raise GroqAPIError('Invalid response from Groq API.') from exc

    return content
