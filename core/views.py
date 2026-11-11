"""Views: recebem as solicitações, exigem autenticação e escolhem a resposta."""
from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q, Sum
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone

from .forms import CampanhaForm, DoacaoForm, DoadorForm, ProjetoSocialForm, VoluntarioForm
from .models import Campanha, Doacao, Doador, ProjetoSocial, Voluntario, formatar_moeda

POR_PAGINA = 20

# Configuração das quatro entidades de cadastro simples.
ENTIDADES = {
    "voluntarios": {
        "model": Voluntario,
        "form": VoluntarioForm,
        "singular": "Voluntário",
        "plural": "Voluntários",
        "subtitulo": "Gerencie os voluntários da instituição.",
        "icone": "bi-people-fill",
        "busca": ["nome", "email", "telefone"],
        "relacionados": [],
        "colunas": [
            ("Nome", "nome"),
            ("E-mail", "email"),
            ("Telefone", "telefone"),
            ("Situação", "get_status_display"),
            ("Cadastro", "data_cadastro"),
        ],
    },
    "doadores": {
        "model": Doador,
        "form": DoadorForm,
        "singular": "Doador",
        "plural": "Doadores",
        "subtitulo": "Cadastre e consulte doadores.",
        "icone": "bi-heart-fill",
        "busca": ["nome", "email", "telefone"],
        "relacionados": [],
        "colunas": [
            ("Nome", "nome"),
            ("Tipo", "get_tipo_doador_display"),
            ("E-mail", "email"),
            ("Telefone", "telefone"),
            ("Cadastro", "data_cadastro"),
        ],
    },
    "projetos": {
        "model": ProjetoSocial,
        "form": ProjetoSocialForm,
        "singular": "Projeto",
        "plural": "Projetos",
        "subtitulo": "Acompanhe os projetos sociais.",
        "icone": "bi-folder-fill",
        "busca": ["nome", "descricao"],
        "relacionados": [],
        "colunas": [
            ("Nome", "nome"),
            ("Situação", "get_status_display"),
            ("Início", "data_inicio"),
            ("Término", "data_fim"),
        ],
    },
    "campanhas": {
        "model": Campanha,
        "form": CampanhaForm,
        "singular": "Campanha",
        "plural": "Campanhas",
        "subtitulo": "Organize campanhas e eventos.",
        "icone": "bi-megaphone-fill",
        "busca": ["nome", "objetivo", "projeto__nome"],
        "relacionados": ["projeto"],
        "colunas": [
            ("Nome", "nome"),
            ("Projeto", "projeto"),
            ("Objetivo", "objetivo"),
            ("Situação", "get_status_display"),
            ("Início", "data_inicio"),
        ],
    },
}

COLUNAS_DOACAO = [
    ("Código", "codigo"),
    ("Doador", "doador"),
    ("Tipo", "get_tipo_doacao_display"),
    ("Valor", "valor_formatado"),
    ("Campanha", "campanha"),
    ("Recebimento", "data_recebimento"),
]


def _config(entidade):
    config = ENTIDADES.get(entidade)
    if config is None:
        raise Http404("Página não encontrada.")
    return config


def _celulas(obj, colunas):
    valores = []
    for _, atributo in colunas:
        valor = getattr(obj, atributo)
        if callable(valor):
            valor = valor()
        valores.append(valor)
    return valores


def _buscar(queryset, termo, campos):
    if not termo:
        return queryset
    filtro = Q()
    for campo in campos:
        filtro |= Q(**{f"{campo}__icontains": termo})
    return queryset.filter(filtro)


def _montar_lista(request, queryset, colunas, campos_busca, contexto, url_editar=None):
    termo = request.GET.get("q", "").strip()
    queryset = _buscar(queryset, termo, campos_busca)
    pagina = Paginator(queryset, POR_PAGINA).get_page(request.GET.get("page"))
    linhas = [
        {
            "celulas": _celulas(obj, colunas),
            "url_editar": url_editar(obj) if url_editar else None,
        }
        for obj in pagina
    ]
    contexto.update(
        {
            "colunas": [titulo for titulo, _ in colunas],
            "linhas": linhas,
            "pagina": pagina,
            "q": termo,
            "ncols": len(colunas) + (1 if url_editar else 0),
            "mostrar_acoes": url_editar is not None,
        }
    )
    return render(request, "core/lista.html", contexto)


