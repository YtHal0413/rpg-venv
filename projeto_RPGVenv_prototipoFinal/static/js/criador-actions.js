// ==========================================
// AÇÕES E MANIPULAÇÃO DA FICHA
// ==========================================

function renderizarConfiguradorEstrutura() {
    // Placeholder compatível com chamadas existentes.
    // Esta função mantém a API e evita erros quando a estrutura de configurações ainda não precisa ser atualizada dinamicamente.
}

function obterRotuloComponente(comp, tipo) {
    const ehComponenteAtributo = tipo === "AtributoSimples" || tipo === "AtributoDuplo" || tipo === "AtributoComplexo";
    if (ehComponenteAtributo) {
        if (typeof comp?.nomeAtributo === "string" && comp.nomeAtributo.trim() !== "") return comp.nomeAtributo;
        return "";
    }
    if (typeof comp?.rotulo === "string" && comp.rotulo.trim() !== "") return comp.rotulo;
    return "";
}

function criarBotaoExcluirComponente(numColuna, secaoId, compId, className = "p-1.5 text-purple-400/50 hover:text-red-400 rounded-lg hover:bg-red-950/20 transition") {
    const btnDel = document.createElement("button");
    btnDel.className = className;
    btnDel.textContent = "×";
    btnDel.onclick = () => {
        removerComponenteFicha(numColuna, secaoId, compId);
        agendarSalvamento();
    };
    return btnDel;
}

function obterValorNumericoContador(el) {
    if (!el) return 0;
    const texto = (el.value ?? el.textContent ?? "").toString();
    return parseInt(texto.replace(/\D/g, ""), 10) || 0;
}

function aplicarCorContador(compId, cor) {
    const bar = document.getElementById(`contador_bar_${compId}`);
    if (bar) bar.style.backgroundColor = cor;
}

function atualizarVisualContador(compId, comp) {
    const bar = document.getElementById(`contador_bar_${compId}`);
    const curEl = document.getElementById(`contador_cur_${compId}`);
    const maxEl = document.getElementById(`contador_max_${compId}`);

    if (!bar || !curEl || !maxEl) return;

    const cur = Math.max(0, obterValorNumericoContador(curEl));
    const max = Math.max(1, obterValorNumericoContador(maxEl) || 1);

    comp.valorAtual = cur;
    comp.valorMaximo = max;

    if (curEl.tagName === "INPUT") {
        curEl.value = cur;
    } else {
        curEl.textContent = cur;
    }

    if (maxEl.tagName === "INPUT") {
        maxEl.value = max;
    } else {
        maxEl.textContent = max;
    }

    const pct = Math.min((cur / max) * 100, 100);
    bar.style.width = `${pct}%`;
    aplicarCorContador(compId, comp.corSeletor || "#a91d22");
}

function atualizarRotuloComponente(numColuna, secaoId, compId, valor, tipo) {
    const campo = tipo === "AtributoSimples" || tipo === "AtributoDuplo" || tipo === "AtributoComplexo" ? "nomeAtributo" : "rotulo";
    atualizarValorComponente(numColuna, secaoId, compId, campo, valor);
}

