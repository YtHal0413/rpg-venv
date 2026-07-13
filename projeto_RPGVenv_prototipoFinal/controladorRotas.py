import functools
import os
import uuid
import json
from flask import Flask, render_template, request, redirect, url_for, session, flash, g, jsonify
from werkzeug.utils import secure_filename
from classes import (
    Usuario, ValidacaoDadosErro, ChaveInvalidaErro
)
from controladorBD import ControladorBD, ConexaoBD
from config import DesenvolvimentoConfig

app = Flask(__name__)
app.config.from_object(DesenvolvimentoConfig)

controlador_bd = ControladorBD(app.config["DATABASE_PATH"])

# ==========================================
# FILTROS PERSONALIZADOS PARA JINJA2
# ==========================================

@app.template_filter('json_dumps')
def json_dumps_filter(data):
    """Converte dados para JSON para uso em templates."""
    return json.dumps(data)

@app.template_filter('json_loads')
def json_loads_filter(data):
    """Converte JSON para objeto Python."""
    try:
        return json.loads(data)
    except:
        return data

# Garante que os diretórios de upload existam
for pasta in [app.config["UPLOAD_FOLDER"], app.config["AVATAR_FOLDER"]]:
    if not os.path.exists(pasta):
        os.makedirs(pasta)


def obter_pasta_livros_usuario(id_usuario):
    """Retorna a pasta de livros do usuário, criando-a quando necessário."""
    pasta_usuario = os.path.join(app.config["UPLOAD_FOLDER"], str(id_usuario))
    os.makedirs(pasta_usuario, exist_ok=True)
    return pasta_usuario


def listar_livros_usuario(id_usuario):
    """Lista os PDFs pertencentes à biblioteca pessoal do usuário."""
    pasta_usuario = obter_pasta_livros_usuario(id_usuario)
    return sorted([nome for nome in os.listdir(pasta_usuario) if nome.lower().endswith(".pdf")])


def normalizar_caminho_arquivo_campanha(nome_arquivo, id_usuario):
    """Retorna o caminho relativo do arquivo considerando a pasta do usuário."""
    if not nome_arquivo:
        return ""

    caminho_limpo = os.path.normpath(str(nome_arquivo)).replace("\\", "/")
    partes = [parte for parte in caminho_limpo.split("/") if parte]
    if not partes:
        return ""

    if len(partes) > 1 and partes[0].isdigit():
        return caminho_limpo

    nome_limpo = partes[-1]
    if nome_limpo.lower().endswith(".pdf"):
        return os.path.join(str(id_usuario), nome_limpo).replace("\\", "/")
    return caminho_limpo


def salvar_livro_usuario(arquivo, id_usuario):
    """Salva um PDF na biblioteca pessoal do usuário."""
    if not arquivo or arquivo.filename == "":
        return None

    nome_seguro = secure_filename(arquivo.filename)
    if not nome_seguro.lower().endswith(".pdf"):
        return None

    pasta_usuario = obter_pasta_livros_usuario(id_usuario)
    caminho_arquivo = os.path.join(pasta_usuario, nome_seguro)
    arquivo.save(caminho_arquivo)
    return os.path.basename(caminho_arquivo)


def remover_livro_usuario(nome_arquivo, id_usuario):
    """Remove um PDF da biblioteca pessoal do usuário."""
    pasta_usuario = obter_pasta_livros_usuario(id_usuario)
    caminho_arquivo = os.path.join(pasta_usuario, os.path.basename(nome_arquivo))
    if os.path.exists(caminho_arquivo):
        os.remove(caminho_arquivo)
        return True
    return False

def extensao_permitida(nome_arquivo):
    """Verifica se a extensão do arquivo é permitida."""
    return '.' in nome_arquivo and \
           nome_arquivo.rsplit('.', 1)[1].lower() in app.config["ALLOWED_EXTENSIONS"]

def salvar_imagem(arquivo, pasta_destino, prefixo=""):
    """Salva uma imagem e retorna o caminho relativo."""
    if not arquivo or arquivo.filename == '':
        return None
    
    if not extensao_permitida(arquivo.filename):
        return None
    
    # Gera nome único para o arquivo
    extensao = arquivo.filename.rsplit('.', 1)[1].lower()
    nome_unico = f"{prefixo}_{uuid.uuid4().hex[:8]}.{extensao}"
    
    # Salva o arquivo
    caminho_completo = os.path.join(pasta_destino, nome_unico)
    arquivo.save(caminho_completo)
    
    # Retorna o caminho relativo para o banco de dados
    return f"/static/{os.path.basename(pasta_destino)}/{nome_unico}"

# Inicialização dinâmica do banco de dados na primeira execução
try:
    controlador_bd.inicializar_banco()
except Exception as e:
    print(f"⚠️ Banco de dados já inicializado ou erro: {e}")

@app.before_request
def carregar_usuario_sessao():
    """Injeta os dados cadastrais do usuário autenticado de forma global na requisição."""
    usuario_id = session.get("usuario_id")
    if usuario_id:
        g.usuario = controlador_bd.obter_usuario(usuario_id)
    else:
        g.usuario = None

def login_requerido(funcao):
    """Decorator de barreira de acesso para rotas protegidas."""
    @functools.wraps(funcao)
    def funcao_decorada(*args, **kwargs):
        if g.usuario is None:
            flash("Acesso negado. Por favor, realize o login para acessar esta página.", "perigo")
            next_url = request.path
            if request.query_string:
                next_url += '?' + request.query_string.decode('utf-8')
            return redirect(url_for("login", next=next_url))
        return funcao(*args, **kwargs)
    return funcao_decorada

