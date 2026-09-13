"""
Заполнение платформы демонстрационными данными:

    python manage.py seed_demo [--admin-email ...] [--admin-pass ...]

Создаёт: контакты сайта, программу «Коралловые холмы» с курсами и уроками,
экзамен с вопросами, задания, библиотеку, новости, FAQ, демо-студента.
Администратора создаёт, только если пользователей ещё нет.

Повторный запуск безопасен: существующие записи обновляются (get_or_create).
"""
import random
from datetime import date, datetime, timedelta
from pathlib import Path

from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.accounts.models import User
from apps.assignments.models import Assignment
from apps.books.models import Book
from apps.core.models import SiteInfo
from apps.courses.models import Course, Enrollment, Lesson, LessonProgress, Program
from apps.exams.models import Attempt, Choice, Exam, Question
from apps.grading.models import Attendance
from apps.library.models import Category, Item
from apps.news.models import FAQ, Post


def _demo_pdf(title: str) -> ContentFile:
    """Собирает минимальный корректный PDF-файл (одна страница с заголовком).

    Нужен, чтобы демо-библиотека выглядела правдоподобно: настоящие PDF
    учитель загрузит сам через админку.
    """
    text = title.encode("ascii", "replace").decode()
    stream = f"BT /F1 22 Tf 72 770 Td ({text}) Tj ET".encode()
    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] /Contents 4 0 R "
        b"/Resources << /Font << /F1 5 0 R >> >> >>",
        b"<< /Length " + str(len(stream)).encode() + b" >>\nstream\n" + stream + b"\nendstream",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
    ]
    out = bytearray(b"%PDF-1.4\n")
    offsets = []
    for number, body in enumerate(objects, start=1):
        offsets.append(len(out))
        out += f"{number} 0 obj\n".encode() + body + b"\nendobj\n"
    xref_at = len(out)
    out += b"xref\n0 " + str(len(objects) + 1).encode() + b"\n0000000000 65535 f \n"
    for offset in offsets:
        out += f"{offset:010d} 00000 n \n".encode()
    out += (
        b"trailer\n<< /Size " + str(len(objects) + 1).encode()
        + b" /Root 1 0 R >>\nstartxref\n" + str(xref_at).encode() + b"\n%%EOF"
    )
    return ContentFile(bytes(out), name="demo.pdf")