function renderizarComponenteFicha(numColuna, secaoId, comp, tipo) {
    const div = document.createElement("div");
    div.className = "p-3 rounded-xl bg-[rgba(39,18,69,0.75)] border border-white/5 flex flex-col justify-between";
    const editavel = estadoFicha.modo === "Edição";
    const modoJogo = estadoFicha.modo === "Jogo";

    const info = document.createElement("div");
    info.className = "flex-grow space-y-1 overflow-hidden";

    const rotuloAtual = obterRotuloComponente(comp, tipo);

    const inputRotulo = document.createElement(editavel || tipo === "AtributoComplexo" ? "input" : "span");
    if (inputRotulo.tagName === "INPUT") {
        inputRotulo.type = "text";
        inputRotulo.value = rotuloAtual;
        inputRotulo.className = "bg-transparent border-b border-white/10 focus:border-violet-400 focus:outline-none text-sm font-bold text-white " + (tipo === "Contador" ? "w-[15.5rem] mb-3" : "w-full mb-2");
        inputRotulo.placeholder = "Rótulo";
        inputRotulo.onchange = (e) => {
            atualizarRotuloComponente(numColuna, secaoId, comp.id, e.target.value, tipo);
            agendarSalvamento();
        };
        if (modoJogo && tipo === "AtributoComplexo") {
            inputRotulo.disabled = true;
            inputRotulo.className += " text-center";
        }
    } else {
        inputRotulo.className = "text-sm font-bold text-purple-200 block truncate mb-2 text-center";
        inputRotulo.textContent = rotuloAtual;
    }

    const acao = document.createElement("div");
    acao.className = "flex items-center space-x-2 flex-shrink-0";

    switch(tipo) {
        case "AtributoSimples":
            div.className = "atributo-card relative flex flex-col justify-between";
            info.className = "flex-grow space-y-1 overflow-hidden mt-[0.6rem] items-end justify-between gap-2";

            const inpSimples = document.createElement("input");
            inpSimples.type = "number";
            inpSimples.value = comp.valorAtributo || 0;
            inpSimples.className = "[appearance:textfield] [&::-webkit-outer-spin-button]:appearance-none [&::-webkit-inner-spin-button]:appearance-none bg-purple-950/60 border border-white/10 rounded-2xl text-center text-xl font-black p-2 text-white focus:outline-none focus:border-violet-400 w-[75px] aspect-square";
            inpSimples.onchange = (e) => {
                atualizarValorComponente(numColuna, secaoId, comp.id, "valorAtributo", parseInt(e.target.value) || 0);
                agendarSalvamento();
            };
            if (!editavel) inpSimples.disabled = true;

            info.appendChild(inpSimples);
            info.appendChild(inputRotulo);

            if (editavel) {
                const btnDel = document.createElement("button");
                btnDel.className = "absolute top-2.5 left-2.5 p-1.5 text-purple-400/50 hover:text-red-400 rounded-lg hover:bg-red-950/20 transition flex items-center justify-center";
                btnDel.textContent = "×";
                btnDel.onclick = () => {
                    removerComponenteFicha(numColuna, secaoId, comp.id);
                    agendarSalvamento();
                };
                div.appendChild(btnDel);
            }
            break;

        case "Contador":
            div.className = "p-3 rounded-xl bg-[rgba(39,18,69,0.75)] border border-white/5 flex flex-col justify-between";
            if (editavel) {
                div.classList.add("relative");
            }
            const divContador = document.createElement("div");
            divContador.className = "flex flex-col gap-2 w-full";

            info.appendChild(inputRotulo);

            const corSeletor = comp.corSeletor || "#2b2631";
            const valorAtual = Number(comp.valorAtual) || 10;
            const valorMaximo = Number(comp.valorMaximo) || 10;

            const containerBarra = document.createElement("div");
            containerBarra.className = "relative w-full h-[30px] border-[2px] border-purple-800 rounded-full bg-[#0f0f0f] flex items-center justify-between overflow-hidden";

            const barraPreenchimento = document.createElement("div");
            barraPreenchimento.id = `contador_bar_${comp.id}`;
            barraPreenchimento.className = "absolute top-0 left-0 h-full transition-all duration-200 ease-out z-10";
            barraPreenchimento.style.backgroundColor = corSeletor;
            barraPreenchimento.style.width = `${Math.min((valorAtual / Math.max(1, valorMaximo)) * 100, 100)}%`;

            const camadaInterativa = document.createElement("div");
            camadaInterativa.className = "absolute inset-0 flex justify-center px-4 z-20";

            const indicadores = document.createElement("div");
            indicadores.className = "text-white text-base font-medium flex items-center gap-1.5";

            const curEl = document.createElement("input");
            curEl.id = `contador_cur_${comp.id}`;
            curEl.type = "number";
            curEl.min = "0";
            curEl.step = "1";
            curEl.className = "bg-transparent border-0 text-white font-semibold text-center w-[50px] outline-none border-b border-transparent hover:border-white/50 focus:border-white [appearance:textfield] [&::-webkit-outer-spin-button]:appearance-none [&::-webkit-inner-spin-button]:appearance-none";
            curEl.value = String(valorAtual);
            curEl.oninput = () => {
                atualizarVisualContador(comp.id, comp);
            };
            curEl.onblur = () => {
                let val = Math.max(0, obterValorNumericoContador(curEl));
                curEl.value = String(val);
                comp.valorAtual = val;
                atualizarVisualContador(comp.id, comp);
                agendarSalvamento();
            };
            curEl.onkeydown = (e) => {
                if (e.key === "Enter") {
                    e.preventDefault();
                    curEl.blur();
                }
            };

            const separador = document.createElement("span");
            separador.textContent = "/";

            const maxEl = document.createElement("input");
            maxEl.id = `contador_max_${comp.id}`;
            maxEl.type = "number";
            maxEl.min = "1";
            maxEl.step = "1";
            maxEl.className = "bg-transparent border-0 text-white font-semibold text-center w-[50px] outline-none border-b border-transparent hover:border-white/50 focus:border-white [appearance:textfield] [&::-webkit-outer-spin-button]:appearance-none [&::-webkit-inner-spin-button]:appearance-none";
            maxEl.value = String(valorMaximo);
            maxEl.oninput = () => {
                atualizarVisualContador(comp.id, comp);
            };
            maxEl.onblur = () => {
                let val = Math.max(1, obterValorNumericoContador(maxEl));
                maxEl.value = String(val);
                comp.valorMaximo = val;
                atualizarVisualContador(comp.id, comp);
                agendarSalvamento();
            };
            maxEl.onkeydown = (e) => {
                if (e.key === "Enter") {
                    e.preventDefault();
                    maxEl.blur();
                }
            };

            indicadores.appendChild(curEl);
            indicadores.appendChild(separador);
            indicadores.appendChild(maxEl);

            camadaInterativa.appendChild(indicadores);

            containerBarra.appendChild(barraPreenchimento);
            containerBarra.appendChild(camadaInterativa);
            divContador.appendChild(containerBarra);

            if (editavel) {
                const seletorCores = document.createElement("div");
                seletorCores.className = "selector-cores";
                const coresPadrao = ["#2b2631", "#946627", "#e72c7a", "#eb2b36", "#f97316", "#d3ac00", "#00ac3f", "#00bb92", "#0e5ee9", "#8b41b6"];
                coresPadrao.forEach(cor => {
                    const btnCor = document.createElement("button");
                    btnCor.style.backgroundColor = cor;
                    btnCor.onclick = () => {
                        atualizarValorComponente(numColuna, secaoId, comp.id, "corSeletor", cor);
                        aplicarCorContador(comp.id, cor);
                        agendarSalvamento();
                        Array.from(seletorCores.children).forEach(child => child.classList.remove("selecionado"));
                        btnCor.classList.add("selecionado");
                    };
                    if (corSeletor === cor) btnCor.classList.add("selecionado");
                    seletorCores.appendChild(btnCor);
                });
                divContador.appendChild(seletorCores);
            }

            atualizarVisualContador(comp.id, comp);

            acao.appendChild(divContador);
            
            if (editavel) {
                const btnDel = document.createElement("button");
                btnDel.className = "absolute top-[0.5rem] left-[17rem] p-1.5 text-purple-400/50 hover:text-red-400 rounded-lg hover:bg-red-950/20 transition flex items-center justify-center";
                btnDel.textContent = "×";
                btnDel.onclick = () => {
                    removerComponenteFicha(numColuna, secaoId, comp.id);
                    agendarSalvamento();
                };
                div.appendChild(btnDel);
            }
            break;

        case "AtributoDuplo":
            div.className = "atributo-card relative flex flex-col justify-between";

            const linhaValoresDuplo = document.createElement("div");
            linhaValoresDuplo.className = "flex items-center flex-col";

            const inpPequeno = document.createElement("input");
            inpPequeno.type = "number";
            inpPequeno.value = comp.valorPequeno || 0;
            inpPequeno.className = "[&::-webkit-outer-spin-button]:appearance-none [&::-webkit-inner-spin-button]:appearance-none text-center focus:border-violet-400 h-[6px] w-[45px] aspect-square bg-transparent border-b border-white/10 focus:border-violet-400 focus:outline-none text-xs font-bold text-white mb-1";
            inpPequeno.onchange = (e) => {
                atualizarValorComponente(numColuna, secaoId, comp.id, "valorPequeno", parseInt(e.target.value) || 0);
                agendarSalvamento();
            };
            if (!editavel) inpPequeno.disabled = true;

            const inpGrande = document.createElement("input");
            inpGrande.type = "number";
            inpGrande.value = comp.valorGrande || 0;
            inpGrande.className = "[appearance:textfield] [&::-webkit-outer-spin-button]:appearance-none [&::-webkit-inner-spin-button]:appearance-none bg-purple-950/60 border border-white/10 rounded-2xl text-center text-lg font-black p-2 text-white focus:outline-none focus:border-violet-400 w-[65px] aspect-square";
            inpGrande.onchange = (e) => {
                atualizarValorComponente(numColuna, secaoId, comp.id, "valorGrande", parseInt(e.target.value) || 0);
                agendarSalvamento();
            };
            if (!editavel) inpGrande.disabled = true;

            linhaValoresDuplo.appendChild(inpPequeno);
            linhaValoresDuplo.appendChild(inpGrande);
            info.appendChild(linhaValoresDuplo);
            info.appendChild(inputRotulo);

            if (editavel) {
                const btnDel = document.createElement("button");
                btnDel.className = "absolute top-2.5 left-2.5 p-1.5 text-purple-400/50 hover:text-red-400 rounded-lg hover:bg-red-950/20 transition flex items-center justify-center";
                btnDel.textContent = "×";
                btnDel.onclick = () => {
                    removerComponenteFicha(numColuna, secaoId, comp.id);
                    agendarSalvamento();
                };
                div.appendChild(btnDel);
            }
            break;

        case "AtributoComplexo":
            div.className = "relative flex flex-row p-[1rem] h-[100px] text-center bg-[rgba(39,18,69,0.75)] border border-white/10 rounded-2xl bg-purple-950/60 items-center";

            info.className = "flex flex-col w-[6rem] mr-[10px] overflow-hidden";
            if (editavel) {
                inputRotulo.className = "bg-transparent border-b border-white/10 focus:border-violet-400 focus:outline-none text-sm font-bold text-white w-full";
                inputRotulo.placeholder = "Rótulo";
            }

            const subtituloComp = document.createElement("input");
            subtituloComp.type = "text";
            subtituloComp.value = comp.subtituloAnotacao || "";
            subtituloComp.placeholder = "Sub-rotulo";
            subtituloComp.className = "bg-transparent border-white/10 focus:border-violet-400 focus:outline-none text-xs font-bold mt-[5px] w-full";
            subtituloComp.onchange = (e) => {
                atualizarValorComponente(numColuna, secaoId, comp.id, "subtituloAnotacao", e.target.value);
                agendarSalvamento();
                if (modoJogo) {
                    subtituloComp.style.display = (e.target.value && e.target.value.trim() !== "") ? "block" : "none";
                }
            };
            if (!editavel) {
                subtituloComp.disabled = true;
                subtituloComp.className += " text-center";
            }
            if (modoJogo) {
                if (!subtituloComp.value || subtituloComp.value.trim() === "") {
                    subtituloComp.style.display = "none";
                } else {
                    subtituloComp.style.display = "block";
                }
            }

            info.appendChild(inputRotulo);
            info.appendChild(subtituloComp);

            const divComplexo = document.createElement("div");
            divComplexo.className = "flex flex-col gap-3 w-full";

            const valoresComplexos = document.createElement("div");
            valoresComplexos.className = "flex items-center gap-1 flex-wrap";

            const inpBase = document.createElement("input");
            inpBase.type = "number";
            inpBase.value = comp.valorBase || 0;
            inpBase.className = "[appearance:textfield] [&::-webkit-outer-spin-button]:appearance-none [&::-webkit-inner-spin-button]:appearance-none bg-purple-950/60 border border-white/10 rounded-2xl text-center text-xs p-2 focus:outline-none focus:border-violet-400 aspect-square w-[40px]";
            inpBase.onchange = (e) => {
                atualizarValorComponente(numColuna, secaoId, comp.id, "valorBase", parseInt(e.target.value) || 0);
                recalcularTotalComplexo(numColuna, secaoId, comp.id);
                agendarSalvamento();
            };
            inpBase.disabled = !editavel;

            const inpBonus = document.createElement("input");
            inpBonus.type = "number";
            inpBonus.value = comp.valorBonus || 0;
            inpBonus.className = "[appearance:textfield] [&::-webkit-outer-spin-button]:appearance-none [&::-webkit-inner-spin-button]:appearance-none bg-purple-950/60 border border-white/10 rounded-2xl text-center text-xs p-2 focus:outline-none focus:border-violet-400 aspect-square w-[40px]";
            inpBonus.onchange = (e) => {
                atualizarValorComponente(numColuna, secaoId, comp.id, "valorBonus", parseInt(e.target.value) || 0);
                recalcularTotalComplexo(numColuna, secaoId, comp.id);
                agendarSalvamento();
            };
            inpBonus.disabled = !editavel;

            const inpOutros = document.createElement("input");
            inpOutros.type = "number";
            inpOutros.value = comp.valorOutros || 0;
            inpOutros.className = "[appearance:textfield] [&::-webkit-outer-spin-button]:appearance-none [&::-webkit-inner-spin-button]:appearance-none bg-purple-950/60 border border-white/10 rounded-2xl text-center text-xs p-2 focus:outline-none focus:border-violet-400 aspect-square w-[40px]";
            inpOutros.onchange = (e) => {
                atualizarValorComponente(numColuna, secaoId, comp.id, "valorOutros", parseInt(e.target.value) || 0);
                recalcularTotalComplexo(numColuna, secaoId, comp.id);
                agendarSalvamento();
            };
            inpOutros.disabled = !editavel;

            const spanTotal = document.createElement("span");
            spanTotal.id = `total_complexo_${comp.id}`;
            spanTotal.className = "text-xs font-black text-violet-300 mx-[0.7rem]";
            spanTotal.textContent = (Number(comp.valorBase) || 0) + (Number(comp.valorBonus) || 0) + (Number(comp.valorOutros) || 0);

            valoresComplexos.appendChild(inpBase);
            valoresComplexos.appendChild(inpBonus);
            valoresComplexos.appendChild(inpOutros);
            valoresComplexos.appendChild(document.createTextNode(" = "));
            valoresComplexos.appendChild(spanTotal);

            divComplexo.appendChild(valoresComplexos);
            acao.className = "flex items-center flex-shrink-0";
            acao.appendChild(divComplexo);
            if (editavel) {
                acao.appendChild(criarBotaoExcluirComponente(numColuna, secaoId, comp.id, "absolute left-[16.5rem] bottom-[0.3rem] p-1.5 text-purple-400/50 hover:text-red-400 rounded-lg hover:bg-red-950/20 transition flex items-center justify-center"));
            }
            break;

        case "Checkbox":
            div.className = "p-3 rounded-xl bg-[rgba(39,18,69,0.75)] border border-white/5 flex flex-row justify-between items-center";
            info.className = "flex-grow space-y-1 overflow-hidden";
            
            if (inputRotulo.tagName === "INPUT") {
                inputRotulo.className = "bg-transparent border-b border-white/10 focus:border-violet-400 focus:outline-none text-sm font-bold text-white w-full";
            } else {
                inputRotulo.className = "text-sm font-bold text-purple-200 block truncate text-left";
            }
            
            info.appendChild(inputRotulo);
            
            const inpCheck = document.createElement("input");
            inpCheck.type = "checkbox";
            inpCheck.checked = comp.estaMarcado || false;
            inpCheck.className = "w-4 h-4 rounded text-violet-400 focus:ring-0 focus:ring-offset-0 bg-transparent border-white/10";
            inpCheck.onchange = (e) => {
                atualizarValorComponente(numColuna, secaoId, comp.id, "estaMarcado", e.target.checked);
                agendarSalvamento();
            };
            
            acao.className = "flex items-center space-x-2 flex-shrink-0";
            acao.appendChild(inpCheck);
            
            if (editavel) {
                acao.appendChild(criarBotaoExcluirComponente(numColuna, secaoId, comp.id));
            }
            break;

        case "InformacaoCurta":
            div.className = "p-3 rounded-xl bg-[rgba(39,18,69,0.75)] border border-white/5 flex flex-col justify-between";
            if (inputRotulo.tagName === "INPUT") {
                inputRotulo.className = "bg-transparent border-b border-white/10 focus:border-violet-400 focus:outline-none text-sm font-bold text-white w-full";
            } else {
                inputRotulo.className = "text-sm font-bold text-purple-200 block truncate text-left mb-2";
            }
            info.appendChild(inputRotulo);
            
            const inpTexto = document.createElement("input");
            inpTexto.type = "text";
            inpTexto.value = comp.campoTexto || "";
            inpTexto.placeholder = "Texto Curto";
            inpTexto.className = "bg-purple-950/60 border border-white/10 rounded-lg px-2 py-1 text-xs text-white focus:outline-none focus:border-violet-400 flex-grow text-left";
            inpTexto.onchange = (e) => {
                atualizarValorComponente(numColuna, secaoId, comp.id, "campoTexto", e.target.value);
                agendarSalvamento();
            };
            if (!editavel) inpTexto.disabled = true;
            acao.appendChild(inpTexto);
            if (editavel) {
                acao.appendChild(criarBotaoExcluirComponente(numColuna, secaoId, comp.id));
            }
            break;

        case "AnotacaoSimples":
            div.className = "bg-purple-950/60 border border-white/5 rounded-2xl p-3";

            const divAnotSimples = document.createElement("div");
            divAnotSimples.className = "flex flex-col gap-2 w-full";

            const cabecalhoAnotSimples = document.createElement("div");
            cabecalhoAnotSimples.className = "flex items-center gap-2";

            const descSimples = document.createElement("input");
            descSimples.type = "text";
            descSimples.value = comp.rotulo || "";
            descSimples.placeholder = "Título da anotação";
            descSimples.className = "bg-transparent border-b border-white/10 focus:border-violet-400 focus:outline-none text-sm font-bold text-white w-full";
            descSimples.onchange = (e) => {
                atualizarValorComponente(numColuna, secaoId, comp.id, "rotulo", e.target.value);
                agendarSalvamento();
            };
            descSimples.disabled = !editavel;
            cabecalhoAnotSimples.appendChild(descSimples);

            const areaSimples = document.createElement("textarea");
            areaSimples.value = comp.descricao || comp.texto || "";
            areaSimples.placeholder = "Descrição...";
            areaSimples.rows = 3;
            areaSimples.className = "auto-altura bg-purple-950/60 border border-white/10 rounded-2xl p-3 text-xs text-purple-200 focus:outline-none focus:border-violet-400 w-full resize-vertical";
            areaSimples.onchange = (e) => {
                atualizarValorComponente(numColuna, secaoId, comp.id, "descricao", e.target.value);
                agendarSalvamento();
            };
            areaSimples.disabled = !editavel;

            divAnotSimples.appendChild(cabecalhoAnotSimples);
            divAnotSimples.appendChild(areaSimples);
            info.appendChild(divAnotSimples);
            if (editavel) {
                acao.appendChild(criarBotaoExcluirComponente(numColuna, secaoId, comp.id));
            }
            break;

        case "AnotacaoCheckbox":
            const divAnotCheck = document.createElement("div");
            divAnotCheck.className = "flex flex-col gap-2 w-full";

            const cabecalhoAnot = document.createElement("div");
            cabecalhoAnot.className = "colapsavel-cabecalho";

            const descCheck = document.createElement("input");
            descCheck.type = "text";
            descCheck.value = comp.rotulo || "";
            descCheck.placeholder = "Título da anotação";
            descCheck.className = "bg-transparent border-b border-white/10 focus:border-violet-400 focus:outline-none text-sm font-bold text-white w-[80%]";
            descCheck.onchange = (e) => {
                atualizarValorComponente(numColuna, secaoId, comp.id, "rotulo", e.target.value);
                agendarSalvamento();
            };
            descCheck.disabled = !editavel;
            cabecalhoAnot.appendChild(descCheck);

            const chkAnot = document.createElement("input");
            chkAnot.type = "checkbox";
            chkAnot.checked = comp.estaMarcado || false;
            chkAnot.className = "w-[17px] h-[17px] rounded text-violet-400 focus:ring-0 focus:ring-offset-0 bg-transparent border-white/10";
            chkAnot.onchange = (e) => {
                atualizarValorComponente(numColuna, secaoId, comp.id, "estaMarcado", e.target.checked);
                agendarSalvamento();
            };
            chkAnot.disabled = false;
            cabecalhoAnot.appendChild(chkAnot);

            const toggleAnot = document.createElement("button");
            toggleAnot.type = "button";
            toggleAnot.className = "colapsavel-toggle";
            toggleAnot.textContent = "•••";
            cabecalhoAnot.appendChild(toggleAnot);

            const conteudoAnot = document.createElement("div");
            conteudoAnot.className = "colapsavel-conteudo";
            const textAreaAt = document.createElement("textarea");
            textAreaAt.value = comp.descricao || "";
            textAreaAt.placeholder = "Descrição longa...";
            textAreaAt.rows = 3;
            textAreaAt.className = "auto-altura bg-purple-950/60 border border-white/10 rounded-2xl p-3 text-xs text-purple-200 focus:outline-none focus:border-violet-400 w-full resize-vertical";
            textAreaAt.onchange = (e) => {
                atualizarValorComponente(numColuna, secaoId, comp.id, "descricao", e.target.value);
                agendarSalvamento();
            };
            textAreaAt.disabled = !editavel;
            conteudoAnot.appendChild(textAreaAt);
            toggleAnot.onclick = () => {
                conteudoAnot.classList.toggle("aberto");
            };

            divAnotCheck.appendChild(cabecalhoAnot);
            divAnotCheck.appendChild(conteudoAnot);
            info.appendChild(divAnotCheck);
            if (editavel) {
                acao.appendChild(criarBotaoExcluirComponente(numColuna, secaoId, comp.id));
            }
            break;

        case "AnotacaoDetalhada":
            const divConteudoAnotDet = document.createElement("div");
            divConteudoAnotDet.className = "flex flex-col gap-2 w-full";

            const cabecalhoAnotDet = document.createElement("div");
            cabecalhoAnotDet.className = "flex flex-row items-center justify-between gap-1";

            const blocoInputsAnotDet = document.createElement("div");
            blocoInputsAnotDet.className = "w-[80%]";

            const inputTituloAnotDet = document.createElement("input");
            inputTituloAnotDet.type = "text";
            inputTituloAnotDet.value = comp.rotulo || "";
            inputTituloAnotDet.placeholder = "Título da anotação";
            inputTituloAnotDet.className = "bg-transparent border-b border-white/10 focus:border-violet-400 focus:outline-none text-sm font-bold text-white w-full";
            inputTituloAnotDet.onchange = (e) => {
                atualizarValorComponente(numColuna, secaoId, comp.id, "rotulo", e.target.value);
                agendarSalvamento();
            };
            inputTituloAnotDet.disabled = !editavel;
            blocoInputsAnotDet.appendChild(inputTituloAnotDet);

            const inputSubtituloAnotDet = document.createElement("input");
            inputSubtituloAnotDet.type = "text";
            inputSubtituloAnotDet.value = comp.anotacaoExtra || "";
            inputSubtituloAnotDet.placeholder = "Texto adicional";
            inputSubtituloAnotDet.className = "bg-transparent border-white/10 focus:border-violet-400 focus:outline-none text-xs font-bold w-full";
            inputSubtituloAnotDet.onchange = (e) => {
                atualizarValorComponente(numColuna, secaoId, comp.id, "anotacaoExtra", e.target.value);
                agendarSalvamento();
            };
            inputSubtituloAnotDet.disabled = !editavel;
            blocoInputsAnotDet.appendChild(inputSubtituloAnotDet);

            cabecalhoAnotDet.appendChild(blocoInputsAnotDet);

            const toggleAnotDet = document.createElement("button");
            toggleAnotDet.type = "button";
            toggleAnotDet.className = "colapsavel-toggle";
            toggleAnotDet.textContent = "•••";
            cabecalhoAnotDet.appendChild(toggleAnotDet);

            const conteudoAnotDet = document.createElement("div");
            conteudoAnotDet.className = "colapsavel-conteudo";

            const areaDescDet = document.createElement("textarea");
            areaDescDet.value = comp.descricao || "";
            areaDescDet.placeholder = "Descrição...";
            areaDescDet.rows = 2;
            areaDescDet.className = "auto-altura bg-purple-950/60 border border-white/10 rounded-2xl p-3 text-xs text-purple-200 focus:outline-none focus:border-violet-400 w-full resize-vertical";
            areaDescDet.onchange = (e) => {
                atualizarValorComponente(numColuna, secaoId, comp.id, "descricao", e.target.value);
                agendarSalvamento();
            };
            if (!editavel) areaDescDet.disabled = true;
            conteudoAnotDet.appendChild(areaDescDet);
            toggleAnotDet.onclick = () => {
                conteudoAnotDet.classList.toggle("aberto");
            };

            divConteudoAnotDet.appendChild(cabecalhoAnotDet);
            divConteudoAnotDet.appendChild(conteudoAnotDet);
            info.appendChild(divConteudoAnotDet);
            if (editavel) {
                acao.appendChild(criarBotaoExcluirComponente(numColuna, secaoId, comp.id));
            }
            break;

        default:
            const spanPlaceholder = document.createElement("span");
            spanPlaceholder.className = "text-xs text-purple-400/50";
            spanPlaceholder.textContent = comp.rotulo || "Componente";
            acao.appendChild(spanPlaceholder);
            if (editavel) {
                acao.appendChild(criarBotaoExcluirComponente(numColuna, secaoId, comp.id));
            }
            break;
    }

    div.appendChild(info);
    div.appendChild(acao);
    return div;
}

