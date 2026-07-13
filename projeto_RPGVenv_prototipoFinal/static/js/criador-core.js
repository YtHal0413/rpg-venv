// ==========================================
// ESTADO GLOBAL E INICIALIZAÇÃO
// ==========================================

let estadoFicha = {
    id: typeof fichaID !== 'undefined' ? fichaID : 1,
    nome: "Novo Personagem",
    subtitulo: "",
    modo: typeof modoInicial !== 'undefined' ? modoInicial : "Jogo",
    podeEditar: typeof podeEditar !== 'undefined' ? !!podeEditar : true,
    avatar: null,
    visibilidade: typeof visibilidadeInicial !== 'undefined' ? visibilidadeInicial : "todos",
    colunas: {
        1: { ativa: true, abas: [], abaAtivaId: null },
        2: { ativa: true, abas: [], abaAtivaId: null },
        3: { ativa: true, abas: [], abaAtivaId: null }
    }
};

let pilhaDadosAtiva = {};
let historicoRolagensSessao = [];
let idGeradorInterno = 1000;
let temporizadorSalvar = null;
let salvamentoEmAndamento = false;
let salvamentoPendente = false;
let colunaAlvoNovaSecao = 1;

// ==========================================
// INICIALIZAÇÃO
// ==========================================
window.addEventListener("DOMContentLoaded", () => {
    inicializarEventosFicha();
    carregarFichaDoServidor();
});
window.addEventListener("pageshow", () => {
    renderizarFichaCompleta();
});

function inicializarEventosFicha() {
    const inputNome = document.getElementById("nome_personagem_topo");
    if (inputNome) {
        inputNome.addEventListener("input", (e) => {
            estadoFicha.nome = e.target.value;
            const cardNome = document.getElementById("nome_personagem_card");
            if (cardNome) cardNome.textContent = e.target.value;
            agendarSalvamento();
        });
    }

    const inputSubtitulo = document.getElementById("subtitulo_card");
    if (inputSubtitulo) {
        inputSubtitulo.addEventListener("input", (e) => {
            estadoFicha.subtitulo = e.target.value;
            agendarSalvamento();
        });
    }
}

// ==========================================
// COMUNICAÇÃO COM O SERVIDOR
// ==========================================
async function carregarFichaDoServidor() {
    try {
        const resposta = await fetch(`/api/ficha/${estadoFicha.id}`);
        if (resposta.ok) {
            const dados = await resposta.json();
            if (dados && dados.id) {
                estadoFicha = {
                    ...estadoFicha,
                    ...dados,
                    modo: "Jogo",
                    visibilidade: dados.visibilidade === "mestres" ? "mestres" : "todos",
                    podeEditar: estadoFicha.podeEditar,
                };
                
                normalizarIdsFicha();
                garantirAbaGeralPrimeiraColuna();
                garantirAbasAtivas();
                renderizarFichaCompleta();
                
                if (dados.avatar) {
                    const img = document.getElementById('avatar_imagem');
                    const placeholder = document.getElementById('avatar_placeholder');
                    if (img) {
                        img.src = dados.avatar;
                        img.classList.remove('hidden');
                        if (placeholder) placeholder.classList.add('hidden');
                    }
                } else {
                    const img = document.getElementById('avatar_imagem');
                    const placeholder = document.getElementById('avatar_placeholder');
                    if (img) img.classList.add('hidden');
                    if (placeholder) placeholder.classList.remove('hidden');
                }
                return;
            }
        }
        renderizarFichaCompleta();
    } catch (erro) {
        console.warn("Falha ao carregar ficha:", erro);
        renderizarFichaCompleta();
    }
}

function garantirAbaGeralPrimeiraColuna() {
    if (!estadoFicha.colunas[1]) return;
    
    const col1 = estadoFicha.colunas[1];
    const temAbaGeral = col1.abas && col1.abas.some(a => a.ehPadrao === true || a.titulo === "Geral");
    
    if (!temAbaGeral) {
        const abaGeral = {
            id: 1000,
            titulo: "Geral",
            ehPadrao: true,
            secoes: []
        };
        col1.abas = col1.abas || [];
        col1.abas.unshift(abaGeral);
        col1.abaAtivaId = 1000;
    }
}

function garantirAbasAtivas() {
    Object.values(estadoFicha.colunas).forEach(coluna => {
        if (coluna && coluna.abas && coluna.abas.length > 0) {
            const temAtiva = coluna.abaAtivaId != null && coluna.abas.some(aba => aba.id == coluna.abaAtivaId);
            if (!temAtiva) {
                coluna.abaAtivaId = coluna.abas[0].id;
            }
        }
    });
}

function normalizarIdsFicha() {
    let maiorId = idGeradorInterno;
    Object.values(estadoFicha.colunas).forEach(coluna => {
        if (!coluna || !coluna.abas) return;
        coluna.abas.forEach(aba => {
            if (!aba.id || aba.id === 0) {
                aba.id = ++maiorId;
            } else {
                maiorId = Math.max(maiorId, aba.id);
            }
            if (aba.secoes) {
                aba.secoes.forEach(secao => {
                    if (!secao.id || secao.id === 0) {
                        secao.id = ++maiorId;
                    } else {
                        maiorId = Math.max(maiorId, secao.id);
                    }
                    if (secao.componentes) {
                        secao.componentes.forEach(comp => {
                            if (!comp.id || comp.id === 0) {
                                comp.id = ++maiorId;
                            } else {
                                maiorId = Math.max(maiorId, comp.id);
                            }
                        });
                    }
                });
            }
        });
        if (coluna.abaAtivaId == null || !coluna.abas.some(aba => aba.id == coluna.abaAtivaId)) {
            coluna.abaAtivaId = coluna.abas.length > 0 ? coluna.abas[0].id : null;
        }
    });
    idGeradorInterno = maiorId;
}

function agendarSalvamento() {
    if (temporizadorSalvar) clearTimeout(temporizadorSalvar);
    temporizadorSalvar = setTimeout(() => {
        temporizadorSalvar = null;
        salvarFichaNoServidor();
    }, 2000);
}

async function salvarFichaNoServidor() {
    if (salvamentoEmAndamento) {
        salvamentoPendente = true;
        return;
    }

    salvamentoEmAndamento = true;
    try {
        const resposta = await fetch(`/api/ficha/${estadoFicha.id}`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(estadoFicha)
        });
        if (resposta.ok) {
            mostrarToastNotificacao("Sincronizado", "Ficha salva com sucesso!", "sucesso");
        }
    } catch (erro) {
        console.warn("Falha ao salvar:", erro);
    } finally {
        salvamentoEmAndamento = false;
        if (salvamentoPendente) {
            salvamentoPendente = false;
            salvarFichaNoServidor();
        }
    }
}