def chave_requerida(funcao):
    """Decorator de restrição para ferramentas de criação (Nível 2)."""
    @functools.wraps(funcao)
    def funcao_decorada(*args, **kwargs):
        if not g.usuario or not g.usuario.chave_ativada:
            flash("Esta funcionalidade exige o resgate de uma chave de produto válida.", "aviso")
            return redirect(url_for("colecoes"))
        return funcao(*args, **kwargs)
    return funcao_decorada

@app.route("/")
def inicio():
    return render_template("inicio.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if g.usuario:
        return redirect(url_for("colecoes"))

    next_url = request.args.get("next")
    if request.method == "POST":
        next_url = request.form.get("next") or next_url
        email = (request.form.get("email") or "").strip()
        senha = (request.form.get("senha") or "").strip()

        if not email or not senha:
            flash("Informe um e-mail e uma senha para continuar.", "perigo")
            return render_template("login.html", next_url=next_url)

        usuario = controlador_bd.obter_usuario_por_email(email)
        senha_hash = Usuario._hash_senha(senha)

        if usuario is None:
            usuario = controlador_bd.cadastrar_usuario(
                nome=email.split("@")[0],
                email=email,
                senha_hash=senha_hash,
                imagem_avatar=None,
            )
        else:
            if not usuario.verificar_senha(senha):
                flash("E-mail ou senha inválidos.", "perigo")
                return render_template("login.html", next_url=next_url)

        session["usuario_id"] = usuario.id
        flash(f"Login realizado com sucesso, {usuario.nome}!", "sucesso")
        if next_url and next_url.startswith("/"):
            return redirect(next_url)
        return redirect(url_for("colecoes"))

    return render_template("login.html", next_url=next_url)

@app.route("/logout")
def logout():
    session.clear()
    flash("Sessão encerrada.", "info")
    return redirect(url_for("inicio"))

@app.route("/perfil", methods=["GET", "POST"])
@login_requerido
def perfil():
    if request.method == "POST":
        novo_nome = request.form.get("nome")
        
        try:
            if not novo_nome or not novo_nome.strip():
                raise ValidacaoDadosErro("O nome não pode ficar vazio.")
            
            # Processa o upload da imagem de avatar
            imagem_avatar = None
            if 'avatar_arquivo' in request.files:
                arquivo = request.files['avatar_arquivo']
                if arquivo and arquivo.filename != '':
                    imagem_avatar = salvar_imagem(arquivo, app.config["AVATAR_FOLDER"], f"user_{g.usuario.id}")
                    if not imagem_avatar:
                        flash("Formato de imagem não suportado. Use PNG, JPG, GIF ou WEBP.", "perigo")
                        return redirect(url_for("perfil"))
            
            # Se não enviou novo arquivo, mantém o existente
            if imagem_avatar is None:
                imagem_avatar = g.usuario.imagem_avatar
            
            g.usuario.nome = novo_nome.strip()
            g.usuario.imagem_avatar = imagem_avatar
            controlador_bd.atualizar_usuario(g.usuario.id, g.usuario.nome, g.usuario.senha_hash, g.usuario.imagem_avatar)
            flash("Perfil atualizado com sucesso!", "sucesso")
            return redirect(url_for("perfil"))
        except ValidacaoDadosErro as e:
            flash(str(e), "perigo")
            
    return render_template("perfil.html", usuario=g.usuario)

@app.route("/resgate", methods=["POST"])
@login_requerido
def resgate():
    chave = request.form.get("chave_produto")
    try:
        if g.usuario.ativar_chave(chave):
            controlador_bd.atualizar_chave_usuario(g.usuario.id, True)
            flash("Chave de produto ativada com sucesso! Funcionalidades desbloqueadas.", "sucesso")
    except ChaveInvalidaErro as e:
        flash(str(e), "perigo")
    return redirect(request.referrer or url_for("colecoes"))

@app.route("/colecoes")
@login_requerido
def colecoes():
    campanhas = controlador_bd.obter_campanhas_usuario(g.usuario.id)
    fichas = controlador_bd.obter_fichas_usuario(g.usuario.id)
    return render_template("colecoes.html", usuario=g.usuario, campanhas=campanhas, fichas=fichas)

@app.route("/campanha/criar", methods=["GET", "POST"])
@login_requerido
@chave_requerida
def criar_campanha():
    if request.method == "POST":
        nome = request.form.get("nome")
        descricao = request.form.get("descricao")
        
        try:
            if not nome or not nome.strip():
                raise ValidacaoDadosErro("O nome da campanha é obrigatório.")
            campanha = controlador_bd.criar_campanha(nome.strip(), g.usuario.id, descricao.strip() if descricao else None)
            flash(f"Campanha '{campanha.nome}' criada com sucesso!", "sucesso")
            return redirect(url_for("campanha_detalhes", id_campanha=campanha.id))
        except ValidacaoDadosErro as e:
            flash(str(e), "perigo")
            
    return render_template("criarCampanha.html")

@app.route("/campanha/entrar", methods=["POST"])
@login_requerido
def entrar_campanha():
    codigo = request.form.get("codigo_campanha")
    try:
        id_campanha = int(codigo)
        campanha = controlador_bd.obter_campanha(id_campanha)
        if campanha:
            controlador_bd.adicionar_usuario_campanha(id_campanha, g.usuario.id)
            flash(f"Você entrou com sucesso na campanha '{campanha.nome}'!", "sucesso")
            return redirect(url_for("campanha_detalhes", id_campanha=campanha.id))
        else:
            flash("Campanha não encontrada com o código fornecido.", "perigo")
    except ValueError:
        flash("Código de campanha inválido.", "perigo")
    return redirect(url_for("colecoes"))

@app.route("/campanha/<int:id_campanha>", methods=["GET", "POST"])
@login_requerido
def campanha_detalhes(id_campanha):
    if request.method == "POST" and g.usuario and g.usuario.id is not None:
        campanha = controlador_bd.obter_campanha(id_campanha)
        if not campanha:
            flash("Campanha não encontrada.", "perigo")
            return redirect(url_for("colecoes"))
        if campanha.id_mestre != g.usuario.id:
            flash("Apenas o mestre pode editar os dados desta campanha.", "perigo")
            return redirect(url_for("campanha_detalhes", id_campanha=id_campanha))

        nome = (request.form.get("nome") or "").strip()
        descricao = (request.form.get("descricao") or "").strip() or None

        if not nome:
            flash("O nome da campanha não pode ficar vazio.", "perigo")
            return redirect(url_for("campanha_detalhes", id_campanha=id_campanha))

        controlador_bd.atualizar_campanha(id_campanha, nome, descricao)
        flash("Dados da campanha atualizados com sucesso!", "sucesso")
        return redirect(url_for("campanha_detalhes", id_campanha=id_campanha))

    campanha = controlador_bd.obter_campanha(id_campanha)
    if not campanha:
        flash("Campanha não encontrada.", "perigo")
        return redirect(url_for("colecoes"))

    mestre = controlador_bd.obter_usuario(campanha.id_mestre)
    fichas_usuario = controlador_bd.obter_fichas_usuario(g.usuario.id)
    ids_fichas_vinculadas = {f.id for f in campanha.personagens if f.id is not None}
    fichas_disponiveis = [f for f in fichas_usuario if f.id not in ids_fichas_vinculadas]
    livros_campanha = campanha.arquivos or []
    biblioteca_pessoal = listar_livros_usuario(g.usuario.id)
    livros_campanha_com_caminho = [
        {
            "nome": livro,
            "caminho": normalizar_caminho_arquivo_campanha(livro, campanha.id_mestre),
        }
        for livro in (campanha.arquivos or [])
    ]

    participantes = []
    for jogador in campanha.jogadores:
        if jogador.id == campanha.id_mestre:
            continue
        fichas_jogador = [f for f in campanha.personagens if f.id_usuario == jogador.id]
        role = "Jogador" if fichas_jogador else "Espectador"
        detalhe = (
            f"{len(fichas_jogador)} personagem{'s' if len(fichas_jogador) != 1 else ''} vinculado{'s' if len(fichas_jogador) != 1 else ''}"
            if fichas_jogador else "Nenhuma ficha vinculada"
        )
        participantes.append({
            "usuario": jogador,
            "role": role,
            "detalhe": detalhe,
            "fichas": fichas_jogador,
        })

    return render_template(
        "campanha.html",
        campanha=campanha,
        mestre=mestre,
        fichas_campanha=campanha.personagens,
        fichas_disponiveis=fichas_disponiveis,
        livros_campanha=livros_campanha_com_caminho,
        biblioteca_pessoal=biblioteca_pessoal,
        participantes=participantes,
    )

@app.route("/campanha/<int:id_campanha>/anexar_arquivo", methods=["POST"])
@login_requerido
def anexar_arquivo_campanha(id_campanha):
    campanha = controlador_bd.obter_campanha(id_campanha)
    if not campanha:
        flash("Campanha não encontrada.", "perigo")
        return redirect(url_for("colecoes"))

    if g.usuario.id != campanha.id_mestre:
        flash("Somente o mestre pode anexar arquivos à campanha.", "perigo")
        return redirect(url_for("campanha_detalhes", id_campanha=id_campanha))

    nome_arquivo = request.form.get("arquivo_campanha")
    if not nome_arquivo:
        flash("Selecione um arquivo para anexar.", "perigo")
        return redirect(url_for("campanha_detalhes", id_campanha=id_campanha))

    nome_arquivo = os.path.basename(nome_arquivo)
    if not nome_arquivo.lower().endswith(".pdf"):
        flash("Arquivo inválido. Selecione um PDF.", "perigo")
        return redirect(url_for("campanha_detalhes", id_campanha=id_campanha))

    caminho_arquivo = os.path.join(obter_pasta_livros_usuario(g.usuario.id), nome_arquivo)
    if not os.path.exists(caminho_arquivo):
        flash("O arquivo selecionado não existe na biblioteca.", "perigo")
        return redirect(url_for("campanha_detalhes", id_campanha=id_campanha))

    controlador_bd.adicionar_arquivo_campanha(id_campanha, nome_arquivo)
    flash("Arquivo anexado à campanha com sucesso!", "sucesso")
    return redirect(url_for("campanha_detalhes", id_campanha=id_campanha))

@app.route("/campanha/<int:id_campanha>/remover_arquivo", methods=["POST"])
@login_requerido
def remover_arquivo_campanha(id_campanha):
    campanha = controlador_bd.obter_campanha(id_campanha)
    if not campanha:
        flash("Campanha não encontrada.", "perigo")
        return redirect(url_for("colecoes"))

    if g.usuario.id != campanha.id_mestre:
        flash("Somente o mestre pode remover atalhos de arquivos desta campanha.", "perigo")
        return redirect(url_for("campanha_detalhes", id_campanha=id_campanha))

    nome_arquivo = request.form.get("nome_arquivo")
    if not nome_arquivo:
        flash("Arquivo não informado.", "perigo")
        return redirect(url_for("campanha_detalhes", id_campanha=id_campanha))

    controlador_bd.remover_arquivo_campanha(id_campanha, os.path.basename(nome_arquivo))
    flash("Vínculo de arquivo removido com sucesso!", "sucesso")
    return redirect(url_for("campanha_detalhes", id_campanha=id_campanha))

@app.route("/campanha/<int:id_campanha>/vincular_ficha", methods=["POST"])
@login_requerido
def vincular_ficha_campanha(id_campanha):
    campanha = controlador_bd.obter_campanha(id_campanha)
    if not campanha:
        flash("Campanha não encontrada.", "perigo")
        return redirect(url_for("colecoes"))

    ficha_id = request.form.get("ficha_id")
    if not ficha_id:
        flash("Selecione um personagem para vincular.", "perigo")
        return redirect(url_for("campanha_detalhes", id_campanha=id_campanha))

    try:
        ficha_id = int(ficha_id)
    except ValueError:
        flash("Seleção inválida.", "perigo")
        return redirect(url_for("campanha_detalhes", id_campanha=id_campanha))

    ficha = controlador_bd.obter_ficha_completa(ficha_id)
    if not ficha or ficha.id_usuario != g.usuario.id:
        flash("Ficha não encontrada ou não pertence a você.", "perigo")
        return redirect(url_for("campanha_detalhes", id_campanha=id_campanha))

    controlador_bd.adicionar_usuario_campanha(id_campanha, g.usuario.id)
    controlador_bd.adicionar_ficha_campanha(id_campanha, ficha_id)
    flash(f"A ficha '{ficha.nome_personagem}' foi vinculada à campanha.", "sucesso")
    return redirect(url_for("campanha_detalhes", id_campanha=id_campanha))

@app.route("/campanha/<int:id_campanha>/remover_ficha", methods=["POST"])
@login_requerido
def remover_ficha_campanha(id_campanha):
    campanha = controlador_bd.obter_campanha(id_campanha)
    if not campanha:
        flash("Campanha não encontrada.", "perigo")
        return redirect(url_for("colecoes"))

    ficha_id = request.form.get("ficha_id")
    if not ficha_id:
        flash("Ficha não informada.", "perigo")
        return redirect(url_for("campanha_detalhes", id_campanha=id_campanha))

    try:
        ficha_id = int(ficha_id)
    except ValueError:
        flash("Seleção inválida.", "perigo")
        return redirect(url_for("campanha_detalhes", id_campanha=id_campanha))

    ficha = controlador_bd.obter_ficha_completa(ficha_id)
    if not ficha:
        flash("Ficha não encontrada.", "perigo")
        return redirect(url_for("campanha_detalhes", id_campanha=id_campanha))

    pode_remover = (g.usuario.id == campanha.id_mestre) or (g.usuario.id == ficha.id_usuario)
    if not pode_remover:
        flash("Você não tem permissão para remover este vínculo.", "perigo")
        return redirect(url_for("campanha_detalhes", id_campanha=id_campanha))

    controlador_bd.remover_ficha_campanha(id_campanha, ficha_id)
    flash("Vínculo de personagem removido com sucesso!", "sucesso")
    return redirect(url_for("campanha_detalhes", id_campanha=id_campanha))

@app.route("/livros", methods=["GET", "POST"])
@login_requerido
def livros():
    if request.method == "POST":
        if request.form.get("deletar_livro"):
            nome_arquivo = request.form.get("deletar_livro")
            if remover_livro_usuario(nome_arquivo, g.usuario.id):
                flash("Livro removido com sucesso!", "sucesso")
            else:
                flash("Arquivo não encontrado.", "perigo")
            return redirect(url_for("livros"))

        if "livro_pdf" not in request.files:
            flash("Nenhum arquivo enviado.", "perigo")
            return redirect(request.url)

        arquivo = request.files["livro_pdf"]
        if arquivo.filename == "":
            flash("Nenhum arquivo selecionado.", "perigo")
            return redirect(request.url)

        if salvar_livro_usuario(arquivo, g.usuario.id):
            flash("Livro adicionado com sucesso!", "sucesso")
            return redirect(url_for("livros"))

        flash("Apenas arquivos PDF são permitidos.", "perigo")

    lista_livros = listar_livros_usuario(g.usuario.id)
    return render_template("livros.html", livros=lista_livros)

# ==========================================
# ROTAS DE PERSONAGENS
# ==========================================

@app.route("/personagens")
@login_requerido
def selecao_personagens():
    """Página que exibe a lista de personagens do usuário e botão para criar novos."""
    fichas = controlador_bd.obter_fichas_usuario(g.usuario.id)
    return render_template("gerenciarPersonagens.html", fichas=fichas, usuario=g.usuario)

@app.route("/ficha/selecao")
@login_requerido
def selecao_criacao():
    """Redireciona para a nova rota de personagens (mantém compatibilidade)."""
    return redirect(url_for("selecao_personagens"))

@app.route("/personagens/<int:id_ficha>/excluir", methods=["POST"])
@login_requerido
@chave_requerida
def excluir_personagem(id_ficha):
    """Exclui um personagem do usuário."""
    ficha = controlador_bd.obter_ficha_completa(id_ficha)
    if not ficha:
        flash("Ficha não encontrada.", "perigo")
        return redirect(url_for("selecao_personagens"))
    try:
        with ConexaoBD(controlador_bd.caminho_db) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM FichaPersonagem WHERE id = ?", (id_ficha,))
            flash("Personagem excluído com sucesso!", "sucesso")
    except Exception as e:
        flash(f"Erro ao excluir Personagem: {str(e)}", "perigo")

    return redirect(url_for("selecao_personagens"))
    

@app.route("/ficha/criar", methods=["POST"])
@login_requerido
@chave_requerida
def criar_ficha():
    nome_personagem = request.form.get("nome_personagem")
    subtitulo = request.form.get("subtitulo", "")
    try:
        if not nome_personagem or not nome_personagem.strip():
            raise ValidacaoDadosErro("O nome do personagem é obrigatório.")
        ficha = controlador_bd.criar_ficha_vazia(nome_personagem.strip(), g.usuario.id, subtitulo.strip())
        flash(f"Personagem '{ficha.nome_personagem}' criado com sucesso!", "sucesso")
        return redirect(url_for("criador_ficha", id_ficha=ficha.id))
    except ValidacaoDadosErro as e:
        flash(str(e), "perigo")
        return redirect(url_for("selecao_personagens"))

def _usuario_tem_acesso_ficha(ficha, usuario_id: int) -> tuple[bool, bool]:
    if ficha.id_usuario == usuario_id:
        return True, True

    if getattr(ficha, "visibilidade", "todos") == "mestres":
        for campanha_id in controlador_bd.obter_campanhas_com_ficha(ficha.id):
            campanha = controlador_bd.obter_campanha(campanha_id)
            if campanha and campanha.id_mestre == usuario_id:
                return True, False
        return False, False

    for campanha_id in controlador_bd.obter_campanhas_com_ficha(ficha.id):
        campanha = controlador_bd.obter_campanha(campanha_id)
        if campanha and (campanha.id_mestre == usuario_id or any(jogador.id == usuario_id for jogador in campanha.jogadores)):
            return True, False

    return False, False

@app.route("/criador/<int:id_ficha>")
@login_requerido
def criador_ficha(id_ficha):
    ficha = controlador_bd.obter_ficha_completa(id_ficha)
    if not ficha:
        flash("Ficha não encontrada.", "perigo")
        return redirect(url_for("colecoes"))

    pode_visualizar, pode_editar = _usuario_tem_acesso_ficha(ficha, g.usuario.id)
    if not pode_visualizar:
        flash("Você não tem permissão para acessar esta ficha.", "perigo")
        return redirect(url_for("colecoes"))

    modo_inicial = "Jogo"
    return render_template(
        "criarPersonagem.html",
        ficha=ficha,
        pode_editar=pode_editar,
        modo_inicial=modo_inicial,
    )

# ==========================================
# ROTA PARA UPLOAD DE AVATAR DO PERSONAGEM
# ==========================================
@app.route("/api/ficha/<int:id_ficha>/avatar", methods=["POST"])
@login_requerido
def api_upload_avatar_personagem(id_ficha):
    """Faz upload do avatar do personagem."""
    ficha = controlador_bd.obter_ficha_completa(id_ficha)
    if not ficha:
        return jsonify({"erro": "Ficha não encontrada"}), 404
    if ficha.id_usuario != g.usuario.id:
        return jsonify({"erro": "Acesso negado"}), 403
    
    if 'avatar' not in request.files:
        return jsonify({"erro": "Nenhum arquivo enviado"}), 400
    
    arquivo = request.files['avatar']
    if arquivo.filename == '':
        return jsonify({"erro": "Nenhum arquivo selecionado"}), 400
    
    caminho_avatar = salvar_imagem(arquivo, app.config["AVATAR_FOLDER"], f"ficha_{id_ficha}")
    if not caminho_avatar:
        return jsonify({"erro": "Formato de arquivo não suportado"}), 400
    
    # Atualiza o avatar no estado da ficha
    try:
        dados_ficha = controlador_bd.obter_ficha_completa(id_ficha)
        if dados_ficha:
            dados_ficha.avatar = caminho_avatar
            controlador_bd.salvar_ficha_completa(dados_ficha)
            return jsonify({
                "status": "success", 
                "avatar_url": caminho_avatar,
                "message": "Avatar atualizado com sucesso!"
            })
    except Exception as e:
        return jsonify({"erro": f"Erro ao salvar avatar: {str(e)}"}), 500
    
    return jsonify({"status": "success", "avatar_url": caminho_avatar})

# ==========================================
# ROTAS DE GERENCIAMENTO DE CAMPANHAS
# ==========================================

@app.route("/campanhas")
@login_requerido
def gerenciar_campanhas():
    """Página que exibe a lista de campanhas do usuário com opções de gerenciamento."""
    campanhas = controlador_bd.obter_campanhas_usuario(g.usuario.id)
    return render_template("gerenciarCampanhas.html", campanhas=campanhas, usuario=g.usuario)

@app.route("/campanha/<int:id_campanha>/excluir", methods=["POST"])
@login_requerido
def excluir_campanha(id_campanha):
    """Exclui uma campanha (apenas o mestre pode excluir)."""
    campanha = controlador_bd.obter_campanha(id_campanha)
    if not campanha:
        flash("Campanha não encontrada.", "perigo")
        return redirect(url_for("gerenciar_campanhas"))
    
    # Verifica se o usuário é o mestre da campanha
    if campanha.id_mestre != g.usuario.id:
        flash("Você não tem permissão para excluir esta campanha.", "perigo")
        return redirect(url_for("gerenciar_campanhas"))
    
    try:
        with ConexaoBD(controlador_bd.caminho_db) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM Campanha WHERE id = ?", (id_campanha,))
            flash("Campanha excluída com sucesso!", "sucesso")
    except Exception as e:
        flash(f"Erro ao excluir campanha: {str(e)}", "perigo")
    
    return redirect(url_for("gerenciar_campanhas"))

@app.route("/campanha/<int:id_campanha>/sair", methods=["POST"])
@login_requerido
def sair_campanha(id_campanha):
    """Remove o jogador da campanha."""
    campanha = controlador_bd.obter_campanha(id_campanha)
    if not campanha:
        flash("Campanha não encontrada.", "perigo")
        return redirect(url_for("gerenciar_campanhas"))
    
    # Verifica se o usuário não é o mestre
    if campanha.id_mestre == g.usuario.id:
        flash("O mestre não pode sair da campanha. Use a opção de excluir.", "perigo")
        return redirect(url_for("gerenciar_campanhas"))
    
    try:
        # Remove o jogador da lista de jogadores
        dados = controlador_bd._obter_dados_json_campanha(id_campanha)
        if g.usuario.id in dados["jogadores"]:
            dados["jogadores"].remove(g.usuario.id)
        with ConexaoBD(controlador_bd.caminho_db) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE Campanha SET lista_personagens = ? WHERE id = ?",
                (json.dumps(dados), id_campanha)
            )
        flash("Você saiu da campanha com sucesso!", "sucesso")
    except Exception as e:
        flash(f"Erro ao sair da campanha: {str(e)}", "perigo")
    
    return redirect(url_for("gerenciar_campanhas"))

