from flask import Flask, render_template, request, redirect, session, url_for, flash, jsonify
import sqlite3
import random
from datetime import date # <--- IMPORTANTE: Necessário para pegar o dia de hoje
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'chave_mestra_briza_killers'
DB_NAME = "brizakillers.db"

def get_db_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

# ... (MANTENHA TODAS AS SUAS ROTAS DE NAVEGAÇÃO IGUAIS AQUI: index, login, cadastro, etc) ...
# COPIE AS ROTAS DE NAVEGAÇÃO DO SEU ARQUIVO ANTERIOR E COLE AQUI
# VOU COLOCAR APENAS A API CORRIGIDA ABAIXO PARA VOCÊ SUBSTITUIR

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
    
    conn = get_db_connection()
    user = conn.execute('SELECT ultimo_bau FROM usuarios WHERE id = ?', (session['usuario_id'],)).fetchone()
    conn.close()
    
    hoje = str(date.today())
    ja_abriu = False
    tempo_restante = ""
    
    if user and user['ultimo_bau'] == hoje:
        ja_abriu = True
        # Calcula tempo até meia-noite
        agora = datetime.now()
        amanha = datetime.combine(date.today() + timedelta(days=1), datetime.min.time())
        diferenca = amanha - agora
        horas, resto = divmod(diferenca.seconds, 3600)
        minutos, segundos = divmod(resto, 60)
        tempo_restante = f"{horas}h {minutos}m" # Formata para mostrar no botão
        
    return render_template('recompensas.html', ja_abriu=ja_abriu, tempo_restante=tempo_restante)
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

# ------------------------------------------------------------------------------
#  AQUI ESTÁ A CORREÇÃO DO BAÚ
# ------------------------------------------------------------------------------

@app.route('/api/abrir_bau', methods=['POST'])
def abrir_bau():
    if 'usuario_id' not in session: return jsonify({'sucesso':False}), 401
    
    conn = get_db_connection()
    
    # 1. VERIFICAR SE JÁ ABRIU HOJE
    user = conn.execute('SELECT ultimo_bau FROM usuarios WHERE id = ?', (session['usuario_id'],)).fetchone()
    hoje = str(date.today()) 
    
    if user['ultimo_bau'] == hoje:
        conn.close()
        return jsonify({'sucesso': False, 'msg': 'Você já abriu o baú hoje! Volte amanhã.'})

    # 2. SE NÃO ABRIU, SORTEIA
    sorte = random.randint(1,100)
    try:
        conn.execute('UPDATE usuarios SET ultimo_bau = ? WHERE id = ?', (hoje, session['usuario_id']))
        
        if sorte <= 50: 
            item, rar, est = "50 Moedas", "comum", 1
            conn.execute('UPDATE usuarios SET moedas=moedas+50 WHERE id=?',(session['usuario_id'],))
        elif sorte <= 80: 
            item, rar, est = "Cupom 10%", "raro", 2
            conn.execute('INSERT INTO meus_cupons (usuario_id, codigo, desconto, origem) VALUES (?,?,?,?)',(session['usuario_id'], f"RARO{random.randint(100,999)}", 10, 'bau'))
        elif sorte <= 95: 
            item, rar, est = "300 Moedas", "epico", 3
            conn.execute('UPDATE usuarios SET moedas=moedas+300 WHERE id=?',(session['usuario_id'],))
        else: 
            item, rar, est = "1000 Moedas", "lendario", 5
            conn.execute('UPDATE usuarios SET moedas=moedas+1000 WHERE id=?',(session['usuario_id'],))
            
        conn.commit()
        return jsonify({'sucesso':True, 'item':item, 'raridade':rar, 'estrelas':est})
        
    except Exception as e: 
        return jsonify({'sucesso':False, 'msg':str(e)})
    finally: 
        conn.close()

# ------------------------------------------------------------------------------

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