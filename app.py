from flask import Flask, render_template, request, redirect, session, url_for, flash, jsonify
import sqlite3
import random
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'chave_secreta_briza'
DB_NAME = "brizakillers.db"

def get_db_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

# --- ROTAS ---

@app.route('/')
def index():
    conn = get_db_connection()
    
    # Pega as 3 notícias mais recentes para o carrossel ou feed
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
    # Top 10 usuários mais ricos
    top_jogadores = conn.execute('SELECT nome_completo, moedas, tipo_usuario FROM usuarios ORDER BY moedas DESC LIMIT 10').fetchall()
    usuario = None
    if 'usuario_id' in session:
        usuario = conn.execute('SELECT * FROM usuarios WHERE id = ?', (session['usuario_id'],)).fetchone()
    conn.close()
    return render_template('ranking.html', jogadores=top_jogadores, usuario=usuario)

# (MANTENHA AQUI AS ROTAS ANTERIORES: login, cadastro, logout, perfil, loja, equipe, recompensas, torneios)
# Para economizar espaço, estou resumindo, mas você deve manter o código de login/cadastro/loja/apis igual ao anterior.
# COPIE AS ROTAS DO app.py ANTERIOR E COLE AQUI SE ELAS NÃO ESTIVEREM PRESENTES.

# --- REPETINDO LOGIN/CADASTRO PRA GARANTIR ---
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
        flash('Erro no login')
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
    produtos = conn.execute('SELECT * FROM produtos').fetchall()
    usuario = None
    if 'usuario_id' in session:
        usuario = conn.execute('SELECT * FROM usuarios WHERE id = ?', (session['usuario_id'],)).fetchone()
    conn.close()
    return render_template('loja.html', produtos=produtos, usuario=usuario)

@app.route('/produto/<int:id>')
def produto_detalhe(id):
    conn = get_db_connection()
    produto = conn.execute('SELECT * FROM produtos WHERE id = ?', (id,)).fetchone()
    
    # Sugestões (Outros produtos da mesma categoria)
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
    desconto = session.get('desconto_valor', 0) # Pega desconto se tiver aplicado
    total_final = total - (total * (desconto / 100))
    
    conn = get_db_connection()
    usuario = None
    if 'usuario_id' in session:
        usuario = conn.execute('SELECT * FROM usuarios WHERE id = ?', (session['usuario_id'],)).fetchone()
    conn.close()
    
    return render_template('carrinho.html', carrinho=session['carrinho'], total=total, desconto=desconto, total_final=total_final, usuario=usuario)

# --- APIS DO CARRINHO ---

@app.route('/api/add_cart', methods=['POST'])
def add_cart():
    data = request.json
    if 'carrinho' not in session: session['carrinho'] = []
    
    # Adiciona o item na lista da sessão
    session['carrinho'].append({
        'id': data['id'],
        'nome': data['nome'],
        'preco': float(data['preco']),
        'img': data['img']
    })
    session.modified = True
    return jsonify({'sucesso': True, 'qtd': len(session['carrinho'])})

@app.route('/api/limpar_carrinho')
def limpar_carrinho():
    session['carrinho'] = []
    session['desconto_valor'] = 0
    return redirect(url_for('carrinho'))

@app.route('/api/validar_cupom', methods=['POST'])
def validar_cupom():
    if 'usuario_id' not in session: return jsonify({'sucesso': False, 'msg': 'Faça login!'})
    
    codigo = request.json.get('codigo')
    conn = get_db_connection()
    
    # Verifica se o cupom existe E se pertence ao usuário
    cupom = conn.execute('SELECT * FROM meus_cupons WHERE codigo = ? AND usuario_id = ?', (codigo, session['usuario_id'])).fetchone()
    conn.close()
    
    if cupom:
        session['desconto_valor'] = cupom['desconto'] # Salva o % na sessão
        return jsonify({'sucesso': True, 'desconto': cupom['desconto']})
    else:
        return jsonify({'sucesso': False, 'msg': 'Cupom inválido ou não é seu!'})

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
    # Pega todas as partidas
    todas_partidas = conn.execute('SELECT * FROM partidas WHERE status = "aberta"').fetchall()
    
    # Separa a primeira para ser o "Destaque" (Main Event)
    destaque = todas_partidas[0] if todas_partidas else None
    lista_jogos = todas_partidas[1:] if len(todas_partidas) > 1 else []
    
    usuario = conn.execute('SELECT moedas FROM usuarios WHERE id = ?', (session['usuario_id'],)).fetchone()
    conn.close()
    
    return render_template('torneios.html', destaque=destaque, partidas=lista_jogos, saldo=usuario['moedas'])

@app.route('/recompensas')
def recompensas():
    if 'usuario_id' not in session: return redirect(url_for('login'))
    return render_template('recompensas.html')

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

