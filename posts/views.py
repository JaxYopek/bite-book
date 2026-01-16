from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Post, PostLike, PostComment
from django import forms
from restaurants.models import Review, Notification
from django.http import JsonResponse

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


@login_required
def post_detail(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    
    # Get review and like info if it's a review post
    review = None
    like_count = 0
    user_has_liked = False
    comments = []
    
    if post.post_type == 'review' and post.menu_item:
        review = Review.objects.filter(
            menu_item=post.menu_item,
            user=post.user,
            rating=post.rating
        ).first()
        
        if review:
            like_count = review.likes.count()
            user_has_liked = review.likes.filter(user=request.user).exists()
            comments = review.comments.select_related('user', 'user__profile').all()
    else:
        # For non-review posts, use PostLike and PostComment
        like_count = post.likes.count()
        user_has_liked = post.likes.filter(user=request.user).exists()
        comments = post.comments.select_related('user', 'user__profile').all()
    
    is_top_reviewer = post.user.profile.is_top_reviewer() if post.user and hasattr(post.user, 'profile') else False
    
    return render(request, 'post_detail.html', {
        'post': post,
        'review': review,
        'like_count': like_count,
        'user_has_liked': user_has_liked,
        'comments': comments,
        'is_top_reviewer': is_top_reviewer
    })


@login_required
def like_post(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    like, created = PostLike.objects.get_or_create(post=post, user=request.user)
    
    if not created:
        # Unlike if already liked
        like.delete()
        liked = False
    else:
        liked = True
        # Create notification for the post author
        if post.user and post.user != request.user:
            Notification.objects.create(
                user=post.user,
                notification_type='post_like',
                post=post,
                triggered_by=request.user
            )
    
    # Return JSON for AJAX or redirect for regular requests
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'liked': liked,
            'like_count': post.likes.count()
        })
    
    # Redirect back to the previous page
    return redirect(request.META.get('HTTP_REFERER', 'feed'))


@login_required
def delete_post(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    
    # Allow the post author or staff to delete it
    if post.user != request.user and not request.user.is_staff:
        return JsonResponse({'success': False, 'error': 'Unauthorized'}, status=403)
    
    post.delete()
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'success': True})
    
    return redirect('feed')


@login_required
def delete_post_comment(request, comment_id):
    comment = get_object_or_404(PostComment, id=comment_id)
    
    # Allow the comment author or staff to delete it
    if comment.user != request.user and not request.user.is_staff:
        return JsonResponse({'success': False, 'error': 'Unauthorized'}, status=403)
    
    comment.delete()
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'success': True})
    
    return redirect(request.META.get('HTTP_REFERER', 'feed'))


@login_required
def add_post_comment(request, post_id):
    if request.method == 'POST':
        post = get_object_or_404(Post, id=post_id)
        text = request.POST.get('text', '').strip()
        
        if text:
            comment = PostComment.objects.create(
                post=post,
                user=request.user,
                text=text
            )
            
            # Create notification for the post author
            if post.user and post.user != request.user:
                Notification.objects.create(
                    user=post.user,
                    notification_type='post_comment',
                    post=post,
                    triggered_by=request.user
                )
            
            # Return JSON for AJAX requests
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                # Get profile info
                profile = None
                display_name = request.user.username
                profile_picture_url = None
                
                if hasattr(request.user, 'profile'):
                    profile = request.user.profile
                    if profile.display_name:
                        display_name = profile.display_name
                    if profile.profile_picture:
                        profile_picture_url = profile.profile_picture.url
                
                return JsonResponse({
                    'success': True,
                    'comment': {
                        'id': comment.id,
                        'text': comment.text,
                        'username': request.user.username,
                        'display_name': display_name,
                        'profile_picture_url': profile_picture_url,
                        'created_at': 'just now'
                    }
                })
    
    return redirect(request.META.get('HTTP_REFERER', 'feed'))