async function enviarRequisicaoFicha(url, options = {}) {
    const requisição = {
        headers: { "Content-Type": "application/json", ...(options.headers || {}) },
        ...options
    };
    try {
        const resposta = await fetch(url, requisição);
        const dados = await resposta.json().catch(() => null);
        if (!resposta.ok) {
            const mensagem = dados?.erro || resposta.statusText || "Erro ao processar a requisição.";
            throw new Error(mensagem);
        }
        return dados;
    } catch (erro) {
        console.warn("Erro na API de ficha:", erro);
        throw erro;
    }
}

function alternarAbaColuna(numColuna, abaId) {
    estadoFicha.colunas[numColuna].abaAtivaId = abaId;
    renderizarColuna(numColuna);
    renderizarConfiguradorEstrutura();
}

async function novaAba(colunaNum) {
    if (!estadoFicha.podeEditar) {
        mostrarToastNotificacao("Acesso negado", "Você só pode visualizar esta ficha em modo jogo.", "erro");
        return;
    }
    const col = estadoFicha.colunas[colunaNum];
    if (col.abas.length >= 3) {
        mostrarToastNotificacao("Limite Excedido", "Máximo de 3 abas por coluna.", "erro");
        return;
    }
    const titulo = prompt("Título da nova aba:");
    if (!titulo || titulo.trim() === "") return;

    let abaId;
    try {
        const dados = await enviarRequisicaoFicha(`/api/ficha/${estadoFicha.id}/aba`, {
            method: "POST",
            body: JSON.stringify({ titulo: titulo.trim(), posicaoColuna: colunaNum })
        });
        abaId = dados?.aba?.id;
    } catch (erro) {
        mostrarToastNotificacao("Aviso", "Não foi possível sincronizar a nova aba com o servidor. A aba será criada localmente e salva em seguida.", "aviso");
    }

    const novaAba = { id: abaId || ++idGeradorInterno, titulo: titulo.trim(), secoes: [] };
    col.abas.push(novaAba);
    col.abaAtivaId = novaAba.id;
    renderizarFichaCompleta();
    mostrarToastNotificacao("Sucesso", `Aba "${titulo}" adicionada!`, "sucesso");
    agendarSalvamento();
    renderizarConfiguradorEstrutura();
}

