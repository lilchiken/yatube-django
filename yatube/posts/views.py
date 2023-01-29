from django.shortcuts import render, get_object_or_404, redirect
from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required
from django.db.models.query import QuerySet

from posts.forms import PostForm, CommentForm
from posts.models import Post, Group, User, Follow
from yatube.settings import POSTS_ON_PAGE as POSTS


def create_page_obj_from_paginator(posts: QuerySet, request):
    return Paginator(posts, POSTS).get_page(request.GET.get('page'))


def index(request):
    posts = Post.objects.select_related('author', 'group')
    page_obj = create_page_obj_from_paginator(posts, request)
    context = {
        'page_obj': page_obj
    }
    return render(request, 'posts/index.html', context)


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    posts = group.posts.select_related('author')
    page_obj = create_page_obj_from_paginator(posts, request)
    context = {
        'group': group,
        'page_obj': page_obj
    }
    return render(request, 'posts/group_list.html', context)


def profile(request, username):
    author = get_object_or_404(User, username=username)
    following = request.user.is_authenticated and Follow.objects.filter(
        user=request.user,
        author=author
    ).exists()
    posts = author.posts.select_related('group')
    page_obj = create_page_obj_from_paginator(posts, request)
    context = {
        'following': following,
        'profile_author': author,
        'page_obj': page_obj
    }
    return render(request, 'posts/profile.html', context)


def post_detail(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    comments = post.comments.all()
    form = CommentForm()
    context = {
        'post': post,
        'comments': comments,
        'form': form
    }
    return render(request, 'posts/post_id.html', context)


@login_required
def post_create(request):
    form = PostForm(request.POST or None,
                    files=request.FILES or None)
    if form.is_valid():
        post = form.save()
        post.author = request.user
        post.save()
        return redirect('posts:profile', post.author)
    return render(request, 'posts/post_create.html', {'form': form})


@login_required
def post_edit(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    if post.author != request.user:
        return redirect('posts:post_detail', post_id)
    form = PostForm(request.POST or None,
                    files=request.FILES or None,
                    instance=post)
    if form.is_valid():
        form.save()
        return redirect('posts:post_detail', post_id)
    context = {
        'form': form,
        'is_edit': True,
        'id': post_id,
    }
    return render(request, 'posts/post_create.html', context)


@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)


@login_required
def follow_index(request):
    page_obj = create_page_obj_from_paginator(
        Post.objects.filter(author__following__user=request.user),
        request
    )
    context = {
        'page_obj': page_obj
    }
    return render(request, 'posts/follow.html', context)


@login_required
def profile_follow(request, username):
    following = User.objects.get(
        username=username
    )
    if request.user != following:
        Follow.objects.get_or_create(
            user=request.user,
            author=following
        )
    return redirect('posts:profile', username=username)


@login_required
def profile_unfollow(request, username):
    following = User.objects.get(
        username=username
    )
    Follow.objects.filter(
        user=request.user,
        author=following
    ).delete()
    return redirect('posts:profile', username=username)
