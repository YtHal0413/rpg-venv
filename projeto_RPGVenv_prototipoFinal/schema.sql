CREATE TABLE IF NOT EXISTS Usuario (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome VARCHAR(100) NOT NULL,
    email VARCHAR(100) NOT NULL,
    senha_hash VARCHAR(255) NOT NULL,
    data_Cadastro DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    imagem_avatar VARCHAR(255) NULL,
    chave_ativada BOOLEAN NOT NULL DEFAULT 0,
    CONSTRAINT UQ_Usuario_Email UNIQUE (email)
);

CREATE TABLE IF NOT EXISTS Campanha (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome VARCHAR(100) NOT NULL,
    descricao TEXT NULL,
    lista_personagens TEXT NULL,
    data_Criacao DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    id_mestre INTEGER NOT NULL,
    CONSTRAINT FK_Campanha_Usuario FOREIGN KEY (id_mestre) REFERENCES Usuario(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS FichaPersonagem (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome_personagem VARCHAR(100) NOT NULL,
    aspecto_personagem VARCHAR(100) NOT NULL DEFAULT "",
    data_Criacao DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    id_usuario INTEGER NOT NULL,
    estrutura_json TEXT NULL,
    CONSTRAINT FK_Ficha_Usuario FOREIGN KEY (id_usuario) REFERENCES Usuario(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS Template (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome_template VARCHAR(100) NOT NULL,
    data_Criacao DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    id_ficha INTEGER NULL,
    id_usuario INTEGER NOT NULL,
    estrutura_json TEXT NULL,
    CONSTRAINT FK_Template_Ficha FOREIGN KEY (id_ficha) REFERENCES FichaPersonagem(id) ON DELETE SET NULL,
    CONSTRAINT FK_Template_Usuario FOREIGN KEY (id_usuario) REFERENCES Usuario(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS Coluna (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    limite_abas INTEGER NOT NULL DEFAULT 5,
    esta_ativa BOOLEAN NOT NULL DEFAULT 1,
    posicao_coluna INTEGER NOT NULL,
    aba_ativa_id INTEGER NULL,
    id_template INTEGER NULL,
    id_ficha INTEGER NULL,
    CONSTRAINT FK_Coluna_Template FOREIGN KEY (id_template) REFERENCES Template(id) ON DELETE CASCADE,
    CONSTRAINT FK_Coluna_Ficha FOREIGN KEY (id_ficha) REFERENCES FichaPersonagem(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS Aba (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    titulo VARCHAR(100) NOT NULL,
    posicao_aba INTEGER NOT NULL,
    id_coluna INTEGER NOT NULL,
    CONSTRAINT FK_Aba_Coluna FOREIGN KEY (id_coluna) REFERENCES Coluna(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS Secao (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    titulo VARCHAR(100) NOT NULL,
    conteudo TEXT NULL,
    posicao_secao INTEGER NOT NULL,
    id_aba INTEGER NOT NULL,
    CONSTRAINT FK_Secao_Aba FOREIGN KEY (id_aba) REFERENCES Aba(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS InformacaoCurta (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    rotulo VARCHAR(100) NOT NULL,
    campo_texto VARCHAR(255) NOT NULL,
    id_secao INTEGER NOT NULL,
    CONSTRAINT FK_InfoCurta_Secao FOREIGN KEY (id_secao) REFERENCES Secao(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS Contador (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    rotulo VARCHAR(100) NOT NULL,
    valor_atual INTEGER NOT NULL,
    valor_maximo INTEGER NOT NULL,
    cor_seletor VARCHAR(50) NULL,
    id_secao INTEGER NOT NULL,
    CONSTRAINT FK_Contador_Secao FOREIGN KEY (id_secao) REFERENCES Secao(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS Checkbox (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    rotulo VARCHAR(100) NOT NULL,
    esta_marcado BOOLEAN NOT NULL DEFAULT 0,
    id_secao INTEGER NOT NULL,
    CONSTRAINT FK_Checkbox_Secao FOREIGN KEY (id_secao) REFERENCES Secao(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS AnotacaoSimples (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    rotulo VARCHAR(100) NOT NULL,
    descricao TEXT NULL,
    id_secao INTEGER NOT NULL,
    CONSTRAINT FK_AnotacaoSimples_Secao FOREIGN KEY (id_secao) REFERENCES Secao(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS AnotacaoDetalhada (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    rotulo VARCHAR(100) NOT NULL,
    descricao TEXT NULL,
    anotacao_extra VARCHAR(100) NOT NULL,
    id_secao INTEGER NOT NULL,
    CONSTRAINT FK_AnotacaoDetalhada_Secao FOREIGN KEY (id_secao) REFERENCES Secao(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS AnotacaoCheckbox (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    rotulo VARCHAR(100) NOT NULL,
    descricao TEXT NULL,
    esta_marcado BOOLEAN NOT NULL DEFAULT 0,
    id_secao INTEGER NOT NULL,
    CONSTRAINT FK_AnotacaoCheckbox_Secao FOREIGN KEY (id_secao) REFERENCES Secao(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS AtributoSimples (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome_atributo VARCHAR(100) NOT NULL,
    valor_atributo INTEGER NOT NULL,
    id_secao INTEGER NOT NULL,
    CONSTRAINT FK_AtributoSimples_Secao FOREIGN KEY (id_secao) REFERENCES Secao(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS AtributoDuplo (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome_atributo VARCHAR(100) NOT NULL,
    valor_grande INTEGER NOT NULL,
    valor_pequeno INTEGER NOT NULL,
    id_secao INTEGER NOT NULL,
    CONSTRAINT FK_AtributoDuplo_Secao FOREIGN KEY (id_secao) REFERENCES Secao(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS AtributoComplexo (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome_atributo VARCHAR(100) NOT NULL,
    subtitulo_anotacao VARCHAR(150) NULL,
    valor_base INTEGER NOT NULL DEFAULT 0,
    valor_bonus INTEGER NOT NULL DEFAULT 0,
    valor_outros INTEGER NOT NULL DEFAULT 0,
    id_secao INTEGER NOT NULL,
    CONSTRAINT FK_AtributoComplexo_Secao FOREIGN KEY (id_secao) REFERENCES Secao(id) ON DELETE CASCADE
);