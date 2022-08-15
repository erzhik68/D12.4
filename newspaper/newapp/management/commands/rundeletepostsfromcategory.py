from django.core.management import BaseCommand

from newapp.models import Post, Category


class Command(BaseCommand):
    # показывает подсказку при вводе "python manage.py <ваша команда> --help"
    help = 'delete all posts from the category'
    # напоминать ли о миграциях. Если true — то будет напоминание о том, что не сделаны все миграции (если такие есть)
    requires_migrations_checks = True

    def add_arguments(self, parser):
        parser.add_argument('id_categories', nargs='+', type=int, help='id Category')

    def handle(self, *args, **kwargs):
        # здесь можете писать любой код, который выполнится при вызове вашей команды
        for id_category in kwargs['id_categories']:
            try:
                category = Category.objects.get(pk=id_category)
                # спрашиваем пользователя, действительно ли он хочет удалить все товары из указанной категории
                self.stdout.write(f'Do you really want to delete all products from the category "{category}"? yes/no')
                answer = input()
                if answer == 'yes':  # в случае подтверждения действительно удаляем все товары из указанной категории
                    Post.objects.filter(post_category=category).delete()
                    self.stdout.write(self.style.SUCCESS(f'All posts from the category "{category}" successfully wiped!'))
                    return
                # в случае неправильного подтверждения, говорим, что в доступе отказано
                self.stdout.write(self.style.ERROR('Access denied'))

            except Category.DoesNotExist:
                raise ConnectionError('Category with id = "%s" does not exist' % id_category)
