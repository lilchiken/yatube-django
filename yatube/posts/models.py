from django.db import models
from django.db.models import Q, F
from django.contrib.auth import get_user_model

from core.models import CreatedModel

User = get_user_model()


class Group(models.Model):
    title = models.CharField(
        max_length=200,
        verbose_name='Название'
    )
    slug = models.SlugField(
        unique=True,
        verbose_name='Слаг'
    )
    description = models.TextField(
        null=True,
        verbose_name='Описание'
    )

    def __str__(self):
        return self.title


class Post(CreatedModel):
    text = models.TextField(
        verbose_name='Текст',
        help_text='Напишите текст поста'
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        null=True,
        verbose_name='Автор'
    )
    group = models.ForeignKey(
        Group,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        help_text='По желанию, вы можете выбрать группу',
        verbose_name='Группа'
    )
    image = models.ImageField(
        'Картинка',
        upload_to='posts/',
        blank=True
    )

    class Meta:
        ordering = ['-created']
        verbose_name = 'Пост'
        verbose_name_plural = 'Посты'
        default_related_name = 'posts'

    def __str__(self):
        return self.text[:15]


class Comment(CreatedModel):
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        verbose_name='Пост'
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Автор'
    )
    text = models.TextField(
        verbose_name='Текст',
        help_text='Напишите комментарий...'
    )

    class Meta:
        default_related_name = 'comments'


class Follow(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='follower'
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='following'
    )

    # class Meta:
    #     constraints = [
    #         # models.CheckConstraint(
    #         #     name='check_not_follow_yourself',
    #         #     check=models.Q(user=models.Q('author'))
    #         # ),
    #         models.UniqueConstraint(
    #             name='unique_follow',
    #             fields=['user', 'author'],
    #             condition=Q(status='DRAFT')
    #         )
    #     ]
#     не получается :(
