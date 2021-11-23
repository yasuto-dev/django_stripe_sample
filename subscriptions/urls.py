from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='subscriptions-home'),
    path('create/', views.create, name='subscriptions-create'),
    path('confirm/', views.confirm, name='subscriptions-confirm'),
    path('list/', views.list, name='subscriptions-list'),
    path('config/', views.stripe_config),
    path('create-checkout-session/', views.create_checkout_session),
    path('success/', views.success),
    path('cancel/', views.cancel),
    path('webhook/', views.stripe_webhook),
    path('users/mypage/', views.mypage_list, name='mypage'),
    path('users/<int:pk>/edit_post/', views.post_update, name='edit_post'),

]
