from django.urls import path
from .views import classify_images

urlpatterns = [
    path('classify/', classify_images, name='classify_images'),
]
