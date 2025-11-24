from flask import Flask, render_template, request, redirect, session, url_for, flash, jsonify
import sqlite3
import random
import os
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'chave_mestra_briza_killers'
DB_NAME = "brizakillers.db"

# --- FUNÇÃO DE AUTO-CORREÇÃO DO BANCO (A SOLUÇÃO) ---
def init_db():
    """Verifica se o banco existe e cria se necessário"""
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        # Verifica se a tabela 'usuarios' existe
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='usuarios'")
        if not cursor.fetchone():
            print("⚠️ Banco não encontrado! Criando tabelas agora...")
            
            # CRIAÇÃO DAS TABELAS
            cursor.executescript('''
                CREATE TABLE IF NOT EXISTS usuarios (id INTEGER PRIMARY KEY AUTOINCREMENT, nome_completo TEXT, email TEXT UNIQUE, senha_hash TEXT, moedas INTEGER DEFAULT 500, tipo_usuario TEXT DEFAULT "torcedor");
                CREATE TABLE IF NOT EXISTS meus_cupons (id INTEGER PRIMARY KEY AUTOINCREMENT, usuario_id INTEGER, codigo TEXT, desconto INTEGER, origem TEXT, data_ganho DATETIME DEFAULT CURRENT_TIMESTAMP, FOREIGN KEY(usuario_id) REFERENCES usuarios(id));
                CREATE TABLE IF NOT EXISTS produtos (id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT, descricao TEXT, preco REAL, imagem_url TEXT, categoria TEXT);
                CREATE TABLE IF NOT EXISTS partidas (id INTEGER PRIMARY KEY AUTOINCREMENT, titulo TEXT, time_a TEXT, time_b TEXT, data_jogo TEXT, odd_a REAL DEFAULT 2.0, odd_b REAL DEFAULT 2.0, status TEXT DEFAULT "aberta", embed_url TEXT);
                CREATE TABLE IF NOT EXISTS apostas (id INTEGER PRIMARY KEY AUTOINCREMENT, usuario_id INTEGER, partida_id INTEGER, valor_apostado INTEGER, time_escolhido TEXT, status TEXT DEFAULT "pendente", FOREIGN KEY(usuario_id) REFERENCES usuarios(id), FOREIGN KEY(partida_id) REFERENCES partidas(id));
                CREATE TABLE IF NOT EXISTS jogadores (id INTEGER PRIMARY KEY AUTOINCREMENT, nickname TEXT, nome_real TEXT, funcao TEXT, jogo TEXT, foto_url TEXT, instagram TEXT, stat_mira INTEGER, stat_inteligencia INTEGER, stat_mecanica INTEGER, mouse TEXT, main_char TEXT, bio TEXT, hype INTEGER DEFAULT 0);
                CREATE TABLE IF NOT EXISTS noticias (id INTEGER PRIMARY KEY AUTOINCREMENT, titulo TEXT, resumo TEXT, conteudo TEXT, imagem_capa TEXT, autor TEXT DEFAULT "Admin", data_postagem DATETIME DEFAULT CURRENT_TIMESTAMP);
                CREATE TABLE IF NOT EXISTS candidatos (id INTEGER PRIMARY KEY AUTOINCREMENT, usuario_id INTEGER, nick_jogo TEXT, rank_atual TEXT, discord TEXT, motivo TEXT, data_inscricao DATETIME DEFAULT CURRENT_TIMESTAMP, FOREIGN KEY(usuario_id) REFERENCES usuarios(id));
            ''')
            
            # INSERÇÃO DE DADOS (SEEDS)
            senha_admin = generate_password_hash("123456")
            cursor.execute("INSERT INTO usuarios (nome_completo, email, senha_hash, moedas, tipo_usuario) VALUES (?, ?, ?, ?, ?)", ('Admin Supremo', 'admin@briza.com', senha_admin, 9999, 'admin'))
            
            cursor.execute("DELETE FROM produtos")
            cursor.execute('''INSERT INTO produtos (nome, descricao, preco, imagem_url, categoria) VALUES 
                ('JERSEY PRO 2025', 'Uniforme oficial.', 119.90, '/static/img/camisaoficial.png', 'uniformes'),
                ('BASIC TEE NEON', 'Casual Oversized.', 79.90, '/static/img/informal.png', 'casual'),
                ('HOODIE KILLERS', 'Moletom tático.', 189.90, '/static/img/moleton.png', 'inverno'),
                ('BONÉ DAD HAT', 'Boné estruturado.', 59.90, '/static/img/bone.png', 'acessorios'),
                ('BERMUDA ATHLETIC', 'Short esportivo.', 89.90, '/static/img/shot.jpg', 'casual'),
                ('CROPPED PRO FEM', 'Baby look jersey.', 79.90, '/static/img/cropt.png', 'uniformes')''')

            cursor.execute("DELETE FROM jogadores")
            cursor.execute('''INSERT INTO jogadores (nickname, nome_real, funcao, jogo, foto_url, instagram, stat_mira, stat_inteligencia, stat_mecanica, mouse, main_char, bio, hype) VALUES 
                ('REX', 'Juan', 'Capitão / Rush', 'Clash Royale', 'https://cdn-icons-png.flaticon.com/512/4140/4140048.png', '@juan_rex', 85, 95, 90, 'Logitech G Pro', 'Gigante Real', 'Lider nato e agressivo.', 120),
                ('PRÍNCIPE', 'Paulo Junior', 'Rei de Soledade', 'Clash Royale', 'https://cdn-icons-png.flaticon.com/512/4140/4140047.png', '@paulo_soledade', 80, 99, 85, 'Razer Viper', 'Príncipe', 'Estrategista defensivo.', 95),
                ('PESTE BRANCA', 'Twilo', 'Dano Crítico', 'Brawl Stars', 'https://cdn-icons-png.flaticon.com/512/4140/4140037.png', '@twilo_peste', 95, 80, 92, 'HyperX Pulsefire', 'Crow', 'Movimentação imprevisível.', 150),
                ('VORTEX', 'Ernandes', 'IGL / Estrategista', 'CS:GO', 'https://cdn-icons-png.flaticon.com/512/4140/4140051.png', '@ernandes_vortex', 88, 100, 85, 'Zowie EC2', 'AWP', 'Controle de mapa absoluto.', 80),
                ('THUNDER', 'Wandson', 'Entry Fragger', 'Valorant', 'https://cdn-icons-png.flaticon.com/512/145/145867.png', '@wandson_thunder', 99, 75, 96, 'Razer Deathadder', 'Jett', 'Reflexos insanos.', 110)''')

            cursor.execute("DELETE FROM partidas")
            cursor.execute("INSERT INTO partidas (titulo, time_a, time_b, data_jogo, odd_a, odd_b, embed_url) VALUES ('GRANDE FINAL', 'Briza Killers', 'Redes FC', 'AO VIVO', 1.8, 2.2, 'https://www.youtube.com/embed/S7x5Z6w7s8s')")
            
            cursor.execute("DELETE FROM noticias")
            cursor.execute("INSERT INTO noticias (titulo, conteudo, imagem_capa) VALUES ('VITÓRIA NA FINAL', 'Dominamos o servidor e trouxemos o troféu!', 'https://cdn-icons-png.flaticon.com/512/5352/5352037.png')")
            
            print("✅ Banco recriado com sucesso!")