# ==========================================
# ENDPOINTS REST API (JSON) PARA O CRIADOR
# ==========================================

@app.route("/api/ficha/<int:id_ficha>", methods=["GET"])
@login_requerido
def api_obter_ficha(id_ficha):
    """Retorna os dados completos estruturados da ficha em JSON."""
    ficha = controlador_bd.obter_ficha_completa(id_ficha)
    if not ficha:
        return jsonify({"erro": "Ficha não encontrada"}), 404

    pode_visualizar, _ = _usuario_tem_acesso_ficha(ficha, g.usuario.id)
    if not pode_visualizar:
        return jsonify({"erro": "Acesso negado"}), 403

    dados = controlador_bd._serializar_ficha(ficha)
    return jsonify(dados)

@app.route("/api/ficha/<int:id_ficha>", methods=["POST"])
@login_requerido
def api_salvar_ficha(id_ficha):
    """Recebe e persiste recursivamente o JSON modificado do criador.js no SQLite3."""
    dados = request.get_json()
    if not dados:
        return jsonify({"erro": "Dados inválidos"}), 400

    ficha_existente = controlador_bd.obter_ficha_completa(id_ficha)
    if not ficha_existente:
        return jsonify({"erro": "Ficha não encontrada"}), 404

    _, pode_editar = _usuario_tem_acesso_ficha(ficha_existente, g.usuario.id)
    if not pode_editar:
        return jsonify({"erro": "Acesso negado"}), 403

    ficha = controlador_bd.construir_ficha_a_partir_dados(
        dados,
        id_ficha,
        g.usuario.id,
    )
    if ficha.avatar is None:
        ficha.avatar = ficha_existente.avatar

    controlador_bd.salvar_ficha_completa(ficha)
    return jsonify({"status": "success"})

