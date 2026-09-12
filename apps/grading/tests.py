"""Тесты подсчёта итоговой оценки (70/25/5, порог 60)."""
from django.test import TestCase
from django.utils import timezone

from apps.accounts.models import User
from apps.assignments.models import Assignment, Submission
from apps.courses.models import Course, Enrollment, Program
from apps.exams.models import Attempt, Choice, Exam, Question
from apps.grading.models import Attendance
from apps.grading.services import compute_course_grade


class GradeCalcTests(TestCase):
    def setUp(self):
        self.student = User.objects.create_user("s@t.local", "pass12345")
        program = Program.objects.create(name="П", slug="p")
        self.course = Course.objects.create(program=program, title="Курс", slug="kurs",
                                            status=Course.Status.ACTIVE)
        self.enrollment = Enrollment.objects.create(student=self.student, course=self.course)

        self.exam = Exam.objects.create(course=self.course, title="Экзамен")
        q = Question.objects.create(exam=self.exam, order=1, text="1?")
        self.ok = Choice.objects.create(question=q, order=1, text="да", is_correct=True)
        Choice.objects.create(question=q, order=2, text="нет", is_correct=False)

        self.a1 = Assignment.objects.create(course=self.course, week=1, title="З1",
                                            description="д", max_points=5)
        self.a2 = Assignment.objects.create(course=self.course, week=2, title="З2",
                                            description="д", max_points=5)

    def _pass_exam(self, choice_ids):
        attempt = Attempt.start_new(self.student, self.exam)
        attempt.finish({self.exam.questions.first().id: {"choices": choice_ids}})
        return attempt

    def test_empty_course_gives_only_activity(self):
        # Нет экзамена, нет оценённых заданий, нет встреч: активность 5, итог 5
        grade = compute_course_grade(self.enrollment)
        self.assertEqual(grade["exam"], 0)
        self.assertEqual(grade["assignments"], 0)
        self.assertEqual(grade["activity"], 5)
        self.assertEqual(grade["total"], 5)
        self.assertFalse(grade["passed"])

    def test_full_math(self):
        # Экзамен 100% → 70; задания 3 из 10 баллов → 7.5; встречи 1 из 2 → 2.5
        self._pass_exam([self.ok.id])
        Submission.objects.create(assignment=self.a1, student=self.student, text="x", score=2)
        Submission.objects.create(assignment=self.a2, student=self.student, text="x", score=1)
        Attendance.objects.create(enrollment=self.enrollment, date="2026-09-01", present=True)
        Attendance.objects.create(enrollment=self.enrollment, date="2026-09-08", present=False)

        grade = compute_course_grade(self.enrollment)
        self.assertEqual(grade["exam"], 70)
        self.assertEqual(grade["assignments"], 7.5)
        self.assertEqual(grade["activity"], 2.5)
        self.assertEqual(grade["total"], 80)
        self.assertTrue(grade["passed"])

    def test_threshold_at_60(self):
        self._pass_exam([self.ok.id])  # экзамен 100% → 70 баллов
        grade = compute_course_grade(self.enrollment)
        self.assertEqual(grade["total"], 75)  # 70 + 0 + 5
        self.assertTrue(grade["passed"])

    def test_best_attempt_counts(self):
        self.exam.max_attempts = 2
        self._pass_exam([])  # первая — 0%
        self._pass_exam([self.ok.id])  # вторая — 100%
        grade = compute_course_grade(self.enrollment)
        self.assertEqual(grade["exam"], 70)
