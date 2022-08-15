import logging
from datetime import date, timedelta

from django.conf import settings

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
from django.core.mail import EmailMultiAlternatives
from django.core.management.base import BaseCommand
from django.template.loader import render_to_string
from django_apscheduler.jobstores import DjangoJobStore
from django_apscheduler.models import DjangoJobExecution

from newapp.models import Category, Post

logger = logging.getLogger(__name__)

def my_job():   # наша задача по выводу текста на экран
    # print("My job in runapscheduler")
    # print(Post.objects.get(id=1))

    for category in Category.objects.all():  # выводим каждую категорию
        #  вывод новостей за последнюю неделю в данной категории
        posts = Post.objects.filter(post_date_time__gt=date.today()-timedelta(weeks=1), post_category__category_name=category)
        for user in Category.objects.get(id=category.pk).subscribers.all():
            # получаем наш html
            html_content = render_to_string(
                'post_dispatch_weekly.html',
                {
                    'post': posts,
                    'date': date.today()-timedelta(weeks=1),
                    'user_name': user.username,
                }
            )
            msg = EmailMultiAlternatives(
                subject=f'Новости и статьи по категории {category} c {date.today()-timedelta(weeks=1)}',
                from_email='erzhan.tleu@yandex.ru',  # здесь указываем почту, с которой будете отправлять
                to=[str(user.email)]  # емаил кому отправляем
            )
            msg.attach_alternative(html_content, "text/html")  # добавляем html
            msg.send()  # отсылаем

# функция которая будет удалять неактуальные задачи
def delete_old_job_executions(max_age=604_800):
    """This job deletes all apscheduler job executions older than `max_age` from the database."""
    DjangoJobExecution.objects.delete_old_job_executions(max_age)


class Command(BaseCommand):
    help = "Runs apscheduler."

    def handle(self, *args, **options):
        scheduler = BlockingScheduler(timezone=settings.TIME_ZONE)
        scheduler.add_jobstore(DjangoJobStore(), "default")

        # добавляем работу нашему задачнику
        scheduler.add_job(
            my_job,
            # trigger=CronTrigger(day_of_week="*/mon"), # запускать каждую неделю в понедельник
            # trigger=CronTrigger(hour='*/1'), # для теста, запуск каждый час
            trigger=CronTrigger(minute='*/1'),  # для теста, запуск каждую минуту
            # Тоже самое что и интервал, но задача тригера таким образом более понятна django
            id="my_job",  # уникальный айди
            max_instances=1,
            replace_existing=True,
        )
        logger.info("Added job 'my_job'.")

        scheduler.add_job(
            delete_old_job_executions,
            trigger=CronTrigger(
                day_of_week="mon", hour="00", minute="00"
            ),
            # Каждую неделю будут удаляться старые задачи, которые либо не удалось выполнить, либо уже выполнять не надо.
            id="delete_old_job_executions",
            max_instances=1,
            replace_existing=True,
        )
        logger.info(
            "Added weekly job: 'delete_old_job_executions'."
        )

        try:
            logger.info("Starting scheduler...")
            scheduler.start()
        except KeyboardInterrupt:
            logger.info("Stopping scheduler...")
            scheduler.shutdown()
            logger.info("Scheduler shut down successfully!")