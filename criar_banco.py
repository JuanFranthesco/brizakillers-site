import sqlite3
from werkzeug.security import generate_password_hash

DB_NAME = 'brizakillers.db'
conn = sqlite3.connect(DB_NAME)
cursor = conn.cursor()

print("🔄 Iniciando a criação do banco de dados...")

# ==============================================================================
# 1. CRIAÇÃO DAS TABELAS
# ==============================================================================

# Tabela de Usuários (Com saldo de moedas para o Ranking)
cursor.execute('''
    CREATE TABLE IF NOT EXISTS usuarios (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome_completo TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        senha_hash TEXT NOT NULL,
        moedas INTEGER DEFAULT 500,
        tipo_usuario TEXT DEFAULT 'torcedor' -- 'admin' ou 'torcedor'
    );
''')

# Tabela de Cupons (Inventário do Jogador)
cursor.execute('''
    CREATE TABLE IF NOT EXISTS meus_cupons (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        usuario_id INTEGER,
        codigo TEXT,
        desconto INTEGER,
        origem TEXT, -- 'bau' ou 'loja'
        data_ganho DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(usuario_id) REFERENCES usuarios(id)
    );
''')

# Tabela de Produtos (Loja)
cursor.execute('''
    CREATE TABLE IF NOT EXISTS produtos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT NOT NULL,
        descricao TEXT,
        preco REAL NOT NULL,
        imagem_url TEXT,
        categoria TEXT
    );
''')

# Tabela de Partidas (Apostas)
cursor.execute('''
    CREATE TABLE IF NOT EXISTS partidas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        titulo TEXT NOT NULL,
        time_a TEXT NOT NULL,
        time_b TEXT NOT NULL,
        data_jogo TEXT,
        odd_a REAL DEFAULT 2.0,
        odd_b REAL DEFAULT 2.0,
        status TEXT DEFAULT 'aberta'
    );
''')

# Tabela de Apostas (Histórico)
cursor.execute('''
    CREATE TABLE IF NOT EXISTS apostas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        usuario_id INTEGER,
        partida_id INTEGER,
        valor_apostado INTEGER,
        time_escolhido TEXT,
        status TEXT DEFAULT 'pendente',
        FOREIGN KEY(usuario_id) REFERENCES usuarios(id),
        FOREIGN KEY(partida_id) REFERENCES partidas(id)
    );
''')

# Tabela de Jogadores (Equipe/Line-up)
cursor.execute('''
    CREATE TABLE IF NOT EXISTS jogadores (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nickname TEXT NOT NULL,
        nome_real TEXT,
        funcao TEXT,
        jogo TEXT,
        foto_url TEXT,
        instagram TEXT,
        stat_mira INTEGER,
        stat_inteligencia INTEGER,
        stat_mecanica INTEGER,
        mouse TEXT,
        main_char TEXT
    );
''')

# Tabela de Notícias (Blog)
cursor.execute('''
    CREATE TABLE IF NOT EXISTS noticias (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        titulo TEXT NOT NULL,
        resumo TEXT,
        conteudo TEXT,
        imagem_capa TEXT,
        autor TEXT DEFAULT 'Admin',
        data_postagem DATETIME DEFAULT CURRENT_TIMESTAMP
    );
''')

# ==============================================================================
# 2. INSERÇÃO DE DADOS (SEEDS)
# ==============================================================================

# --- USUÁRIOS ---
senha_admin = generate_password_hash("123456")
try:
    # Admin Principal
    cursor.execute("INSERT INTO usuarios (nome_completo, email, senha_hash, moedas, tipo_usuario) VALUES (?, ?, ?, ?, ?)",
                   ('Admin Supremo', 'admin@briza.com', senha_admin, 9999, 'admin'))
    
    # Usuários Fakes para o Ranking ficar bonito na apresentação
    cursor.execute("INSERT INTO usuarios (nome_completo, email, senha_hash, moedas) VALUES ('João Gamer', 'joao@teste.com', ?, 1500)", (senha_admin,))
    cursor.execute("INSERT INTO usuarios (nome_completo, email, senha_hash, moedas) VALUES ('Maria Pro', 'maria@teste.com', ?, 2300)", (senha_admin,))
    cursor.execute("INSERT INTO usuarios (nome_completo, email, senha_hash, moedas) VALUES ('Pedro Noob', 'pedro@teste.com', ?, 50)", (senha_admin,))
