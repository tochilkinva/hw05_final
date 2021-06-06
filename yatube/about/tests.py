from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from posts.models import Group, Post

User = get_user_model()


class TaskPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Создаём тестовую запись в БД user и group
        cls.user = User.objects.create_user('Test',
                                            'Test@Test.com', 'testpass')
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

    def setUp(self):
        self.guest_client = Client()
        # Создаем авторизованный клиент
        self.authorized_client = Client()
        self.authorized_client.force_login(TaskPagesTests.user)

        # Пост с группой
        self.task = Post.objects.create(
            text='Test text',
            author=TaskPagesTests.user,
            group=TaskPagesTests.group
        )

    # Проверка About
    def test_about_exists_at_desired_location(self):
        """Страницы About доступны любому пользователю."""
        url_names = {
            '/about/author/': HTTPStatus.OK,
            '/about/tech/': HTTPStatus.OK,
        }
        for adress, status_code in url_names.items():
            with self.subTest(adress=adress):
                response = self.guest_client.get(adress)
                self.assertEqual(response.status_code, status_code)

    def test_about_use_correct_template(self):
        """Страницы About используют соответствующий шаблон."""
        templates_pages_names = {
            'about/author.html': reverse('about:author'),
            'about/tech.html': reverse('about:tech'),
        }
        for template, reverse_name in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.guest_client.get(reverse_name)
                self.assertTemplateUsed(response, template)
