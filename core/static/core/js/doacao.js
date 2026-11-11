/* Interações do formulário "Registrar doação".
   A validação definitiva é sempre feita no servidor; aqui o objetivo é
   orientar quem preenche (campos que mudam conforme o tipo, contador e estado). */
(function () {
  "use strict";

  var form = document.getElementById("form-doacao");
  if (!form) { return; }

  var doador = form.elements["doador"];
  var valor = form.elements["valor"];
  var descricao = form.elements["descricao"];
  var data = form.elements["data_recebimento"];
  var tipos = form.querySelectorAll('input[name="tipo_doacao"]');

  var grupoValor = document.getElementById("grupo-valor");
  var obrigDescricao = document.getElementById("obrig-descricao");
  var dicaDescricao = document.getElementById("dica-descricao");
  var contador = document.getElementById("contador");
  var estado = document.getElementById("estado-form");
  var estadoTexto = document.getElementById("estado-texto");
  var LIMITE = 500;

  function tipoAtual() {
    var marcado = form.querySelector('input[name="tipo_doacao"]:checked');
    return marcado ? marcado.value : "";
  }

  function valorNumerico() {
    // Aceita "1.500,00", "500,00" ou "500.50".
    var texto = (valor.value || "").trim();
    if (!texto) { return NaN; }
    if (texto.indexOf(",") !== -1) { texto = texto.replace(/\./g, "").replace(",", "."); }
    return Number(texto);
  }

  function formularioValido() {
    if (!doador.value || !data.value) { return false; }
    if (tipoAtual() === "financeira") {
      var n = valorNumerico();
      return !isNaN(n) && n > 0;
    }
    if (tipoAtual() === "material") {
      return descricao.value.trim().length > 0;
    }
    return false;
  }

  function atualizar() {
    var financeira = tipoAtual() === "financeira";

    // Valor só faz sentido em doações financeiras.
    grupoValor.hidden = !financeira;
    // Descrição é obrigatória apenas em doações materiais.
    obrigDescricao.hidden = financeira;
    dicaDescricao.textContent = financeira ? " (opcional para doações financeiras)" : "";

    contador.textContent = descricao.value.length + " / " + LIMITE + " caracteres";

    var valido = formularioValido();
    estado.setAttribute("data-estado", valido ? "valido" : "pendente");
    estado.querySelector("i").className =
      "bi " + (valido ? "bi-check-circle-fill" : "bi-info-circle-fill");
    estadoTexto.textContent = valido
      ? "Dados válidos! Pronto para salvar."
      : "Preencha os campos obrigatórios.";
  }

  form.addEventListener("input", atualizar);
  form.addEventListener("change", atualizar);
  tipos.forEach(function (t) { t.addEventListener("change", atualizar); });
  atualizar();
})();
