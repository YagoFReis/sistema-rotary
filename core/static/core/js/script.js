/* Preferências de acessibilidade e interações gerais da interface. */
(function () {
  "use strict";

  var raiz = document.documentElement;
  var TAMANHOS = [100, 112, 125, 150, 175, 200]; // % do texto base (até 200%)

  function ler(chave) {
    try { return window.localStorage.getItem(chave); } catch (e) { return null; }
  }
  function gravar(chave, valor) {
    try { window.localStorage.setItem(chave, valor); } catch (e) { /* ignora */ }
  }

  function indiceTamanho() {
    var i = parseInt(ler("rotary-tamanho"), 10);
    return isNaN(i) || i < 0 || i >= TAMANHOS.length ? 0 : i;
  }
  function aplicarTamanho(i) {
    raiz.style.fontSize = TAMANHOS[i] + "%";
    gravar("rotary-tamanho", String(i));
  }
  function aplicarTema(tema) {
    if (tema === "escuro") { raiz.setAttribute("data-tema", "escuro"); }
    else { raiz.removeAttribute("data-tema"); }
    gravar("rotary-tema", tema);
  }
  function aplicarContraste(ativo) {
    if (ativo) { raiz.setAttribute("data-contraste", "alto"); }
    else { raiz.removeAttribute("data-contraste"); }
    gravar("rotary-contraste", ativo ? "1" : "0");
  }

  // Aplica as preferências salvas o mais cedo possível (evita "piscar" a tela).
  aplicarTamanho(indiceTamanho());
  aplicarTema(ler("rotary-tema") === "escuro" ? "escuro" : "claro");
  aplicarContraste(ler("rotary-contraste") === "1");

  document.addEventListener("DOMContentLoaded", function () {
    // Menu lateral recolhível (telas pequenas)
    var botaoMenu = document.getElementById("btn-menu");
    var menu = document.getElementById("menu");
    if (botaoMenu && menu) {
      botaoMenu.addEventListener("click", function () {
        var aberto = menu.classList.toggle("aberto");
        botaoMenu.setAttribute("aria-expanded", aberto ? "true" : "false");
      });
      document.addEventListener("keydown", function (e) {
        if (e.key === "Escape" && menu.classList.contains("aberto")) {
          menu.classList.remove("aberto");
          botaoMenu.setAttribute("aria-expanded", "false");
          botaoMenu.focus();
        }
      });
    }

    // Tema claro/escuro
    var botaoTema = document.getElementById("btn-tema");
    function atualizarBotaoTema() {
      if (!botaoTema) { return; }
      var escuro = raiz.getAttribute("data-tema") === "escuro";
      botaoTema.setAttribute("aria-pressed", escuro ? "true" : "false");
      var icone = botaoTema.querySelector("i");
      if (icone) { icone.className = "bi " + (escuro ? "bi-moon-fill" : "bi-sun-fill"); }
    }
    if (botaoTema) {
      botaoTema.addEventListener("click", function () {
        aplicarTema(raiz.getAttribute("data-tema") === "escuro" ? "claro" : "escuro");
        atualizarBotaoTema();
      });
    }
    atualizarBotaoTema();

    // Menu de acessibilidade
    var botaoContraste = document.querySelector('[data-acao="contraste"]');
    function atualizarBotaoContraste() {
      if (botaoContraste) {
        botaoContraste.setAttribute(
          "aria-pressed", raiz.getAttribute("data-contraste") === "alto" ? "true" : "false"
        );
      }
    }
    atualizarBotaoContraste();

    document.querySelectorAll("[data-acao]").forEach(function (botao) {
      botao.addEventListener("click", function () {
        var acao = botao.getAttribute("data-acao");
        var i = indiceTamanho();
        if (acao === "aumentar" && i < TAMANHOS.length - 1) { aplicarTamanho(i + 1); }
        else if (acao === "diminuir" && i > 0) { aplicarTamanho(i - 1); }
        else if (acao === "restaurar") { aplicarTamanho(0); }
        else if (acao === "contraste") {
          aplicarContraste(raiz.getAttribute("data-contraste") !== "alto");
          atualizarBotaoContraste();
        }
      });
    });
  });
})();
