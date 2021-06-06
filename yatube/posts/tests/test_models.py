from django.contrib.auth import get_user_model
from django.test import TestCase
from posts.models import Group, Post

User = get_user_model()


class PostsModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        """Создаём тестовый пост в БД"""
        super().setUpClass()
        user = User.objects.create_user('Test', 'Test@Test.com', 'testpass')
        group = Group.objects.create(title='GroupTest',
                                     description='GroupDescription')
        cls.task = Post.objects.create(
            text='Тестовый текст поста',
            author=user,
            group=group
        )

    def test_object_name_is_title_field(self):
        """Проверка __str__  у PostModel"""
        task = PostsModelTest.task
        expected_object_name = task.text[:15]
        self.assertEqual(expected_object_name, str(task))

    def test_group_name_is_title_field(self):
        """Проверка __str__  у GroupModel"""
        task = PostsModelTest.task
        expected_object_name = task.group.title
        self.assertEqual(expected_object_name, str(task.group))
