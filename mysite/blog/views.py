from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404
from django.http import Http404, HttpResponse
from django.views.decorators.http import require_POST

from .models import Post
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.views.generic import ListView
from .forms import EmailPostForm, LoginForm, UserRegistration, CommentForm
# Create your views here.
from django.core.mail import send_mail
from django.contrib.auth import authenticate, login


class PostListView(ListView):
    queryset = Post.published.all()
    context_object_name = 'posts'
    paginate_by = 3
    template_name = 'blog/post/list.html'


def post_list(request):
    post_list = Post.published.all()
    paginator = Paginator(post_list, 3)
    page_number = request.GET.get('page', 1)
    try:
        posts = paginator.page(page_number)
    except PageNotAnInteger:
        posts = paginator.page(1)
    except EmptyPage:
        posts = paginator.page(paginator.num_pages)
    return render(request,
                  'blog/post/list.html',
                  {'posts': posts})


def post_detail(request, year, month, day, post):
    post = get_object_or_404(Post,
                             status=Post.Status.PUBLISHED,
                             slug=post,
                             publish__year=year,
                             publish__month=month,
                             publish__day=day)
    comments = post.comments.filter(active=True)
    form = CommentForm()
    return render(request,
                  'blog/post/detail.html',
                  {'post': post,
                   'comments': comments,
                   'form': form})


def post_share(request, post_id):
    post = get_object_or_404(Post, id=post_id, status=Post.Status.PUBLISHED)
    sent = False
    if request.method == 'POST':
        form = EmailPostForm(request.POST)
        if form.is_valid():
            cd = form.cleaned_data
            post_url = request.build_absolute_uri(post.get_absolute_url())
            subject = f"{cd['name']} recommends you read {post.title}"
            message = f"Read {post.title} at {post_url}\n\n {cd['name']}\'s comments: {cd['comments']}"
            send_mail(subject, message, 'django.email.post.recomendation@gmail.com', [cd['to']])
            sent = True
    else:
        form = EmailPostForm()
    return render(request, 'blog/post/share.html', {'post': post,
                                                    'form': form,
                                                    'sent': sent})


def register(request):
    if request.method == 'POST':
        form = UserRegistration(request.POST)
        if form.is_valid():
            new_user = form.save(commit=False)
            new_user.set_password(form.cleaned_data['password'])
            new_user.save()
            cd = form.cleaned_data
            subject = f"Welcome {cd['first_name']} to MyBlog!"
            message = f"Thank you {cd['first_name']} for joining MyBlog.\n" \
                      f" Your account {cd['username']} has been successfully created!" \
                      f"Best wishes\n" \
                      f"M.P."
            send_mail(subject, message, 'django.email.post.recomendation@gmail.com', [cd['email']])
            return render(request, 'registration/register_done.html', {'new_user': new_user})
    else:
        form = UserRegistration()
    return render(request, 'registration/register.html', {'form': form})


@require_POST
@login_required
def post_comment(request, post_id):
    post = get_object_or_404(Post, id=post_id, status=Post.Status.PUBLISHED)
    comment = None
    form = CommentForm(data=request.POST)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.post = post
        comment.user = request.user
        comment.save()
    return render(request, 'blog/post/comment.html',
                  {'post': post,
                   'form': form,
                   'comment': comment})



# def user_login(request):
#     print('test')
#     if request.method == 'POST':
#         form = LoginForm(request.POST)
#         print('0')
#         if form.is_valid():
#             cd = form.cleaned_data
#             user = authenticate(request,
#                                 username=cd['username'],
#                                 password=cd['password'])
#             print('1')
#             if user is not None:
#                 if user.is_active:
#                     login(request, user)
#                     print('2')
#                     return HttpResponse('Authenticated successfully')
#                 else:
#                     print('3')
#                     return HttpResponse('Disabled account')
#             else:
#                 return HttpResponse('Invalid login')
#     else:
#         form = LoginForm()
#         print('5')
#     return render(request, 'blog/account/login.html', {'form': form})
