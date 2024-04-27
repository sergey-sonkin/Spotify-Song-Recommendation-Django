import datetime

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .models import Question


# Create your tests here.
def create_question(question_text, days):
    time = timezone.now() + datetime.timedelta(days=days)
    return Question.objects.create(question_text=question_text, pub_date=time)


class QuestionModelTests(TestCase):
    def test_was_published_recently_with_old_question(self):
        """
        was_published_recently() returns False for questions whose pub_date
        is older than 1 day.
        """
        time = timezone.now() - datetime.timedelta(days=1, seconds=1)
        old_question = Question(pub_date=time)
        self.assertIs(old_question.was_published_recently(), False)

    def test_was_published_recently_with_recent_question(self):
        """
        was_published_recently() returns True for questions whose pub_date
        is within the last day.
        """
        time = timezone.now() - datetime.timedelta(hours=23, minutes=59, seconds=59)
        recent_question = Question(pub_date=time)
        self.assertIs(recent_question.was_published_recently(), True)


class QuestionIndexViewTests(TestCase):
    def test_no_questions(self):
         = self.client.get(reverse("polls:index"))
        self.assertEqual(.status_code, 200)
        self.assertContains(, "No polls are available")
        self.assertQuerysetEqual(.context["latest_question_list"], [])

    def test_past_question(self):
        question = create_question(question_text="Past year question", days=-30)
         = self.client.get(reverse("polls:index"))
        self.assertQuerysetEqual(.context["latest_question_list"], [question])

    def test_future_question_and_past_question(self):
        question = create_question(question_text="Past question.", days=-30)
        create_question(question_text="Future quesiton.", days=30)
         = self.client.get(reverse("polls:index"))
        self.assertQuerysetEqual(.context["latest_question_list"], [question])

    def past_two_questions(self):
        question1 = create_question(question_text="Past question 1.", days=-30)
        question2 = create_question(question_text="Past question 2.", days=-5)
         = self.client.get(reverse("polls:index"))
        self.assertQuerysetEqual(
            .context["latest_question_list"], [question2, question1]
        )


class QuestionDetailViewTests(TestCase):
    def test_future_questions(self):
        future_question = create_question(question_text="Future question.", days=5)
        url = reverse("polls:detail", args=(future_question.id,))
         = self.client.get(url)
        self.assertEqual(.status_code, 404)

    def test_past_question(self):
        past_question = create_question(question_text="Past Queston.", days=-5)
        url = reverse("polls:detail", args=(past_question.id,))
         = self.client.get(url)
        self.assertContains(, past_question.question_text)