@app.route("/api/ficha/<int:id_ficha>/template", methods=["POST"])
@login_requerido
def api_criar_template(id_ficha):
    dados = request.get_json(silent=True) or {}
    nome_template = (dados.get("nome") or request.form.get("nome") or "").strip()
    if not nome_template:
        return jsonify({"erro": "Informe um nome para o template."}), 400

    ficha = controlador_bd.obter_ficha_completa(id_ficha)
    if not ficha or ficha.id_usuario != g.usuario.id:
        return jsonify({"erro": "Ficha não encontrada."}), 404

    estrutura_json = controlador_bd._serializar_ficha(ficha)
    template_id = controlador_bd.criar_template(nome_template, id_ficha, g.usuario.id, estrutura_json)
    return jsonify({"status": "success", "id": template_id, "nome": nome_template})
@app.route("/api/ficha/<int:id_ficha>/template", methods=["GET"])
@login_requerido
def api_listar_templates(id_ficha):
    ficha = controlador_bd.obter_ficha_completa(id_ficha)
    if not ficha:
        return jsonify({"erro": "Ficha não encontrada."}), 404

    pode_visualizar, _ = _usuario_tem_acesso_ficha(ficha, g.usuario.id)
    if not pode_visualizar:
        return jsonify({"erro": "Acesso negado"}), 403

    templates = controlador_bd.obter_templates_por_usuario(g.usuario.id)
    return jsonify({"templates": templates})

