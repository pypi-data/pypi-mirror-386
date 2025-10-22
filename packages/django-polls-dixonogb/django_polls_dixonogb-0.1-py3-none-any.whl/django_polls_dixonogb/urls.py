from django.urls import path

from . import views


# ----------------------------------------------------------

# app_name = "polls" #For Namespacing URL names when using the {% url %} template tag from index.html link.
# urlpatterns = [
#     # ex: /polls/
#     path("", views.index, name="index"),
#     # ex: /polls/34/
#     path("<int:question_id>/", views.detail, name="detail"),
#     # ex: /polls/34/results/
#     path("<int:question_id>/results/", views.results, name="results"),
#     # ex: /polls/34/vote/
#     path("<int:question_id>/vote/", views.vote, name="vote"),
# ]

app_name = "polls" #For generic views with less code.
urlpatterns = [
    path("", views.IndexView.as_view(), name="index"),
    path("<int:pk>/", views.DetailView.as_view(), name="detail"),
    path("<int:pk>/results/", views.ResultsView.as_view(), name="results"),
    path("<int:question_id>/vote/", views.vote, name="vote"),
]