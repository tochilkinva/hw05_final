import shutil
import tempfile

from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import models
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from posts.models import Follow, Group, Post

User = get_user_model()


@override_settings(MEDIA_ROOT=tempfile.mkdtemp())
class TaskPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        # Создаем временную папку для медиа-файлов;
        settings.MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)

        # Создаём тестовую запись в БД user и group
        cls.user = User.objects.create_user('Test',
                                            'Test@Test.com', 'testpass')
        cls.user2 = User.objects.create_user('Test2',
                                             'Test2@Test.com', 'testpass2')
        cls.user3 = User.objects.create_user('Test3',
                                             'Test3@Test.com', 'testpass3')
        cls.group = Group.objects.create(title='GroupTest',
                                         slug="test-slug",
                                         description='GroupDescription')
        cls.group2 = Group.objects.create(title='GroupTest2',
                                          slug="other-slug2",
                                          description='GroupDescription2')
        # Посты без группы
        for i in range(14):
            Post.objects.create(
                text='Тестовый текст поста',
                author=cls.user,
            )
        # Пост в другую группу
        Post.objects.create(
            text='Test text2',
            author=cls.user,
            group=cls.group2
        )

        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x01\x00'
            b'\x01\x00\x00\x00\x00\x21\xf9\x04'
            b'\x01\x0a\x00\x01\x00\x2c\x00\x00'
            b'\x00\x00\x01\x00\x01\x00\x00\x02'
            b'\x02\x4c\x01\x00\x3b'
        )
        cls.uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )

    @classmethod
    def tearDownClass(cls):
        # Рекурсивно удаляем временную папку после завершения тестов
        shutil.rmtree(settings.MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def setUp(self):
        # Создаем авторизованный клиент
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(TaskPagesTests.user)
        self.authorized_client2 = Client()
        self.authorized_client2.force_login(TaskPagesTests.user2)
        self.authorized_client3 = Client()
        self.authorized_client3.force_login(TaskPagesTests.user3)

        # Пост с группой
        self.task = Post.objects.create(
            text='Test text',
            author=TaskPagesTests.user,
            group=TaskPagesTests.group,
            image=TaskPagesTests.uploaded
        )

    # Проверяем используемые шаблоны
    def test_pages_use_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_pages_names = {
            'index.html': reverse('index'),
            'group.html': (
                reverse('group_posts', kwargs={'slug': 'test-slug'})
            ),
            'post_edit.html': reverse('new_post'),
        }
        for template, reverse_name in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    # Тест паджинатора
    def test_first_page_contains_ten_records(self):
        response = self.authorized_client.get(reverse('index'))
        self.assertEqual(len(response.context.get('page').object_list), 10)

    def test_second_page_contains_six_records(self):
        response = self.client.get(reverse('index') + '?page=2')
        self.assertEqual(len(response.context.get('page').object_list), 6)

    def test_paginator_on_group_page(self):
        response = self.authorized_client.get(
            reverse('group_posts', kwargs={'slug': 'test-slug'})
        )
        self.assertEqual(len(response.context.get('page').object_list), 1)

    def test_paginator_on_profile_page(self):
        response = self.authorized_client.get(
            f'/{TaskPagesTests.user.username}/')
        self.assertEqual(len(response.context.get('page').object_list), 10)

    # Проверка словаря контекста
    def test_home_page_shows_correct_context(self):
        """Шаблон index сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('index'))
        post_fields = {
            'text': models.TextField,
            'pub_date': models.DateTimeField,
            'author': models.ForeignKey,
            'group': models.ForeignKey,
            'image': models.ImageField,
        }
        # Проверяем поля формы context
        for value, expected in post_fields.items():
            with self.subTest(value=value):
                one_post = response.context.get('page').object_list[0]
                one_field = one_post._meta.get_field(value)
                self.assertIsInstance(one_field, expected)

    def test_group_page_shows_correct_context(self):
        """Шаблон group сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('group_posts', kwargs={'slug': 'test-slug'})
        )
        one_post = response.context.get('page').object_list[0]
        self.assertEqual(one_post.text, 'Test text')
        self.assertEqual(one_post.author.username, 'Test')
        self.assertEqual(one_post.group.title, 'GroupTest')
        self.assertEqual(one_post.image, self.task.image)

    def test_newpost_page_shows_correct_context(self):
        """Шаблон new_post сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('new_post'))
        post_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }
        for value, expected in post_fields.items():
            with self.subTest(value=value):
                form_field = response.context['form'].fields[value]
                self.assertIsInstance(form_field, expected)

    def test_profile_shows_correct_context(self):
        """Шаблон profile сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            f'/{TaskPagesTests.user.username}/')
        one_post = response.context.get('page').object_list[0]
        self.assertEqual(one_post.text, 'Test text')
        self.assertEqual(one_post.author.username, 'Test')
        self.assertEqual(one_post.group.title, 'GroupTest')
        self.assertEqual(one_post.image, self.task.image)

    def test_post_page_shows_correct_context(self):
        """Шаблон отдельного поста сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            f'/{TaskPagesTests.user.username}/{self.task.id}/')
        one_post = response.context.get('post')
        self.assertEqual(one_post.text, 'Test text')
        self.assertEqual(one_post.author.username, 'Test')
        self.assertEqual(one_post.group.title, 'GroupTest')
        self.assertEqual(one_post.image, self.task.image)

    # Проверка появления постов там где надо
    def test_post_with_group_appears_correctly_on_home(self):
        """Пост с группой появляется на главной странице сайта"""
        response = self.authorized_client.get(reverse('index'))
        one_post = response.context.get('page').object_list[0]
        self.assertEqual(one_post.text, self.task.text)
        self.assertEqual(one_post.author.username, self.task.author.username)
        self.assertEqual(one_post.group.title, self.task.group.title)

    def test_post_with_group_appears_correctly_on_group(self):
        """Пост с группой появляется на странице группы"""
        response = self.authorized_client.get(
            reverse('group_posts', kwargs={'slug': 'test-slug'})
        )
        one_post = response.context.get('page').object_list[0]
        self.assertEqual(one_post.text, self.task.text)
        self.assertEqual(one_post.author.username, self.task.author.username)
        self.assertEqual(one_post.group.title, self.task.group.title)

    def test_post_with_group_not_appears_in_another_group(self):
        """Пост с группой не появляется на странице другой группы"""
        response = self.authorized_client.get(
            reverse('group_posts', kwargs={'slug': 'other-slug2'})
        )
        one_post = response.context.get('page').object_list[0]
        self.assertNotEqual(one_post.group.title, self.task.group.title)

    # Проверка работы кэша
    def test_post_with_group_appears_correctly_on_home(self):
        """Кэш на главной странице работает корректно"""
        # Кэшируем главную страницу
        response = self.authorized_client.get(reverse('index'))
        one_post = response.content
        # Создаем новый пост
        Post.objects.create(
            text='New Text',
            author=TaskPagesTests.user,
        )
        # Обновляем запрос к главной странице
        cached_response = self.authorized_client.get(reverse('index'))
        cached_one_post = cached_response.content
        # Контент должен быть одинаковым т.к. все закэшировано
        self.assertEqual(one_post, cached_one_post)

    def test_authorized_client_can_follow(self):
        """Авторизованный пользователь может подписываться и отписываться"""
        # Считаем кол-во подписок
        following_count = Follow.objects.filter(
            user=TaskPagesTests.user2).count()
        # Подписываемся
        self.authorized_client2.get(
            reverse('profile_follow',
                    kwargs={'username': TaskPagesTests.user}))
        # Проверяем увеличение кол-ва подписок
        self.assertEqual(Follow.objects.filter(
            user=TaskPagesTests.user2).count(), following_count + 1)
        # Отписываемся
        self.authorized_client2.get(
            reverse('profile_unfollow',
                    kwargs={'username': TaskPagesTests.user}))
        # Проверяем уменьшение кол-ва подписок
        self.assertEqual(Follow.objects.filter(
            user=TaskPagesTests.user2).count(), following_count)

    def test_post_appears_in_followers_list(self):
        """Пост появляется в ленте тех, кто на него подписан"""
        # Подписываемся на TaskPagesTests.user
        self.authorized_client2.get(
            reverse('profile_follow',
                    kwargs={'username': TaskPagesTests.user}))
        # TaskPagesTests.user создает пост
        Post.objects.create(
            text='Post for followers',
            author=TaskPagesTests.user,
        )
        # Смотрим ленту нашего user authorized_client2
        response = self.authorized_client2.get(reverse('follow_index'))
        one_post = response.context.get('page').object_list[0]
        self.assertEqual(one_post.text, 'Post for followers')

        # Пост не появился в ленте другого user authorized_client3
        response = self.authorized_client3.get(reverse('follow_index'))
        one_post = response.context.get('page').object_list
        self.assertEqual(len(one_post), 0)
