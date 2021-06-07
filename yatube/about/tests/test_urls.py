from http import HTTPStatus

from django.test import Client, TestCase


class TaskUrlsTests(TestCase):

    def setUp(self):
        self.guest_client = Client()

    # Проверка About
    def test_about_exists_at_desired_location(self):
        """Страницы About и Tech доступны любому пользователю."""
        url_names = {
            '/about/author/': HTTPStatus.OK,
            '/about/tech/': HTTPStatus.OK,
        }
        for adress, status_code in url_names.items():
            with self.subTest(adress=adress):
                response = self.guest_client.get(adress)
                self.assertEqual(response.status_code, status_code)
