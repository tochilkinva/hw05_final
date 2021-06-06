from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from posts.models import Group, Post

User = get_user_model()


class StaticURLTests(TestCase):
    def setUp(self):
        self.guest_client = Client()

    def test_homepage(self):
        response = self.guest_client.get('/')
        self.assertEqual(response.status_code, HTTPStatus.OK)


class TaskURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.group = Group.objects.create(title='GroupTest',
                                         slug="group-test-slug",
                                         description='GroupDescription')
        cls.user = User.objects.create_user('Test',
                                            'Test@Test.com', 'testpass')
        cls.post = Post.objects.create(
            text='Test text',
            author=cls.user,
            group=cls.group
        )
        cls.another_user = User.objects.create_user('Another')

    def setUp(self):
        # Создаем неавторизованный клиент
        self.guest_client = Client()
        # Создаем пользователя и авторизуем его
        self.authorized_client = Client()
        self.authorized_client.force_login(TaskURLTests.user)

        self.another_authorized_client = Client()
        self.another_authorized_client.force_login(TaskURLTests.another_user)

    def test_authorized_client_urls_exists_at_desired_location(self):
        """Страницы доступны авторизованному пользователю."""
        url_names = {
            '/': HTTPStatus.OK,
            '/new/': HTTPStatus.OK,
            '/group/group-test-slug/': HTTPStatus.OK,
        }
        for adress, status_code in url_names.items():
            with self.subTest(adress=adress):
                response = self.authorized_client.get(adress)
                self.assertEqual(response.status_code, status_code)

    def test_anonymous_client_urls_exists_at_desired_location(self):
        """Страницы доступны любому пользователю."""
        url_names = {
            '/': HTTPStatus.OK,
            '/new/': HTTPStatus.FOUND,
            '/group/group-test-slug/': HTTPStatus.OK,
        }
        for adress, status_code in url_names.items():
            with self.subTest(adress=adress):
                response = self.guest_client.get(adress)
                self.assertEqual(response.status_code, status_code)

    def test_anonymous_client_urls_redirect(self):
        """Перенаправление анонимного пользователя на страницу логина."""
        response = self.guest_client.get('/new/', follow=True)
        self.assertRedirects(
            response,
            (f"{reverse('login')}?next={reverse('new_post')}"))

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_url_names = {
            'index.html': '/',
            'post_edit.html': '/new/',
            'group.html': '/group/group-test-slug/',
        }
        for template, adress in templates_url_names.items():
            with self.subTest(adress=adress):
                response = self.authorized_client.get(adress)
                self.assertTemplateUsed(response, template)

    def test_post_edit_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        adress = reverse('post_edit', kwargs={
            'username': TaskURLTests.user.username,
            'post_id': TaskURLTests.post.id})
        response = self.authorized_client.get(adress)
        self.assertTemplateUsed(response, 'post_edit.html')

    def test_profile_post_exists_at_desired_location(self):
        """Страница профайла и поста доступна любому пользователю."""
        url_names = {
            f'/{TaskURLTests.user.username}/': HTTPStatus.OK,
            f'/{TaskURLTests.user.username}/{TaskURLTests.post.id}/':
            HTTPStatus.OK,
        }
        for adress, status_code in url_names.items():
            with self.subTest(adress=adress):
                response = self.guest_client.get(adress)
                self.assertEqual(response.status_code, status_code)

    def test_edit_post_is_available_for_author(self):
        """Страница редактирования поста доступна автору, а другим нет."""
        adress = reverse('post_edit', kwargs={
            'username': TaskURLTests.user.username,
            'post_id': TaskURLTests.post.id})

        redirect_adress = reverse('post_view', kwargs={
            'username': TaskURLTests.user.username,
            'post_id': TaskURLTests.post.id})

        response = self.guest_client.get(adress)
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertRedirects(response,
                             f"{reverse('login')}?next={adress}")

        response = self.authorized_client.get(adress)
        self.assertEqual(response.status_code, HTTPStatus.OK)

        response = self.another_authorized_client.get(adress)
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertRedirects(response, redirect_adress)

    def test_404_page(self):
        response = self.guest_client.get('/qwerty/', follow=True)
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
