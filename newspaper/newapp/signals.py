from datetime import date, timedelta

from django.core.mail import EmailMultiAlternatives
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.template.loader import render_to_string

from .models import Post, Category


# в декоратор передаётся первым аргументом сигнал, на который будет реагировать эта функция,
# и в отправители надо передать также модель
@receiver(post_save, sender=Post)
# создаём функцию обработчик с параметрами под регистрацию сигнала
def notify_users_post(sender, instance, created, **kwargs):
    post = Post.objects.get(id=instance.id)
    # выводим категорию для текущей новости
    for cat in post.post_category.all():
        category_for_subsc_users = Category.objects.get(id=cat.id)
        # выводим список пользователей подписанных на данную категорию
        for user in category_for_subsc_users.subscribers.all():
            # получаем наш html
            html_content = render_to_string(
                'post_dispatch.html',
                {
                    'post': instance,
                    'user_name': user.username,
                }
            )
            msg = EmailMultiAlternatives(
                subject=instance.post_title,
                # body=f'{post.post_text} \n Здравствуй, {user.username}. Новая статья в твоем любимом разделе!',
                from_email='erzhan.tleu@yandex.ru',  # здесь указываем почту, с которой будете отправлять
                to=[str(user.email)]  # емаил кому отправляем
            )
            msg.attach_alternative(html_content, "text/html")  # добавляем html
            msg.send()  # отсылаем
# коннектим наш сигнал к функции обработчику и указываем, к какой именно модели после сохранения привязать функцию
# post_save.connect(notify_users_post, sender=Post) # теперь вместо него будем использовать декоратор @receiver