async function removerAbaColuna(colunaNum, abaId) {
    if (!estadoFicha.podeEditar) {
        mostrarToastNotificacao("Acesso negado", "Você só pode visualizar esta ficha em modo jogo.", "erro");
        return;
    }

    const col = estadoFicha.colunas[colunaNum];
    const abaARemover = col.abas.find(a => a.id === abaId);

    if (abaARemover && (abaARemover.ehPadrao === true || abaARemover.titulo === "Geral")) {
        mostrarToastNotificacao("Ação não permitida", "A aba 'Geral' não pode ser removida.", "aviso");
        return;
    }

    try {
        await enviarRequisicaoFicha(`/api/ficha/${estadoFicha.id}/aba/${abaId}`, { method: "DELETE" });
    } catch (erro) {
        mostrarToastNotificacao("Aviso", "Não foi possível remover a aba no servidor. A aba será removida localmente.", "aviso");
    }

    col.abas = col.abas.filter(a => a.id !== abaId);
    if (col.abaAtivaId === abaId) {
        col.abaAtivaId = col.abas.length > 0 ? col.abas[0].id : null;
    }
    renderizarFichaCompleta();
    agendarSalvamento();
    renderizarConfiguradorEstrutura();
}

function abrirModalNovaSecao(colunaNum) {
    colunaAlvoNovaSecao = colunaNum;
    document.getElementById("modal_nova_secao").classList.remove("hidden");
}

