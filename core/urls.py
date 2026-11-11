from django.contrib.auth import views as auth_views
from django.urls import path

from . import views
from .forms import LoginForm

urlpatterns = [
    path("", views.inicio, name="inicio"),
    path(
        "login/",
        auth_views.LoginView.as_view(
            template_name="core/login.html",
            authentication_form=LoginForm,
            redirect_authenticated_user=True,
        ),
        name="login",
    ),
    path("sair/", auth_views.LogoutView.as_view(), name="logout"),
    # Doações (rotas específicas antes das rotas genéricas)
    path("doacoes/", views.doacao_lista, name="doacao_lista"),
    path("doacoes/nova/", views.doacao_nova, name="doacao_nova"),
    path("doacoes/<int:pk>/confirmacao/", views.doacao_sucesso, name="doacao_sucesso"),
    # Voluntários, doadores, projetos e campanhas
    path("<slug:entidade>/", views.lista, name="lista"),
    path("<slug:entidade>/novo/", views.novo, name="novo"),
    path("<slug:entidade>/<int:pk>/editar/", views.editar, name="editar"),
]
