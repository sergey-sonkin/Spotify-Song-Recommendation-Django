from django.urls import path

from songs import views

app_name = "songs"
urlpatterns = [
    path("process_form/", views.process_form, name="process_form"),
    path("submit/", views.submit, name="submit"),
    path("<int:song_id>/", views.detail, name="detail"),
]