@app.route("/api/ficha/<int:id_ficha>/template/<int:template_id>/apply", methods=["POST"])
@login_requerido
def api_aplicar_template(id_ficha, template_id):
    ficha_existente = controlador_bd.obter_ficha_completa(id_ficha)
    if not ficha_existente or ficha_existente.id_usuario != g.usuario.id:
        return jsonify({"erro": "Ficha não encontrada."}), 404

    template = controlador_bd.obter_template_por_id(template_id)
    if not template:
        return jsonify({"erro": "Template não encontrado."}), 404
    
    # Verificar se o template pertence ao usuário ou se id_usuario é None (compatibilidade com dados antigos)
    if template.get("id_usuario") is not None and template["id_usuario"] != g.usuario.id:
        return jsonify({"erro": "Acesso negado ao template."}), 403

    dados_template = template.get("estrutura_json") or {}
    ficha = controlador_bd.construir_ficha_a_partir_dados(dados_template, id_ficha, g.usuario.id, preservar_ids=False)
    ficha.nome_personagem = ficha_existente.nome_personagem
    subtitulo_existente = getattr(ficha_existente, "subtitulo", None) or getattr(ficha_existente, "aspecto", "") or getattr(ficha_existente, "aspecto_personagem", "")
    ficha.aspecto_personagem = subtitulo_existente
    ficha.subtitulo = subtitulo_existente
    ficha.aspecto = subtitulo_existente
    ficha.avatar = ficha_existente.avatar
    ficha.visibilidade = getattr(ficha_existente, "visibilidade", "todos")

    controlador_bd.salvar_ficha_completa(ficha)
    return jsonify(controlador_bd._serializar_ficha(ficha))

