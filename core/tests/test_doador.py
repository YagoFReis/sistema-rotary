from django.test import TestCase
from core.models import Doador


class DoadorTest(TestCase):

    def test_criar_doador(self):
        doador = Doador.objects.create(
            nome="Empresa Solidária",
            email="contato@empresa.com",
            tipo_doador=Doador.Tipo.JURIDICA
        )

        self.assertEqual(doador.nome, "Empresa Solidária")
        self.assertEqual(doador.tipo_doador, "juridica")
        self.assertIsNotNone(doador.data_cadastro)

    def test_tipo_padrao_pessoa_fisica(self):
        doador = Doador.objects.create(nome="Pedro")
        self.assertEqual(doador.tipo_doador, "fisica")

    def test_representacao_textual(self):
        doador = Doador.objects.create(nome="Ana")
        self.assertEqual(str(doador), "Ana")

    def test_ordenacao_por_nome(self):
        Doador.objects.create(nome="Zeca")
        Doador.objects.create(nome="Ana")

        nomes = list(
            Doador.objects.values_list("nome", flat=True)
        )

        self.assertEqual(nomes, ["Ana", "Zeca"])