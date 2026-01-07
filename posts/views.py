from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .models import Post
from django import forms

class DiaryEntryForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ['title', 'review_text']

@login_required
def create_diary_entry(request):
    if request.method == 'POST':
        form = DiaryEntryForm(request.POST)
        if form.is_valid():
            post = form.save(commit=False)
            post.user = request.user
            post.post_type = 'diary'
            post.save()
            return redirect('feed')
    else:
        form = DiaryEntryForm()
    return render(request, 'create_diary_entry.html', {'form': form})
