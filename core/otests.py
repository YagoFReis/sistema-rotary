"""Testes unitários e de integração do MVP."""
import datetime
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .forms import DoacaoForm
from .models import Campanha, Doacao, Doador, ProjetoSocial, Voluntario, formatar_moeda


def hoje():
    return timezone.localdate()


def criar_projeto(**extra):
    dados = {"nome": "Projeto Escola", "descricao": "Apoio escolar", "data_inicio": hoje()}
    dados.update(extra)
    return ProjetoSocial.objects.create(**dados)


def criar_campanha(projeto=None, **extra):
    dados = {
        "nome": "Campanha Solidária",
        "objetivo": "Arrecadar material escolar",
        "data_inicio": hoje(),
        "projeto": projeto or criar_projeto(),
    }
    dados.update(extra)
    return Campanha.objects.create(**dados)


def criar_doador(**extra):
    dados = {"nome": "Empresa Exemplo Ltda.", "tipo_doador": Doador.Tipo.JURIDICA}
    dados.update(extra)
    return Doador.objects.create(**dados)


class ModelosTests(TestCase):
    def test_doacao_financeira_exige_valor_positivo(self):
        doador = criar_doador()
        for valor in (None, Decimal("0"), Decimal("-10")):
            doacao = Doacao(
                doador=doador,
                tipo_doacao=Doacao.Tipo.FINANCEIRA,
                valor=valor,
                data_recebimento=hoje(),
            )
            with self.assertRaises(ValidationError) as ctx:
                doacao.full_clean()
            self.assertIn("valor", ctx.exception.message_dict)

    def test_doacao_material_exige_descricao(self):
        doacao = Doacao(
            doador=criar_doador(),
            tipo_doacao=Doacao.Tipo.MATERIAL,
            descricao="   ",
            data_recebimento=hoje(),
        )
        with self.assertRaises(ValidationError) as ctx:
            doacao.full_clean()
        self.assertIn("descricao", ctx.exception.message_dict)

    def test_doacao_material_valida_ignora_valor(self):
        doacao = Doacao(
            doador=criar_doador(),
            tipo_doacao=Doacao.Tipo.MATERIAL,
            descricao="10 cestas básicas",
            valor=Decimal("99"),
            data_recebimento=hoje(),
        )
        doacao.full_clean()
        doacao.save()
        doacao.refresh_from_db()
        self.assertIsNone(doacao.valor)
        self.assertIsNone(doacao.valor_formatado)

    def test_codigo_da_doacao(self):
        doacao = Doacao.objects.create(
            doador=criar_doador(),
            tipo_doacao=Doacao.Tipo.FINANCEIRA,
            valor=Decimal("500.00"),
            data_recebimento=hoje(),
        )
        self.assertEqual(doacao.codigo, f"DOA-{doacao.pk:04d}")
        self.assertEqual(doacao.valor_formatado, "R$ 500,00")

    def test_restricao_no_banco_impede_doacao_financeira_sem_valor(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            Doacao.objects.create(
                doador=criar_doador(),
                tipo_doacao=Doacao.Tipo.FINANCEIRA,
                valor=None,
                data_recebimento=hoje(),
            )

    def test_periodo_de_projeto_e_campanha_deve_ser_consistente(self):
        inicio = hoje()
        fim = inicio - datetime.timedelta(days=1)
        with self.assertRaises(ValidationError):
            ProjetoSocial(nome="X", descricao="Y", data_inicio=inicio, data_fim=fim).full_clean()
        with self.assertRaises(ValidationError):
            Campanha(
                nome="X",
                objetivo="Y",
                data_inicio=inicio,
                data_fim=fim,
                projeto=criar_projeto(),
            ).full_clean()

    def test_formatar_moeda(self):
        self.assertEqual(formatar_moeda(Decimal("1234.5")), "R$ 1.234,50")
        self.assertIsNone(formatar_moeda(None))


class FormularioDoacaoTests(TestCase):
    def setUp(self):
        self.doador = criar_doador()

    def dados(self, **extra):
        base = {
            "doador": self.doador.pk,
            "tipo_doacao": "financeira",
            "valor": "500,00",
            "descricao": "",
            "data_recebimento": hoje().isoformat(),
        }
        base.update(extra)
        return base

    def test_aceita_valor_no_formato_brasileiro(self):
        form = DoacaoForm(self.dados(valor="1.500,50"))
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.cleaned_data["valor"], Decimal("1500.50"))

    def test_rejeita_financeira_sem_valor_e_valor_negativo(self):
        self.assertFalse(DoacaoForm(self.dados(valor="")).is_valid())
        self.assertFalse(DoacaoForm(self.dados(valor="-5,00")).is_valid())
        self.assertFalse(DoacaoForm(self.dados(valor="0")).is_valid())

    def test_rejeita_material_sem_descricao(self):
        form = DoacaoForm(self.dados(tipo_doacao="material", valor=""))
        self.assertFalse(form.is_valid())
        self.assertIn("descricao", form.errors)

    def test_descricao_limitada_a_500_caracteres(self):
        form = DoacaoForm(self.dados(descricao="a" * 501))
        self.assertFalse(form.is_valid())