function fecharModalNovaSecao() {
    document.getElementById("modal_nova_secao").classList.add("hidden");
    document.getElementById("titulo_secao_novo").value = "";
}

async function salvarNovaSecao() {
    if (!estadoFicha.podeEditar) {
        mostrarToastNotificacao("Acesso negado", "Você só pode visualizar esta ficha em modo jogo.", "erro");
        return;
    }
    const titulo = document.getElementById("titulo_secao_novo").value.trim();
    const tipo = document.getElementById("tipo_componente_secao").value;
    if (!titulo) {
        mostrarToastNotificacao("Erro", "Título da seção é obrigatório.", "erro");
        return;
    }

    const col = estadoFicha.colunas[colunaAlvoNovaSecao];
    const aba = col.abas.find(a => a.id === col.abaAtivaId);
    if (!aba) {
        mostrarToastNotificacao("Erro", "Nenhuma aba ativa.", "erro");
        return;
    }

    let secaoId;
    try {
        const dados = await enviarRequisicaoFicha(`/api/ficha/${estadoFicha.id}/secao`, {
            method: "POST",
            body: JSON.stringify({ titulo, abaId: aba.id, tipo })
        });
        secaoId = dados?.secao?.id;
    } catch (erro) {
        mostrarToastNotificacao("Aviso", "Não foi possível sincronizar a seção com o servidor. A seção será criada localmente e salva em seguida.", "aviso");
    }

    aba.secoes.push({ id: secaoId || ++idGeradorInterno, titulo, tipo, componentes: [] });
    fecharModalNovaSecao();
    renderizarFichaCompleta();
    mostrarToastNotificacao("Sucesso", `Seção "${titulo}" criada!`, "sucesso");
    agendarSalvamento();
}

async function removerSecaoAba(numColuna, secaoId) {
    if (!estadoFicha.podeEditar) {
        mostrarToastNotificacao("Acesso negado", "Você só pode visualizar esta ficha em modo jogo.", "erro");
        return;
    }
    const col = estadoFicha.colunas[numColuna];
    const aba = col.abas.find(a => a.id === col.abaAtivaId);

    try {
        await enviarRequisicaoFicha(`/api/ficha/${estadoFicha.id}/secao/${secaoId}`, { method: "DELETE" });
    } catch (erro) {
        mostrarToastNotificacao("Aviso", "Não foi possível remover a seção no servidor. A seção será removida localmente.", "aviso");
    }

    if (aba) {
        aba.secoes = aba.secoes.filter(s => s.id !== secaoId);
        renderizarFichaCompleta();
        agendarSalvamento();
    }
}

async function adicionarComponenteSecao(numColuna, secaoId, tipo) {
    if (!estadoFicha.podeEditar) {
        mostrarToastNotificacao("Acesso negado", "Você só pode visualizar esta ficha em modo jogo.", "erro");
        return;
    }
    const col = estadoFicha.colunas[numColuna];
    const aba = col.abas.find(a => a.id === col.abaAtivaId);
    if (!aba) return;
    const secao = aba.secoes.find(s => s.id === secaoId);
    if (!secao) return;
    secao.componentes = secao.componentes || [];

    let novoComp = null;
    try {
        const dados = await enviarRequisicaoFicha(`/api/ficha/${estadoFicha.id}/componente`, {
            method: "POST",
            body: JSON.stringify({ secaoId, tipo })
        });
        novoComp = dados?.componente;
    } catch (erro) {
        mostrarToastNotificacao("Aviso", "Não foi possível sincronizar o componente com o servidor. O componente será criado localmente e salvo em seguida.", "aviso");
    }

    if (!novoComp) {
        novoComp = { id: ++idGeradorInterno };
        switch(tipo) {
            case "AtributoSimples": novoComp.nomeAtributo = ""; novoComp.valorAtributo = 0; break;
            case "AtributoDuplo": novoComp.nomeAtributo = ""; novoComp.valorGrande = 0; novoComp.valorPequeno = 0; break;
            case "AtributoComplexo": novoComp.nomeAtributo = ""; novoComp.valorBase = 0; novoComp.valorBonus = 0; novoComp.valorOutros = 0; novoComp.subtituloAnotacao = ""; break;
            case "Contador": novoComp.rotulo = ""; novoComp.valorAtual = 0; novoComp.valorMaximo = 10; novoComp.corSeletor = "#2b2631"; break;
            case "Checkbox": novoComp.rotulo = ""; novoComp.estaMarcado = false; break;
            case "InformacaoCurta": novoComp.rotulo = ""; novoComp.campoTexto = ""; break;
            case "AnotacaoSimples": novoComp.rotulo = ""; novoComp.descricao = ""; break;
            case "AnotacaoCheckbox": novoComp.rotulo = ""; novoComp.descricao = ""; novoComp.estaMarcado = false; break;
            case "AnotacaoDetalhada": novoComp.rotulo = ""; novoComp.descricao = ""; novoComp.anotacaoExtra = ""; break;
            default: break;
        }
    }

    secao.componentes.push(novoComp);
    renderizarFichaCompleta();
    mostrarToastNotificacao("Sucesso", "Elemento adicionado.", "sucesso");
    agendarSalvamento();
}

async function removerComponenteFicha(numColuna, secaoId, compId) {
    if (!estadoFicha.podeEditar) {
        mostrarToastNotificacao("Acesso negado", "Você só pode visualizar esta ficha em modo jogo.", "erro");
        return;
    }
    const col = estadoFicha.colunas[numColuna];
    const aba = col.abas.find(a => a.id === col.abaAtivaId);
    if (!aba) return;
    const secao = aba.secoes.find(s => s.id === secaoId);
    if (!secao) return;

    try {
        await enviarRequisicaoFicha(`/api/ficha/${estadoFicha.id}/componente/${compId}`, { method: "DELETE" });
    } catch (erro) {
        mostrarToastNotificacao("Aviso", "Não foi possível remover o componente no servidor. A remoção será aplicada localmente.", "aviso");
    }

    secao.componentes = secao.componentes.filter(c => c.id !== compId);
    renderizarFichaCompleta();
    agendarSalvamento();
}

async function atualizarValorComponente(numColuna, secaoId, compId, campo, valor) {
    const col = estadoFicha.colunas[numColuna];
    const aba = col.abas.find(a => a.id === col.abaAtivaId);
    if (!aba) return;
    const secao = aba.secoes.find(s => s.id === secaoId);
    if (!secao) return;
    const comp = secao.componentes.find(c => c.id === compId);
    if (!comp) return;

    comp[campo] = valor;

    const payload = { [campo]: valor };
    if (campo === "nomeAtributo" || campo === "rotulo" || campo === "descricao" || campo === "campoTexto" || campo === "subtituloAnotacao") {
        payload[campo] = valor;
    }

    try {
        await enviarRequisicaoFicha(`/api/ficha/${estadoFicha.id}/componente/${compId}`, {
            method: "PUT",
            body: JSON.stringify(payload)
        });
    } catch (erro) {
        // Keep local change and fallback to full save
    }
}

function recalcularTotalComplexo(numColuna, secaoId, compId) {
    const col = estadoFicha.colunas[numColuna];
    const aba = col.abas.find(a => a.id === col.abaAtivaId);
    if (!aba) return;
    const secao = aba.secoes.find(s => s.id === secaoId);
    if (!secao) return;
    const comp = secao.componentes.find(c => c.id === compId);
    if (comp) {
        const display = document.getElementById(`total_complexo_${compId}`);
        if (display) {
            display.textContent = (Number(comp.valorBase) || 0) + (Number(comp.valorBonus) || 0) + (Number(comp.valorOutros) || 0);
        }
    }
}

