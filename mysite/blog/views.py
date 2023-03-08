from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import PermissionRequiredMixin, LoginRequiredMixin
from django.shortcuts import render, get_object_or_404
from django.http import Http404, HttpResponse
from django.urls import reverse_lazy, reverse
from django.utils.text import slugify
from django.views.decorators.http import require_POST
from .models import Post, Comment
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.views.generic import ListView, CreateView, UpdateView
from .forms import EmailPostForm, LoginForm, UserRegistration, CommentForm
from django.core.mail import send_mail
from django.contrib.auth import authenticate, login
from .forms import PostForm
from taggit.models import Tag
from django.db.models import Count
from rest_framework import viewsets
from .serializers import PostSerializer, CommentSerializer


class PostViewSet(viewsets.ModelViewSet):
    queryset = Post.objects.all()
    serializer_class = PostSerializer


class CommentViewSet(viewsets.ModelViewSet):
    queryset = Comment.objects.all()
    serializer_class = CommentSerializer


class PostCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView, ):
    model = Post
    form_class = PostForm
    login_url = 'blog:login'
    template_name = 'blog/post/create_post.html'
    # permission_denied_message = "You don't have permission."
    permission_required = 'blog.add_post'
    # def get_permission_denied_message(self):
    #     return self.permission_denied_message

    def form_valid(self, form):
        form.instance.author = self.request.user
        form.instance.slug = slugify(form.instance.title)
        return super().form_valid(form)

    def get_success_url(self):
        # if self.== 'PB':
        #     self.success_url == 'blog:post_list'
        # else:
        #     self.success_url == 'blog:post_drafted_list'
        return reverse_lazy('blog:post_list')


class PostUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = Post
    fields = ['title', 'body', 'status', 'tags']
    template_name = 'blog/post/update_post.html'
    permission_required = 'blog.change_post'

    def return_to_detail(self):
        post = get_object_or_404(Post, id=self.kwargs['pk'])
        if post.status == 'PB':
            return reverse('blog:post_detail', kwargs={'year': post.publish.year,
                                                       'month': post.publish.month,
                                                       'day': post.publish.day,
                                                       'post': post.slug})
        else:
            return reverse('blog:post_draft_detail', kwargs={'year': post.publish.year,
                                                             'month': post.publish.month,
                                                             'day': post.publish.day,
                                                             'post': post.slug})

    def form_valid(self, form):
        post = get_object_or_404(Post, id=self.kwargs['pk'])
        form.instance.post = post
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['updated'] = True
        ctx['cancel'] = self.return_to_detail()
        return ctx

    def get_success_url(self):
        to_detail = self.return_to_detail()
        return to_detail


class PostListView(ListView):
    queryset = Post.published.all()
    context_object_name = 'posts'
    paginate_by = 5
    template_name = 'blog/post/list.html'


class PostDraftListView(ListView):
    context_object_name = 'posts'
    paginate_by = 5
    template_name = 'blog/post/drafted_list.html'

    def get_queryset(self):
        return Post.drafted.filter(author=self.request.user)


def post_list(request, tag_slug=None):
    post_list = Post.published.all()
    tag = None
    if tag_slug:
        tag = get_object_or_404(Tag, slug=tag_slug)
        post_list = post_list.filter(tags__in=[tag])
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
                  {'posts': posts,
                   'tag': tag})


def post_detail(request, year, month, day, post):
    post = get_object_or_404(Post,
                             status=Post.Status.PUBLISHED,
                             slug=post,
                             publish__year=year,
                             publish__month=month,
                             publish__day=day)
    comments = post.comments.filter(active=True)
    form = CommentForm()
    post_tags_ids = post.tags.values_list('id', flat=True)
    similar_posts = Post.published.filter(tags__in=post_tags_ids) \
        .exclude(id=post.id)
    similar_posts = similar_posts.annotate(same_tags=Count('tags')) \
                                 .order_by('-same_tags', '-publish')[:4]

    return render(request,
                  'blog/post/detail.html',
                  {'post': post,
                   'comments': comments,
                   'form': form,
                   'similar_posts': similar_posts})


def post_draft_detail(request, year, month, day, post):
    post = get_object_or_404(Post,
                             status=Post.Status.DRAFT,
                             slug=post,
                             publish__year=year,
                             publish__month=month,
                             publish__day=day)

    return render(request,
                  'blog/post/detail.html',
                  {'post': post,})


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