@app.route("/api/ficha/<int:id_ficha>/template/<int:template_id>", methods=["DELETE"])
@login_requerido
def api_deletar_template(id_ficha, template_id):
    ficha = controlador_bd.obter_ficha_completa(id_ficha)
    if not ficha or ficha.id_usuario != g.usuario.id:
        return jsonify({"erro": "Ficha não encontrada."}), 404

    template = controlador_bd.obter_template_por_id(template_id)
    if not template:
        return jsonify({"erro": "Template não encontrado."}), 404
    
    # Verificar se o template pertence ao usuário ou se id_usuario é None (compatibilidade com dados antigos)
    if template.get("id_usuario") is not None and template["id_usuario"] != g.usuario.id:
        return jsonify({"erro": "Acesso negado ao template."}), 403

    sucesso = controlador_bd.deletar_template(template_id)
    if not sucesso:
        return jsonify({"erro": "Falha ao excluir template."}), 500

    return jsonify({"status": "success"})

# ==========================================
# ENDPOINTS PARA CRUD DE ESTRUTURA
# ==========================================

@app.route("/api/ficha/<int:id_ficha>/aba", methods=["POST"])
@login_requerido
def api_criar_aba(id_ficha):
    """Cria uma nova aba em uma coluna."""
    ficha = controlador_bd.obter_ficha_completa(id_ficha)
    if not ficha or ficha.id_usuario != g.usuario.id:
        return jsonify({"erro": "Ficha não encontrada."}), 404

    dados = request.get_json(silent=True) or {}
    titulo_aba = (dados.get("titulo") or "Nova Aba").strip()
    posicao_coluna = dados.get("posicaoColuna", 1)
    
    # Encontra a coluna
    coluna = None
    for col in ficha.colunas:
        if col.posicao_coluna == posicao_coluna:
            coluna = col
            break
    
    if not coluna:
        return jsonify({"erro": "Coluna não encontrada."}), 404
    
    # Cria nova aba
    from classes import Aba
    aba = Aba(id=None, id_coluna=None, titulo=titulo_aba, posicao_aba=len(coluna.abas) + 1)
    coluna.adicionar_aba(aba)
    
    controlador_bd.salvar_ficha_completa(ficha)
    return jsonify({"status": "success", "aba": {"id": aba.id, "titulo": aba.titulo}})