# Roda a verificação assim que o app inicia
init_db()

def get_db_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

# ==============================================================================
#                               ROTAS
# ==============================================================================

@app.route('/')
def index():
    conn = get_db_connection()
    noticias = conn.execute('SELECT * FROM noticias ORDER BY id DESC LIMIT 3').fetchall()
    usuario = None
    if 'usuario_id' in session:
        usuario = conn.execute('SELECT * FROM usuarios WHERE id = ?', (session['usuario_id'],)).fetchone()
    conn.close()
    return render_template('index.html', usuario=usuario, noticias=noticias)

@app.route('/noticias')
def pagina_noticias():
    conn = get_db_connection()
    noticias = conn.execute('SELECT * FROM noticias ORDER BY id DESC').fetchall()
    usuario = None
    if 'usuario_id' in session:
        usuario = conn.execute('SELECT * FROM usuarios WHERE id = ?', (session['usuario_id'],)).fetchone()
    conn.close()
    return render_template('noticias.html', noticias=noticias, usuario=usuario)

@app.route('/ranking')
def ranking():
    conn = get_db_connection()
    top_jogadores = conn.execute('SELECT nome_completo, moedas, tipo_usuario FROM usuarios ORDER BY moedas DESC LIMIT 10').fetchall()
    usuario = None
    if 'usuario_id' in session:
        usuario = conn.execute('SELECT * FROM usuarios WHERE id = ?', (session['usuario_id'],)).fetchone()
    conn.close()
    return render_template('ranking.html', jogadores=top_jogadores, usuario=usuario)

