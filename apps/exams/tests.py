"""Тесты экзаменов: автопроверка — главный механизм, обязан работать точно."""
from django.test import TestCase

from apps.accounts.models import User
from apps.courses.models import Course, Enrollment, Program
from apps.exams.models import Attempt, Choice, Exam, Question


class AttemptGradeTests(TestCase):
    """Автопроверка попытки: один ответ, несколько ответов, пропуск."""

    def setUp(self):
        self.student = User.objects.create_user("s@t.local", "pass12345")
        program = Program.objects.create(name="П", slug="p")
        self.course = Course.objects.create(program=program, title="Курс", slug="kurs",
                                            status=Course.Status.ACTIVE)
        self.enrollment = Enrollment.objects.create(student=self.student, course=self.course)
        self.exam = Exam.objects.create(course=self.course, title="Экзамен", pass_percent=60)

        # Вопрос 1: один правильный (1 балл)
        self.q1 = Question.objects.create(exam=self.exam, order=1, text="1?",
                                          q_type=Question.Type.SINGLE)
        self.c1 = [
            Choice.objects.create(question=self.q1, order=i, text=f"в{i}", is_correct=(i == 2))
            for i in range(1, 5)
        ]
        # Вопрос 2: несколько правильных (2 балла)
        self.q2 = Question.objects.create(exam=self.exam, order=2, text="2?",
                                          q_type=Question.Type.MULTI, points=2)
        self.c2 = [
            Choice.objects.create(question=self.q2, order=i, text=f"в{i}",
                                  is_correct=i in (1, 3))
            for i in range(1, 5)
        ]

    def test_all_correct_is_100(self):
        attempt = Attempt.start_new(self.student, self.exam)
        attempt.finish({
            self.q1.id: {"choices": [self.c1[1].id]},
            self.q2.id: {"choices": [self.c2[0].id, self.c2[2].id]},
        })
        attempt.refresh_from_db()
        self.assertEqual(attempt.score_percent, 100)
        self.assertTrue(attempt.passed)
        self.assertEqual(attempt.points_earned, 3)
        self.assertEqual(attempt.points_max, 3)

    def test_partial_strict_for_multi(self):
        # В multi выбран только один из двух правильных → 0 за вопрос
        attempt = Attempt.start_new(self.student, self.exam)
        attempt.finish({
            self.q1.id: {"choices": [self.c1[1].id]},
            self.q2.id: {"choices": [self.c2[0].id]},
        })
        attempt.refresh_from_db()
        self.assertEqual(attempt.points_earned, 1)
        self.assertEqual(attempt.score_percent, round(1 / 3 * 100))
        self.assertFalse(attempt.passed)

    def test_unanswered_zero_but_finished(self):
        attempt = Attempt.start_new(self.student, self.exam)
        attempt.finish({})
        attempt.refresh_from_db()
        self.assertEqual(attempt.points_earned, 0)
        self.assertEqual(attempt.score_percent, 0)
        self.assertIsNotNone(attempt.finished_at)

    def test_finish_twice_keeps_first(self):
        attempt = Attempt.start_new(self.student, self.exam)
        attempt.finish({self.q1.id: [self.c1[1].id]})
        attempt.finish({self.q1.id: [self.c1[0].id]})  # повтор — игнорируется
        attempt.refresh_from_db()
        self.assertEqual(attempt.points_earned, 1)

    def test_attempts_limit(self):
        self.exam.max_attempts = 1
        self.exam.save()
        Attempt.start_new(self.student, self.exam).finish({})
        with self.assertRaises(PermissionError):
            Attempt.start_new(self.student, self.exam)


class OpenQuestionTests(TestCase):
    """Свободный ответ: ждёт учителя, потом баллы попадают в итог."""

    def setUp(self):
        self.student = User.objects.create_user("s@t.local", "pass12345")
        program = Program.objects.create(name="П", slug="p")
        self.course = Course.objects.create(program=program, title="Курс", slug="kurs")
        Enrollment.objects.create(student=self.student, course=self.course)
        self.exam = Exam.objects.create(course=self.course, title="Экзамен", pass_percent=50)
        self.q_choice = Question.objects.create(
            exam=self.exam, order=1, text="Выбор?", q_type=Question.Type.SINGLE
        )
        self.ok_choice = Choice.objects.create(
            question=self.q_choice, order=1, text="да", is_correct=True
        )
        self.q_open = Question.objects.create(
            exam=self.exam, order=2, text="Расскажите…", q_type=Question.Type.OPEN, points=2
        )

    def test_open_answer_waits_for_teacher(self):
        attempt = Attempt.start_new(self.student, self.exam)
        attempt.finish({
            self.q_choice.id: {"choices": [self.ok_choice.id]},
            self.q_open.id: {"text": "Мой развёрнутый ответ"},
        })
        attempt.refresh_from_db()

        answer = attempt.answers.get(question=self.q_open)
        self.assertTrue(answer.needs_grading)
        self.assertEqual(answer.text, "Мой развёрнутый ответ")
        self.assertTrue(attempt.is_pending_manual)
        self.assertEqual(attempt.status_label, "На проверке учителя")
        # Пока ручной оценки нет — только авточасть (1 из 3 баллов)
        self.assertEqual(attempt.points_earned, 1)

    def test_teacher_grading_finalizes_score(self):
        attempt = Attempt.start_new(self.student, self.exam)
        attempt.finish({
            self.q_choice.id: {"choices": [self.ok_choice.id]},
            self.q_open.id: {"text": "Ответ"},
        })
        answer = attempt.answers.get(question=self.q_open)

        attempt.grade_open_answer(answer, points=2, feedback="Отлично")
        attempt.refresh_from_db()

        self.assertEqual(attempt.points_earned, 3)
        self.assertEqual(attempt.score_percent, 100)
        self.assertTrue(attempt.passed)
        self.assertFalse(attempt.is_pending_manual)

        answer.refresh_from_db()
        self.assertEqual(answer.feedback, "Отлично")

    def test_grading_capped_by_question_points(self):
        attempt = Attempt.start_new(self.student, self.exam)
        attempt.finish({self.q_open.id: {"text": "Ответ"}})
        answer = attempt.answers.get(question=self.q_open)
        attempt.grade_open_answer(answer, points=99)  # больше максимума
        answer.refresh_from_db()
        self.assertEqual(answer.points, 2)  # обрезано до баллов вопроса