@app.route("/api/ficha/<int:id_ficha>/aba/<int:aba_id>", methods=["DELETE"])
@login_requerido
def api_deletar_aba(id_ficha, aba_id):
    """Deleta uma aba."""
    ficha = controlador_bd.obter_ficha_completa(id_ficha)
    if not ficha or ficha.id_usuario != g.usuario.id:
        return jsonify({"erro": "Ficha não encontrada."}), 404
    
    # Encontra e remove a aba
    for coluna in ficha.colunas:
        for aba in coluna.abas[:]:
            if aba.id == aba_id:
                coluna.abas.remove(aba)
                controlador_bd.salvar_ficha_completa(ficha)
                return jsonify({"status": "success"})
    
    return jsonify({"erro": "Aba não encontrada."}), 404

@app.route("/api/ficha/<int:id_ficha>/secao", methods=["POST"])
@login_requerido
def api_criar_secao(id_ficha):
    """Cria uma nova seção em uma aba."""
    ficha = controlador_bd.obter_ficha_completa(id_ficha)
    if not ficha or ficha.id_usuario != g.usuario.id:
        return jsonify({"erro": "Ficha não encontrada."}), 404

    dados = request.get_json(silent=True) or {}
    titulo_secao = (dados.get("titulo") or "Nova Seção").strip()
    tipo_componente = dados.get("tipo", "AtributoSimples")
    aba_id = dados.get("abaId")
    
    # Encontra a aba
    aba = None
    for coluna in ficha.colunas:
        for a in coluna.abas:
            if a.id == aba_id:
                aba = a
                break
        if aba:
            break
    
    if not aba:
        return jsonify({"erro": "Aba não encontrada."}), 404
    
    # Cria nova seção
    from classes import Secao
    secao = Secao(id=None, id_aba=None, titulo=titulo_secao, posicao_secao=len(aba.secoes) + 1, tipo=tipo_componente)
    aba.adicionar_secao(secao)
    
    controlador_bd.salvar_ficha_completa(ficha)
    return jsonify({"status": "success", "secao": {"id": secao.id, "titulo": secao.titulo}})