class Command(BaseCommand):
    help = "Заполнить платформу демонстрационными данными"

    def add_arguments(self, parser):
        parser.add_argument("--admin-email", default="admin@academy.local")
        parser.add_argument("--admin-pass", default="admin12345")

    def handle(self, *args, **options):
        self.stdout.write("Наполняю платформу демо-данными…")

        # --- Контакты сайта ---------------------------------------------------
        SiteInfo.objects.update_or_create(
            pk=1,
            defaults={
                "site_name": "Академия Ибн Усаймина",
                "tagline": "Дистанционное изучение шариатских наук по книгам с сопровождением",
                "whatsapp": "998901234567",
                "telegram": "ibn_usaymin_academy",
                "email": "info@academy.local",
                "about_footer": "Образовательная платформа: курсы по книгам, уроки, "
                                "задания и экзамены с проверкой знаний.",
                "submissions_via_messengers": True,  # демо: резервная сдача через мессенджеры
                "show_books": True,                 # раздел книг включён
                "payment_details": "8600 1234 5678 9012 — Академия (Uzcard)\n"
                                   "Чек присылайте на WhatsApp поддержки.",
                "show_donations": True,
                "donations_details": "8600 1234 5678 9012 — поддержка проекта",
            },
        )

        # --- Администратор ----------------------------------------------------
        if not User.objects.filter(is_superuser=True).exists():
            User.objects.create_superuser(
                email=options["admin_email"], password=options["admin_pass"],
                first_name="Администратор",
            )
            self.stdout.write(self.style.SUCCESS(
                f"Администратор: {options['admin_email']} / {options['admin_pass']} "
                "(смените пароль!)"
            ))

        # --- Факультеты (программы) и курсы ------------------------------------
        program, _ = Program.objects.update_or_create(
            slug="korallrovye-kholmy",
            defaults={
                "name": "Факультет акыды",
                "summary": "Коралловые холмы — положения о джиннах",
                "description": "Полный разбор книги «Акамуль-марджан фи ахкамиль-джан» "
                               "Кады аш-Шибли: сотворение, виды, способности, "
                               "взаимодействие с людьми и защита от них. "
                               "Каждая часть — отдельный курс с уроками, заданиями "
                               "и итоговым экзаменом.",
                "order": 1,
            },
        )

        course_data = [
            ("Введение в мир джиннов", "Часть 1", Course.Status.FINISHED),
            ("Сотворение и природа джиннов", "Часть 2", Course.Status.FINISHED),
            ("Виды и разновидности джиннов", "Часть 3", Course.Status.FINISHED),
            ("Обиталища и животные джиннов", "Часть 4", Course.Status.ACTIVE),
            ("Джинны и люди: взаимодействие", "Часть 5", Course.Status.REGISTRATION),
            ("Колдовство и защита от джиннов", "Часть 6", Course.Status.SOON),
            ("Путь к спасению: этапы испытаний", "Часть 7", Course.Status.SOON),
        ]
        courses = {}
        for order, (title, book_part, status) in enumerate(course_data, start=1):
            slug = f"dzhinny-chast-{order}"
            courses[order], _ = Course.objects.update_or_create(
                slug=slug,
                defaults={
                    "program": program,
                    "title": title,
                    "book": f"«Коралловые холмы», {book_part}",
                    "author": "Кады аш-Шибли",
                    "summary": f"{title}: уроки с разбором текста книги, конспектами "
                               f"и проверкой знаний.",
                    "status": status,
                    "order": order,
                    "start_date": date(2026, 8, 3) + timedelta(days=7 * (order - 1)),
                    "end_date": date(2026, 8, 3) + timedelta(days=7 * order),
                },
            )
        # курс с открытой регистрацией — корректные даты окна
        courses[5].registration_start = date(2026, 9, 7)
        courses[5].registration_end = date(2026, 9, 30)
        courses[5].start_date = date(2026, 10, 1)
        courses[5].end_date = date(2026, 11, 20)
        courses[5].save(update_fields=["registration_start", "registration_end",
                                        "start_date", "end_date"])

        # --- Другие факультеты: арабский язык и фикх (курсы скоро) -------------
        other_faculties = [
            ("fakultet-arabskogo-yazyka", "Факультет арабского языка",
             "От алфавита до свободного чтения книг",
             "Основы арабского языка: алфавит, чтение, грамматика (нахв) и морфология "
             "(сарф) — с опорой на классические учебные тексты.", 2,
             [("Чтение и письмо: первый уровень", "«Мадина», том 1")]),
            ("fakultet-fikha", "Факультет фикха",
             "Практические положения шариата по мазхабу",
             "Пошаговое изучение фикха: очищение, молитва, пост, закят и хадж — "
             "по классическим трудам с разбором доказательств.", 3,
             [("Очищение и молитва", "«Уmdat-ul-ahkam», раздел 1")]),
        ]
        for slug, name, summary, description, order, course_rows in other_faculties:
            faculty, _ = Program.objects.update_or_create(
                slug=slug,
                defaults={"name": name, "summary": summary,
                          "description": description, "order": order},
            )
            for c_order, (c_title, c_book) in enumerate(course_rows, start=1):
                course, _ = Course.objects.update_or_create(
                    slug=f"{slug}-kurs-{c_order}",
                    defaults={
                        "program": faculty,
                        "title": c_title,
                        "book": c_book,
                        "author": "",
                        "summary": f"{c_title}: курс факультета «{name}».",
                        "status": Course.Status.ACTIVE if slug.startswith("fakultet-arabskogo")
                                  else Course.Status.SOON,
                        "is_free": slug.startswith("fakultet-arabskogo"),  # демо свободного курса
                        "order": c_order,
                    },
                )
                # Свободному курсу — пара уроков, чтобы можно было пройти
                if course.is_free:
                    Lesson.objects.update_or_create(
                        course=course, order=1,
                        defaults={
                            "week": 1, "title": "Алфавит: 28 букв",
                            "summary": "Первый урок свободного курса.",
                            "content": "Разбор алфавита с примерами. Конспект открыт всем "
                                       "зарегистрированным — свободный доступ.",
                        },
                    )
                    Lesson.objects.update_or_create(
                        course=course, order=2,
                        defaults={
                            "week": 1, "title": "Соединение букв и огласовки",
                            "summary": "Учимся читать слоги.",
                            "content": "Практика чтения слогов и первых слов.",
                        },
                    )

        # --- Уроки активного курса ---------------------------------------------
        lesson_titles = [
            "Понятие обиталищ джиннов в шариате",
            "Пустыни, развалины и заброшенные места",
            "Джинны и вода: колодцы и моря",
            "Животные, связанные с джиннами",
            "Дом человека и правила входа",
            "Мечети и места поклонения",
            "Как обезопасить своё жилище",
            "Обобщение части и ответы на вопросы",
        ]
        active_course = courses[4]
        for order, title in enumerate(lesson_titles, start=1):
            Lesson.objects.update_or_create(
                course=active_course,
                order=order,
                defaults={
                    "week": (order - 1) // 2 + 1,
                    "title": title,
                    "summary": "Разбор соответствующего раздела книги с опорой "
                               "на коранические аяты и достоверные хадисы.",
                    "content": "Конспект урока появится здесь. Учитель заполняет его "
                               "в админке: текст, видео, аудио и PDF-файл.",
                },
            )

        # --- Экзамен по активному курсу -----------------------------------------
        exam, _ = Exam.objects.update_or_create(
            course=active_course,
            kind=Exam.Kind.FINAL,
            defaults={
                "title": "Итоговый экзамен: обиталища джиннов",
                "description": "Проверка знаний по части 4 книги «Коралловые холмы».",
                "time_limit_min": 30,
                "max_attempts": 3,
                "pass_percent": 60,
            },
        )
        questions = [
            ("Из чего сотворены джинны?", "single",
             [("Из света", False), ("Из огня", True), ("Из глины", False), ("Из воды", False)]),
            ("Какие из перечисленных мест достоверно связаны с обитанием джиннов?", "multi",
             [("Пустыни", True), ("Развалины", True), ("Мечети", False), ("Колодцы", True)]),
            ("Что рекомендуется говорить при входе в дом, чтобы не вредили джинны?", "single",
             [("Бисмиллях", True), ("Альхамдулиллях", False), ("Астагфируллах", False)]),
            ("Джинны видят нас, а мы их не видим — это:", "single",
             [("Проявление их природы", True), ("Выдумка", False), ("Колдовство", False)]),
            ("Какие средства защиты от джиннов достоверны?", "multi",
             [("Аяты «Аль-Курси»", True), ("Обереги и талисманы", False),
              ("Утренние и вечерние азкары", True), ("Соль на пороге", False)]),
            ("Опишите своими словами, как обезопасить дом по сунне "
             "(свободный ответ — проверит учитель)", "open", []),
        ]
        for order, (text, q_type, choices) in enumerate(questions, start=1):
            question, _ = Question.objects.update_or_create(
                exam=exam, order=order,
                defaults={"text": text, "q_type": q_type, "points": 1},
            )
            Choice.objects.filter(question=question).delete()
            for c_order, (c_text, is_correct) in enumerate(choices, start=1):
                Choice.objects.create(
                    question=question, order=c_order, text=c_text, is_correct=is_correct
                )

        # --- Задания --------------------------------------------------------------
        assignment_data = [
            (1, "Составить конспект: три категории обиталищ", "Выпишите из текста книги "
             "категории мест, связанных с джиннами, с указанием источника каждого вывода."),
            (2, "Хадисы о запрете справлять нужду в ямы", "Найдите и выпишите хадисы темы, "
             "укажите степень достоверности по комментариям шейха."),
            (3, "Практика: азкары входа в дом", "Составьте порядок азкаров входа в дом "
             "со ссылками на источники."),
        ]
        for week, title, description in assignment_data:
            Assignment.objects.update_or_create(
                course=active_course, week=week,
                defaults={
                    "title": title,
                    "description": description,
                    "max_points": 5,
                    # Дедлайны — от текущего дня, чтобы демо всегда показывало
                    # живые бейджи «осталось меньше суток / 2 дня / …».
                    "due_at": timezone.now() + timedelta(days=week + 1, hours=3),
                },
            )

        # --- Библиотека --------------------------------------------------------------
        # Слаги — только латиницей: они попадают в адрес страницы (/library/<slug>/)
        lib = [
            ("Акыда", "akida", [("Три основы (краткий вариант)", "pdf"),
                                ("Книга таухида — главные темы", "pdf")]),
            ("Хадисы", "hadisy", [("Сорок хадисов ан-Навави — содержание", "pdf"),
                                  ("Методика работы с текстом хадиса", "pdf")]),
            ("Фикх", "fikh", [("Очищение: базовые положения", "pdf")]),
            ("Сира", "sira", [("Жизнеописание Пророка ﷺ — хронология", "pdf")]),
            ("Адаб", "adab", [("Адаб требующего знания", "pdf")]),
        ]
        for order, (cat_name, cat_slug, items) in enumerate(lib, start=1):
            category, _ = Category.objects.update_or_create(
                slug=cat_slug,
                defaults={"name": cat_name, "order": order},
            )
            for title, item_type in items:
                item, _ = Item.objects.update_or_create(
                    category=category, title=title,
                    defaults={
                        "item_type": item_type,
                        "description": "Демонстрационный материал. Замените настоящим "
                                       "файлом через админку.",
                        "views": random.randint(3, 96),
                    },
                )
                if not item.file:
                    item.file.save(f"{title[:40]}.pdf", _demo_pdf(title), save=True)

        # --- Книги: три полки — бесплатные, онлайн, продаются ------------------
        demo_books = [
            ("paid", "Коралловые холмы. О положениях, касающихся джиннов", "Кады аш-Шибли",
             "Полный перевод книги с комментариями — та, по которой идёт факультет акыды.",
             "65 000 сум", ""),
            ("paid", "Сборник уроков по акиде", "преподаватели академии",
             "Конспекты уроков факультета акыды в одном издании.", "45 000 сум", ""),
            ("free", "Три основы (краткий вариант)", "",
             "Классический трактат для начинающих — раздаем свободно.", "Бесплатно",
             "https://example.com/tri-osnovy.pdf"),
            ("online", "Сорок хадисов ан-Навави — текст с огласовками", "",
             "Чтение прямо в браузере, с разметкой для заучивания.", "Онлайн",
             "https://example.com/40-hadisov"),
        ]
        for order, (kind, title, author, description, price, read_url) in enumerate(demo_books, start=1):
            Book.objects.update_or_create(
                title=title,
                defaults={
                    "kind": kind,
                    "author": author,
                    "description": description,
                    "price": price,
                    "read_url": read_url,
                    "order_pub": order,
                    "is_published": True,
                },
            )

        # --- Онлайн-встречи ------------------------------------------------------
        if True:
            from apps.meetings.models import Meeting

            meeting_data = [
                ("Вопросы и ответы по части 4", timezone.now() + timedelta(days=2),
                 "Научная встреча: разбор сложных вопросов книги. Подключение по ссылке."),
                ("Вводная встреча части 5", timezone.now() + timedelta(days=9),
                 "Знакомство с планом курса «Джинны и люди: взаимодействие»."),
                ("Итоги месяца", timezone.now() - timedelta(days=5),
                 "Разбор типичных ошибок в заданиях, ответы на вопросы студентов."),
            ]
            for title, starts_at, description in meeting_data:
                Meeting.objects.update_or_create(
                    title=title, starts_at=starts_at,
                    defaults={
                        "course": active_course,
                        "description": description,
                        "duration_min": 60,
                        "link": "https://meet.google.com/demo-link",
                    },
                )

        # --- Новости -------------------------------------------------------------------
        posts = [
            ("Открыта регистрация на часть 5 «Джинны и люди»",
             "Регистрация на пятую часть курса «Коралловые холмы» открыта с 7 сентября. "
             "Записаться можно до 30 сентября — кнопка «Записаться» на странице курса."),
            ("Идёт обучение по части 4 «Обиталища и животные джиннов»",
             "Четвёртая часть курса в разгаре: еженедельные уроки, задания и итоговый "
             "экзамен в конце. Успевайте выполнять задания до дедлайна."),
            ("Платформа запущена",
             "Академия Ибн Усаймина начинает работу: программа по книге «Коралловые холмы», "
             "библиотека материалов и проверка знаний. Добро пожаловать на обучение."),
        ]
        for order, (title, body) in enumerate(posts):
            Post.objects.update_or_create(
                slug=f"news-{order + 1}",
                defaults={
                    "title": title,
                    "excerpt": body[:180],
                    "body": body,
                    "published_at": timezone.make_aware(
                        datetime(2026, 9, 1) + timedelta(days=order * 4)
                    ),
                    "is_published": True,
                },
            )

        # --- FAQ -----------------------------------------------------------------------
        faqs = [
            ("Сколько стоит обучение?",
             "Стоимость и условия каждого курса публикуются на его странице в окно "
             "регистрации. Курсы со статусом «Свободный доступ» открыты всем "
             "зарегистрированным без зачисления."),
            ("Нужно ли проходить курсы по порядку?", "Нет. Регистрация открывается "
             "последовательно, но порядок изучения свободный — начинайте с доступного."),
            ("Выдаётся ли сертификат?", "Сертификат не выдаётся. Вместо него — академическая "
             "выписка с оценками, доступная для печати."),
            ("Как выставляется итог?", "Экзамен 70% + задания 25% + посещение встреч 5%. "
             "Порог зачёта — 60 баллов из 100."),
            ("Что делать, если не сдал курс?", "Ничего страшного: провал одного курса "
             "не влияет на остальные. Можно перезаписаться и пройти заново."),
            ("Как связаться с поддержкой?", "Через WhatsApp или Telegram — контакты "
             "на странице «Контакты»."),
        ]
        for order, (question, answer) in enumerate(faqs, start=1):
            FAQ.objects.update_or_create(
                question=question, defaults={"answer": answer, "order": order}
            )

        # --- Демо-студент с прогрессом ------------------------------------------------------
        student, created = User.objects.get_or_create(
            email="student@demo.local",
            defaults={"first_name": "Ясин", "last_name": "Ахмадов", "password": "!!"},
        )
        if created:
            student.set_password("student12345")
            student.save()
            self.stdout.write(self.style.SUCCESS(
                "Демо-студент: student@demo.local / student12345"
            ))

        enrollment, _ = Enrollment.objects.get_or_create(
            student=student, course=active_course
        )
        first_lessons = active_course.lessons.order_by("order")[:3]
        for lesson in first_lessons:
            LessonProgress.objects.get_or_create(enrollment=enrollment, lesson=lesson)
        Attendance.objects.get_or_create(
            enrollment=enrollment, date=date(2026, 9, 1), defaults={"present": True}
        )
        Attendance.objects.get_or_create(
            enrollment=enrollment, date=date(2026, 9, 8), defaults={"present": True}
        )

        # --- Форум: разделы и демо-темы -----------------------------------------
        from apps.forum.models import Board, Post as ForumPost, Thread

        forum_boards = [
            ("Статьи", "stati", "Разборы и переводы от преподавателей", 1),
            ("Вопросы и ответы", "voprosy-i-otvety", "Спрашивайте — отвечаем по мере сил", 2),
            ("Общий раздел", "obshchiy", "Знакомства, новости и всё остальное", 3),
        ]
        for name, slug, description, order in forum_boards:
            Board.objects.update_or_create(
                slug=slug, defaults={"name": name, "description": description, "order": order},
            )

        teacher_user = User.objects.filter(is_staff=True).first()
        thread_main, _ = Thread.objects.update_or_create(
            title="Правила форума: адаб и модерация",
            defaults={
                "board": Board.objects.get(slug="stati"),
                "author": teacher_user,
                "body": "Ассаляму алейкум ва рахматуллах.\n\n"
                        "1. Пишем с адабом, без споров ради спора.\n"
                        "2. Даём далили (доказательства) там, где говорим о шариате.\n"
                        "3. Темы обычных пользователей публикуются после проверки.\n\n"
                        "БаракаЛлаху фикум!",
                "is_approved": True, "is_pinned": True,
            },
        )
        Thread.objects.update_or_create(
            title="Как совмещать учёбу с работой?",
            defaults={
                "board": Board.objects.get(slug="voprosy-i-otvety"),
                "author": student,
                "body": "Работаю до вечера. Как правильно распределить время на чтение "
                        "недельной нормы книги и заданий?",
                "is_approved": True,
            },
        )
        ForumPost.objects.update_or_create(
            thread=thread_main, author=teacher_user,
            defaults={"body": "Добавлю: реклама и сторонние ссылки удаляются без обсуждения."},
        )

        # --- Оплата: демо-счёт с рассрочкой для студента ------------------------
        from apps.payments.models import Invoice

        invoice, created = Invoice.objects.get_or_create(
            student=student, title="Оплата семестра (демо)",
            defaults={
                "kind": Invoice.Kind.TUITION,
                "course": active_course,
                "total": 1_000_000,
                "note": "Рассрочка на 3 части. Реквизиты — в блоке выше.",
                "is_active": True,
            },
        )
        if created or not invoice.installments.exists():
            invoice.create_schedule(3)

        self.stdout.write(self.style.SUCCESS("Готово! Откройте http://127.0.0.1:8000/"))