@app.route('/api/comprar_cupom', methods=['POST'])
def comprar_cupom():
    if 'usuario_id' not in session: return jsonify({'sucesso':False})
    data = request.json
    conn = get_db_connection()
    try:
        u = conn.execute('SELECT moedas FROM usuarios WHERE id=?',(session['usuario_id'],)).fetchone()
        cost = data.get('custo')
        if u['moedas'] < cost: return jsonify({'sucesso':False, 'msg':'Pobre'})
        conn.execute('UPDATE usuarios SET moedas=moedas-? WHERE id=?',(cost, session['usuario_id']))
        conn.execute('INSERT INTO meus_cupons (usuario_id, codigo, desconto, origem) VALUES (?,?,?,?)',(session['usuario_id'], f"LOJA{data.get('desconto')}-{random.randint(100,999)}", data.get('desconto'), 'loja'))
        conn.commit()
        return jsonify({'sucesso':True, 'novo_saldo':u['moedas']-cost, 'codigo':'OK'})
    except Exception as e: return jsonify({'sucesso':False, 'msg':str(e)})
    finally: conn.close()

@app.route('/loja-moedas')
def loja_moedas():
    """Loja de Trocas (Gastar Moedas por Cupons)"""
    if 'usuario_id' not in session: return redirect(url_for('login'))
    
    conn = get_db_connection()
    usuario = conn.execute('SELECT * FROM usuarios WHERE id = ?', (session['usuario_id'],)).fetchone()
    conn.close()
    
    return render_template('loja_moedas.html', usuario=usuario)

# --- ÁREA ADMINISTRATIVA (GOD MODE) ---

@app.route('/admin')
def admin_panel():
    # 1. Segurança: Verifica se está logado e se é admin
    if 'usuario_id' not in session: return redirect(url_for('login'))
    
    conn = get_db_connection()
    user = conn.execute('SELECT * FROM usuarios WHERE id = ?', (session['usuario_id'],)).fetchone()
    
    # Se não for admin, chuta pra fora
    if user['tipo_usuario'] != 'admin':
        flash('Acesso negado! Apenas a staff pode entrar aqui.')
        return redirect(url_for('perfil'))
    
    # Pega dados para listar
    noticias = conn.execute('SELECT * FROM noticias ORDER BY id DESC').fetchall()
    partidas = conn.execute('SELECT * FROM partidas ORDER BY id DESC').fetchall()
    conn.close()
    
    return render_template('admin.html', usuario=user, noticias=noticias, partidas=partidas)

@app.route('/admin/criar_noticia', methods=['POST'])
def criar_noticia():
    if 'usuario_id' not in session: return jsonify({'sucesso': False})
    
    titulo = request.form['titulo']
    texto = request.form['conteudo']
    img = request.form['imagem']
    
    conn = get_db_connection()
    conn.execute('INSERT INTO noticias (titulo, conteudo, imagem_capa) VALUES (?, ?, ?)', (titulo, texto, img))
    conn.commit()
    conn.close()
    return redirect(url_for('admin_panel'))

@app.route('/admin/criar_partida', methods=['POST'])
def criar_partida():
    if 'usuario_id' not in session: return jsonify({'sucesso': False})
    
    titulo = request.form['titulo']
    time_a = request.form['time_a']
    time_b = request.form['time_b']
    odd_a = request.form['odd_a']
    odd_b = request.form['odd_b']
    link = request.form['link'] # Link do YouTube
    
    conn = get_db_connection()
    conn.execute('''
        INSERT INTO partidas (titulo, time_a, time_b, data_jogo, odd_a, odd_b, embed_url, status) 
        VALUES (?, ?, ?, "AO VIVO", ?, ?, ?, "aberta")
    ''', (titulo, time_a, time_b, odd_a, odd_b, link))
    conn.commit()
    conn.close()
    return redirect(url_for('admin_panel'))

@app.route('/admin/deletar/<tipo>/<int:id>')
def deletar_item(tipo, id):
    if 'usuario_id' not in session: return redirect(url_for('login'))
    
    conn = get_db_connection()
    # Verifica se é admin de novo por segurança
    u = conn.execute('SELECT tipo_usuario FROM usuarios WHERE id=?', (session['usuario_id'],)).fetchone()
    if u['tipo_usuario'] == 'admin':
        if tipo == 'noticia':
            conn.execute('DELETE FROM noticias WHERE id = ?', (id,))
        elif tipo == 'partida':
            conn.execute('DELETE FROM partidas WHERE id = ?', (id,))
        conn.commit()
    
    conn.close()
    return redirect(url_for('admin_panel'))

if __name__ == '__main__':
    app.run(debug=True)