function definirModo(novoModo) {
    if (!estadoFicha.podeEditar) {
        estadoFicha.modo = "Jogo";
        const btnJogo = document.getElementById("btn_modo_jogo");
        if (btnJogo) btnJogo.className = "px-4 py-2 rounded-lg text-xs font-bold transition flex items-center space-x-1.5 bg-violet-400 text-purple-950 shadow-lg shadow-violet-500/10";
        document.querySelectorAll(".btn-edicao-visivel").forEach(el => el.classList.add("hidden"));
        renderizarFichaCompleta();
        return;
    }
    estadoFicha.modo = novoModo;
    const btnJogo = document.getElementById("btn_modo_jogo");
    const btnEdicao = document.getElementById("btn_modo_edicao");

    if (novoModo === "Jogo") {
        btnJogo.className = "px-4 py-2 rounded-lg text-xs font-bold transition flex items-center space-x-1.5 bg-violet-400 text-purple-950 shadow-lg shadow-violet-500/10";
        btnEdicao.className = "px-4 py-2 rounded-lg text-xs font-bold transition flex items-center space-x-1.5 text-purple-300 hover:text-white";
        document.querySelectorAll(".btn-edicao-visivel").forEach(el => el.classList.add("hidden"));
    } else {
        btnEdicao.className = "px-4 py-2 rounded-lg text-xs font-bold transition flex items-center space-x-1.5 bg-violet-400 text-purple-950 shadow-lg shadow-violet-500/10";
        btnJogo.className = "px-4 py-2 rounded-lg text-xs font-bold transition flex items-center space-x-1.5 text-purple-300 hover:text-white";
        document.querySelectorAll(".btn-edicao-visivel").forEach(el => el.classList.remove("hidden"));
    }
    renderizarFichaCompleta();
    agendarSalvamento();
}

function mudarFoto() {
    if (!estadoFicha.podeEditar) {
        mostrarToastNotificacao("Acesso negado", "Você só pode visualizar esta ficha em modo jogo.", "erro");
        return;
    }
    const input = document.createElement('input');
    input.type = 'file';
    input.accept = 'image/*';

    input.onchange = async function(e) {
        const arquivo = e.target.files[0];
        if (!arquivo) return;

        if (arquivo.size > 16 * 1024 * 1024) {
            mostrarToastNotificacao("Erro", "Arquivo muito grande. Máximo 16MB.", "erro");
            return;
        }

        const formatosPermitidos = ['image/png', 'image/jpeg', 'image/gif', 'image/webp'];
        if (!formatosPermitidos.includes(arquivo.type)) {
            mostrarToastNotificacao("Erro", "Formato não suportado. Use PNG, JPG, GIF ou WEBP.", "erro");
            return;
        }

        mostrarToastNotificacao("Upload", "Enviando imagem...", "info");

        const formData = new FormData();
        formData.append('avatar', arquivo);

        try {
            const resposta = await fetch(`/api/ficha/${estadoFicha.id}/avatar`, {
                method: 'POST',
                body: formData
            });

            const dados = await resposta.json();
            if (dados.status === 'success') {
                const img = document.getElementById('avatar_imagem');
                const placeholder = document.getElementById('avatar_placeholder');
                if (img) {
                    img.src = dados.avatar_url + '?t=' + Date.now();
                    img.classList.remove('hidden');
                }
                if (placeholder) placeholder.classList.add('hidden');
                estadoFicha.avatar = dados.avatar_url;
                mostrarToastNotificacao("Sucesso", "Avatar atualizado!", "sucesso");
                agendarSalvamento();
            } else {
                mostrarToastNotificacao("Erro", dados.erro || "Falha ao atualizar avatar.", "erro");
            }
        } catch (erro) {
            mostrarToastNotificacao("Erro", "Falha ao fazer upload da imagem.", "erro");
        }
    };

    input.click();
}

function removerFoto() {
    if (!estadoFicha.podeEditar) {
        mostrarToastNotificacao("Acesso negado", "Você só pode visualizar esta ficha em modo jogo.", "erro");
        return;
    }
    const avatarImg = document.getElementById('avatar_imagem');
    const avatarPlaceholder = document.getElementById('avatar_placeholder');

    if (avatarImg) {
        avatarImg.classList.add('hidden');
        avatarImg.src = '';
    }
    if (avatarPlaceholder) {
        avatarPlaceholder.classList.remove('hidden');
    }

    if (estadoFicha) {
        estadoFicha.avatar = null;
        agendarSalvamento();
    }

    mostrarToastNotificacao("Avatar removido", "A imagem de perfil foi removida.", "alerta");
}

function mostrarToastNotificacao(titulo, texto, tipo) {
    let container = document.getElementById("painel_notificacoes");
    if (!container) {
        container = document.createElement('div');
        container.id = 'painel_notificacoes';
        container.className = 'fixed bottom-6 right-6 z-50 flex flex-col gap-3 max-w-sm w-full';
        container.style.pointerEvents = 'none';
        document.body.appendChild(container);
    }

    const toast = document.createElement("div");
    let cor = "";
    if (tipo === "sucesso") {
        cor = "border-emerald-500/30 bg-emerald-950/50";
    } else if (tipo === "erro") {
        cor = "border-red-500/30 bg-red-950/50";
    } else if (tipo === "alerta") {
        cor = "border-yellow-500/30 bg-yellow-950/50";
    } else {
        cor = "border-violet-500/30 bg-violet-950/50";
    }

    toast.className = `toast-notificacao relative p-4 rounded-xl text-sm ${cor} text-white backdrop-blur-md shadow-2xl overflow-hidden`;
    toast.style.pointerEvents = 'auto';
    toast.style.animation = 'slideIn 0.3s ease-out forwards';

    toast.innerHTML = `
        <div class="absolute bottom-0 left-0 h-1 bg-gradient-to-r 
            ${tipo === 'sucesso' ? 'from-emerald-400 to-emerald-600' : 
              tipo === 'erro' ? 'from-red-400 to-red-600' : 
              tipo === 'alerta' ? 'from-yellow-400 to-yellow-600' : 
              'from-violet-400 to-violet-600'}"
            style="width: 100%; animation: progressBar 5s linear forwards;">
        </div>
        <div class="flex items-start space-x-3 relative z-10">
            <div class="flex-shrink-0 mt-0.5">
                ${tipo === 'sucesso' ? 
                    `<svg class="w-5 h-5 text-emerald-400" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>` :
                    tipo === 'erro' ?
                    `<svg class="w-5 h-5 text-red-400" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" d="M12 9v3.75m9-.75a9 9 0 11-18 0 9 9 0 0118 0zm-9 3.75h.008v.008H12v-.008z" />
                    </svg>` :
                    tipo === 'alerta' ?
                    `<svg class="w-5 h-5 text-yellow-400" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126zM12 15.75h.007v.008H12v-.008z" />
                    </svg>` :
                    `<svg class="w-5 h-5 text-violet-400" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" d="M11.25 11.25l.041-.02a.75.75 0 011.063.852l-.708 2.836a.75.75 0 001.063.853l.041-.021M21 12a9 9 0 11-18 0 9 9 0 0118 0zm-9-3.75h.008v.008H12v-.008z" />
                    </svg>`
                }
            </div>
            <div class="flex-1 min-w-0">
                <p class="text-sm font-bold text-white">${titulo}</p>
                <p class="text-xs text-purple-200 mt-0.5">${texto}</p>
            </div>
            <button onclick="fecharToast(this)" class="flex-shrink-0 text-purple-400 hover:text-white transition ml-2">
                <svg class="w-4 h-4" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
                </svg>
            </button>
        </div>
    `;

    container.appendChild(toast);

    setTimeout(() => {
        if (toast.parentNode) {
            toast.classList.add('fechando');
            setTimeout(() => {
                if (toast.parentNode) {
                    toast.remove();
                }
            }, 300);
        }
    }, 5000);
}

function fecharToast(button) {
    const toast = button.closest('.toast-notificacao');
    if (toast) {
        toast.classList.add('fechando');
        setTimeout(() => {
            if (toast.parentNode) {
                toast.remove();
            }
        }, 300);
    }
}

function abrirModalTemplate() {
    document.getElementById("modal_template").classList.remove("hidden");
    document.getElementById("nome_template_input").focus();
}

function fecharModalTemplate() {
    document.getElementById("modal_template").classList.add("hidden");
}

