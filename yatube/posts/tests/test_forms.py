import shutil
import tempfile

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, Client, override_settings
from django.urls import reverse
from django.conf import settings

from posts.models import Post, Group, User

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
class FormsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='test')
        cls.group = Group.objects.create(
            title='test group',
            slug='test'
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.guest = Client()
        self.client = Client()
        self.client.force_login(self.user)

    def test_create_form(self):
        post_count = Post.objects.count()
        uploaded = SimpleUploadedFile(
            name='new_small.gif',
            content=EXAMPLE_SMALL_GIF,
            content_type='image/gif'
        )
        data = {
            'text': 'test text',
            'group': FormsTest.group.id,
            'image': uploaded
        }
        self.client.post(
            reverse('posts:post_create'),
            data=data,
            follow=True
        )
        post = Post.objects.last()
        self.assertEqual(Post.objects.count(), post_count + 1)
        attrs_equal = {
            post.text: data['text'],
            post.group: FormsTest.group,
            post.author: FormsTest.user,
            post.image.name: Post.image.field.upload_to + uploaded.name
        }
        for attrs, excepted in attrs_equal.items():
            with self.subTest(atrs=attrs):
                self.assertEqual(attrs, excepted)

    def test_post_edit(self):
        new_post = Post.objects.create(
            text='test',
            author=FormsTest.user
        )
        posts_count = Post.objects.count()
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=EXAMPLE_SMALL_GIF,
            content_type='image/gif'
        )
        data = {
            'text': 'this is test post two but upgraded',
            'group': FormsTest.group.id,
            'image': uploaded
        }
        self.client.post(
            reverse('posts:post_edit', kwargs={
                'post_id': new_post.id
            }),
            data=data
        )
        self.assertEqual(Post.objects.count(), posts_count)
        new_post.refresh_from_db()
        attrs_equal = {
            new_post.text: data['text'],
            new_post.group: FormsTest.group,
            new_post.author: FormsTest.user,
            new_post.image: f'posts/{uploaded.name}'
        }
        for attr, excepted in attrs_equal.items():
            with self.subTest(attr=attr, exc=excepted):
                self.assertEqual(attr, excepted)

    def test_comments_for_guest(self):
        new_post = Post.objects.create(
            text='test text',
            author=FormsTest.user
        )
        data = {
            'text': 'test comment'
        }
        self.guest.post(
            reverse('posts:add_comment', kwargs={
                'post_id': new_post.id
            }),
            data=data
        )
        new_post.refresh_from_db()
        self.assertEqual(new_post.comments.count(), 0)