except:
    print("ℹ️ Usuários já existem.")

# --- PRODUTOS (LOJA MINIMALISTA) ---
cursor.execute("DELETE FROM produtos")
cursor.execute('''
    INSERT INTO produtos (nome, descricao, preco, imagem_url, categoria) VALUES 
    ('JERSEY PRO 2025', 'Uniforme oficial de competição. Tecnologia Dry-Fit.', 119.90, '/static/img/camisaoficial.png', 'uniformes'),
    ('BASIC TEE NEON', 'Camiseta casual Oversized. Algodão Premium.', 79.90, '/static/img/informal.png', 'casual'),
    ('HOODIE KILLERS', 'Moletom tático com acabamento em neon.', 189.90, '/static/img/moleton.png', 'inverno'),
    ('BONÉ DAD HAT', 'Boné desestruturado com logo bordado.', 59.90, '/static/img/bone.png', 'acessorios'),
    ('BERMUDA ATHLETIC', 'Short esportivo. Speed surface.', 89.90, '/static/img/shot.jpg', 'casual'),
    ('CROPPED PRO FEM', 'Baby look estilo jersey. Corte atlético.', 79.90, '/static/img/cropt.png', 'uniformes')
''')

# --- PARTIDAS (APOSTAS) ---
# ... (Mantenha o início igual)

# --- ATUALIZAÇÃO TABELA PARTIDAS ---
cursor.execute("DROP TABLE IF EXISTS partidas")
cursor.execute('''
    CREATE TABLE partidas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        titulo TEXT NOT NULL,
        time_a TEXT NOT NULL,
        time_b TEXT NOT NULL,
        data_jogo TEXT,
        odd_a REAL DEFAULT 2.0,
        odd_b REAL DEFAULT 2.0,
        status TEXT DEFAULT 'aberta',
        embed_url TEXT -- Novo campo para o link do vídeo (Twitch/Youtube)
    );
''')

# ... (Mantenha as outras tabelas iguais) ...

# SEEDS DAS PARTIDAS (Com links de vídeo reais para teste)
cursor.execute('''
    INSERT INTO partidas (titulo, time_a, time_b, data_jogo, odd_a, odd_b, embed_url) VALUES
    ('GRANDE FINAL REGIONAL', 'Briza Killers', 'Redes FC', 'AO VIVO AGORA', 1.8, 2.2, 'https://www.youtube.com/embed/LiveVideoID'), 
    ('SHOWMATCH DOS PROFESSORES', 'Prof. João', 'Prof. Maria', 'AMANHÃ 10:00', 5.0, 1.1, '')
''')

# DICA: No YouTube, pegue o ID de qualquer vídeo de Clash Royale para testar.
# Ex: https://www.youtube.com/embed/S7x5Z6w7s8s (Um vídeo aleatório de torneio)

# ... (Mantenha o commit e close)

cursor.execute("DROP TABLE IF EXISTS jogadores")
cursor.execute('''
    CREATE TABLE jogadores (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nickname TEXT NOT NULL,
        nome_real TEXT,
        funcao TEXT,
        jogo TEXT,
        foto_url TEXT,
        instagram TEXT,
        stat_mira INTEGER,
        stat_inteligencia INTEGER,
        stat_mecanica INTEGER,
        mouse TEXT,
        main_char TEXT,
        bio TEXT  -- Nova coluna para a história do jogador
    );
''')