async function salvarComoTemplate() {
    const nome = document.getElementById("nome_template_input").value.trim();
    if (!nome) {
        mostrarToastNotificacao("Erro", "Informe um nome.", "erro");
        return;
    }
    try {
        const resp = await fetch(`/api/ficha/${estadoFicha.id}/template`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ nome })
        });
        if (resp.ok) {
            mostrarToastNotificacao("Template salvo", `"${nome}" criado com sucesso!`, "sucesso");
            fecharModalTemplate();
        } else {
            const dados = await resp.json();
            mostrarToastNotificacao("Erro", dados.erro || "Não foi possível salvar.", "erro");
        }
    } catch {
        mostrarToastNotificacao("Erro", "Falha ao criar template.", "erro");
    }
}

async function abrirModalTemplateList() {
    const modal = document.getElementById("modal_template_list");
    const lista = document.getElementById("lista_templates_disponiveis");
    if (modal) modal.classList.remove("hidden");
    if (lista) lista.innerHTML = '<p class="text-sm text-purple-300">Carregando templates...</p>';

    try {
        const dados = await enviarRequisicaoFicha(`/api/ficha/${estadoFicha.id}/template`);
        renderizarListaTemplates(dados.templates || []);
    } catch (erro) {
        if (lista) lista.innerHTML = '<p class="text-sm text-purple-300">Falha ao carregar templates.</p>';
        mostrarToastNotificacao("Erro", "Não foi possível carregar os templates.", "erro");
    }
}

function fecharModalTemplateList() {
    const modal = document.getElementById("modal_template_list");
    if (modal) modal.classList.add("hidden");
}

function renderizarListaTemplates(templates) {
    const lista = document.getElementById("lista_templates_disponiveis");
    if (!lista) return;
    lista.innerHTML = "";

    if (!templates.length) {
        lista.innerHTML = '<p class="text-sm text-purple-300">Nenhum template salvo ainda.</p>';
        return;
    }

    templates.forEach((template) => {
        const item = document.createElement("div");
        item.className = "bg-purple-950/80 border border-white/10 rounded-3xl p-4 grid gap-3 sm:grid-cols-[1fr_auto] items-start";
        item.innerHTML = `
            <div class="space-y-1">
                <p class="font-semibold text-white">${template.nomeTemplate}</p>
                <p class="text-xs text-purple-300">Criado em ${template.dataCriacao || 'data desconhecida'}</p>
            </div>
            <div class="flex gap-2">
                <button type="button" class="px-4 py-2 rounded-xl bg-violet-400 text-purple-950 font-bold text-xs hover:bg-violet-500 transition">Aplicar</button>
                <button type="button" class="px-4 py-2 rounded-xl bg-red-500 text-white font-bold text-xs hover:bg-red-600 transition">Excluir</button>
            </div>
        `;

        const botaoAplicar = item.querySelector("button:first-of-type");
        const botaoExcluir = item.querySelector("button:last-of-type");
        if (botaoAplicar) {
            botaoAplicar.addEventListener("click", () => aplicarTemplate(template.id, template.nomeTemplate));
        }
        if (botaoExcluir) {
            botaoExcluir.addEventListener("click", () => deletarTemplate(template.id, template.nomeTemplate));
        }
        lista.appendChild(item);
    });
}

async function deletarTemplate(templateId, nomeTemplate) {
    if (!confirm(`Excluir o template "${nomeTemplate}" não pode ser desfeito. Continuar?`)) {
        return;
    }

    try {
        await enviarRequisicaoFicha(`/api/ficha/${estadoFicha.id}/template/${templateId}`, {
            method: "DELETE"
        });

        mostrarToastNotificacao("Template excluído", `O template "${nomeTemplate}" foi removido.`, "sucesso");
        abrirModalTemplateList();
    } catch (erro) {
        mostrarToastNotificacao("Erro", "Falha ao excluir o template.", "erro");
    }
}

async function aplicarTemplate(templateId, nomeTemplate) {
    if (!confirm(`Aplicar o template "${nomeTemplate}" substituirá a estrutura atual da ficha. Continuar?`)) {
        return;
    }

    try {
        const dados = await enviarRequisicaoFicha(`/api/ficha/${estadoFicha.id}/template/${templateId}/apply`, {
            method: "POST"
        });

        estadoFicha = {
            ...estadoFicha,
            ...dados,
            modo: estadoFicha.modo,
            podeEditar: estadoFicha.podeEditar
        };

        normalizarIdsFicha();
        garantirAbaGeralPrimeiraColuna();
        garantirAbasAtivas();
        renderizarFichaCompleta();
        fecharModalTemplateList();
        mostrarToastNotificacao("Template aplicado", `O template "${nomeTemplate}" foi carregado.`, "sucesso");
    } catch (erro) {
        mostrarToastNotificacao("Erro", "Não foi possível aplicar o template.", "erro");
    }
}

function limparFichaCompleta() {
    if (!confirm("Tem certeza que deseja limpar todos os dados da ficha? Esta ação não pode ser desfeita.")) return;

    estadoFicha.colunas = {
        1: { ativa: true, abas: [], abaAtivaId: null },
        2: { ativa: true, abas: [], abaAtivaId: null },
        3: { ativa: true, abas: [], abaAtivaId: null }
    };
    renderizarFichaCompleta();
    fecharGavetaLateral("config");
    mostrarToastNotificacao("Limpeza", "Todos os dados foram removidos.", "alerta");
    agendarSalvamento();
}

function abrirGavetaLateral(tipo) {
    fecharGavetaLateral("config");
    fecharGavetaLateral("historico");
    const gaveta = document.getElementById(`gaveta_${tipo}`);
    if (gaveta) {
        gaveta.classList.remove("-translate-x-full");
        if (tipo === "config") renderizarConfiguradorEstrutura();
    }
}

function fecharGavetaLateral(tipo) {
    const gaveta = document.getElementById(`gaveta_${tipo}`);
    if (gaveta) gaveta.classList.add("-translate-x-full");
}

function definirVisibilidade(novaVisibilidade) {
    if (!estadoFicha.podeEditar) {
        mostrarToastNotificacao("Acesso negado", "Você só pode visualizar esta ficha em modo jogo.", "erro");
        return;
    }
    estadoFicha.visibilidade = novaVisibilidade;
    renderizarConfiguradorEstrutura();
    agendarSalvamento();
}

function abrirModalResgate() {
    document.getElementById("modal_resgate_global").classList.remove("hidden");
}

function fecharModalResgate() {
    document.getElementById("modal_resgate_global").classList.add("hidden");
}

function abrirDiceRoller() {
    document.getElementById("modal_dice_roller").classList.remove("hidden");
}

function fecharDiceRoller() {
    document.getElementById("modal_dice_roller").classList.add("hidden");
}

function adicionarDadoPilha(dado) {
    if (!pilhaDadosAtiva[dado]) pilhaDadosAtiva[dado] = 0;
    pilhaDadosAtiva[dado]++;
    const badge = document.getElementById(`badge_${dado}`);
    if (badge) {
        badge.textContent = pilhaDadosAtiva[dado];
        badge.classList.remove("hidden");
    }
    atualizarFormulaExibida();
}

function removerUltimoDadoPilha() {
    const chaves = Object.keys(pilhaDadosAtiva);
    if (chaves.length === 0) return;
    const ultima = chaves[chaves.length - 1];
    if (pilhaDadosAtiva[ultima] > 0) {
        pilhaDadosAtiva[ultima]--;
        const badge = document.getElementById(`badge_${ultima}`);
        if (badge) {
            badge.textContent = pilhaDadosAtiva[ultima];
            if (pilhaDadosAtiva[ultima] === 0) {
                badge.classList.add("hidden");
                delete pilhaDadosAtiva[ultima];
            }
        }
    }
    atualizarFormulaExibida();
}

function limparPilhaDados() {
    pilhaDadosAtiva = {};
    document.querySelectorAll("[id^='badge_']").forEach(b => {
        b.textContent = "0";
        b.classList.add("hidden");
    });
    const bonusInput = document.getElementById("bonus_dados");
    if (bonusInput) bonusInput.value = "0";
    const formulaInput = document.getElementById("input_formula_rolagem");
    if (formulaInput) formulaInput.value = "";
    atualizarFormulaExibida();
}