# --- LOGIN E CADASTRO ---

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        senha = request.form['senha']
        conn = get_db_connection()
        user = conn.execute('SELECT * FROM usuarios WHERE email = ?', (email,)).fetchone()
        conn.close()
        if user and check_password_hash(user['senha_hash'], senha):
            session['usuario_id'] = user['id']
            session['nome'] = user['nome_completo']
            return redirect(url_for('perfil'))
        flash('Dados incorretos!')
    return render_template('login.html')

@app.route('/cadastro', methods=['GET', 'POST'])
def cadastro():
    if request.method == 'POST':
        nome = request.form['nome']
        email = request.form['email']
        senha = request.form['senha']
        if senha != request.form['confirmar_senha']: return render_template('cadastro.html')
        try:
            conn = get_db_connection()
            conn.execute('INSERT INTO usuarios (nome_completo, email, senha_hash) VALUES (?,?,?)', (nome, email, generate_password_hash(senha)))
            conn.commit()
            conn.close()
            return redirect(url_for('login'))
        except: pass
    return render_template('cadastro.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/perfil')
def perfil():
    if 'usuario_id' not in session: return redirect(url_for('login'))
    conn = get_db_connection()
    u = conn.execute('SELECT * FROM usuarios WHERE id=?',(session['usuario_id'],)).fetchone()
    c = conn.execute('SELECT * FROM meus_cupons WHERE usuario_id=?',(session['usuario_id'],)).fetchall()
    conn.close()
    return render_template('perfil.html', usuario=u, cupons=c)

# --- ÁREAS DO SITE ---

@app.route('/loja')
def loja():
    conn = get_db_connection()
    p = conn.execute('SELECT * FROM produtos').fetchall()
    u = None
    if 'usuario_id' in session: u = conn.execute('SELECT * FROM usuarios WHERE id=?',(session['usuario_id'],)).fetchone()
    conn.close()
    return render_template('loja.html', produtos=p, usuario=u)

@app.route('/produto/<int:id>')
def produto_detalhe(id):
    conn = get_db_connection()
    produto = conn.execute('SELECT * FROM produtos WHERE id = ?', (id,)).fetchone()
    sugestoes = conn.execute('SELECT * FROM produtos WHERE categoria = ? AND id != ? LIMIT 3', (produto['categoria'], id)).fetchall()
    usuario = None
    if 'usuario_id' in session:
        usuario = conn.execute('SELECT * FROM usuarios WHERE id = ?', (session['usuario_id'],)).fetchone()
    conn.close()
    return render_template('produto.html', p=produto, sugestoes=sugestoes, usuario=usuario)

@app.route('/carrinho')
def carrinho():
    if 'carrinho' not in session: session['carrinho'] = []
    total = sum(item['preco'] for item in session['carrinho'])
    desconto = session.get('desconto_valor', 0)
    total_final = total - (total * (desconto / 100))
    conn = get_db_connection()
    usuario = None
    if 'usuario_id' in session:
        usuario = conn.execute('SELECT * FROM usuarios WHERE id = ?', (session['usuario_id'],)).fetchone()
    conn.close()
    return render_template('carrinho.html', carrinho=session['carrinho'], total=total, desconto=desconto, total_final=total_final, usuario=usuario)

@app.route('/loja-moedas')
def loja_moedas():
    if 'usuario_id' not in session: return redirect(url_for('login'))
    conn = get_db_connection()
    usuario = conn.execute('SELECT * FROM usuarios WHERE id = ?', (session['usuario_id'],)).fetchone()
    conn.close()
    return render_template('loja_moedas.html', usuario=usuario)

@app.route('/equipes')
def equipe():
    conn = get_db_connection()
    j = conn.execute('SELECT * FROM jogadores').fetchall()
    u = None
    if 'usuario_id' in session: u = conn.execute('SELECT * FROM usuarios WHERE id=?',(session['usuario_id'],)).fetchone()
    conn.close()
    return render_template('equipes.html', jogadores=j, usuario=u)

@app.route('/torneios')
def torneios():
    if 'usuario_id' not in session: return redirect(url_for('login'))
    conn = get_db_connection()
    todas = conn.execute('SELECT * FROM partidas WHERE status="aberta"').fetchall()
    destaque = todas[0] if todas else None
    lista = todas[1:] if len(todas) > 1 else []
    u = conn.execute('SELECT moedas FROM usuarios WHERE id=?',(session['usuario_id'],)).fetchone()
    conn.close()
    return render_template('torneios.html', destaque=destaque, partidas=lista, saldo=u['moedas'])

@app.route('/recompensas')
def recompensas():
    if 'usuario_id' not in session: return redirect(url_for('login'))
    return render_template('recompensas.html')