# SEED COM BIOGRAFIAS
cursor.execute('''
    INSERT INTO jogadores (nickname, nome_real, funcao, jogo, foto_url, instagram, stat_mira, stat_inteligencia, stat_mecanica, mouse, main_char, bio) VALUES 
    
    ('REX', 'Juan', 'Capitão / Rush', 'Clash Royale', 'https://cdn-icons-png.flaticon.com/512/4140/4140048.png', '@juan_rex', 
    85, 95, 90, 'Logitech G Pro', 'Gigante Real', 
    'Conhecido por sua agressividade calculada. Rex lidera a Briza Killers desde 2023 e é especialista em quebrar defesas impenetráveis nos minutos finais.'),
    
    ('PRÍNCIPE', 'Paulo Junior', 'Rei de Soledade', 'Clash Royale', 'https://cdn-icons-png.flaticon.com/512/4140/4140047.png', '@paulo_soledade', 
    80, 99, 85, 'Razer Viper', 'Príncipe', 
    'O mestre do controle de lane. Paulo joga xadrez enquanto os outros jogam damas. Sua leitura de elixir do oponente é considerada a melhor do estado.'),
    
    ('PESTE BRANCA', 'Twilo', 'Dano Crítico', 'Brawl Stars', 'https://cdn-icons-png.flaticon.com/512/4140/4140037.png', '@twilo_peste', 
    95, 80, 92, 'HyperX Pulsefire', 'Crow', 
    'Movimentação imprevisível e mira laser. Twilo é o pesadelo dos suportes inimigos, sempre flanqueando e causando caos na backline.'),
    
    ('VORTEX', 'Ernandes', 'IGL / Estrategista', 'CS:GO', 'https://cdn-icons-png.flaticon.com/512/4140/4140051.png', '@ernandes_vortex', 
    88, 100, 85, 'Zowie EC2', 'AWP', 
    'A mente fria da equipe. Vortex estuda os adversários antes de cada partida e sempre tem uma granada preparada para anular a tática inimiga.'),
    
    ('THUNDER', 'Wandson', 'Entry Fragger', 'Valorant', 'https://cdn-icons-png.flaticon.com/512/145/145867.png', '@wandson_thunder', 
    99, 75, 96, 'Razer Deathadder', 'Jett', 
    'Reflexos sobre-humanos. Thunder é o primeiro a entrar e o último a cair. Seu estilo de jogo explosivo garante a vantagem numérica nos rounds decisivos.')
''')

# --- NOTÍCIAS (BLOG) ---
cursor.execute("DELETE FROM noticias")
cursor.execute('''
    INSERT INTO noticias (titulo, resumo, conteudo, imagem_capa) VALUES 
    ('VITÓRIA ESMAGADORA NA FINAL', 'A Briza Killers dominou o servidor e trouxe o troféu para casa.', 'Foi uma partida intensa, mas com a estratégia do Vortex e a mira do Thunder, conseguimos fechar o mapa em 13-0. Agradecemos a torcida!', 'https://cdn-icons-png.flaticon.com/512/5352/5352037.png'),
    ('NOVA COLEÇÃO NA LOJA', 'Confira os novos moletons e camisas oficiais.', 'A coleção 2025 chegou com tecnologia Dry-Fit e design cyberpunk. Membros do site tem desconto exclusivo usando os cupons do baú.', 'https://cdn-icons-png.flaticon.com/512/3081/3081072.png'),
    ('PENEIRA ABERTA: QUER SER PRO?', 'Estamos buscando novos talentos para a Academy.', 'Se você joga Clash Royale ou Valorant e tem rank alto, inscreva-se na nossa peneira. O link está na bio do Instagram.', 'https://cdn-icons-png.flaticon.com/512/1642/1642260.png')
''')

conn.commit()
conn.close()
print("✅ BANCO DE DADOS ATUALIZADO COM SUCESSO! 🚀")
print("Agora rode 'python app.py' e acesse o site.")