from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import override_settings
from rest_framework import status
from rest_framework.test import APITestCase

from apps.enrollments.models import Enrollment

from .models import Category, Course, Lesson, Section


class LessonAIActionsTests(APITestCase):
    def setUp(self):
        user_model = get_user_model()
        self.instructor = user_model.objects.create_user(
            email='instructor@example.com',
            username='instructor1',
            password='pass1234',
            role='instructor',
        )
        self.student = user_model.objects.create_user(
            email='student@example.com',
            username='student1',
            password='pass1234',
            role='student',
        )
        self.other_student = user_model.objects.create_user(
            email='other@example.com',
            username='other1',
            password='pass1234',
            role='student',
        )

        self.category = Category.objects.create(name='Programming')
        self.course = Course.objects.create(
            instructor=self.instructor,
            category=self.category,
            title='Python Basics',
            description='Course description',
            price=0,
            is_published=True,
        )
        self.section = Section.objects.create(course=self.course, title='Intro', order=1)
        self.lesson = Lesson.objects.create(
            section=self.section,
            title='Variables',
            content='Variables store values. Python is dynamically typed.',
            order=1,
            duration_minutes=10,
        )

        Enrollment.objects.create(student=self.student, course=self.course)

        self.summary_url = f'/api/courses/{self.course.id}/sections/{self.section.id}/lessons/{self.lesson.id}/summary/'
        self.chat_url = f'/api/courses/{self.course.id}/sections/{self.section.id}/lessons/{self.lesson.id}/chat/'

    def test_summary_requires_authentication(self):
        response = self.client.post(self.summary_url, {}, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_summary_forbidden_for_unenrolled_student(self):
        self.client.force_authenticate(user=self.other_student)
        response = self.client.post(self.summary_url, {}, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    @override_settings(GROQ_API_KEY='')
    def test_chat_returns_503_when_api_key_missing(self):
        self.client.force_authenticate(user=self.student)
        response = self.client.post(self.chat_url, {'message': 'Explain variables'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_503_SERVICE_UNAVAILABLE)

    @override_settings(GROQ_API_KEY='test-key', GROQ_MODEL='llama-3.1-8b-instant')
    @patch('apps.courses.views.chat_completion', return_value='Variables are names bound to values.')
    def test_chat_returns_ai_reply(self, mock_chat_completion):
        self.client.force_authenticate(user=self.student)
        response = self.client.post(self.chat_url, {'message': 'What is a variable?'}, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['reply'], 'Variables are names bound to values.')
        self.assertEqual(response.data['model'], 'llama-3.1-8b-instant')
        mock_chat_completion.assert_called_once()

    @override_settings(GROQ_API_KEY='test-key', GROQ_MODEL='llama-3.1-8b-instant')
    @patch('apps.courses.views.chat_completion', return_value='This lesson explains variables and dynamic typing.')
    def test_summary_returns_ai_summary(self, mock_chat_completion):
        self.client.force_authenticate(user=self.instructor)
        response = self.client.post(self.summary_url, {}, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['summary'], 'This lesson explains variables and dynamic typing.')
        self.assertEqual(response.data['model'], 'llama-3.1-8b-instant')
        mock_chat_completion.assert_called_once()

    @override_settings(GROQ_API_KEY='test-key', GROQ_MODEL='llama-3.1-8b-instant')
    @patch('apps.courses.views.chat_completion', return_value='Summary generated from transcript.')
    def test_summary_uses_transcript_when_content_empty(self, mock_chat_completion):
        self.lesson.content = ''
        self.lesson.transcript = 'This is the video transcript for the lesson.'
        self.lesson.save(update_fields=['content', 'transcript'])

        self.client.force_authenticate(user=self.instructor)
        response = self.client.post(self.summary_url, {}, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['summary'], 'Summary generated from transcript.')
        mock_chat_completion.assert_called_once()