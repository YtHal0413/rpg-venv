import hashlib
from typing import Optional


class PlataformaErro(Exception):
    """Erro base do domínio da aplicação."""


class ValidacaoDadosErro(PlataformaErro):
    """Erro de validação de dados de entrada."""


class ChaveInvalidaErro(PlataformaErro):
    """Erro para chaves inválidas ou expiradas."""


class Usuario:
    def __init__(self, id: Optional[int] = None, nome: str = "", email: str = "", senha_hash: str = "", imagem_avatar: Optional[str] = None, chave_ativada: bool = False):
        self.id = id
        self.nome = nome
        self.email = email
        self.senha_hash = senha_hash
        self.imagem_avatar = imagem_avatar
        self.chave_ativada = chave_ativada

    def verificar_senha(self, senha: str) -> bool:
        if not senha:
            return False
        return self.senha_hash == self._hash_senha(senha)

    @staticmethod
    def _hash_senha(senha: str) -> str:
        return hashlib.sha256(senha.encode("utf-8")).hexdigest()

    def ativar_chave(self, chave: str) -> bool:
        from config import Config

        if chave == Config.CHAVE_TESTE_VALIDA:
            self.chave_ativada = True
            return True
        raise ChaveInvalidaErro("A chave informada é inválida ou não pode ser resgatada.")


class Campanha:
    def __init__(self, id: Optional[int] = None, nome: str = "", id_mestre: Optional[int] = None, descricao: Optional[str] = None):
        self.id = id
        self.nome = nome
        self.id_mestre = id_mestre
        self.descricao = descricao
        self.jogadores = []
        self.personagens = []
        self.arquivos = []

    def adicionar_jogador(self, usuario: Usuario) -> None:
        if usuario not in self.jogadores:
            self.jogadores.append(usuario)

    def adicionar_personagem(self, personagem: "FichaPersonagem") -> None:
        if personagem not in self.personagens:
            self.personagens.append(personagem)


class FichaPersonagem:
    def __init__(self, id: Optional[int] = None, nome_personagem: str = "Novo Personagem", id_usuario: Optional[int] = None, aspecto: str = "", avatar: Optional[str] = None, visibilidade: str = "todos"):
        self.id = id
        self.nome_personagem = nome_personagem
        self.aspecto = aspecto
        self.id_usuario = id_usuario
        self.avatar = avatar 
        self.visibilidade = visibilidade
        self.colunas = []

    @property
    def aspecto_personagem(self):
        return self.subtitulo

    @aspecto_personagem.setter
    def aspecto_personagem(self, value):
        self.subtitulo = value
        self.aspecto = value

    def adicionar_coluna(self, coluna: "Coluna") -> None:
        if coluna not in self.colunas:
            self.colunas.append(coluna)


class Coluna:
    def __init__(self, id: Optional[int] = None, id_template: Optional[int] = None, posicao_coluna: int = 1, limite_abas: int = 3, esta_ativa: bool = True, aba_ativa_id: Optional[int] = None, id_ficha: Optional[int] = None):
        self.id = id
        self.id_template = id_template
        self.id_ficha = id_ficha
        self.posicao_coluna = posicao_coluna
        self.limite_abas = limite_abas
        self.esta_ativa = esta_ativa
        self.abaAtivaId = aba_ativa_id
        self.abas = []

    def adicionar_aba(self, aba: "Aba") -> None:
        if aba not in self.abas:
            self.abas.append(aba)


class Aba:
    def __init__(self, id: Optional[int] = None, id_coluna: Optional[int] = None, titulo: str = "Nova Aba", posicao_aba: int = 1):
        self.id = id
        self.id_coluna = id_coluna
        self.titulo = titulo
        self.posicao_aba = posicao_aba
        self.secoes = []

    def adicionar_secao(self, secao: "Secao") -> None:
        if secao not in self.secoes:
            self.secoes.append(secao)


