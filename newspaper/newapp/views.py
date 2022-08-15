# print(data.__dict__) чтоб узнать все варианты
import logging

from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django import forms
from django.core.cache import cache

from django.http import request, HttpResponse, HttpResponseRedirect
from django.shortcuts import render, redirect
from django.views.generic import ListView, UpdateView, CreateView, DetailView, \
    DeleteView  # импортируем класс, который говорит нам о том, что в этом представлении мы будем выводить список объектов из БД

from .models import Post, Author, Category
from .filters import PostFilter  # импортируем фильтр
from .forms import PostForm  # импортируем нашу форму

from datetime import datetime, date


class PostsList(LoginRequiredMixin, ListView):
    model = Post  # указываем модель, объекты которой мы будем выводить
    template_name = 'posts.html'  # указываем имя шаблона, в котором будет лежать HTML, в нём будут все инструкции о том, как именно пользователю должны вывестись наши объекты
    context_object_name = 'posts'  # это имя списка, в котором будут лежать все объекты, его надо указать, чтобы обратиться к самому списку объектов через HTML-шаблон
    ordering = ['-id']
    paginate_by = 5  # поставим постраничный вывод в один элемент

    # form_class = PostForm # добавляем форм класс, чтобы получать доступ к форме через метод POST

    # метод get_context_data нужен нам для того, чтобы мы могли передать переменные в шаблон. В возвращаемом словаре context будут храниться все переменные. Ключи этого словари и есть переменные, к которым мы сможем потом обратиться через шаблон
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)  # получили весь контекст из класса-родителя
        context['time_now'] = datetime.utcnow()  # добавим переменную текущей даты time_now
        #        context['value1'] = None  # добавим ещё одну пустую переменную, чтобы на её примере посмотреть работу другого фильтра
        context['filter'] = PostFilter(self.request.GET, queryset=self.get_queryset())  # вписываем наш фильтр в контекст
        #        context['form'] = PostForm()
        context['is_not_authors'] = not self.request.user.groups.filter(name='authors').exists()  # добавили новую контекстную переменную is_not_authors
        return context

    # def post(self, request, *args, **kwargs):
    #     form = self.form_class(request.POST) # создаём новую форму, забиваем в неё данные из POST-запроса
    #     if form.is_valid(): # если данные в форме ввели всё правильно, то сохраняем новый пост
    #         form.save()
    #     return super().get(request, *args, **kwargs)


class PostsSearch(ListView):
    model = Post
    template_name = 'newapp/search.html'
    context_object_name = 'posts'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['filter'] = PostFilter(self.request.GET,
                                       queryset=self.get_queryset())  # вписываем наш фильтр в контекст
        return context

# создаём представление, в котором будут детали конкретной отдельной новости
# class PostDetail(DetailView):
#     model = Post # модель всё та же, но мы хотим получать детали конкретной отдельной новости
#     template_name = 'post.html' # название шаблона будет post.html
#     context_object_name = 'post' # название поста

# дженерик для получения деталей о товаре
class PostDetailView(DetailView):
    model = Post
    template_name = 'newapp/post_detail.html'
    context_object_name = 'post'

    #  queryset = Post.objects.all() # Если предоставлено, значение queryset заменяет значение, предоставленное для model

    # пишем функцию, чтоб ввести доп параметр is_not_subscribed для contextа.
    # Используем в шаблоне, если пользователь подписан на категорию данной новости, то кнопка не видна.
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        for cat in context['post'].post_category.all():
            c = Category.objects.get(id=cat.id)
            context['is_not_subscribed'] = not c.subscribers.filter(username=self.request.user.username).exists()
        return context

    def get_object(self, *args, **kwargs): # переопределяем метод получения объекта, как ни странно
        obj = cache.get(f'post-{self.kwargs["pk"]}', None) # кэш очень похож на словарь, и метод get действует также.
        # Он забирает значение по ключу, если его нет, то забирает None.

        # если объекта нет в кэше, то получаем его и записываем в кэш
        if not obj:
            obj = super().get_object(queryset=self.queryset)
            cache.set(f'post-{self.kwargs["pk"]}', obj)

        return obj

# дженерик для создания поста. Указываем имя шаблона и класс формы.
class PostCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    logging.info('>>>>>>>>>>>>some message<<<<<<<<<<<<<<<<<')
    model = Post
    template_name = 'newapp/post_create.html'
    form_class = PostForm
    permission_required = ('newapp.add_post',)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # context['form'] = PostForm
        return context

    def form_valid(self, PostForm):
        self.object = PostForm.save(commit=False)
        new_author, created = Author.objects.get_or_create(
            author_user=self.request.user
        )
        self.object.post_author = new_author
        # self.object.post_author = Author.objects.get(author_user=self.request.user)
        if Post.objects.filter(post_date_time__date=date.today(), post_author__author_user__username=self.request.user).count() < 3:
            self.object = PostForm.save()
            return super().form_valid(PostForm)
        else:
            return HttpResponseRedirect('/')

# дженерик для редактирования поста
class PostUpdateView(PermissionRequiredMixin, UpdateView):
    template_name = 'newapp/post_create.html'
    form_class = PostForm
    permission_required = ('newapp.change_post',)

    # метод get_object используем вместо queryset, чтобы получить информацию о посте к-рый мы собираемся редактировать
    def get_object(self, **kwargs):
        id = self.kwargs.get('pk')
        return Post.objects.get(pk=id)

# дженерик для удаления поста
class PostDeleteView(PermissionRequiredMixin, DeleteView):
    template_name = 'newapp/post_delete.html'
    queryset = Post.objects.all()
    success_url = '/posts/'
    permission_required = ('newapp.delete_post',)


# подписываем пользователя на категорию новостей
@login_required
def subscribe_me(request, pk=0):
    post = Post.objects.get(id=pk)
    for cat in post.post_category.all():
        c = Category.objects.get(id=cat.id)
        if not c.subscribers.filter(username=request.user.username).exists():
            c.subscribers.add(request.user)
    return redirect('/')
