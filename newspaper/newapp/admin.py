from django.contrib import admin
from .models import Author, Category, Post, PostCategory, Comment, Subscriber

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    '''Категории'''
    list_display = ('id', 'category_name', 'get_subscribers')

    def get_subscribers(self, obj):
        return "\n".join([s.username for s in obj.subscribers.all()])

@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    '''Новость или статья'''
    list_display = ('id', 'post_type', 'post_author', 'get_category', 'post_date_time', 'post_title', 'post_text', 'post_rating')
    list_display_links = ('id', 'post_title',)

    # for ManyToManyField fields we create a custom method and add that method's name to list_display
    # OR define a model method and use that, see the comments in class Post file models.py
    def get_category(self, obj):
        return "\n".join([cat.category_name for cat in obj.post_category.all()])

admin.site.register(Author)
admin.site.register(Subscriber)
admin.site.register(PostCategory)
admin.site.register(Comment)
