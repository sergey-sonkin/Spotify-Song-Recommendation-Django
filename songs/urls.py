from django.urls import path

from songs import views

app_name = "songs"
urlpatterns = [
    path("<int:song_id>/", views.detail, name="detail"),
    path("", views.submit, name="submit"),
]
