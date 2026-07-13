import sqlite3
import os
import json
import time
from classes import (
    Usuario, Campanha, FichaPersonagem, Coluna, Aba, Secao,
    ComponenteSecao, InformacaoCurta, Contador, Checkbox,
    AtributoSimples, AtributoDuplo, AtributoComplexo,
    AnotacaoSimples, AnotacaoCheckbox, AnotacaoDetalhada,
    PlataformaErro, ValidacaoDadosErro
)

class ConexaoBD:
    def __init__(self, caminho_db: str = "rpg_plataforma.db"):
        self.caminho_db = caminho_db
        self.conexao = None

    def __enter__(self):
        self.conexao = sqlite3.connect(self.caminho_db)
        self.conexao.row_factory = sqlite3.Row
        self.conexao.execute("PRAGMA foreign_keys = ON;")
        return self.conexao

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.conexao:
            if exc_type is not None:
                self.conexao.rollback()
            else:
                self.conexao.commit()
            self.conexao.close()


class ControladorBD:
    def __init__(self, caminho_db: str = "rpg_plataforma.db"):
        self.caminho_db = caminho_db
        self._ultimo_id_gerado = 0

    def inicializar_banco(self, caminho_schema: str = "schema.sql"):
        caminho_schema_real = caminho_schema
        if not os.path.isabs(caminho_schema_real):
            caminho_schema_real = os.path.join(os.path.dirname(__file__), caminho_schema_real)

        if not os.path.exists(caminho_schema_real):
            raise PlataformaErro(f"Arquivo de esquema '{caminho_schema_real}' nao encontrado.")
        
        with open(caminho_schema_real, "r", encoding="utf-8") as f:
            script_sql = f.read()

        with ConexaoBD(self.caminho_db) as conn:
            conn.executescript(script_sql)
            self._garantir_coluna_estrutura_json(conn)
            self._garantir_coluna_id_ficha(conn)
            self._garantir_coluna_aba_ativa_id(conn)

    def _garantir_coluna_estrutura_json(self, conn):
        try:
            conn.execute("ALTER TABLE FichaPersonagem ADD COLUMN estrutura_json TEXT")
        except sqlite3.OperationalError as exc:
            if "duplicate column name" not in str(exc).lower():
                raise

    def _garantir_coluna_id_ficha(self, conn):
        try:
            conn.execute("ALTER TABLE Coluna ADD COLUMN id_ficha INTEGER NULL")
        except sqlite3.OperationalError as exc:
            if "duplicate column name" not in str(exc).lower():
                raise

    def _garantir_coluna_aba_ativa_id(self, conn):
        try:
            conn.execute("ALTER TABLE Coluna ADD COLUMN aba_ativa_id INTEGER NULL")
        except sqlite3.OperationalError as exc:
            if "duplicate column name" not in str(exc).lower():
                raise

    # ==========================================
    # OPERAÇÕES DE USUÁRIO
    # ==========================================
    
    def cadastrar_usuario(self, nome: str, email: str, senha_hash: str, imagem_avatar: str = None) -> Usuario:
        query = """
            INSERT INTO Usuario (nome, email, senha_hash, imagem_avatar)
            VALUES (?, ?, ?, ?)
        """
        try:
            with ConexaoBD(self.caminho_db) as conn:
                cursor = conn.cursor()
                cursor.execute(query, (nome, email, senha_hash, imagem_avatar))
                id_gerado = cursor.lastrowid
                return Usuario(id_gerado, nome, email, senha_hash, imagem_avatar)
        except sqlite3.IntegrityError:
            raise ValidacaoDadosErro("O e-mail informado ja esta cadastrado no sistema.")

    def obter_usuario(self, id_usuario: int) -> Usuario:
        query = "SELECT * FROM Usuario WHERE id = ?"
        with ConexaoBD(self.caminho_db) as conn:
            cursor = conn.cursor()
            cursor.execute(query, (id_usuario,))
            row = cursor.fetchone()
            if row:
                user = Usuario(row["id"], row["nome"], row["email"], row["senha_hash"], row["imagem_avatar"])
                if row["chave_ativada"] == 1:
                    user.ativar_chave("HA4H4nF1tR1A0HA4")
                return user
        return None

    def obter_usuario_por_email(self, email: str) -> Usuario:
        query = "SELECT * FROM Usuario WHERE email = ?"
        with ConexaoBD(self.caminho_db) as conn:
            cursor = conn.cursor()
            cursor.execute(query, (email,))
            row = cursor.fetchone()
            if row:
                user = Usuario(row["id"], row["nome"], row["email"], row["senha_hash"], row["imagem_avatar"])
                if row["chave_ativada"] == 1:
                    user.ativar_chave("HA4H4nF1tR1A0HA4")
                return user
        return None

    def atualizar_chave_usuario(self, id_usuario: int, status_chave: bool):
        query = "UPDATE Usuario SET chave_ativada = ? WHERE id = ?"
        with ConexaoBD(self.caminho_db) as conn:
            conn.execute(query, (1 if status_chave else 0, id_usuario))

    def atualizar_usuario(self, id_usuario: int, nome: str, senha_hash: str, imagem_avatar: str = None):
        query = "UPDATE Usuario SET nome = ?, senha_hash = ?, imagem_avatar = ? WHERE id = ?"
        with ConexaoBD(self.caminho_db) as conn:
            conn.execute(query, (nome, senha_hash, imagem_avatar, id_usuario))

    # ==========================================
    # OPERAÇÕES DE CAMPANHA
    # ==========================================
    
    def criar_campanha(self, nome: str, id_mestre: int, descricao: str = None) -> Campanha:
        query = """
            INSERT INTO Campanha (nome, descricao, id_mestre, lista_personagens)
            VALUES (?, ?, ?, ?)
        """
        dados_iniciais = json.dumps({"jogadores": [], "personagens": [], "arquivos": []})
        with ConexaoBD(self.caminho_db) as conn:
            cursor = conn.cursor()
            cursor.execute(query, (nome, descricao, id_mestre, dados_iniciais))
            id_gerado = cursor.lastrowid
            return Campanha(id_gerado, nome, id_mestre, descricao)

    def obter_campanha(self, id_campanha: int) -> Campanha:
        query = "SELECT * FROM Campanha WHERE id = ?"
        with ConexaoBD(self.caminho_db) as conn:
            cursor = conn.cursor()
            cursor.execute(query, (id_campanha,))
            row = cursor.fetchone()
            if row:
                camp = Campanha(row["id"], row["nome"], row["id_mestre"], row["descricao"])
                try:
                    if row["lista_personagens"]:
                        dados = json.loads(row["lista_personagens"])
                        for j_id in dados.get("jogadores", []):
                            u = self.obter_usuario(j_id)
                            if u:
                                camp.adicionar_jogador(u)
                        for ficha_id in dados.get("personagens", []):
                            ficha = self.obter_ficha_completa(ficha_id)
                            if ficha:
                                camp.adicionar_personagem(ficha)
                        for arquivo in dados.get("arquivos", []):
                            if arquivo:
                                camp.arquivos.append(arquivo)
                except Exception:
                    pass
                return camp
        return None

    def _obter_dados_json_campanha(self, id_campanha: int) -> dict:
        with ConexaoBD(self.caminho_db) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT lista_personagens FROM Campanha WHERE id = ?", (id_campanha,))
            row = cursor.fetchone()
            dados = {"jogadores": [], "personagens": [], "arquivos": []}
            if row and row["lista_personagens"]:
                try:
                    dados = json.loads(row["lista_personagens"])
                except Exception:
                    dados = {"jogadores": [], "personagens": [], "arquivos": []}
            if "jogadores" not in dados:
                dados["jogadores"] = []
            if "personagens" not in dados:
                dados["personagens"] = []
            if "arquivos" not in dados:
                dados["arquivos"] = []
            return dados

    def adicionar_usuario_campanha(self, id_campanha: int, id_usuario: int):
        dados = self._obter_dados_json_campanha(id_campanha)
        if id_usuario not in dados["jogadores"]:
            dados["jogadores"].append(id_usuario)
        with ConexaoBD(self.caminho_db) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE Campanha SET lista_personagens = ? WHERE id = ?",
                (json.dumps(dados), id_campanha)
            )

    def adicionar_ficha_campanha(self, id_campanha: int, id_ficha: int):
        dados = self._obter_dados_json_campanha(id_campanha)
        if id_ficha not in dados["personagens"]:
            dados["personagens"].append(id_ficha)
        with ConexaoBD(self.caminho_db) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE Campanha SET lista_personagens = ? WHERE id = ?",
                (json.dumps(dados), id_campanha)
            )

    def adicionar_arquivo_campanha(self, id_campanha: int, nome_arquivo: str):
        dados = self._obter_dados_json_campanha(id_campanha)
        if nome_arquivo not in dados["arquivos"]:
            dados["arquivos"].append(nome_arquivo)
        with ConexaoBD(self.caminho_db) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE Campanha SET lista_personagens = ? WHERE id = ?",
                (json.dumps(dados), id_campanha)
            )

    def remover_arquivo_campanha(self, id_campanha: int, nome_arquivo: str):
        dados = self._obter_dados_json_campanha(id_campanha)
        if nome_arquivo in dados["arquivos"]:
            dados["arquivos"].remove(nome_arquivo)
        with ConexaoBD(self.caminho_db) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE Campanha SET lista_personagens = ? WHERE id = ?",
                (json.dumps(dados), id_campanha)
            )

    def remover_ficha_campanha(self, id_campanha: int, id_ficha: int):
        dados = self._obter_dados_json_campanha(id_campanha)
        if id_ficha in dados["personagens"]:
            dados["personagens"].remove(id_ficha)
        with ConexaoBD(self.caminho_db) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE Campanha SET lista_personagens = ? WHERE id = ?",
                (json.dumps(dados), id_campanha)
            )

    def obter_campanhas_usuario(self, id_usuario: int) -> list:
        campanhas = []
        with ConexaoBD(self.caminho_db) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM Campanha")
            rows = cursor.fetchall()
            for row in rows:
                pertence = False
                if row["id_mestre"] == id_usuario:
                    pertence = True
                else:
                    try:
                        if row["lista_personagens"]:
                            dados = json.loads(row["lista_personagens"])
                            if id_usuario in dados.get("jogadores", []):
                                pertence = True
                    except Exception:
                        pass
                if pertence:
                    campanhas.append(Campanha(row["id"], row["nome"], row["id_mestre"], row["descricao"]))
        return campanhas

    def atualizar_campanha(self, id_campanha: int, nome: str, descricao: str = None):
        with ConexaoBD(self.caminho_db) as conn:
            conn.execute(
                "UPDATE Campanha SET nome = ?, descricao = ? WHERE id = ?",
                (nome, descricao, id_campanha)
            )

    # ==========================================
    # OPERAÇÕES DE FICHA PERSONAGEM
    # ==========================================
    
    def criar_ficha_vazia(self, nome: str, id_usuario: int, subtitulo: str = "") -> FichaPersonagem:
        query = "INSERT INTO FichaPersonagem (nome_personagem, aspecto_personagem, id_usuario, estrutura_json) VALUES (?, ?, ?, ?)"
        estrutura_inicial = json.dumps({
            "id": None,
            "nome": nome,
            "subtitulo": subtitulo,
            "avatar": None,
            "visibilidade": "todos",
            "colunas": {
                "1": {
                    "ativa": True,
                    "abaAtivaId": 1000,
                    "abas": [
                        {
                            "id": 1000,
                            "titulo": "Geral",
                            "ehPadrao": True,
                            "secoes": []
                        }
                    ]
                },
                "2": {"ativa": True, "abaAtivaId": None, "abas": []},
                "3": {"ativa": True, "abaAtivaId": None, "abas": []},
            },
        })
        with ConexaoBD(self.caminho_db) as conn:
            cursor = conn.cursor()
            cursor.execute(query, (nome, subtitulo, id_usuario, estrutura_inicial))
            id_gerado = cursor.lastrowid
            ficha = FichaPersonagem(id_gerado, nome, id_usuario, subtitulo)
            ficha.colunas = [
                Coluna(id_template=None, posicao_coluna=1, esta_ativa=True, limite_abas=3, id_ficha=id_gerado),
                Coluna(id_template=None, posicao_coluna=2, esta_ativa=True, limite_abas=3, id_ficha=id_gerado),
                Coluna(id_template=None, posicao_coluna=3, esta_ativa=True, limite_abas=3, id_ficha=id_gerado),
            ]
            ficha.colunas[0].adicionar_aba(Aba(id=None, id_coluna=None, titulo="Geral", posicao_aba=1))
            self._salvar_estrutura_em_tabelas(cursor, ficha)
            return ficha

    def obter_fichas_usuario(self, id_usuario: int) -> list:
        """Retorna todas as fichas de um usuário com seus avatares carregados."""
        query = "SELECT * FROM FichaPersonagem WHERE id_usuario = ?"
        fichas = []
        with ConexaoBD(self.caminho_db) as conn:
            cursor = conn.cursor()
            cursor.execute(query, (id_usuario,))
            rows = cursor.fetchall()
            for row in rows:
                r = dict(row)
                ficha = FichaPersonagem(r.get("id"), r.get("nome_personagem", r.get("nome", "Novo Personagem")), id_usuario, r.get("aspecto_personagem", ""))
                ficha.avatar = None
                ficha.visibilidade = "todos"
                ficha.subtitulo = r.get("aspecto_personagem", "")
                # Carrega avatar do JSON se existir
                if r.get("estrutura_json"):
                    try:
                        dados = json.loads(r.get("estrutura_json"))
                        ficha.avatar = dados.get("avatar", None)
                        ficha.subtitulo = dados.get("subtitulo", "")
                        ficha.visibilidade = dados.get("visibilidade", "todos")
                    except:
                        pass
                fichas.append(ficha)
        return fichas

    def salvar_ficha_completa(self, ficha: FichaPersonagem):
        """Salva a ficha completa com todos os componentes e avatar."""
        subtitulo = getattr(ficha, "subtitulo", None)
        if subtitulo is None or subtitulo == "":
            subtitulo = getattr(ficha, "aspecto", "") or getattr(ficha, "aspecto_personagem", "")

        with ConexaoBD(self.caminho_db) as conn:
            cursor = conn.cursor()
            
            # Salva a estrutura em tabelas individuais primeiro para garantir IDs atribuídos
            self._salvar_estrutura_em_tabelas(cursor, ficha)
            
            # Salva o JSON da ficha com IDs já definidos
            payload = self._serializar_ficha(ficha)
            cursor.execute(
                """INSERT INTO FichaPersonagem 
                   (id, nome_personagem, aspecto_personagem, id_usuario, estrutura_json) 
                   VALUES (?, ?, ?, ?, ?) 
                   ON CONFLICT(id) DO UPDATE SET 
                   nome_personagem=excluded.nome_personagem, 
                   aspecto_personagem=excluded.aspecto_personagem, 
                   estrutura_json=excluded.estrutura_json""",
                (ficha.id, ficha.nome_personagem, subtitulo, ficha.id_usuario, json.dumps(payload))
            )
    
    def _salvar_estrutura_em_tabelas(self, cursor, ficha: FichaPersonagem):
        """Salva estrutura da ficha nas tabelas: Coluna, Aba, Secao e Componentes."""
        id_ficha = ficha.id
        
        # Deleta estrutura antiga da ficha antes de recriar
        cursor.execute("DELETE FROM Coluna WHERE id_ficha = ?", (id_ficha,))
        
        for coluna in (ficha.colunas or []):
            coluna_id = coluna.id or self._gerar_id_unico("coluna")
            coluna.id = coluna_id
            
            cursor.execute(
                """INSERT INTO Coluna (id, id_ficha, posicao_coluna, esta_ativa, limite_abas, aba_ativa_id, id_template)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (coluna_id, id_ficha, coluna.posicao_coluna, coluna.esta_ativa, coluna.limite_abas, coluna.abaAtivaId, coluna.id_template)
            )
            
            for aba in (coluna.abas or []):
                aba_id = aba.id or self._gerar_id_unico("aba")
                aba.id_coluna = coluna_id
                aba.id = aba_id
                
                cursor.execute(
                    """INSERT INTO Aba (id, id_coluna, titulo, posicao_aba)
                       VALUES (?, ?, ?, ?)""",
                    (aba_id, coluna_id, aba.titulo, aba.posicao_aba)
                )
                
                for secao in (aba.secoes or []):
                    secao_id = secao.id or self._gerar_id_unico("secao")
                    secao.id_aba = aba_id
                    secao.id = secao_id
                    
                    tipo_secao = getattr(secao, "tipo", None)
                    if not tipo_secao:
                        tipo_secao = secao.componentes[0].__class__.__name__ if secao.componentes else "AtributoSimples"
                    
                    cursor.execute(
                        """INSERT INTO Secao (id, id_aba, titulo, posicao_secao, conteudo)
                           VALUES (?, ?, ?, ?, ?)""",
                        (secao_id, aba_id, secao.titulo, secao.posicao_secao, tipo_secao)
                    )
                    
                    for componente in (secao.componentes or []):
                        self._salvar_componente(cursor, componente, secao_id)
    
    def _carregar_estrutura_em_tabelas(self, cursor, ficha: FichaPersonagem):
        """Carrega a estrutura de colunas, abas, seções e componentes a partir das tabelas."""
        cursor.execute("SELECT * FROM Coluna WHERE id_ficha = ? ORDER BY posicao_coluna", (ficha.id,))
        for r_col in cursor.fetchall():
            rc = dict(r_col)
            coluna = Coluna(
                rc.get("id"),
                rc.get("id_template"),
                rc.get("posicao_coluna", 1),
                rc.get("limite_abas", 3),
                bool(rc.get("esta_ativa", True)),
                rc.get("aba_ativa_id"),
                rc.get("id_ficha")
            )

            cursor.execute("SELECT * FROM Aba WHERE id_coluna = ? ORDER BY posicao_aba", (coluna.id,))
            for r_aba in cursor.fetchall():
                ra = dict(r_aba)
                aba = Aba(ra.get("id"), coluna.id, ra.get("titulo", "Nova Aba"), ra.get("posicao_aba", 1))
                
                cursor.execute("SELECT * FROM Secao WHERE id_aba = ? ORDER BY posicao_secao", (aba.id,))
                for r_sec in cursor.fetchall():
                    rs = dict(r_sec)
                    secao = Secao(
                        rs.get("id"),
                        aba.id,
                        rs.get("titulo", "Nova Seção"),
                        rs.get("posicao_secao", 1),
                        rs.get("conteudo", "AtributoSimples")
                    )
                    self._carregar_componentes_secao(cursor, secao)
                    aba.adicionar_secao(secao)
                coluna.adicionar_aba(aba)
            ficha.adicionar_coluna(coluna)
    
    def _gerar_id_unico(self, tipo: str) -> int:
        """Gera um ID único determinístico evitando colisões no mesmo processo."""
        novo_id = int(time.time_ns())
        if novo_id <= self._ultimo_id_gerado:
            novo_id = self._ultimo_id_gerado + 1
        self._ultimo_id_gerado = novo_id
        return novo_id
    
    def criar_template(self, nome_template: str, id_ficha: int, id_usuario: int, estrutura_json: dict = None) -> int:
        with ConexaoBD(self.caminho_db) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO Template (nome_template, id_ficha, id_usuario, estrutura_json) VALUES (?, ?, ?, ?)",
                (nome_template, id_ficha, id_usuario, json.dumps(estrutura_json) if estrutura_json is not None else None)
            )
            return cursor.lastrowid

    def obter_templates_por_usuario(self, id_usuario: int) -> list:
        with ConexaoBD(self.caminho_db) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id, nome_template, data_Criacao FROM Template WHERE id_usuario = ? ORDER BY data_Criacao DESC",
                (id_usuario,)
            )
            templates = []
            for row in cursor.fetchall():
                templates.append({
                    "id": row["id"],
                    "nomeTemplate": row["nome_template"],
                    "dataCriacao": row["data_Criacao"]
                })
            return templates

    def obter_template_por_id(self, id_template: int) -> dict:
        with ConexaoBD(self.caminho_db) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id, nome_template, data_Criacao, id_ficha, id_usuario, estrutura_json FROM Template WHERE id = ?",
                (id_template,)
            )
            row = cursor.fetchone()
            if not row:
                return None

            return {
                "id": row["id"],
                "nomeTemplate": row["nome_template"],
                "dataCriacao": row["data_Criacao"],
                "id_ficha": row["id_ficha"],
                "id_usuario": row["id_usuario"],
                "estrutura_json": json.loads(row["estrutura_json"]) if row["estrutura_json"] else None
            }

    def deletar_template(self, id_template: int) -> bool:
        with ConexaoBD(self.caminho_db) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM Template WHERE id = ?", (id_template,))
            return cursor.rowcount > 0

    # ==========================================
    # SERIALIZAÇÃO E DESERIALIZAÇÃO
    # ==========================================
    
    def construir_ficha_a_partir_dados(self, dados: dict, id_ficha: int, id_usuario: int, preservar_ids: bool = True) -> FichaPersonagem:
        subtitulo = dados.get("subtitulo") or dados.get("aspecto") or dados.get("aspectoPersonagem") or ""
        ficha = FichaPersonagem(
            id_ficha,
            dados.get("nome", "Novo Personagem"),
            id_usuario,
            subtitulo
        )
        ficha.subtitulo = subtitulo
        ficha.aspecto = subtitulo
        ficha.aspecto_personagem = subtitulo
        ficha.avatar = dados.get("avatar")
        ficha.visibilidade = dados.get("visibilidade", "todos")

        for pos_str, col_dados in dados.get("colunas", {}).items():
            pos = int(pos_str)
            coluna = Coluna(
                id_template=None,
                posicao_coluna=pos,
                esta_ativa=col_dados.get("ativa", True),
                aba_ativa_id=col_dados.get("abaAtivaId"),
            )

            aba_id_map = {}
            for aba_dados in col_dados.get("abas", []):
                aba_id = aba_dados.get("id") if preservar_ids else self._gerar_id_unico("aba")
                aba = Aba(
                    aba_id,
                    None,
                    aba_dados.get("titulo", "Nova Aba"),
                    aba_dados.get("posicao_aba", 1),
                )
                aba.ehPadrao = aba_dados.get("ehPadrao", False)

                if not preservar_ids and aba_dados.get("id") is not None:
                    aba_id_map[aba_dados.get("id")] = aba.id

                for sec_dados in aba_dados.get("secoes", []):
                    secao_id = sec_dados.get("id") if preservar_ids else self._gerar_id_unico("secao")
                    secao = Secao(
                        secao_id,
                        None,
                        sec_dados.get("titulo", "Nova Seção"),
                        sec_dados.get("posicao_secao", 1),
                        sec_dados.get("tipo", "AtributoSimples")
                    )
                    tipo = secao.tipo

                    for comp_dados in sec_dados.get("componentes", []):
                        componente = self._criar_componente_a_partir_json(tipo, comp_dados, use_template_id=preservar_ids)
                        if componente:
                            secao.adicionar_componente(componente)

                    aba.adicionar_secao(secao)
                coluna.adicionar_aba(aba)

            if not preservar_ids and coluna.abaAtivaId is not None:
                coluna.abaAtivaId = aba_id_map.get(coluna.abaAtivaId, coluna.abaAtivaId)

            ficha.adicionar_coluna(coluna)

        return ficha

    def _serializar_ficha(self, ficha: FichaPersonagem) -> dict:
        return {
            "id": ficha.id,
            "nome": ficha.nome_personagem,
            "subtitulo": getattr(ficha, "subtitulo", ""),
            "avatar": getattr(ficha, "avatar", None),
            "visibilidade": getattr(ficha, "visibilidade", "todos"),
            "colunas": {
                str(col.posicao_coluna): self._serializar_coluna(col) for col in (ficha.colunas or [])
            },
        }

    def _serializar_coluna(self, coluna: Coluna) -> dict:
        return {
            "ativa": coluna.esta_ativa,
            "abaAtivaId": getattr(coluna, "abaAtivaId", None),
            "abas": [self._serializar_aba(aba) for aba in coluna.abas],
        }

    def _serializar_aba(self, aba: Aba) -> dict:
        return {
            "id": aba.id,
            "titulo": aba.titulo,
            "secoes": [self._serializar_secao(secao) for secao in aba.secoes],
        }

    def _serializar_secao(self, secao: Secao) -> dict:
        return {
            "id": secao.id,
            "titulo": secao.titulo,
            "tipo": getattr(secao, "tipo", secao.componentes[0].__class__.__name__ if secao.componentes else "AtributoSimples"),
            "componentes": [self._serializar_componente(comp) for comp in secao.componentes],
        }

    def _serializar_componente(self, comp: ComponenteSecao) -> dict:
        """Serializa componente da classe (snake_case) para JSON do frontend (camelCase)"""
        dados = {"id": comp.id}
        # Componentes com rotulo
        if hasattr(comp, "rotulo"):
            dados["rotulo"] = comp.rotulo
        # AtributoSimples, AtributoDuplo, AtributoComplexo
        if hasattr(comp, "nome_atributo"):
            dados["nomeAtributo"] = comp.nome_atributo
        if hasattr(comp, "valor_atributo"):
            dados["valorAtributo"] = comp.valor_atributo
        if hasattr(comp, "valor_pequeno"):
            dados["valorPequeno"] = comp.valor_pequeno
        if hasattr(comp, "valor_grande"):
            dados["valorGrande"] = comp.valor_grande
        if hasattr(comp, "valor_base"):
            dados["valorBase"] = comp.valor_base
        if hasattr(comp, "valor_bonus"):
            dados["valorBonus"] = comp.valor_bonus
        if hasattr(comp, "valor_outros"):
            dados["valorOutros"] = comp.valor_outros
        if hasattr(comp, "subtitulo_anotacao"):
            dados["subtituloAnotacao"] = comp.subtitulo_anotacao
        if hasattr(comp, "criterio_ordenacao"):
            dados["criterioOrdenacao"] = comp.criterio_ordenacao
        # Contador
        if hasattr(comp, "valor_atual"):
            dados["valorAtual"] = comp.valor_atual
        if hasattr(comp, "valor_maximo"):
            dados["valorMaximo"] = comp.valor_maximo
        if hasattr(comp, "cor_seletor"):
            dados["corSeletor"] = comp.cor_seletor
        # Checkbox
        if hasattr(comp, "esta_marcado"):
            dados["estaMarcado"] = comp.esta_marcado
        # InformacaoCurta
        if hasattr(comp, "campo_texto"):
            dados["campoTexto"] = comp.campo_texto
        # Anotações
        if hasattr(comp, "descricao"):
            dados["descricao"] = comp.descricao
        if hasattr(comp, "anotacao_extra"):
            dados["anotacaoExtra"] = comp.anotacao_extra
        return dados

    def _salvar_componente(self, cursor, comp: ComponenteSecao, id_secao: int):
        if comp.id is None:
            comp.id = self._gerar_id_unico("componente")

        if isinstance(comp, InformacaoCurta):
            cursor.execute(
                "INSERT INTO InformacaoCurta (id, rotulo, campo_texto, id_secao) VALUES (?, ?, ?, ?) ON CONFLICT(id) DO UPDATE SET rotulo=excluded.rotulo, campo_texto=excluded.campo_texto",
                (comp.id, comp.rotulo, comp.campo_texto, id_secao)
            )
        elif isinstance(comp, Contador):
            cursor.execute(
                "INSERT INTO Contador (id, rotulo, valor_atual, valor_maximo, cor_seletor, id_secao) VALUES (?, ?, ?, ?, ?, ?) ON CONFLICT(id) DO UPDATE SET rotulo=excluded.rotulo, valor_atual=excluded.valor_atual, valor_maximo=excluded.valor_maximo, cor_seletor=excluded.cor_seletor",
                (comp.id, comp.rotulo, comp.valor_atual, comp.valor_maximo, comp.cor_seletor, id_secao)
            )
        elif isinstance(comp, Checkbox):
            cursor.execute(
                "INSERT INTO Checkbox (id, rotulo, esta_marcado, id_secao) VALUES (?, ?, ?, ?) ON CONFLICT(id) DO UPDATE SET rotulo=excluded.rotulo, esta_marcado=excluded.esta_marcado",
                (comp.id, comp.rotulo, 1 if comp.esta_marcado else 0, id_secao)
            )
        elif isinstance(comp, AtributoComplexo):
            cursor.execute(
                "INSERT INTO AtributoComplexo (id, nome_atributo, subtitulo_anotacao, valor_base, valor_bonus, valor_outros, id_secao) VALUES (?, ?, ?, ?, ?, ?, ?) ON CONFLICT(id) DO UPDATE SET nome_atributo=excluded.nome_atributo, subtitulo_anotacao=excluded.subtitulo_anotacao, valor_base=excluded.valor_base, valor_bonus=excluded.valor_bonus, valor_outros=excluded.valor_outros",
                (comp.id, comp.nome_atributo, comp.subtitulo_anotacao, comp.valor_base, comp.valor_bonus, comp.valor_outros, id_secao)
            )
        elif isinstance(comp, AtributoDuplo):
            cursor.execute(
                "INSERT INTO AtributoDuplo (id, nome_atributo, valor_grande, valor_pequeno, id_secao) VALUES (?, ?, ?, ?, ?) ON CONFLICT(id) DO UPDATE SET nome_atributo=excluded.nome_atributo, valor_grande=excluded.valor_grande, valor_pequeno=excluded.valor_pequeno",
                (comp.id, comp.nome_atributo, comp.valor_grande, comp.valor_pequeno, id_secao)
            )
        elif isinstance(comp, AtributoSimples):
            cursor.execute(
                "INSERT INTO AtributoSimples (id, nome_atributo, valor_atributo, id_secao) VALUES (?, ?, ?, ?) ON CONFLICT(id) DO UPDATE SET nome_atributo=excluded.nome_atributo, valor_atributo=excluded.valor_atributo",
                (comp.id, comp.nome_atributo, comp.valor_atributo, id_secao)
            )
        elif isinstance(comp, AnotacaoCheckbox):
            cursor.execute(
                "INSERT INTO AnotacaoCheckbox (id, rotulo, descricao, esta_marcado, id_secao) VALUES (?, ?, ?, ?, ?) ON CONFLICT(id) DO UPDATE SET rotulo=excluded.rotulo, descricao=excluded.descricao, esta_marcado=excluded.esta_marcado",
                (comp.id, comp.rotulo, comp.descricao, 1 if comp.esta_marcado else 0, id_secao)
            )
        elif isinstance(comp, AnotacaoDetalhada):
            cursor.execute(
                "INSERT INTO AnotacaoDetalhada (id, rotulo, descricao, anotacao_extra, id_secao) VALUES (?, ?, ?, ?, ?) ON CONFLICT(id) DO UPDATE SET rotulo=excluded.rotulo, descricao=excluded.descricao, anotacao_extra=excluded.anotacao_extra",
                (comp.id, comp.rotulo, comp.descricao, comp.anotacao_extra, id_secao)
            )
        elif isinstance(comp, AnotacaoSimples):
            cursor.execute(
                "INSERT INTO AnotacaoSimples (id, rotulo, descricao, id_secao) VALUES (?, ?, ?, ?) ON CONFLICT(id) DO UPDATE SET rotulo=excluded.rotulo, descricao=excluded.descricao",
                (comp.id, comp.rotulo, comp.descricao, id_secao)
            )

    def obter_campanhas_com_ficha(self, id_ficha: int) -> list:
        campanhas = []
        with ConexaoBD(self.caminho_db) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM Campanha")
            for row in cursor.fetchall():
                dados = self._obter_dados_json_campanha_id(conn, row["id"])
                if id_ficha in dados.get("personagens", []):
                    campanhas.append(row["id"])
        return campanhas

    def _obter_dados_json_campanha_id(self, conn, id_campanha: int) -> dict:
        cursor = conn.cursor()
        cursor.execute("SELECT lista_personagens FROM Campanha WHERE id = ?", (id_campanha,))
        row = cursor.fetchone()
        dados = {"jogadores": [], "personagens": [], "arquivos": []}
        if row and row["lista_personagens"]:
            try:
                dados = json.loads(row["lista_personagens"])
            except Exception:
                dados = {"jogadores": [], "personagens": [], "arquivos": []}
        if "jogadores" not in dados:
            dados["jogadores"] = []
        if "personagens" not in dados:
            dados["personagens"] = []
        if "arquivos" not in dados:
            dados["arquivos"] = []
        return dados

    def obter_ficha_completa(self, id_ficha: int) -> FichaPersonagem:
        """Recupera uma ficha completa com todos os componentes e avatar."""
        with ConexaoBD(self.caminho_db) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM FichaPersonagem WHERE id = ?", (id_ficha,))
            row_ficha = cursor.fetchone()
            if not row_ficha:
                return None

            row = dict(row_ficha)

            ficha = FichaPersonagem(row.get("id"), row.get("nome_personagem", row.get("nome", "Novo Personagem")), row.get("id_usuario", row.get("id_Usuario")), row.get("aspecto_personagem", ""))
            subtitulo = row.get("aspecto_personagem", "")
            ficha.subtitulo = subtitulo
            ficha.aspecto = subtitulo
            ficha.aspecto_personagem = subtitulo
            ficha.avatar = None
            ficha.visibilidade = "todos"

            cursor.execute("SELECT COUNT(1) AS cnt FROM Coluna WHERE id_ficha = ?", (row.get("id"),))
            col_count = cursor.fetchone()
            if col_count and col_count[0] > 0:
                if row.get("estrutura_json"):
                    try:
                        dados = json.loads(row.get("estrutura_json"))
                        ficha.nome_personagem = dados.get("nome", row.get("nome_personagem", row.get("nome_Personagem")))
                        subtitulo_json = dados.get("subtitulo") or dados.get("aspecto") or dados.get("aspectoPersonagem") or row.get("aspecto_personagem", "")
                        ficha.subtitulo = subtitulo_json
                        ficha.aspecto = subtitulo_json
                        ficha.aspecto_personagem = subtitulo_json
                        ficha.avatar = dados.get("avatar", None)
                        ficha.visibilidade = dados.get("visibilidade", "todos")
                    except Exception:
                        pass
                self._carregar_estrutura_em_tabelas(cursor, ficha)
                return ficha

            if row.get("estrutura_json"):
                try:
                    dados = json.loads(row.get("estrutura_json"))
                    ficha.nome_personagem = dados.get("nome", row.get("nome_personagem", row.get("nome_Personagem")))
                    subtitulo_json = dados.get("subtitulo") or dados.get("aspecto") or dados.get("aspectoPersonagem") or row.get("aspecto_personagem", "")
                    ficha.subtitulo = subtitulo_json
                    ficha.aspecto = subtitulo_json
                    ficha.aspecto_personagem = subtitulo_json
                    ficha.avatar = dados.get("avatar", None)
                    ficha.visibilidade = dados.get("visibilidade", "todos")
                    
                    for pos_str, col_dados in dados.get("colunas", {}).items():
                        pos = int(pos_str)
                        coluna = Coluna(id_template=None, posicao_coluna=pos, esta_ativa=col_dados.get("ativa", True), limite_abas=3)
                        for aba_dados in col_dados.get("abas", []):
                            aba = Aba(id_coluna=None, titulo=aba_dados.get("titulo", "Nova Aba"), posicao_aba=1)
                            for sec_dados in aba_dados.get("secoes", []):
                                secao = Secao(
                                    id_aba=None,
                                    titulo=sec_dados.get("titulo", "Nova Seção"),
                                    posicao_secao=1,
                                    tipo=sec_dados.get("tipo", "AtributoSimples")
                                )
                                for comp_dados in sec_dados.get("componentes", []):
                                    comp = self._criar_componente_a_partir_json(sec_dados.get("tipo", "AtributoSimples"), comp_dados)
                                    if comp:
                                        secao.adicionar_componente(comp)
                                aba.adicionar_secao(secao)
                            coluna.adicionar_aba(aba)
                        ficha.adicionar_coluna(coluna)
                    
                    if not ficha.colunas:
                        ficha.colunas = [
                            Coluna(id_template=None, posicao_coluna=1, esta_ativa=True, limite_abas=3),
                            Coluna(id_template=None, posicao_coluna=2, esta_ativa=True, limite_abas=3),
                            Coluna(id_template=None, posicao_coluna=3, esta_ativa=True, limite_abas=3),
                        ]
                    return ficha
                except Exception:
                    pass

            # Fallback para dados antigos (sem JSON)
            cursor.execute("SELECT * FROM Coluna WHERE id_template IS NULL")
            rows_colunas = cursor.fetchall()
            for r_col in rows_colunas:
                rc = dict(r_col)
                coluna = Coluna(rc.get("id"), None, rc.get("posicao_coluna", 1), rc.get("limite_abas", 3), bool(rc.get("esta_ativa", True)))
                
                cursor.execute("SELECT * FROM Aba WHERE id_coluna = ?", (coluna.id,))
                rows_abas = cursor.fetchall()
                for r_aba in rows_abas:
                    ra = dict(r_aba)
                    aba = Aba(ra.get("id"), coluna.id, ra.get("titulo", "Nova Aba"), ra.get("posicao_aba", 1))

                    cursor.execute("SELECT * FROM Secao WHERE id_aba = ?", (aba.id,))
                    rows_secoes = cursor.fetchall()
                    for r_sec in rows_secoes:
                        rs = dict(r_sec)
                        secao = Secao(rs.get("id"), aba.id, rs.get("titulo", "Nova Seção"), rs.get("posicao_secao", 1), rs.get("conteudo"))
                        self._carregar_componentes_secao(cursor, secao)
                        aba.adicionar_secao(secao)
                    coluna.adicionar_aba(aba)
                ficha.adicionar_coluna(coluna)

            if not ficha.colunas:
                ficha.colunas = [
                    Coluna(id_template=None, posicao_coluna=1, esta_ativa=True, limite_abas=3),
                    Coluna(id_template=None, posicao_coluna=2, esta_ativa=True, limite_abas=3),
                    Coluna(id_template=None, posicao_coluna=3, esta_ativa=True, limite_abas=3),
                ]
            return ficha

    def _criar_componente_a_partir_json(self, tipo: str, comp_dados: dict, use_template_id: bool = False):
        """Cria componente a partir de dados JSON do frontend (camelCase → snake_case da classe)"""
        # Use template's ID only if explicitly requested, otherwise generate new IDs
        comp_id = comp_dados.get("id") if use_template_id else None
        if tipo == "AtributoSimples":
            nome = comp_dados.get("nomeAtributo") if "nomeAtributo" in comp_dados else ""
            valor = comp_dados.get("valorAtributo", 0)
            return AtributoSimples(comp_id, None, nome, valor)
        if tipo == "AtributoDuplo":
            nome = comp_dados.get("nomeAtributo") if "nomeAtributo" in comp_dados else ""
            grande = comp_dados.get("valorGrande", 0)
            pequeno = comp_dados.get("valorPequeno", 0)
            return AtributoDuplo(comp_id, None, nome, grande, pequeno)
        if tipo == "AtributoComplexo":
            nome = comp_dados.get("nomeAtributo") if "nomeAtributo" in comp_dados else ""
            base = comp_dados.get("valorBase", 0)
            bonus = comp_dados.get("valorBonus", 0)
            subt = comp_dados.get("subtituloAnotacao", "")
            outros = comp_dados.get("valorOutros", 0)
            crit = comp_dados.get("criterioOrdenacao", 0)
            return AtributoComplexo(comp_id, None, nome, base, bonus, subt, outros, crit)
        if tipo == "Contador":
            rotulo = comp_dados.get("rotulo") if "rotulo" in comp_dados else ""
            atual = comp_dados.get("valorAtual", 0)
            maximo = comp_dados.get("valorMaximo", 10)
            cor = comp_dados.get("corSeletor") if "corSeletor" in comp_dados else "#2b2631"
            return Contador(comp_id, None, rotulo, atual, maximo, cor)
        if tipo == "Checkbox":
            rotulo = comp_dados.get("rotulo", "")
            marcado = comp_dados.get("estaMarcado", False)
            return Checkbox(comp_id, None, rotulo, marcado)
        if tipo == "InformacaoCurta":
            rotulo = comp_dados.get("rotulo", "")
            texto = comp_dados.get("campoTexto", "")
            return InformacaoCurta(comp_id, None, rotulo, texto)
        if tipo == "AnotacaoSimples":
            rotulo = comp_dados.get("rotulo", "")
            descricao = comp_dados.get("descricao", "")
            return AnotacaoSimples(comp_id, None, rotulo, descricao)
        if tipo == "AnotacaoCheckbox":
            rotulo = comp_dados.get("rotulo", "")
            descricao = comp_dados.get("descricao", "")
            marcado = comp_dados.get("estaMarcado", False)
            return AnotacaoCheckbox(comp_id, None, rotulo, descricao, marcado)
        if tipo == "AnotacaoDetalhada":
            rotulo = comp_dados.get("rotulo", "")
            descricao = comp_dados.get("descricao", "")
            extra = comp_dados.get("anotacaoExtra", "")
            return AnotacaoDetalhada(comp_id, None, rotulo, descricao, extra)
        return None

    def _carregar_componentes_secao(self, cursor, secao: Secao):
        id_sec = secao.id
        
        cursor.execute("SELECT * FROM InformacaoCurta WHERE id_secao = ?", (id_sec,))
        for r in cursor.fetchall():
            rr = dict(r)
            rot = rr.get("rotulo", "")
            secao.adicionar_componente(InformacaoCurta(rr.get("id"), id_sec, rot, rr.get("campo_texto", "")))

        cursor.execute("SELECT * FROM Contador WHERE id_secao = ?", (id_sec,))
        for r in cursor.fetchall():
            rr = dict(r)
            secao.adicionar_componente(Contador(rr.get("id"), id_sec, rr.get("rotulo", "Recurso"), rr.get("valor_atual", 0), rr.get("valor_maximo", 0), rr.get("cor_seletor", "default")))

        cursor.execute("SELECT * FROM Checkbox WHERE id_secao = ?", (id_sec,))
        for r in cursor.fetchall():
            rr = dict(r)
            secao.adicionar_componente(Checkbox(rr.get("id"), id_sec, rr.get("rotulo", ""), bool(rr.get("esta_marcado", False))))

        cursor.execute("SELECT * FROM AtributoSimples WHERE id_secao = ?", (id_sec,))
        for r in cursor.fetchall():
            rr = dict(r)
            secao.adicionar_componente(AtributoSimples(rr.get("id"), id_sec, rr.get("nome_atributo", "Atributo"), rr.get("valor_atributo", 0)))

        cursor.execute("SELECT * FROM AtributoDuplo WHERE id_secao = ?", (id_sec,))
        for r in cursor.fetchall():
            rr = dict(r)
            secao.adicionar_componente(AtributoDuplo(rr.get("id"), id_sec, rr.get("nome_atributo", "Atributo"), rr.get("valor_grande", 0), rr.get("valor_pequeno", 0)))

        cursor.execute("SELECT * FROM AtributoComplexo WHERE id_secao = ?", (id_sec,))
        for r in cursor.fetchall():
            rr = dict(r)
            secao.adicionar_componente(AtributoComplexo(rr.get("id"), id_sec, rr.get("nome_atributo", "Atributo"), rr.get("valor_base", 0), rr.get("valor_bonus", 0), rr.get("subtitulo_anotacao", ""), rr.get("valor_outros", ""), rr.get("criterio_ordenacao", 0)))

        cursor.execute("SELECT * FROM AnotacaoSimples WHERE id_secao = ?", (id_sec,))
        for r in cursor.fetchall():
            rr = dict(r)
            secao.adicionar_componente(AnotacaoSimples(rr.get("id"), id_sec, rr.get("rotulo", ""), rr.get("descricao", "")))

        cursor.execute("SELECT * FROM AnotacaoCheckbox WHERE id_secao = ?", (id_sec,))
        for r in cursor.fetchall():
            rr = dict(r)
            secao.adicionar_componente(AnotacaoCheckbox(rr.get("id"), id_sec, rr.get("rotulo", ""), rr.get("descricao", ""), bool(rr.get("esta_marcado", False))))

        cursor.execute("SELECT * FROM AnotacaoDetalhada WHERE id_secao = ?", (id_sec,))
        for r in cursor.fetchall():
            rr = dict(r)
            secao.adicionar_componente(AnotacaoDetalhada(rr.get("id"), id_sec, rr.get("rotulo", ""), rr.get("descricao", ""), rr.get("anotacao_extra", "")))