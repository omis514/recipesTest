"""
URL configuration for recipify project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path
from recipes import views
from recipes.views import comment_view
from recipes.views import rating_view

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", views.home, name="home"),
    path("dashboard/", views.dashboard, name="dashboard"),
    path("log_in/", views.LogInView.as_view(), name="log_in"),
    path("log_out/", views.log_out, name="log_out"),
    path("password/", views.PasswordView.as_view(), name="password"),
    path("profile/", views.ProfileUpdateView.as_view(), name="profile"),
    path("sign_up/", views.SignUpView.as_view(), name="sign_up"),
    path("users/", views.user_list, name="user_list"),
    path(
        "reported-recipes/", views.reported_recipes_list, name="reported_recipes_list"
    ),
    path(
        "reported-recipes/<int:recipe_id>/",
        views.recipe_reports_detail,
        name="recipe_reports_detail",
    ),
    path("recipe/create/", views.RecipeCreateView.as_view(), name="recipe_create"),
    path("recipes/<int:pk>/", views.recipe_detail_view, name="recipe_detail"),
    path("recipes/<int:pk>/report/", views.report_recipe, name="report_recipe"),
    path("recipes/", views.recipe_list_view.recipe_list, name="recipe_list"),
    path(
        "recipes/<int:recipe_pk>/comment/", comment_view.add_comment, name="add_comment"
    ),
    path(
        "recipes/comment/<int:comment_pk>/like/",
        comment_view.like_comment,
        name="like_comment",
    ),
    path(
        "recipes/comment/<int:comment_pk>/delete/",
        comment_view.delete_comment,
        name="delete_comment",
    ),
    path(
        "recipes/<int:recipe_pk>/comments/api/",
        comment_view.recipe_comments_api,
        name="recipe_comments_api",
    ),
    path(
        "api/users/mentions/", comment_view.get_user_mentions, name="get_user_mentions"
    ),
    path("recipes/<int:pk>/favorite/", views.toggle_favorite, name="toggle_favorite"),
    path("recipes/<int:recipe_pk>/rate/", rating_view.submit_rating, name="submit_rating"),
    path("recipes/<int:recipe_pk>/rate/delete/", rating_view.delete_rating, name="delete_rating"),
]
urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
