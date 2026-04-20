from django.urls import path
from .views import response_api, test_chatbot, test_github_api

urlpatterns = [
    # ... other URLs
    path('testChatbot/', test_chatbot, name='testchatbot'),
    # In urls.py
    path('api/test-github/', test_github_api, name='test_github_api'),
    path('api/chatbot/', response_api, name='chatbot_api'),
]