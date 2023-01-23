from django import forms

from posts.models import Post, Comment


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ('text', 'group', 'image')

    def clean_text(self):
        data = self.cleaned_data['text']

        if '' == data.lower():
            raise forms.ValidationError('Зачем нужен пустой пост?')
        return data


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ('text',)

    def clean_text(self):
        data = self.cleaned_data['text']

        if '' == data.lower():
            raise forms.ValidationError('Зачем нужен пустой комментарий?')
        return data
