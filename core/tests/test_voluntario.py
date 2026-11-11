
from django.test import TestCase
from core.models import Voluntario


class VoluntarioTest(TestCase):

    def test_criar_voluntario(self):
        voluntario = Voluntario.objects.create(
            nome="João Silva",
            email="joao@email.com",
            telefone="62999999999"
        )

        self.assertEqual(voluntario.nome, "João Silva")
        self.assertEqual(voluntario.status, Voluntario.Status.ATIVO)
        self.assertIsNotNone(voluntario.data_cadastro)

    def test_status_padrao_ativo(self):
        voluntario = Voluntario.objects.create(nome="Maria")

        self.assertEqual(voluntario.status, "ativo")

    def test_representacao_textual(self):
        voluntario = Voluntario.objects.create(nome="Carlos")

        self.assertEqual(str(voluntario), "Carlos")

    def test_ordenacao_por_nome(self):
        Voluntario.objects.create(nome="Zeca")
        Voluntario.objects.create(nome="Ana")

        nomes = list(
            Voluntario.objects.values_list("nome", flat=True)
        )

        self.assertEqual(nomes, ["Ana", "Zeca"])
