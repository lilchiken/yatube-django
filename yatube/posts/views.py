from django.shortcuts import render, \
    get_object_or_404, \
    get_list_or_404, \
    redirect
from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required
from django.db.models.query import QuerySet
from django.views.decorators.cache import cache_page
from django.http.response import Http404

from posts.forms import PostForm, CommentForm
from posts.models import Post, Group, User, Follow
from yatube.settings import POSTS_ON_PAGE as POSTS


def paginator(posts: QuerySet,
              request):
    return Paginator(posts, POSTS).get_page(request.GET.get('page'))


@cache_page(20, key_prefix='index_page')
def index(request):
    posts = Post.objects.all()
    page_obj = paginator(posts, request)
    context = {
        'page_obj': page_obj
    }
    return render(request, 'posts/index.html', context)


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    posts = group.posts.all()
    page_obj = paginator(posts, request)
    context = {
        'group': group,
        'page_obj': page_obj
    }
    return render(request, 'posts/group_list.html', context)


def profile(request, username):
    author = get_object_or_404(User, username=username)
    following = False
    if request.user.is_authenticated:
        following = Follow.objects.filter(
            user=request.user,
            author=author
        ).first()
        if following:
            following = True
        else:
            following = False
    posts = author.posts.all()
    page_obj = paginator(posts, request)
    context = {
        'following': following,
        'username': author,
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
    if request.method == 'POST':
        if form.is_valid():
            post = form.save()
            post.author = request.user
            post.save()
            return redirect('posts:profile', post.author)
        return render(
            request,
            'posts/post_create.html',
            {'form': form}
        )
    return render(request, 'posts/post_create.html', {'form': form})


@login_required
def post_edit(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    if post.author != request.user:
        return redirect('posts:post_detail', post_id)
    is_edit = True
    form = PostForm(request.POST or None,
                    files=request.FILES or None,
                    instance=post)
    if form.is_valid():
        form.save()
        return redirect('posts:post_detail', post_id)
    return render(
        request,
        'posts/post_create.html',
        {
            'form': form,
            'is_edit': is_edit,
            'id': post_id,
        }
    )


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
    try:
        authors = get_list_or_404(Follow,
                                  user=request.user)
        id_post_list = []
        [[id_post_list.append(post.id) for post in author.author.posts.all()]
         for author in authors]
        posts_set = Post.objects.filter(id__in=id_post_list)
        page_obj = paginator(posts_set, request)
    except Http404:
        page_obj = paginator([], request)
    return render(request,
                  'posts/follow.html',
                  {'page_obj': page_obj})


@login_required
def profile_follow(request, username):
    following = User.objects.get(
        username=username
    )
    check_follow = Follow.objects.filter(
        user=request.user,
        author=following
    ).first()
    if request.user != following and check_follow is None:
        Follow.objects.create(
            user=request.user,
            author=following
        )
    return redirect('posts:profile', username=username)


@login_required
def profile_unfollow(request, username):
    following = User.objects.get(
        username=username
    )
    relation = Follow.objects.get(
        user=request.user,
        author=following
    )
    relation.delete()
    return redirect('posts:profile', username=username)
