import tempfile
import shutil

from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.cache import cache
from django.core.paginator import Page
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django.conf import settings
from django import forms

from posts.models import Post, Group, User, Comment, Follow

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)
EXAMPLE_SMALL_GIF = (
    b'\x47\x49\x46\x38\x39\x61\x02\x00'
    b'\x01\x00\x80\x00\x00\x00\x00\x00'
    b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
    b'\x00\x00\x00\x2C\x00\x00\x00\x00'
    b'\x02\x00\x01\x00\x00\x02\x02\x0C'
    b'\x0A\x00\x3B'
)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostPagesTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.small_gif = SimpleUploadedFile(name='small.gif',
                                           content=EXAMPLE_SMALL_GIF,
                                           content_type='image/gif')
        cls.user = User.objects.create_user(username='test')
        cls.user_for_follow = User.objects.create_user(username='follower')
        cls.group = Group.objects.create(
            title='test group',
            slug='test'
        )
        cls.post = Post.objects.create(
            text='test text',
            author=PostPagesTest.user,
            group=PostPagesTest.group,
            image=PostPagesTest.small_gif
        )
        cls.TEMPLATES_PAGES_NAMES = {
            reverse('posts:group_list', kwargs={
                'slug': PostPagesTest.group.slug
            }): 'posts/group_list.html',
            reverse('posts:post_detail', kwargs={
                'post_id': PostPagesTest.post.id
            }): 'posts/post_id.html',
            reverse('posts:profile', kwargs={
                'username': PostPagesTest.user.username
            }): 'posts/profile.html'
        }
        cls.TEMPLATES_FORMS_PAGES = {
            reverse('posts:post_edit', kwargs={
                'post_id': PostPagesTest.post.id
            }): 'posts/post_create.html',
            reverse('posts:post_create'): 'posts/post_create.html',
        }

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(PostPagesTest.user)
        cache.clear()

    def tearDown(self):
        cache.clear()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    @staticmethod
    def set_dict(obj: Client.get) -> dict:
        attrs = {
            obj.text: PostPagesTest.post.text,
            obj.group: PostPagesTest.post.group,
            obj.author: PostPagesTest.post.author,
            obj.image: PostPagesTest.post.image
        }
        return attrs

    def smart_test_context(
            self,
            response: Client.get,
            *args,
    ):
        """

        :param response: Client.get (like response.Client.get)
        :param args: expected list[method of Unittest(like self.assertEqual),
                                  dict[str(name container of response.context):
                                       member of container]]
        :return: None
        """
        for method, kwargs in args:
            for cont, member in kwargs.items():
                with self.subTest(attr=member,
                                  container=response.context[cont]):
                    method(
                        member,
                        response.context[cont]
                    )

    def test_pages_uses_correct_template(self):
        new_dict = {**self.TEMPLATES_PAGES_NAMES,
                    **self.TEMPLATES_FORMS_PAGES}
        for reverse_name, template in new_dict.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_context_main(self):
        response = self.authorized_client.get(reverse('posts:main'))
        self.assertIn(
            PostPagesTest.post, response.context['page_obj']
        )
        self.assertIsInstance(response.context['page_obj'],
                              Page)
        self.assertIsInstance(response.context['page_obj'][0],
                              Post)
        obj = response.context['page_obj'][0]
        for test_atr, excepted_atr in self.set_dict(obj).items():
            with self.subTest(test_atr=test_atr):
                self.assertEqual(test_atr, excepted_atr)

    def test_cache_main(self):
        user_for_delete = User.objects.create_user(
            username='delete'
        )
        Post.objects.create(
            text='delete',
            author=user_for_delete
        )
        response = self.authorized_client.get(reverse('posts:main'))
        content_before_delete = response.content
        user_for_delete.delete()
        content_after_delete = response.content
        self.assertEqual(content_after_delete, content_before_delete)
        cache.clear()
        response = self.authorized_client.get(reverse('posts:main'))
        content_after_cache_clear = response.content
        self.assertNotEqual(content_after_cache_clear, content_before_delete)

    def test_context_group(self):
        response = self.authorized_client.get(reverse(
            'posts:group_list',
            kwargs={
                'slug': PostPagesTest.group.slug
            }
        ))
        self.smart_test_context(
            response,
            [self.assertIn, {'page_obj': PostPagesTest.post}],
            [self.assertEqual, {'group': PostPagesTest.group}]
        )
        self.assertIsInstance(response.context['page_obj'][0],
                              Post)
        self.assertIn(PostPagesTest.small_gif.name,
                      response.context['page_obj'][0].image.name)
        obj = response.context['page_obj'][0]
        for test_atr, excepted_atr in self.set_dict(obj).items():
            with self.subTest(test_atr=test_atr):
                self.assertEqual(test_atr, excepted_atr)

    def test_context_profile(self):
        response = self.authorized_client.get(reverse('posts:profile', kwargs={
            'username': PostPagesTest.user.username
        }))
        self.smart_test_context(
            response,
            [self.assertIn, {'page_obj': PostPagesTest.post}],
            [self.assertEqual, {'profile_author': PostPagesTest.user}]
        )
        self.assertIsInstance(response.context['page_obj'][0],
                              Post)
        self.assertIn(PostPagesTest.small_gif.name,
                      response.context['page_obj'][0].image.name)
        obj = response.context['page_obj'][0]
        for test_atr, excepted_atr in self.set_dict(obj).items():
            with self.subTest(test_atr=test_atr):
                self.assertEqual(test_atr, excepted_atr)

    def test_context_post_detail(self):
        comment = Comment.objects.create(
            text='test comment',
            author=PostPagesTest.user,
            post=PostPagesTest.post
        )
        response = self.authorized_client.get(reverse(
            'posts:post_detail',
            kwargs={
                'post_id': PostPagesTest.post.id
            }
        ))
        self.smart_test_context(
            response,
            [self.assertEqual, {'post': PostPagesTest.post}],
            [self.assertIn, {'comments': comment}]
        )
        self.assertIn(PostPagesTest.small_gif.name,
                      response.context['post'].image.name)
        obj = response.context['post']
        for test_atr, excepted_atr in self.set_dict(obj).items():
            with self.subTest(test_atr=test_atr):
                self.assertEqual(test_atr, excepted_atr)

    def test_context_post_edit(self):
        response = self.authorized_client.get(reverse(
            'posts:post_edit',
            kwargs={
                'post_id': PostPagesTest.post.id
            }
        ))
        self.smart_test_context(response,
                                [self.assertEqual,
                                 {'is_edit': True,
                                  'id': PostPagesTest.post.id}])

    def test_form_in_forms_pages(self):
        for url in self.TEMPLATES_FORMS_PAGES.keys():
            response = self.authorized_client.get(url)
            form_fields = {
                'text': forms.CharField,
                'group': forms.ChoiceField
            }
            for value, excepted in form_fields.items():
                with self.subTest(value=value, url=url):
                    form_field = response.context.get('form').fields.get(value)
                    self.assertIsInstance(form_field, excepted)

    def test_another_group(self):
        another_group = Group.objects.get_or_create(
            title='another test group',
            slug='another_test'
        )
        response = self.client.get(
            reverse('posts:group_list', kwargs={
                'slug': another_group[0].slug
            })
        )
        self.smart_test_context(response,
                                [self.assertNotIn,
                                 {'page_obj': PostPagesTest.post}])

    def test_follow_users(self):
        follow = Follow.objects.filter(
            user=PostPagesTest.user,
            author=PostPagesTest.user_for_follow
        )
        self.assertFalse(follow.exists())
        self.authorized_client.get(reverse(
            'posts:profile_follow',
            kwargs={'username': PostPagesTest.user_for_follow.username}
        ))
        self.assertTrue(follow.exists())

    def test_unfollow_users(self):
        Follow.objects.create(
            user=PostPagesTest.user,
            author=PostPagesTest.user_for_follow
        )
        self.authorized_client.get(reverse(
            'posts:profile_unfollow',
            kwargs={'username': PostPagesTest.user_for_follow.username}
        ))
        self.assertFalse(
            Follow.objects.filter(
                user=PostPagesTest.user,
                author=PostPagesTest.user_for_follow
            ).exists()
        )

    def test_new_post_followers(self):
        Follow.objects.create(
            user=PostPagesTest.user,
            author=PostPagesTest.user_for_follow
        )
        post = Post.objects.create(
            text='test text',
            author=PostPagesTest.user_for_follow
        )
        response = self.authorized_client.get(reverse('posts:follow_index'))
        self.assertIn(post, response.context['page_obj'])
        self.assertEqual(post, response.context['page_obj'][0])

    def test_no_post_no_follower(self):
        self.assertFalse(
            Follow.objects.filter(
                user=PostPagesTest.user,
                author=PostPagesTest.user_for_follow
            ).exists()
        )
        post = Post.objects.create(
            text='test text',
            author=PostPagesTest.user_for_follow
        )
        response = self.authorized_client.get(reverse('posts:follow_index'))
        self.assertIsInstance(response.context['page_obj'], Page)
        self.assertNotIn(post, response.context['page_obj'])


class PaginatorPagesTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='test')
        cls.group = Group.objects.create(
            title='test group',
            slug='slug'
        )
        user = User.objects.last()
        group = Group.objects.last()
        posts = [Post(text='test text',
                      author=user,
                      group=group) for _ in range(15)]
        Post.objects.bulk_create(posts)
        cls.TEST_PAGES = [
            reverse('posts:main'),
            reverse('posts:group_list', kwargs={
                'slug': group.slug
            }),
            reverse('posts:profile', kwargs={
                'username': user.username
            })
        ]
        cls.COUNT_POSTS_ON_PAGES = [
            (1, 10),
            (2, 5)
        ]

    def setUp(self):
        self.client = Client()

    def test_pages_paginator(self):
        for reverse_name in self.TEST_PAGES:
            for page_num, excepted_count in self.COUNT_POSTS_ON_PAGES:
                with self.subTest(
                        reverse_name=reverse_name,
                        page=page_num
                ):
                    response = self.client.get(
                        reverse_name + f'?page={page_num}'
                    )
                    self.assertEqual(
                        len(response.context['page_obj']), excepted_count
                    )
