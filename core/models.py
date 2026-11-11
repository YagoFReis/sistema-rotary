"""Modelos das cinco entidades do sistema e suas regras de negócio."""
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.db import models
from django.db.models import Q
from django.utils import timezone


def hoje():
    return timezone.localdate()


def formatar_moeda(valor):
    """Formata um valor como moeda brasileira: R$ 1.234,50."""
    if valor is None:
        return None
    texto = f"{Decimal(valor):,.2f}"
    texto = texto.replace(",", "X").replace(".", ",").replace("X", ".")
    return f"R$ {texto}"


validador_telefone = RegexValidator(
    regex=r"^[0-9()+\-\s]{8,20}$",
    message="Informe um telefone válido, com DDD (somente números, espaços, +, - e parênteses).",
)


class Voluntario(models.Model):
    class Status(models.TextChoices):
        ATIVO = "ativo", "Ativo"
        INATIVO = "inativo", "Inativo"

    id_voluntario = models.AutoField(primary_key=True)
    nome = models.CharField("Nome", max_length=150)
    email = models.EmailField("E-mail", blank=True)
    telefone = models.CharField(
        "Telefone", max_length=20, blank=True, validators=[validador_telefone]
    )
    data_cadastro = models.DateField("Data de cadastro", default=hoje, editable=False)
    status = models.CharField(
        "Situação", max_length=10, choices=Status.choices, default=Status.ATIVO
    )

    class Meta:
        ordering = ["nome"]
        verbose_name = "voluntário"
        verbose_name_plural = "voluntários"

    def __str__(self):
        return self.nome


class Doador(models.Model):
    class Tipo(models.TextChoices):
        FISICA = "fisica", "Pessoa física"
        JURIDICA = "juridica", "Pessoa jurídica"

    id_doador = models.AutoField(primary_key=True)
    nome = models.CharField("Nome", max_length=150)
    email = models.EmailField("E-mail", blank=True)
    telefone = models.CharField(
        "Telefone", max_length=20, blank=True, validators=[validador_telefone]
    )
    tipo_doador = models.CharField(
        "Tipo de doador", max_length=10, choices=Tipo.choices, default=Tipo.FISICA
    )
    data_cadastro = models.DateField("Data de cadastro", default=hoje, editable=False)

    class Meta:
        ordering = ["nome"]
        verbose_name = "doador"
        verbose_name_plural = "doadores"

    def __str__(self):
        return self.nome


def _validar_periodo(data_inicio, data_fim):
    if data_inicio and data_fim and data_fim < data_inicio:
        raise ValidationError(
            {"data_fim": "A data de término não pode ser anterior à data de início."}
        )


class ProjetoSocial(models.Model):
    class Status(models.TextChoices):
        PLANEJADO = "planejado", "Planejado"
        EM_ANDAMENTO = "em_andamento", "Em andamento"
        CONCLUIDO = "concluido", "Concluído"
        CANCELADO = "cancelado", "Cancelado"

    id_projeto = models.AutoField(primary_key=True)
    nome = models.CharField("Nome", max_length=150)
    descricao = models.TextField("Descrição", max_length=1000)
    data_inicio = models.DateField("Data de início")
    data_fim = models.DateField("Data de término", null=True, blank=True)
    status = models.CharField(
        "Situação", max_length=15, choices=Status.choices, default=Status.PLANEJADO
    )

    class Meta:
        ordering = ["-data_inicio", "nome"]
        verbose_name = "projeto social"
        verbose_name_plural = "projetos sociais"

    def __str__(self):
        return self.nome

    def clean(self):
        super().clean()
        _validar_periodo(self.data_inicio, self.data_fim)


class Campanha(models.Model):
    class Status(models.TextChoices):
        PLANEJADA = "planejada", "Planejada"
        ATIVA = "ativa", "Ativa"
        CONCLUIDA = "concluida", "Concluída"
        CANCELADA = "cancelada", "Cancelada"

    id_campanha = models.AutoField(primary_key=True)
    nome = models.CharField("Nome", max_length=150)
    descricao = models.TextField("Descrição", max_length=1000, blank=True)
    objetivo = models.CharField("Objetivo", max_length=255)
    data_inicio = models.DateField("Data de início")
    data_fim = models.DateField("Data de término", null=True, blank=True)
    status = models.CharField(
        "Situação", max_length=10, choices=Status.choices, default=Status.PLANEJADA
    )
    projeto = models.ForeignKey(
        ProjetoSocial,
        verbose_name="Projeto",
        on_delete=models.PROTECT,
        related_name="campanhas",
    )

    class Meta:
        ordering = ["-data_inicio", "nome"]
        verbose_name = "campanha"
        verbose_name_plural = "campanhas"

    def __str__(self):
        return self.nome

    def clean(self):
        super().clean()
        _validar_periodo(self.data_inicio, self.data_fim)


class Doacao(models.Model):
    class Tipo(models.TextChoices):
        FINANCEIRA = "financeira", "Financeira"
        MATERIAL = "material", "Material"

    id_doacao = models.AutoField(primary_key=True)
    doador = models.ForeignKey(
        Doador, verbose_name="Doador", on_delete=models.PROTECT, related_name="doacoes"
    )
    campanha = models.ForeignKey(
        Campanha,
        verbose_name="Campanha relacionada",
        on_delete=models.PROTECT,
        related_name="doacoes",
        null=True,
        blank=True,
    )
    tipo_doacao = models.CharField(
        "Tipo de doação", max_length=10, choices=Tipo.choices, default=Tipo.FINANCEIRA
    )
    descricao = models.TextField("Descrição", max_length=500, blank=True)
    valor = models.DecimalField(
        "Valor (R$)", max_digits=12, decimal_places=2, null=True, blank=True
    )
    data_recebimento = models.DateField("Data de recebimento")

    class Meta:
        ordering = ["-data_recebimento", "-id_doacao"]
        verbose_name = "doação"
        verbose_name_plural = "doações"
        constraints = [
            models.CheckConstraint(
                condition=Q(tipo_doacao="financeira", valor__gt=0) | Q(tipo_doacao="material"),
                name="doacao_financeira_exige_valor_positivo",
            ),
            models.CheckConstraint(
                condition=Q(tipo_doacao="financeira") | ~Q(descricao=""),
                name="doacao_material_exige_descricao",
            ),
        ]

    def __str__(self):
        return self.codigo or "Nova doação"

    @property
    def codigo(self):
        return f"DOA-{self.pk:04d}" if self.pk else ""

    @property
    def valor_formatado(self):
        """Valor em reais; vazio (None) para doações materiais."""
        if self.tipo_doacao != self.Tipo.FINANCEIRA:
            return None
        return formatar_moeda(self.valor)

    def clean(self):
        super().clean()
        erros = {}
        self.descricao = (self.descricao or "").strip()
        if self.tipo_doacao == self.Tipo.FINANCEIRA:
            if self.valor is None or self.valor <= 0:
                erros["valor"] = "Informe um valor maior que zero para doações financeiras."
        elif self.tipo_doacao == self.Tipo.MATERIAL:
            if not self.descricao:
                erros["descricao"] = "Descreva o item recebido em doações materiais."
            self.valor = None
        if erros:
            raise ValidationError(erros)