class AutenticacaoTests(TestCase):
    def test_paginas_exigem_login(self):
        urls = [
            reverse("inicio"),
            reverse("lista", args=["voluntarios"]),
            reverse("novo", args=["doadores"]),
            reverse("doacao_lista"),
            reverse("doacao_nova"),
            reverse("doacao_sucesso", args=[1]),
        ]
        for url in urls:
            resposta = self.client.get(url)
            self.assertEqual(resposta.status_code, 302, url)
            self.assertTrue(resposta["Location"].startswith(reverse("login")), url)

    def test_login_e_logout(self):
        get_user_model().objects.create_user("diretor", password="Senha-Forte-123")
        resposta = self.client.post(
            reverse("login"), {"username": "diretor", "password": "Senha-Forte-123"}
        )
        self.assertRedirects(resposta, reverse("inicio"))
        resposta = self.client.post(reverse("logout"))
        self.assertRedirects(resposta, reverse("login"))
        self.assertEqual(self.client.get(reverse("inicio")).status_code, 302)

    def test_login_invalido(self):
        resposta = self.client.post(reverse("login"), {"username": "x", "password": "y"})
        self.assertEqual(resposta.status_code, 200)
        self.assertContains(resposta, "alerta-error")

    def test_senha_armazenada_com_pbkdf2_sha256(self):
        usuario = get_user_model().objects.create_user("u", password="Senha-Forte-123")
        self.assertTrue(usuario.password.startswith("pbkdf2_sha256$"))


class BaseLogadaTestCase(TestCase):
    def setUp(self):
        get_user_model().objects.create_user("diretor", password="Senha-Forte-123")
        self.client.login(username="diretor", password="Senha-Forte-123")


class CadastrosTests(BaseLogadaTestCase):
    def test_painel_mostra_indicadores(self):
        criar_doador()
        Voluntario.objects.create(nome="Maria")
        Doacao.objects.create(
            doador=Doador.objects.first(),
            tipo_doacao=Doacao.Tipo.FINANCEIRA,
            valor=Decimal("1500"),
            data_recebimento=hoje(),
        )
        resposta = self.client.get(reverse("inicio"))
        self.assertEqual(resposta.status_code, 200)
        self.assertContains(resposta, "Sistema de Gerenciamento de Projetos Sociais")
        self.assertContains(resposta, "R$ 1.500,00")
        self.assertContains(resposta, "1 registro")

    def test_cadastrar_e_consultar_voluntario(self):
        resposta = self.client.post(
            reverse("novo", args=["voluntarios"]),
            {"nome": "Maria Souza", "email": "maria@exemplo.org", "telefone": "62 99999-0000", "status": "ativo"},
        )
        self.assertRedirects(resposta, reverse("lista", args=["voluntarios"]))
        self.assertEqual(Voluntario.objects.get().data_cadastro, hoje())
        lista = self.client.get(reverse("lista", args=["voluntarios"]))
        self.assertContains(lista, "Maria Souza")
        busca = self.client.get(reverse("lista", args=["voluntarios"]), {"q": "inexistente"})
        self.assertContains(busca, "Nenhum registro encontrado")

    def test_editar_doador(self):
        doador = criar_doador(nome="Antigo")
        resposta = self.client.post(
            reverse("editar", args=["doadores", doador.pk]),
            {"nome": "Novo Nome", "email": "", "telefone": "", "tipo_doador": "fisica"},
        )
        self.assertRedirects(resposta, reverse("lista", args=["doadores"]))
        doador.refresh_from_db()
        self.assertEqual(doador.nome, "Novo Nome")

    def test_nome_obrigatorio(self):
        resposta = self.client.post(
            reverse("novo", args=["doadores"]), {"nome": "", "tipo_doador": "fisica"}
        )
        self.assertEqual(resposta.status_code, 200)
        self.assertEqual(Doador.objects.count(), 0)

    def test_campanha_depende_de_projeto(self):
        resposta = self.client.get(reverse("novo", args=["campanhas"]))
        self.assertRedirects(resposta, reverse("novo", args=["projetos"]))

    def test_cadastrar_campanha_vinculada_a_projeto(self):
        projeto = criar_projeto()
        resposta = self.client.post(
            reverse("novo", args=["campanhas"]),
            {
                "nome": "Campanha do Agasalho",
                "projeto": projeto.pk,
                "objetivo": "Arrecadar agasalhos",
                "descricao": "",
                "data_inicio": hoje().isoformat(),
                "data_fim": "",
                "status": "ativa",
            },
        )
        self.assertRedirects(resposta, reverse("lista", args=["campanhas"]))
        self.assertEqual(Campanha.objects.get().projeto, projeto)

    def test_entidade_inexistente_retorna_404(self):
        self.assertEqual(self.client.get("/inexistente/").status_code, 404)

    def test_paginacao_com_vinte_registros_por_pagina(self):
        Voluntario.objects.bulk_create([Voluntario(nome=f"Voluntario {i:03d}") for i in range(45)])
        pagina1 = self.client.get(reverse("lista", args=["voluntarios"]))
        self.assertEqual(len(pagina1.context["linhas"]), 20)
        pagina3 = self.client.get(reverse("lista", args=["voluntarios"]), {"page": 3})
        self.assertEqual(len(pagina3.context["linhas"]), 5)