# --- ADMIN ---
@app.route('/admin')
def admin_panel():
    if 'usuario_id' not in session: return redirect(url_for('login'))
    conn = get_db_connection()
    user = conn.execute('SELECT * FROM usuarios WHERE id = ?', (session['usuario_id'],)).fetchone()
    if user['tipo_usuario'] != 'admin':
        conn.close()
        return redirect(url_for('perfil'))
    noticias = conn.execute('SELECT * FROM noticias ORDER BY id DESC').fetchall()
    partidas = conn.execute('SELECT * FROM partidas ORDER BY id DESC').fetchall()
    conn.close()
    return render_template('admin.html', usuario=user, noticias=noticias, partidas=partidas)

@app.route('/admin/criar_noticia', methods=['POST'])
def criar_noticia():
    if 'usuario_id' not in session: return jsonify({'sucesso': False})
    conn = get_db_connection()
    conn.execute('INSERT INTO noticias (titulo, conteudo, imagem_capa) VALUES (?, ?, ?)', (request.form['titulo'], request.form['conteudo'], request.form['imagem']))
    conn.commit()
    conn.close()
    return redirect(url_for('admin_panel'))

@app.route('/admin/criar_partida', methods=['POST'])
def criar_partida():
    if 'usuario_id' not in session: return jsonify({'sucesso': False})
    conn = get_db_connection()
    conn.execute('INSERT INTO partidas (titulo, time_a, time_b, data_jogo, odd_a, odd_b, embed_url, status) VALUES (?, ?, ?, "AO VIVO", ?, ?, ?, "aberta")', (request.form['titulo'], request.form['time_a'], request.form['time_b'], request.form['odd_a'], request.form['odd_b'], request.form['link']))
    conn.commit()
    conn.close()
    return redirect(url_for('admin_panel'))

@app.route('/admin/deletar/<tipo>/<int:id>')
def deletar_item(tipo, id):
    if 'usuario_id' not in session: return redirect(url_for('login'))
    conn = get_db_connection()
    u = conn.execute('SELECT tipo_usuario FROM usuarios WHERE id=?', (session['usuario_id'],)).fetchone()
    if u['tipo_usuario'] == 'admin':
        tabela = 'noticias' if tipo == 'noticia' else 'partidas'
        conn.execute(f'DELETE FROM {tabela} WHERE id = ?', (id,))
        conn.commit()
    conn.close()
    return redirect(url_for('admin_panel'))

# --- APIS ---
@app.route('/api/abrir_bau', methods=['POST'])
def abrir_bau():
    if 'usuario_id' not in session: return jsonify({'sucesso':False}), 401
    sorte = random.randint(1,100)
    conn = get_db_connection()
    try:
        if sorte <= 50: item, rar, est = "50 Moedas", "comum", 1; conn.execute('UPDATE usuarios SET moedas=moedas+50 WHERE id=?',(session['usuario_id'],))
        elif sorte <= 80: item, rar, est = "Cupom 10%", "raro", 2; conn.execute('INSERT INTO meus_cupons (usuario_id, codigo, desconto, origem) VALUES (?,?,?,?)',(session['usuario_id'], f"RARO{random.randint(100,999)}", 10, 'bau'))
        elif sorte <= 95: item, rar, est = "300 Moedas", "epico", 3; conn.execute('UPDATE usuarios SET moedas=moedas+300 WHERE id=?',(session['usuario_id'],))
        else: item, rar, est = "1000 Moedas", "lendario", 5; conn.execute('UPDATE usuarios SET moedas=moedas+1000 WHERE id=?',(session['usuario_id'],))
        conn.commit()
        return jsonify({'sucesso':True, 'item':item, 'raridade':rar, 'estrelas':est})
    except Exception as e: return jsonify({'sucesso':False, 'msg':str(e)})
    finally: conn.close()

@app.route('/api/apostar', methods=['POST'])
def apostar():
    if 'usuario_id' not in session: return jsonify({'sucesso':False})
    data = request.json
    conn = get_db_connection()
    try:
        u = conn.execute('SELECT moedas FROM usuarios WHERE id=?',(session['usuario_id'],)).fetchone()
        val = int(data.get('valor'))
        if u['moedas'] < val: return jsonify({'sucesso':False, 'msg':'Saldo insuficiente'})
        conn.execute('UPDATE usuarios SET moedas=moedas-? WHERE id=?',(val, session['usuario_id']))
        conn.execute('INSERT INTO apostas (usuario_id, partida_id, valor_apostado, time_escolhido) VALUES (?,?,?,?)',(session['usuario_id'], data.get('partida_id'), val, data.get('time')))
        conn.commit()
        return jsonify({'sucesso':True, 'novo_saldo':u['moedas']-val})
    except Exception as e: return jsonify({'sucesso':False, 'msg':str(e)})
    finally: conn.close()

