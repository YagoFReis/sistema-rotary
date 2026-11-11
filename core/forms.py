"""Formulários: validam as entradas no servidor e aplicam o estilo Bootstrap."""
from django import forms
from django.contrib.auth.forms import AuthenticationForm

from .models import Campanha, Doacao, Doador, ProjetoSocial, Voluntario


class BootstrapMixin:
    """Aplica classes Bootstrap aos widgets e marca campos inválidos."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for campo in self.fields.values():
            widget = campo.widget
            if isinstance(widget, (forms.RadioSelect, forms.CheckboxInput)):
                classe = "form-check-input"
            elif isinstance(widget, forms.Select):
                classe = "form-select"
            else:
                classe = "form-control"
            widget.attrs["class"] = f"{widget.attrs.get('class', '')} {classe}".strip()

    def full_clean(self):
        super().full_clean()
        if self.is_bound:
            for nome in self.errors:
                if nome in self.fields:
                    widget = self.fields[nome].widget
                    widget.attrs["class"] = f"{widget.attrs.get('class', '')} is-invalid".strip()


def _widget_data():
    return forms.DateInput(format="%Y-%m-%d", attrs={"type": "date"})


class LoginForm(BootstrapMixin, AuthenticationForm):
    username = forms.CharField(
        label="Usuário",
        widget=forms.TextInput(attrs={"autofocus": True, "autocomplete": "username"}),
    )
    password = forms.CharField(
        label="Senha",
        strip=False,
        widget=forms.PasswordInput(attrs={"autocomplete": "current-password"}),
    )


class VoluntarioForm(BootstrapMixin, forms.ModelForm):
    class Meta:
        model = Voluntario
        fields = ["nome", "email", "telefone", "status"]


class DoadorForm(BootstrapMixin, forms.ModelForm):
    class Meta:
        model = Doador
        fields = ["nome", "email", "telefone", "tipo_doador"]


class ProjetoSocialForm(BootstrapMixin, forms.ModelForm):
    class Meta:
        model = ProjetoSocial
        fields = ["nome", "descricao", "data_inicio", "data_fim", "status"]
        widgets = {
            "descricao": forms.Textarea(attrs={"rows": 4}),
            "data_inicio": _widget_data(),
            "data_fim": _widget_data(),
        }


class CampanhaForm(BootstrapMixin, forms.ModelForm):
    class Meta:
        model = Campanha
        fields = ["nome", "projeto", "objetivo", "descricao", "data_inicio", "data_fim", "status"]
        widgets = {
            "descricao": forms.Textarea(attrs={"rows": 3}),
            "data_inicio": _widget_data(),
            "data_fim": _widget_data(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["projeto"].empty_label = "Selecione o projeto"


class DoacaoForm(BootstrapMixin, forms.ModelForm):
    # Aceita valores no formato brasileiro (ex.: 1.500,00 ou 500,00).
    valor = forms.DecimalField(
        label="Valor (R$)",
        required=False,
        max_digits=12,
        decimal_places=2,
        localize=True,
        widget=forms.TextInput(attrs={"inputmode": "decimal", "placeholder": "0,00"}),
    )

    class Meta:
        model = Doacao
        fields = ["doador", "tipo_doacao", "valor", "campanha", "descricao", "data_recebimento"]
        widgets = {
            "tipo_doacao": forms.RadioSelect(),
            "descricao": forms.Textarea(attrs={"rows": 3, "maxlength": 500}),
            "data_recebimento": _widget_data(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["doador"].empty_label = "Selecione o doador"
        self.fields["campanha"].empty_label = "Nenhuma (opcional)"
        self.fields["doador"].queryset = Doador.objects.order_by("nome")
        self.fields["campanha"].queryset = Campanha.objects.order_by("nome")
