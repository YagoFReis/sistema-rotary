from datetime import date
from django.core.exceptions import ValidationError
from django.test import TestCase
from core.models import ProjetoSocial, Campanha


class CampanhaTest(TestCase):

    def setUp(self):
        self.projeto = ProjetoSocial.objects.create(
            nome="Projeto de Solidariedade",
            descricao="Ações sociais.",
            data_inicio=date(2026, 1, 1)
        )

    def test_criar_campanha(self):
        campanha = Campanha.objects.create(
            nome="Campanha do Agasalho",
            objetivo="Arrecadar roupas.",
            data_inicio=date(2026, 2, 1),
            projeto=self.projeto
        )

        self.assertEqual(
            campanha.status,
            Campanha.Status.PLANEJADA
        )
        self.assertEqual(campanha.projeto, self.projeto)

    def test_representacao_textual(self):
        campanha = Campanha.objects.create(
            nome="Natal Solidário",
            objetivo="Arrecadar brinquedos.",
            data_inicio=date(2026, 2, 1),
            projeto=self.projeto
        )

        self.assertEqual(str(campanha), "Natal Solidário")

    def test_data_final_anterior_a_inicial_e_invalida(self):
        campanha = Campanha(
            nome="Campanha inválida",
            objetivo="Teste.",
            data_inicio=date(2026, 5, 10),
            data_fim=date(2026, 5, 1),
            projeto=self.projeto
        )

        with self.assertRaises(ValidationError):
            campanha.full_clean()

    def test_campanha_sem_projeto_e_invalida(self):
        campanha = Campanha(
            nome="Campanha sem projeto",
            objetivo="Teste.",
            data_inicio=date(2026, 5, 1)
        )

        with self.assertRaises(ValidationError):
            campanha.full_clean()