class Secao:
    def __init__(self, id: Optional[int] = None, id_aba: Optional[int] = None, titulo: str = "Nova Seção", posicao_secao: int = 1, tipo: str = "AtributoSimples"):
        self.id = id
        self.id_aba = id_aba
        self.titulo = titulo
        self.posicao_secao = posicao_secao
        self.tipo = tipo
        self.componentes = []

    def adicionar_componente(self, componente: "ComponenteSecao") -> None:
        if componente not in self.componentes:
            self.componentes.append(componente)


class ComponenteSecao:
    def __init__(self, id: Optional[int] = None, id_secao: Optional[int] = None):
        self.id = id
        self.id_secao = id_secao


class InformacaoCurta(ComponenteSecao):
    def __init__(self, id: Optional[int] = None, id_secao: Optional[int] = None, rotulo: str = "", campo_texto: str = ""):
        super().__init__(id, id_secao)
        self.rotulo = rotulo
        self.campo_texto = campo_texto


class Contador(ComponenteSecao):
    def __init__(self, id: Optional[int] = None, id_secao: Optional[int] = None, rotulo: str = "", valor_atual: int = 0, valor_maximo: int = 0, cor_seletor: str = "default"):
        super().__init__(id, id_secao)
        self.rotulo = rotulo
        self.valor_atual = valor_atual
        self.valor_maximo = valor_maximo
        self.cor_seletor = cor_seletor

class Checkbox(ComponenteSecao):
    def __init__(self, id: Optional[int] = None, id_secao: Optional[int] = None, rotulo: str = "", esta_marcado: bool = False):
        super().__init__(id, id_secao)
        self.rotulo = rotulo
        self.esta_marcado = esta_marcado


class AtributoSimples(ComponenteSecao):
    def __init__(self, id: Optional[int] = None, id_secao: Optional[int] = None, nome_atributo: str = "", valor_atributo: int = 0):
        super().__init__(id, id_secao)
        self.nome_atributo = nome_atributo
        self.valor_atributo = valor_atributo


class AtributoDuplo(ComponenteSecao):
    def __init__(self, id: Optional[int] = None, id_secao: Optional[int] = None, nome_atributo: str = "", valor_grande: int = 0, valor_pequeno: int = 0):
        super().__init__(id, id_secao)
        self.nome_atributo = nome_atributo
        self.valor_grande = valor_grande
        self.valor_pequeno = valor_pequeno


class AtributoComplexo(ComponenteSecao):
    def __init__(self, id: Optional[int] = None, id_secao: Optional[int] = None, nome_atributo: str = "", valor_base: int = 0, valor_bonus: int = 0, subtitulo_anotacao: str = "", valor_outros: int = 0, criterio_ordenacao: int = 0):
        super().__init__(id, id_secao)
        self.nome_atributo = nome_atributo
        self.valor_base = valor_base
        self.valor_bonus = valor_bonus
        self.valor_outros = valor_outros
        self.subtitulo_anotacao = subtitulo_anotacao
        self.criterio_ordenacao = criterio_ordenacao

class AnotacaoSimples(ComponenteSecao):
    def __init__(self, id: Optional[int] = None, id_secao: Optional[int] = None, rotulo: str = "", descricao: str = ""):
        super().__init__(id, id_secao)
        self.rotulo = rotulo
        self.descricao = descricao


class AnotacaoCheckbox(ComponenteSecao):
    def __init__(self, id: Optional[int] = None, id_secao: Optional[int] = None, rotulo: str = "", descricao: str = "", esta_marcado: bool = False):
        super().__init__(id, id_secao)
        self.rotulo = rotulo
        self.descricao = descricao
        self.esta_marcado = esta_marcado


class AnotacaoDetalhada(ComponenteSecao):
    def __init__(self, id: Optional[int] = None, id_secao: Optional[int] = None, rotulo: str = "", descricao: str = "", anotacao_extra: str = ""):
        super().__init__(id, id_secao)
        self.rotulo = rotulo
        self.descricao = descricao
        self.anotacao_extra = anotacao_extra