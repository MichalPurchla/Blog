from django.urls import path
from . import views
from django.contrib.auth import views as auth_views


app_name = 'blog'

urlpatterns = [
    path('', views.PostListView.as_view(), name='post_list'),
    path('draft/', views.PostDraftListView.as_view(), name='post_drafted_list'),
    path('<int:year>/<int:month>/<int:day>/<slug:post>/',
         views.post_detail,
         name='post_detail'),
    path('draft/<int:year>/<int:month>/<int:day>/<slug:post>/', views.post_draft_detail, name='post_draft_detail'),
    path('<int:post_id>/share/', views.post_share, name='post_share'),
    path('add_post/', views.PostCreateView.as_view(), name='create_post'),
    path('update_post/<int:pk>/', views.PostUpdateView.as_view(), name='update_post'),
    path('login/', auth_views.LoginView.as_view(next_page='blog:post_list'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(template_name='registration/logout.html',
                                                  next_page=None), name='logout'),
    path('register/', views.register, name='register'),
    path('<int:post_id>/comment/', views.post_comment, name='post_comment'),
]
