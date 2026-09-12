"""
Подсчёт итоговой оценки за курс — «мозг» модуля grading.

Формула как на hdat.sa/Tases:
    Экзамен 70%  +  Задания 25%  +  Активность (встречи) 5%  =  максимум 100
    Зачёт курса — от 60 баллов. Провал одного курса не влияет на другие.

Все компоненты считаются «мягко»: нет экзаменов — 0 за экзамен; нет записей
о встречах — начисляется полная активность (студента не наказываем за то,
что учитель не вёл список).
"""
from apps.grading.models import Attendance, Transcript

EXAM_WEIGHT = 70
ASSIGNMENTS_WEIGHT = 25
ACTIVITY_WEIGHT = 5
PASS_THRESHOLD = 60


def compute_course_grade(enrollment) -> dict:
    """Считает компоненты итога для конкретной записи на курс.
    Возвращает словарь: exam / assignments / activity / total / passed."""
    from django.apps import apps

    grade = {
        "exam": 0.0,
        "assignments": 0.0,
        "activity": float(ACTIVITY_WEIGHT),
        "total": 0.0,
        "passed": False,
    }

    # --- Экзамен: лучшая закрытая попытка итогового экзамена (70%) ---
    if apps.is_installed("apps.exams"):
        from apps.exams.models import Exam

        final_exams = Exam.objects.filter(course=enrollment.course, kind=Exam.Kind.FINAL)
        best_percent = 0
        for exam in final_exams:
            best = exam.best_attempt(enrollment.student)
            if best:
                best_percent = max(best_percent, best.score_percent)
        grade["exam"] = round(best_percent / 100 * EXAM_WEIGHT, 1)

    # --- Задания: доля набранных баллов от суммы всех заданий курса (25%) ---
    if apps.is_installed("apps.assignments"):
        from apps.assignments.models import Assignment, Submission

        assignments = Assignment.objects.filter(
            course=enrollment.course, is_published=True
        )
        max_sum = sum(assignments.values_list("max_points", flat=True)) or 0
        if max_sum:
            scored = Submission.objects.filter(
                assignment__in=assignments,
                student=enrollment.student,
                score__isnull=False,
            ).values_list("score", flat=True)
            earned = sum(scored) or 0
            grade["assignments"] = round(
                min(float(earned), float(max_sum)) / float(max_sum) * ASSIGNMENTS_WEIGHT, 1
            )

    # --- Активность: доля посещённых встреч (5%) ---
    total_meetings = enrollment.attendance.count()
    if total_meetings:
        present = enrollment.attendance.filter(present=True).count()
        grade["activity"] = round(present / total_meetings * ACTIVITY_WEIGHT, 1)

    grade["total"] = round(
        grade["exam"] + grade["assignments"] + grade["activity"], 1
    )
    grade["passed"] = grade["total"] >= PASS_THRESHOLD
    return grade


def issue_transcript(enrollment) -> Transcript:
    """Создаёт (или обновляет) академическую выписку по текущим баллам."""
    grade = compute_course_grade(enrollment)
    transcript, _ = Transcript.objects.update_or_create(
        enrollment=enrollment,
        defaults={
            "student_name": str(enrollment.student),
            "course_title": enrollment.course.title,
            "exam_points": grade["exam"],
            "assignment_points": grade["assignments"],
            "activity_points": grade["activity"],
            "total_points": grade["total"],
            "passed": grade["passed"],
        },
    )
    return transcript
