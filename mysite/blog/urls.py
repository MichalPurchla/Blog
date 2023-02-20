from django.urls import path
from . import views
from django.contrib.auth import views as auth_views


app_name = 'blog'

urlpatterns = [
    # path('', views.post_list, name='post_list'),
    # path('<int:id>/', views.post_detail, name='post_detail'),
    path('', views.PostListView.as_view(), name='post_list'),
    path('<int:year>/<int:month>/<int:day>/<slug:post>/',
         views.post_detail,
         name='post_detail'),
    path('<int:post_id>/share/', views.post_share, name='post_share'),
    # path('login/', views.user_login, name='login'),
    path('login/', auth_views.LoginView.as_view(next_page='blog:post_list'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(template_name='registration/logout.html',
                                                  next_page=None), name='logout'),
]
