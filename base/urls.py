from django.urls import path
from .views import (
    UserLoginAPIView,
    chatbot_interact,
    categories,
    users_policies,
    displayPolicies,
    joinPolicy,
    add_insurance_policy,
    remove_insurance_policy,
    get_claims,
    submit_claim,
    update_claim_status,
    getUsersCommunicatedWith,
    getChats,
    addMessage,
    deleteMessage
)

urlpatterns = [
    path('login/', UserLoginAPIView.as_view(), name='user-login'),
    
    path('chatbot-interaction/', chatbot_interact, name='chatbot-interation'),
    
    # Categories
    path('categories/', categories, name='list-categories'),
    
    # User Policies
    path('users/<int:userId>/policies/', users_policies, name='user-policies'),
    
    # Display Policies
    path('policies/display/', displayPolicies, name='display-policies'),

    # User join Policy
    path('join-policy/', joinPolicy, name='join-policy'),
    
    # Add Insurance Policy
    path('policies/add/', add_insurance_policy, name='add-insurance-policy'),
    
    # Remove Insurance Policy
    path('policies/remove/', remove_insurance_policy, name='remove-insurance-policy'),
    
    path('get-claims/<int:userId>/', get_claims, name='get-claims'),
    
    # Submit Claim
    path('claims/submit/', submit_claim, name='submit-claim'),
    
    # Update Claim Status
    path('claims/update-status/', update_claim_status, name='update-claim-status'),
    
    
    path('users/communicated-with/', getUsersCommunicatedWith, name='users-communicated-with'),
    path('chats/', getChats, name='get-chats'),
    path('messages/add/', addMessage, name='add-message'),
    path('messages/delete/', deleteMessage, name='delete-message'),
]