@login_required
def inicio(request):
    total_financeiro = (
        Doacao.objects.filter(tipo_doacao=Doacao.Tipo.FINANCEIRA).aggregate(total=Sum("valor"))[
            "total"
        ]
        or Decimal("0")
    )
    cartoes = [
        {
            "classe": "voluntarios",
            "titulo": "Voluntários",
            "descricao": "Gerencie os voluntários da instituição.",
            "icone": "bi-people-fill",
            "url": reverse("lista", args=["voluntarios"]),
            "total": Voluntario.objects.count(),
        },
        {
            "classe": "doadores",
            "titulo": "Doadores",
            "descricao": "Cadastre e consulte doadores.",
            "icone": "bi-heart-fill",
            "url": reverse("lista", args=["doadores"]),
            "total": Doador.objects.count(),
        },
        {
            "classe": "projetos",
            "titulo": "Projetos",
            "descricao": "Acompanhe os projetos sociais.",
            "icone": "bi-folder-fill",
            "url": reverse("lista", args=["projetos"]),
            "total": ProjetoSocial.objects.count(),
        },
        {
            "classe": "campanhas",
            "titulo": "Campanhas",
            "descricao": "Organize campanhas e eventos.",
            "icone": "bi-megaphone-fill",
            "url": reverse("lista", args=["campanhas"]),
            "total": Campanha.objects.count(),
        },
        {
            "classe": "doacoes",
            "titulo": "Doações",
            "descricao": "Registre e consulte doações.",
            "icone": "bi-box2-heart-fill",
            "url": reverse("doacao_lista"),
            "total": Doacao.objects.count(),
        },
    ]
    return render(
        request,
        "core/inicio.html",
        {
            "secao": "inicio",
            "cartoes": cartoes,
            "total_financeiro": formatar_moeda(total_financeiro),
        },
    )


@login_required
def lista(request, entidade):
    config = _config(entidade)
    queryset = config["model"].objects.all()
    if config["relacionados"]:
        queryset = queryset.select_related(*config["relacionados"])
    contexto = {
        "secao": entidade,
        "titulo": config["plural"],
        "subtitulo": config["subtitulo"],
        "icone": config["icone"],
        "url_novo": reverse("novo", args=[entidade]),
        "rotulo_novo": f"Novo(a) {config['singular'].lower()}",
    }
    return _montar_lista(
        request,
        queryset,
        config["colunas"],
        config["busca"],
        contexto,
        url_editar=lambda obj: reverse("editar", args=[entidade, obj.pk]),
    )


def _formulario_entidade(request, entidade, instancia=None):
    config = _config(entidade)

    if entidade == "campanhas" and instancia is None and not ProjetoSocial.objects.exists():
        messages.warning(
            request, "Cadastre ao menos um projeto antes de criar uma campanha."
        )
        return redirect("novo", entidade="projetos")

    form = config["form"](request.POST or None, instance=instancia)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, f"{config['singular']} salvo(a) com sucesso.")
        return redirect("lista", entidade=entidade)

    acao = "Editar" if instancia else "Novo(a)"
    return render(
        request,
        "core/formulario.html",
        {
            "secao": entidade,
            "titulo": f"{acao} {config['singular'].lower()}",
            "icone": config["icone"],
            "form": form,
            "url_cancelar": reverse("lista", args=[entidade]),
        },
    )


@login_required
def novo(request, entidade):
    return _formulario_entidade(request, entidade)


@login_required
def editar(request, entidade, pk):
    config = _config(entidade)
    instancia = get_object_or_404(config["model"], pk=pk)
    return _formulario_entidade(request, entidade, instancia)


@login_required
def doacao_lista(request):
    queryset = Doacao.objects.select_related("doador", "campanha")
    contexto = {
        "secao": "doacoes",
        "titulo": "Doações",
        "subtitulo": "Registre e consulte doações.",
        "icone": "bi-box2-heart-fill",
        "url_novo": reverse("doacao_nova"),
        "rotulo_novo": "Registrar doação",
    }
    return _montar_lista(
        request,
        queryset,
        COLUNAS_DOACAO,
        ["doador__nome", "campanha__nome", "descricao"],
        contexto,
    )


@login_required
def doacao_nova(request):
    if not Doador.objects.exists():
        messages.warning(request, "Cadastre ao menos um doador antes de registrar uma doação.")
        return redirect("novo", entidade="doadores")

    if request.method == "POST":
        form = DoacaoForm(request.POST)
        if form.is_valid():
            doacao = form.save()
            return redirect("doacao_sucesso", pk=doacao.pk)
    else:
        form = DoacaoForm(initial={"data_recebimento": timezone.localdate()})

    return render(request, "core/doacao_form.html", {"secao": "doacoes", "form": form})


@login_required
def doacao_sucesso(request, pk):
    # Os dados exibidos vêm do registro efetivamente salvo no banco.
    doacao = get_object_or_404(Doacao.objects.select_related("doador", "campanha"), pk=pk)
    return render(request, "core/doacao_sucesso.html", {"secao": "doacoes", "doacao": doacao})
