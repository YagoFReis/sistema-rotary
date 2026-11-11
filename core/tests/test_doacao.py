
from datetime import date
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db.models.deletion import ProtectedError
from django.test import TestCase

from core.models import Doador, ProjetoSocial, Campanha, Doacao


class DoacaoTest(TestCase):

    def setUp(self):
        self.doador = Doador.objects.create(
            nome="João Silva"
        )

        self.projeto = ProjetoSocial.objects.create(
            nome="Projeto Social",
            descricao="Ações solidárias.",
            data_inicio=date(2026, 1, 1)
        )

        self.campanha = Campanha.objects.create(
            nome="Campanha de Alimentos",
            objetivo="Arrecadar alimentos.",
            data_inicio=date(2026, 2, 1),
            projeto=self.projeto
        )

    def test_criar_doacao_financeira(self):
        doacao = Doacao(
            doador=self.doador,
            campanha=self.campanha,
            tipo_doacao=Doacao.Tipo.FINANCEIRA,
            valor=Decimal("150.00"),
            data_recebimento=date(2026, 3, 1)
        )

        doacao.full_clean()
        doacao.save()

        self.assertEqual(doacao.valor, Decimal("150.00"))

    def test_doacao_financeira_exige_valor_positivo(self):
        doacao = Doacao(
            doador=self.doador,
            tipo_doacao=Doacao.Tipo.FINANCEIRA,
            valor=Decimal("0.00"),
            data_recebimento=date(2026, 3, 1)
        )

        with self.assertRaises(ValidationError):
            doacao.full_clean()

    def test_doacao_material_exige_descricao(self):
        doacao = Doacao(
            doador=self.doador,
            tipo_doacao=Doacao.Tipo.MATERIAL,
            descricao="   ",
            data_recebimento=date(2026, 3, 1)
        )

        with self.assertRaises(ValidationError):
            doacao.full_clean()

    def test_doacao_material_nao_deve_ter_valor(self):
        doacao = Doacao(
            doador=self.doador,
            tipo_doacao=Doacao.Tipo.MATERIAL,
            descricao="Cestas básicas",
            valor=Decimal("100.00"),
            data_recebimento=date(2026, 3, 1)
        )

        doacao.full_clean()

        self.assertIsNone(doacao.valor)

    def test_valor_formatado(self):
        doacao = Doacao(
            doador=self.doador,
            tipo_doacao=Doacao.Tipo.FINANCEIRA,
            valor=Decimal("1234.50"),
            data_recebimento=date(2026, 3, 1)
        )

        self.assertEqual(
            doacao.valor_formatado,
            "R$ 1.234,50"
        )

    def test_codigo_da_doacao(self):
        doacao = Doacao.objects.create(
            doador=self.doador,
            tipo_doacao=Doacao.Tipo.FINANCEIRA,
            valor=Decimal("50.00"),
            data_recebimento=date(2026, 3, 1)
        )

        self.assertEqual(doacao.codigo, f"DOA-{doacao.pk:04d}")

    def test_nao_pode_excluir_doador_com_doacao(self):
        Doacao.objects.create(
            doador=self.doador,
            tipo_doacao=Doacao.Tipo.FINANCEIRA,
            valor=Decimal("50.00"),
            data_recebimento=date(2026, 3, 1)
        )

        with self.assertRaises(ProtectedError):
            self.doador.delete()

    def test_nao_pode_excluir_campanha_com_doacao(self):
        Doacao.objects.create(
            doador=self.doador,
            campanha=self.campanha,
            tipo_doacao=Doacao.Tipo.FINANCEIRA,
            valor=Decimal("50.00"),
            data_recebimento=date(2026, 3, 1)
        )

        with self.assertRaises(ProtectedError):
            self.campanha.delete()