function atualizarFormulaExibida() {
    const container = document.getElementById("formula_rolagem_exibida");
    if (!container) return;
    const partes = [];
    for (const [dado, qtd] of Object.entries(pilhaDadosAtiva)) {
        if (qtd > 0) partes.push(`${qtd}${dado}`);
    }
    const bonusInput = document.getElementById("bonus_dados");
    const bonus = bonusInput ? parseInt(bonusInput.value) || 0 : 0;
    if (bonus !== 0) partes.push(bonus > 0 ? `+${bonus}` : `${bonus}`);
    
    const inputFormula = document.getElementById("input_formula_rolagem");
    if (inputFormula) {
        if (partes.length > 0) {
            inputFormula.value = partes.join("+").replace(/\+\+/g, "+").replace(/^\+/, "");
        } else {
            inputFormula.value = "";
        }
    }
}

function parseFormulaRolagem(formula) {
    if (typeof formula !== "string") formula = "";

    // Remove todos os espaços em branco, independente da quantidade/posição
    const semEspacos = formula.replace(/\s+/g, "");

    // Campo vazio é válido e representa bônus zero
    if (semEspacos === "") {
        return { valido: true, valor: 0 };
    }

    // Aceita apenas sequências de números inteiros antecedidos por + ou -
    // Ex: "+5+2+3" ou "+5+3+2-1"
    const regexValido = /^([+\-]\d+)+$/;
    if (!regexValido.test(semEspacos)) {
        return { valido: false, valor: 0 };
    }

    // Soma cada termo assinado encontrado na fórmula
    const termos = semEspacos.match(/[+\-]\d+/g) || [];
    const valor = termos.reduce((soma, termo) => soma + parseInt(termo, 10), 0);

    return { valido: true, valor };
}

function aplicarFormulaRolagem() {
    // Chamada durante a digitação (oninput/onchange): apenas sincroniza o bônus
    // silenciosamente. Nenhuma notificação de erro é exibida aqui, evitando
    // poluição visual a cada alteração do campo. A validação com aviso ao
    // usuário só ocorre ao pressionar "Rolar Dados" (ver rolarPilhaDadosAtiva).
    const input = document.getElementById("input_formula_rolagem");
    if (!input) return;

    // Remove qualquer destaque de erro deixado por uma tentativa anterior de rolagem
    input.classList.remove("border-red-500/50");
    input.classList.add("border-white/10");

    const resultado = parseFormulaRolagem(input.value);

    const bonusInput = document.getElementById("bonus_dados");
    if (bonusInput && resultado.valido) {
        bonusInput.value = resultado.valor;
    }
    // Se inválido, apenas não atualiza o bônus — sem notificar o usuário agora.
}

function ajustarCamposOperacao() {
    const op = document.querySelector("input[name='tipo_operacao_dados']:checked");
    if (!op) return;
    const panel = document.getElementById("painel_sub_opcoes");
    const rolarManter = document.getElementById("sub_rolar_manter");
    if (op.value === "Rolar_Manter") {
        panel.classList.remove("hidden");
        rolarManter.classList.remove("hidden");
    } else {
        panel.classList.add("hidden");
        rolarManter.classList.add("hidden");
    }
}

function alternarCamposSucesso() {
    const chk = document.getElementById("chk_definir_sucesso");
    const panel = document.getElementById("painel_definir_sucesso_campos");
    if (chk && panel) panel.classList.toggle("hidden", !chk.checked);
}

function executarRolagemDiretaAtalho(formula) {
    const padrao = /^(\d+)d(\d+)([\+\-]\d+)?$/;
    const match = formula.match(padrao);
    if (!match) {
        mostrarToastNotificacao("Fórmula Inválida", "Use formato: 1d20 ou 3d6+5", "erro");
        return;
    }
    const qtd = parseInt(match[1]);
    const faces = parseInt(match[2]);
    const mod = match[3] ? parseInt(match[3]) : 0;
    const resultados = [];
    for (let i = 0; i < qtd; i++) {
        resultados.push(Math.floor(Math.random() * faces) + 1);
    }
    const total = resultados.reduce((a, b) => a + b, 0) + mod;
    mostrarToastNotificacao("Rolagem: " + formula, `Total: ${total} (${resultados.join(", ")})`, "sucesso");
    adicionarLogHistorico(resultados, total, 0, false);
}

function rolarPilhaDadosAtiva() {
    const chaves = Object.keys(pilhaDadosAtiva);
    if (chaves.length === 0) {
        mostrarToastNotificacao("Aviso", "Selecione pelo menos um dado.", "alerta");
        return;
    }

    // Valida a fórmula de bônus somente agora, ao pressionar "Rolar Dados".
    // É aqui (e apenas aqui) que uma notificação de fórmula inválida é exibida.
    const inputFormula = document.getElementById("input_formula_rolagem");
    const resultadoFormula = parseFormulaRolagem(inputFormula ? inputFormula.value : "");

    if (!resultadoFormula.valido) {
        mostrarToastNotificacao("Erro", "Fórmula de bônus inválida. Use apenas números precedidos de + ou -, Ex: +5+3-1", "erro");
        if (inputFormula) {
            inputFormula.classList.add("border-red-500/50");
            inputFormula.classList.remove("border-white/10");
            setTimeout(() => {
                inputFormula.classList.remove("border-red-500/50");
                inputFormula.classList.add("border-white/10");
            }, 2000);
        }
        return;
    }

    const op = document.querySelector("input[name='tipo_operacao_dados']:checked");
    const tipo = op ? op.value : "Somatório";
    const bonus = resultadoFormula.valor;
    if (inputFormula) {
        const bonusInput = document.getElementById("bonus_dados");
        if (bonusInput) bonusInput.value = bonus;
    }
    const usarSucesso = document.getElementById("chk_definir_sucesso").checked;
    const usarExplosao = document.getElementById("chk_explosao_dados").checked;

    let valores = [];
    for (const [dado, qtd] of Object.entries(pilhaDadosAtiva)) {
        const faces = parseInt(dado.replace("d", ""));
        for (let i = 0; i < qtd; i++) {
            let rolada = Math.floor(Math.random() * faces) + 1;
            valores.push(rolada);
            if (usarExplosao && rolada === faces) {
                valores.push(Math.floor(Math.random() * faces) + 1);
            }
        }
    }

    let final = 0;
    let sucessos = 0;
    if (usarSucesso) {
        const min = parseInt(document.getElementById("valor_sucesso_minimo").value) || 0;
        const cond = document.getElementById("condicao_sucesso").value;
        valores.forEach(v => {
            if (cond === ">=" && v >= min) sucessos++;
            else if (cond === "=" && v === min) sucessos++;
            else if (cond === "<=" && v <= min) sucessos++;
        });
        final = sucessos;
    } else if (tipo === "Somatório") {
        final = valores.reduce((a, b) => a + b, 0) + bonus;
    } else if (tipo === "Rolar_Manter") {
        const manter = document.querySelector("input[name='manter_opcao']:checked");
        final = (manter && manter.value === "Maior") ? Math.max(...valores) : Math.min(...valores);
        final += bonus;
    }

    const msg = usarSucesso ? `${sucessos} Sucesso(s)` : `Total: ${final}`;
    mostrarToastNotificacao("Rolagem Realizada!", `${msg} (${valores.join(", ")})`, "sucesso");
    adicionarLogHistorico(valores, final, sucessos, usarSucesso);
    fecharDiceRoller();
    limparPilhaDados();
}

function adicionarLogHistorico(valores, final, sucessos, usarSucesso) {
    const container = document.getElementById("lista_historico_rolagens");
    if (!container) return;
    const placeholder = container.querySelector("p");
    if (placeholder) placeholder.remove();

    const item = document.createElement("div");
    item.className = "p-4 bg-purple-950/40 border border-white/5 rounded-2xl space-y-2";
    item.innerHTML = `
        <div class="flex items-center justify-between">
            <span class="text-xs font-mono text-purple-300 font-bold">${usarSucesso ? "Contagem de Sucessos" : "Rolagem"}</span>
            <span class="text-[10px] text-purple-400/50">${new Date().toLocaleTimeString()}</span>
        </div>
        <p class="text-sm font-bold text-white">${usarSucesso ? sucessos + " Sucesso(s)" : "Total: " + final}</p>
        <p class="text-[10px] font-mono text-purple-400">Valores: [${valores.join(", ")}]</p>
    `;
    container.insertBefore(item, container.firstChild);
}