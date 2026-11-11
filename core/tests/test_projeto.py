from datetime import date
from django.core.exceptions import ValidationError
from django.test import TestCase
from core.models import ProjetoSocial


class ProjetoSocialTest(TestCase):

    def test_criar_projeto(self):
        projeto = ProjetoSocial.objects.create(
            nome="Campanha de Alimentos",
            descricao="Arrecadação de alimentos.",
            data_inicio=date(2026, 1, 10)
        )

        self.assertEqual(
            projeto.status,
            ProjetoSocial.Status.PLANEJADO
        )
        self.assertIsNone(projeto.data_fim)

    def test_representacao_textual(self):
        projeto = ProjetoSocial.objects.create(
            nome="Projeto Solidariedade",
            descricao="Ação social.",
            data_inicio=date(2026, 1, 10)
        )

        self.assertEqual(str(projeto), "Projeto Solidariedade")

    def test_data_final_anterior_a_inicial_e_invalida(self):
        projeto = ProjetoSocial(
            nome="Projeto inválido",
            descricao="Teste de período.",
            data_inicio=date(2026, 5, 10),
            data_fim=date(2026, 5, 1)
        )

        with self.assertRaises(ValidationError):
            projeto.full_clean()

    def test_periodo_valido(self):
        projeto = ProjetoSocial(
            nome="Projeto válido",
            descricao="Teste de período.",
            data_inicio=date(2026, 5, 1),
            data_fim=date(2026, 5, 10)
        )

        projeto.full_clean()