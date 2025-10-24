
from django.contrib.auth.decorators import login_required
from django.urls import path
from rest_framework.routers import SimpleRouter

from plugin_megaexample import views

router = SimpleRouter()
urlpatterns = [
    path('', views.ProjectListView.as_view(), name='index'),
    path(
        'upload-file/',
        login_required(views.UploadFileApiView.as_view()),
        name='upload-file',
    ),
]
urlpatterns += router.urls
