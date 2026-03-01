
from django.urls import path
from .views import todays_tips

app_name = "tips"   # namespacing for {% url 'tips:...' %}

urlpatterns = [
    path("today/", todays_tips, name="tips"),  # navbar uses {% url 'tips:tips' %}
]