@app.route("/api/ficha/<int:id_ficha>/secao/<int:secao_id>", methods=["DELETE"])
@login_requerido
def api_deletar_secao(id_ficha, secao_id):
    """Deleta uma seção."""
    ficha = controlador_bd.obter_ficha_completa(id_ficha)
    if not ficha or ficha.id_usuario != g.usuario.id:
        return jsonify({"erro": "Ficha não encontrada."}), 404
    
    # Encontra e remove a seção
    for coluna in ficha.colunas:
        for aba in coluna.abas:
            for secao in aba.secoes[:]:
                if secao.id == secao_id:
                    aba.secoes.remove(secao)
                    controlador_bd.salvar_ficha_completa(ficha)
                    return jsonify({"status": "success"})
    
    return jsonify({"erro": "Seção não encontrada."}), 404

@app.route("/api/ficha/<int:id_ficha>/componente", methods=["POST"])
@login_requerido
def api_criar_componente(id_ficha):
    """Cria um novo componente em uma seção."""
    ficha = controlador_bd.obter_ficha_completa(id_ficha)
    if not ficha or ficha.id_usuario != g.usuario.id:
        return jsonify({"erro": "Ficha não encontrada."}), 404

    dados = request.get_json(silent=True) or {}
    secao_id = dados.get("secaoId")
    tipo_componente = dados.get("tipo", "AtributoSimples")
    
    # Encontra a seção
    secao = None
    for coluna in ficha.colunas:
        for aba in coluna.abas:
            for sec in aba.secoes:
                if sec.id == secao_id:
                    secao = sec
                    break
    
    if not secao:
        return jsonify({"erro": "Seção não encontrada."}), 404
    
    # Cria o componente
    componente = controlador_bd._criar_componente_a_partir_json(tipo_componente, dados)
    if not componente:
        return jsonify({"erro": "Tipo de componente inválido."}), 400
    
    secao.adicionar_componente(componente)
    controlador_bd.salvar_ficha_completa(ficha)
    
    comp_serializado = controlador_bd._serializar_componente(componente)
    return jsonify({"status": "success", "componente": comp_serializado})

@app.route("/api/ficha/<int:id_ficha>/componente/<int:comp_id>", methods=["PUT"])
@login_requerido
def api_atualizar_componente(id_ficha, comp_id):
    """Atualiza um componente."""
    ficha = controlador_bd.obter_ficha_completa(id_ficha)
    if not ficha or ficha.id_usuario != g.usuario.id:
        return jsonify({"erro": "Ficha não encontrada."}), 404

    dados = request.get_json(silent=True) or {}
    
    # Encontra e atualiza o componente
    for coluna in ficha.colunas:
        for aba in coluna.abas:
            for secao in aba.secoes:
                for i, comp in enumerate(secao.componentes):
                    if comp.id == comp_id:
                        # Atualiza os campos do componente
                        if "rotulo" in dados:
                            comp.rotulo = dados["rotulo"]
                        if "valorAtual" in dados:
                            comp.valor_atual = int(dados["valorAtual"])
                        if "valorMaximo" in dados:
                            comp.valor_maximo = int(dados["valorMaximo"])
                        if "corSeletor" in dados:
                            comp.cor_seletor = dados["corSeletor"]
                        if "estaMarcado" in dados:
                            comp.esta_marcado = bool(dados["estaMarcado"])
                        if "campoTexto" in dados:
                            comp.campo_texto = dados["campoTexto"]
                        if "descricao" in dados:
                            comp.descricao = dados["descricao"]
                        if "nomeAtributo" in dados:
                            comp.nome_atributo = dados["nomeAtributo"]
                        if "valorAtributo" in dados:
                            comp.valor_atributo = int(dados["valorAtributo"])
                        if "valorGrande" in dados:
                            comp.valor_grande = int(dados["valorGrande"])
                        if "valorPequeno" in dados:
                            comp.valor_pequeno = int(dados["valorPequeno"])
                        if "valorBase" in dados:
                            comp.valor_base = int(dados["valorBase"])
                        if "valorBonus" in dados:
                            comp.valor_bonus = int(dados["valorBonus"])
                        if "valorOutros" in dados:
                            comp.valor_outros = int(dados["valorOutros"])
                        if "subtituloAnotacao" in dados:
                            comp.subtitulo_anotacao = dados["subtituloAnotacao"]
                        if "anotacaoExtra" in dados:
                            comp.anotacao_extra = dados["anotacaoExtra"]
                        
                        controlador_bd.salvar_ficha_completa(ficha)
                        comp_serializado = controlador_bd._serializar_componente(comp)
                        return jsonify({"status": "success", "componente": comp_serializado})
    
    return jsonify({"erro": "Componente não encontrado."}), 404

@app.route("/api/ficha/<int:id_ficha>/componente/<int:comp_id>", methods=["DELETE"])
@login_requerido
def api_deletar_componente(id_ficha, comp_id):
    """Deleta um componente."""
    ficha = controlador_bd.obter_ficha_completa(id_ficha)
    if not ficha or ficha.id_usuario != g.usuario.id:
        return jsonify({"erro": "Ficha não encontrada."}), 404
    
    # Encontra e remove o componente
    for coluna in ficha.colunas:
        for aba in coluna.abas:
            for secao in aba.secoes:
                for comp in secao.componentes[:]:
                    if comp.id == comp_id:
                        secao.componentes.remove(comp)
                        controlador_bd.salvar_ficha_completa(ficha)
                        return jsonify({"status": "success"})
    
    return jsonify({"erro": "Componente não encontrado."}), 404

if __name__ == "__main__":
    app.run(debug=True)