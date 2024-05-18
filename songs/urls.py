from django.urls import path

from songs import views

app_name = "polls"
urlpatterns = [
    path("<int:song_id>/", views.detail, name="detail"),
]
