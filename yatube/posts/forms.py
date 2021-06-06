from django import forms
from django.utils.translation import gettext_lazy as _

from .models import Comment, Post


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ['text', 'group', 'image']
        labels = {
            'text': _('Текст записи'),
            'group': _('Группа'),
        }
        help_texts = {
            'text': _('Добавьте текст записи'),
            'group': _('Выберите группу, либо оставьте поле пустым'),
        }


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['text']
        labels = {
            'text': _('Текст комментария'),
        }
        help_texts = {
            'text': _('Добавьте текст комментария'),
        }
