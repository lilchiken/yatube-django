from django.test import TestCase

from posts.models import Group, Post, User


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='Тестовый слаг',
            description='Тестовое описание',
        )
        user = User.objects.last()
        cls.post = Post.objects.create(
            author=user,
            text='Тестовый пост, где больше 15 символов',
        )

    def test_models_have_correct_object_names(self):
        models_str = {
            PostModelTest.post.text[:15]: PostModelTest.post,
            PostModelTest.group.title: PostModelTest.group
        }
        for attr, expected_value in models_str.items():
            with self.subTest(attr=attr):
                self.assertEqual(
                    str(expected_value), attr
                )

    def test_post_have_correct_verbose_name(self):
        post = PostModelTest.post
        field_verboses = {
            'text': 'Текст',
            'author': 'Автор',
            'group': 'Группа'
        }
        for field, excepted_value in field_verboses.items():
            with self.subTest(field=field):
                self.assertEqual(
                    post._meta.get_field(field).verbose_name, excepted_value
                )

    def test_post_have_correct_help_text(self):
        post = PostModelTest.post
        field_help_texts = {
            'text': 'Напишите текст поста',
            'group': 'По желанию, вы можете выбрать группу'
        }
        for field, excepted_value in field_help_texts.items():
            with self.subTest(field=field):
                self.assertEqual(
                    post._meta.get_field(field).help_text, excepted_value
                )