@app.route('/api/add_cart', methods=['POST'])
def add_cart():
    data = request.json
    if 'carrinho' not in session: session['carrinho'] = []
    session['carrinho'].append({'id':data['id'], 'nome':data['nome'], 'preco':float(data['preco']), 'img':data['img']})
    session.modified = True
    return jsonify({'sucesso':True})

@app.route('/api/limpar_carrinho')
def limpar_carrinho():
    session['carrinho'] = []
    session['desconto_valor'] = 0
    return redirect(url_for('carrinho'))

@app.route('/api/validar_cupom', methods=['POST'])
def validar_cupom():
    if 'usuario_id' not in session: return jsonify({'sucesso':False})
    conn = get_db_connection()
    cupom = conn.execute('SELECT * FROM meus_cupons WHERE codigo=? AND usuario_id=?',(request.json.get('codigo'), session['usuario_id'])).fetchone()
    conn.close()
    if cupom:
        session['desconto_valor'] = cupom['desconto']
        return jsonify({'sucesso':True, 'desconto':cupom['desconto']})
    return jsonify({'sucesso':False, 'msg':'Cupom inválido'})

@app.route('/api/comprar_cupom', methods=['POST'])
def comprar_cupom():
    if 'usuario_id' not in session: return jsonify({'sucesso':False})
    data = request.json
    conn = get_db_connection()
    try:
        u = conn.execute('SELECT moedas FROM usuarios WHERE id=?',(session['usuario_id'],)).fetchone()
        cost = data.get('custo')
        if u['moedas'] < cost: return jsonify({'sucesso':False, 'msg':'Saldo Insuficiente'})
        conn.execute('UPDATE usuarios SET moedas=moedas-? WHERE id=?',(cost, session['usuario_id']))
        conn.execute('INSERT INTO meus_cupons (usuario_id, codigo, desconto, origem) VALUES (?,?,?,?)',(session['usuario_id'], f"LOJA{data.get('desconto')}-{random.randint(100,999)}", data.get('desconto'), 'loja'))
        conn.commit()
        return jsonify({'sucesso':True, 'novo_saldo':u['moedas']-cost, 'codigo':'OK'})
    except Exception as e: return jsonify({'sucesso':False, 'msg':str(e)})
    finally: conn.close()

@app.route('/api/apoiar_jogador', methods=['POST'])
def apoiar_jogador():
    if 'usuario_id' not in session: return jsonify({'sucesso':False, 'msg':'Faça login'})
    data = request.json
    custo = 50
    conn = get_db_connection()
    try:
        u = conn.execute('SELECT moedas FROM usuarios WHERE id=?',(session['usuario_id'],)).fetchone()
        if u['moedas'] < custo: return jsonify({'sucesso':False, 'msg':'Moedas insuficientes'})
        conn.execute('UPDATE usuarios SET moedas=moedas-? WHERE id=?',(custo, session['usuario_id']))
        conn.execute('UPDATE jogadores SET hype=hype+1 WHERE id=?',(data.get('jogador_id'),))
        novo = conn.execute('SELECT hype FROM jogadores WHERE id=?',(data.get('jogador_id'),)).fetchone()['hype']
        conn.commit()
        return jsonify({'sucesso':True, 'novo_saldo':u['moedas']-custo, 'novo_hype':novo})
    except Exception as e: return jsonify({'sucesso':False, 'msg':str(e)})
    finally: conn.close()

@app.route('/api/inscrever', methods=['POST'])
def inscrever():
    if 'usuario_id' not in session: return jsonify({'sucesso':False})
    data = request.json
    conn = get_db_connection()
    try:
        if conn.execute('SELECT id FROM candidatos WHERE usuario_id=?',(session['usuario_id'],)).fetchone():
            return jsonify({'sucesso':False, 'msg':'Já inscrito'})
        conn.execute('INSERT INTO candidatos (usuario_id, nick_jogo, rank_atual, discord, motivo) VALUES (?,?,?,?,?)',
                     (session['usuario_id'], data.get('nick'), data.get('rank'), data.get('discord'), data.get('motivo')))
        conn.commit()
        return jsonify({'sucesso':True, 'msg':'Inscrição enviada!'})
    except Exception as e: return jsonify({'sucesso':False, 'msg':str(e)})
    finally: conn.close()

if __name__ == '__main__':
    app.run(debug=True)