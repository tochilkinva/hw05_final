import shutil
import tempfile
from http import HTTPStatus

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from posts.models import Group, Post

User = get_user_model()


@override_settings(MEDIA_ROOT=tempfile.mkdtemp())
class TaskCreateFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Создаем временную папку для медиа-файлов;
        settings.MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)

        # Создаём тестовую запись в БД user и group
        cls.user = User.objects.create_user('Test',
                                            'Test@Test.com', 'testpass')
        cls.group = Group.objects.create(title='GroupTest',
                                         description='GroupDescription',
                                         slug='GroupSlug')
        cls.another_group = Group.objects.create(
            title='AnotherGroupTest',
            description='AnotherGroupDescription',
            slug='AnotherGroupSlug')

        cls.task = Post.objects.create(
            text='Test Text',
            author=cls.user,
        )

    @classmethod
    def tearDownClass(cls):
        # Рекурсивно удаляем временную папку после завершения тестов
        shutil.rmtree(settings.MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def setUp(self):
        self.guest_client = Client()
        # Создаем авторизованный клиент
        self.authorized_client = Client()
        self.authorized_client.force_login(TaskCreateFormTests.user)

    # Проверяем используемые шаблоны
    def test_create_form_task(self):
        """Валидная форма создает запись в Post"""
        posts_count = Post.objects.count()

        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x01\x00'
            b'\x01\x00\x00\x00\x00\x21\xf9\x04'
            b'\x01\x0a\x00\x01\x00\x2c\x00\x00'
            b'\x00\x00\x01\x00\x01\x00\x00\x02'
            b'\x02\x4c\x01\x00\x3b'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        form_data = {
            'text': 'Это тестовый текст',
            'group': TaskCreateFormTests.group.id,
            'image': uploaded,
        }
        # Отправляем POST-запрос
        response = self.authorized_client.post(
            reverse('new_post'),
            data=form_data,
            follow=True
        )
        # Проверяем, увеличилось ли число постов
        self.assertEqual(Post.objects.count(), posts_count + 1)
        # Проверям редирект после содания поста
        self.assertRedirects(response, reverse('index'))
        # Проверяем, что создалась запись с нашим текстом
        created_post = Post.objects.filter(text=form_data['text'],)
        self.assertEqual(created_post[0].text, form_data['text'])
        self.assertEqual(created_post[0].group, TaskCreateFormTests.group)
        self.assertEqual(created_post[0].author, TaskCreateFormTests.user)
        self.assertEqual(created_post[0].image, 'posts/small.gif')
        # Проверим, что ничего не упало и страница отдаёт код 200
        self.assertEqual(response.status_code, HTTPStatus.OK)

    # Проверяем редактирование поста авторизованным клиентом
    def test_edit_post_task(self):
        """При редактировании поста через форму все ок"""
        adress = reverse('post_edit', kwargs={
            'username': TaskCreateFormTests.user.username,
            'post_id': TaskCreateFormTests.task.id})
        form_data = {
            'text': 'Test Text 2222',
            'group': TaskCreateFormTests.another_group.id
        }
        # Отправляем POST-запрос
        response = self.authorized_client.post(
            adress,
            data=form_data,
            follow=True
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertTrue(
            Post.objects.filter(text=form_data['text']).exists()
        )
        self.assertEqual(
            Post.objects.filter(text=form_data['text'])[0].group.slug,
            TaskCreateFormTests.another_group.slug)

    # Проверяем публикацию поста неавторизованным клиентом
    def test_guest_client_cannot_create_post_task(self):
        """Неавторизованный клиент не может опубликовать пост"""
        form_data = {
            'text': 'Этот пост не создали',
            'group': TaskCreateFormTests.group.id
        }
        # Отправляем POST-запрос
        response = self.guest_client.post(
            reverse('new_post'),
            data=form_data,
            follow=True
        )
        self.assertRedirects(
            response, (f"{reverse('login')}?next={reverse('new_post')}"))
        self.assertFalse(
            Post.objects.filter(text=form_data['text'],).exists())

    # Проверяем комментарии
    def test_guest_client_cannot_create_comments_task(self):
        """Только авторизованный клиент может комментировать посты"""
        adress = reverse('add_comment', kwargs={
            'username': TaskCreateFormTests.user.username,
            'post_id': TaskCreateFormTests.task.id})
        form_data = {
            'text': 'Test comment',
        }
        # Отправляем POST-запрос
        response = self.guest_client.post(
            adress,
            data=form_data,
            follow=True
        )
        self.assertRedirects(
            response, (f"{reverse('login')}?next={adress}"))
