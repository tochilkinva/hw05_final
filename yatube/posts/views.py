from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from .forms import CommentForm, PostForm
from .models import Comment, Follow, Group, Post

User = get_user_model()


def index(request):
    post_list = Post.objects.all()
    paginator = Paginator(post_list, settings.POSTS_PER_PAGE)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    form = PostForm()
    return render(request, 'index.html', {'page': page, 'form': form})


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    posts_list = group.posts_in_group.all()
    paginator = Paginator(posts_list, settings.POSTS_PER_PAGE)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    return render(request, 'group.html', {'group': group, 'page': page})


def profile(request, username):
    author = get_object_or_404(User, username=username)
    posts_list = author.author_posts.all()
    paginator = Paginator(posts_list, settings.POSTS_PER_PAGE)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    post_num = author.author_posts.count()

    if request.user.is_authenticated:
        following = Follow.objects.filter(user=request.user,
                                          author=author).exists()
    else:
        following = False

    following_count = Follow.objects.filter(user=author).count()
    followers_count = Follow.objects.filter(author=author).count()

    profile = author

    context = {'author': author, 'page': page,
               'post_num': post_num, 'following': following,
               'profile': profile, 'followers_count': followers_count,
               'following_count': following_count}

    return render(request, 'profile.html', context)


def post_view(request, username, post_id):
    post = get_object_or_404(Post, id=post_id, author__username=username)
    author = post.author
    post_num = author.author_posts.count()
    comments = Comment.objects.filter(post=post)
    form = PostForm()
    comments_form = CommentForm()

    if request.user.is_authenticated:
        following = Follow.objects.filter(user=request.user,
                                          author=author).exists()
    else:
        following = False

    following_count = Follow.objects.filter(user=author).count()
    followers_count = Follow.objects.filter(author=author).count()
    context = {'author': author, 'post': post, 'post_num': post_num,
               'comments': comments, 'form': form,
               'comments_form': comments_form,
               'following': following, 'followers_count': followers_count,
               'following_count': following_count}

    return render(request, 'post.html', context)


@login_required
def new_post(request):
    is_new_post = True
    if request.method != 'POST':
        form = PostForm()
        return render(request, 'post_edit.html',
                      {'form': form, 'is_new_post': is_new_post})

    form = PostForm(request.POST or None,
                    files=request.FILES or None)

    if form.is_valid():
        post = form.save(commit=False)
        post.author = request.user
        post.save()
        return redirect('index')

    return render(request, 'post_edit.html',
                  {'form': form, 'is_new_post': is_new_post})


@login_required
def post_edit(request, username, post_id):
    is_new_post = False
    post = get_object_or_404(Post, id=post_id, author__username=username)

    is_author = (post.author.username == request.user.username)
    if not is_author:
        return redirect(reverse('post_view', args=[username, post_id]))

    form = PostForm(request.POST or None,
                    files=request.FILES or None,
                    instance=post)

    if request.method == 'POST':
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.save()
            return redirect('post_edit', username=username, post_id=post_id)

    context = {'form': form, 'username': username, 'post': post,
               'post_id': post_id, 'is_new_post': is_new_post}
    return render(request, 'post_edit.html', context)


@login_required
def add_comment(request, username, post_id):
    post = get_object_or_404(Post, id=post_id)
    form = CommentForm(request.POST or None)
    if request.method == 'POST':
        if form.is_valid():
            comment = form.save(commit=False)
            comment.post = post
            comment.author = request.user
            comment.save()

    return redirect(reverse('post_view', args=[username, post_id]))


def page_not_found(request, exception):
    return render(
        request,
        "misc/404.html",
        {"path": request.path},
        status=404
    )


def server_error(request):
    return render(request, "misc/500.html", status=500)


@login_required
def follow_index(request):
    follow = Follow.objects.filter(user=request.user).values_list('author')
    post_list = Post.objects.filter(author__pk__in=follow)
    paginator = Paginator(post_list, settings.POSTS_PER_PAGE)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    return render(request, 'follow.html', {'page': page})


@login_required
def profile_follow(request, username):
    user = request.user
    author = User.objects.get(username=username)
    is_follower = Follow.objects.filter(user=user, author=author)
    if user != author and not is_follower.exists():
        Follow.objects.create(user=user, author=author)
    return redirect(reverse('profile', args=[username]))


@login_required
def profile_unfollow(request, username):
    user = request.user
    author = User.objects.get(username=username)
    is_follower = Follow.objects.filter(user=user, author=author)
    if is_follower.exists():
        Follow.objects.filter(user=user, author=author).delete()
    return redirect(reverse('profile', args=[username]))
