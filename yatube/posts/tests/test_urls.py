from http import HTTPStatus

from django.test import TestCase, Client
from django.urls import reverse, Resolver404, resolve

from posts.models import Post, Group, User


class StaticURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.other_user = User.objects.create_user(username='user without post')
        cls.user = User.objects.create_user(username='test')
        cls.group = Group.objects.create(
            title='test group',
            slug='test'
        )
        cls.post = Post.objects.create(
            text='test text',
            author=StaticURLTests.user,
            group=StaticURLTests.group
        )
        cls.URLS_TEMPLATES_FOR_GUEST = {
            f'/group/{StaticURLTests.group.slug}/': 'posts/group_list.html',
            f'/profile/{StaticURLTests.user.username}/': 'posts/profile.html',
            f'/posts/{StaticURLTests.post.id}/': 'posts/post_id.html',
        }
        cls.URLS_TEMPLATES_FOR_USER = {
            f'/posts/{StaticURLTests.post.id}/edit/': 'posts/post_create.html',
            '/create/': 'posts/post_create.html',
        }

    def setUp(self):
        self.guest_client = Client()
        self.other_authorized_client = Client()
        self.other_authorized_client.force_login(StaticURLTests.other_user)
        self.authorized_client = Client()
        self.authorized_client.force_login(StaticURLTests.user)

    def test_guest_roots(self):
        with self.assertRaises(Resolver404):
            resolve('404')
            self.assertEqual(
                self.authorized_client.get('404').response_code,
                HTTPStatus.NOT_FOUND
            )
        for url in self.URLS_TEMPLATES_FOR_GUEST:
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_guest_redirects(self):
        for url in self.URLS_TEMPLATES_FOR_USER:
            with self.subTest(url=url):
                response = self.guest_client.get(url, follow=True)
                self.assertRedirects(
                    response,
                    reverse('users:login') + '?next=' + url
                )

    def test_other_user_roots(self):
        response = self.other_authorized_client.get(
            f'/posts/{StaticURLTests.post.id}/edit/',
            follow=True
        )
        self.assertRedirects(
            response,
            reverse('posts:post_detail', kwargs={
                'post_id': StaticURLTests.post.id
            })
        )

    def test_edit_post(self):
        response = self.authorized_client.get(
            f'/posts/{StaticURLTests.post.id}/edit/'
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_used_templates(self):
        with self.assertRaises(Resolver404):
            resolve('404')
            self.assertTemplateUsed(
                self.authorized_client.get('404'),
                'core/404.html'
            )
        new_dict = {**self.URLS_TEMPLATES_FOR_USER,
                    **self.URLS_TEMPLATES_FOR_GUEST}
        for url, template in new_dict.items():
            with self.subTest(url=url):
                response = self.authorized_client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)
                self.assertTemplateUsed(response, template)