class DoacaoFluxoTests(BaseLogadaTestCase):
    def setUp(self):
        super().setUp()
        self.doador = criar_doador()
        self.campanha = criar_campanha()

    def test_sem_doador_redireciona_para_cadastro(self):
        Doador.objects.all().delete()
        resposta = self.client.get(reverse("doacao_nova"))
        self.assertRedirects(resposta, reverse("novo", args=["doadores"]))

    def test_formulario_traz_data_de_hoje(self):
        resposta = self.client.get(reverse("doacao_nova"))
        self.assertContains(resposta, hoje().isoformat())

    def test_registrar_doacao_financeira_e_ver_confirmacao(self):
        resposta = self.client.post(
            reverse("doacao_nova"),
            {
                "doador": self.doador.pk,
                "tipo_doacao": "financeira",
                "valor": "500,00",
                "campanha": self.campanha.pk,
                "descricao": "Doação para apoiar as ações sociais da instituição.",
                "data_recebimento": "2026-11-06",
            },
        )
        doacao = Doacao.objects.get()
        self.assertRedirects(resposta, reverse("doacao_sucesso", args=[doacao.pk]))
        self.assertEqual(doacao.valor, Decimal("500.00"))

        pagina = self.client.get(reverse("doacao_sucesso", args=[doacao.pk]))
        self.assertContains(pagina, "Doação registrada com sucesso!")
        self.assertContains(pagina, "Empresa Exemplo Ltda.")
        self.assertContains(pagina, "Campanha Solidária")
        self.assertContains(pagina, "Financeira")
        self.assertContains(pagina, "R$ 500,00")
        self.assertContains(pagina, "06/11/2026")
        self.assertContains(pagina, doacao.codigo)

    def test_registrar_doacao_material_sem_campanha(self):
        resposta = self.client.post(
            reverse("doacao_nova"),
            {
                "doador": self.doador.pk,
                "tipo_doacao": "material",
                "valor": "",
                "campanha": "",
                "descricao": "20 cobertores",
                "data_recebimento": hoje().isoformat(),
            },
        )
        doacao = Doacao.objects.get()
        self.assertRedirects(resposta, reverse("doacao_sucesso", args=[doacao.pk]))
        pagina = self.client.get(reverse("doacao_sucesso", args=[doacao.pk]))
        self.assertContains(pagina, "Material")
        self.assertContains(pagina, "20 cobertores")
        self.assertContains(pagina, "Sem campanha")
        self.assertNotContains(pagina, "R$ ")

    def test_doacao_financeira_sem_valor_nao_e_salva(self):
        resposta = self.client.post(
            reverse("doacao_nova"),
            {
                "doador": self.doador.pk,
                "tipo_doacao": "financeira",
                "valor": "",
                "data_recebimento": hoje().isoformat(),
            },
        )
        self.assertEqual(resposta.status_code, 200)
        self.assertContains(resposta, "valor maior que zero")
        self.assertEqual(Doacao.objects.count(), 0)

    def test_doacao_material_sem_descricao_nao_e_salva(self):
        resposta = self.client.post(
            reverse("doacao_nova"),
            {
                "doador": self.doador.pk,
                "tipo_doacao": "material",
                "descricao": "",
                "data_recebimento": hoje().isoformat(),
            },
        )
        self.assertEqual(resposta.status_code, 200)
        self.assertContains(resposta, "Descreva o item recebido")
        self.assertEqual(Doacao.objects.count(), 0)

    def test_listagem_de_doacoes_e_busca(self):
        Doacao.objects.create(
            doador=self.doador,
            tipo_doacao=Doacao.Tipo.FINANCEIRA,
            valor=Decimal("250"),
            data_recebimento=hoje(),
        )
        lista = self.client.get(reverse("doacao_lista"))
        self.assertContains(lista, "R$ 250,00")
        self.assertContains(lista, "Empresa Exemplo Ltda.")
        vazia = self.client.get(reverse("doacao_lista"), {"q": "zzz"})
        self.assertContains(vazia, "Nenhum registro encontrado")

    def test_confirmacao_de_doacao_inexistente(self):
        self.assertEqual(self.client.get(reverse("doacao_sucesso", args=[9999])).status_code, 404)
