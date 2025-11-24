import sqlite3
from werkzeug.security import generate_password_hash

DB_NAME = 'brizakillers.db'
conn = sqlite3.connect(DB_NAME)
cursor = conn.cursor()

print("🔄 Recriando Banco de Dados Completo...")

# ==============================================================================
# 1. LIMPEZA E CRIAÇÃO DAS TABELAS
# ==============================================================================

# Apaga tabelas antigas para garantir que a estrutura nova seja criada
cursor.executescript('''
    DROP TABLE IF EXISTS usuarios;
    DROP TABLE IF EXISTS meus_cupons;
    DROP TABLE IF EXISTS produtos;
    DROP TABLE IF EXISTS partidas;
    DROP TABLE IF EXISTS apostas;
    DROP TABLE IF EXISTS jogadores;
    DROP TABLE IF EXISTS noticias;
    DROP TABLE IF EXISTS candidatos;
''')

# Tabela de Usuários (Com trava de data para o Baú)
cursor.execute('''
    CREATE TABLE usuarios (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome_completo TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        senha_hash TEXT NOT NULL,
        moedas INTEGER DEFAULT 500,
        tipo_usuario TEXT DEFAULT 'torcedor',
        ultimo_bau TEXT -- Guarda a data YYYY-MM-DD da última abertura
    );
''')

# Tabela de Cupons
cursor.execute('''
    CREATE TABLE meus_cupons (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        usuario_id INTEGER,
        codigo TEXT,
        desconto INTEGER,
        origem TEXT,
        data_ganho DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(usuario_id) REFERENCES usuarios(id)
    );
''')

# Tabela de Produtos
cursor.execute('''
    CREATE TABLE produtos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT NOT NULL,
        descricao TEXT,
        preco REAL NOT NULL,
        imagem_url TEXT,
        categoria TEXT
    );
''')

# Tabela de Partidas (Com Embed de Vídeo)
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
        embed_url TEXT -- Link do YouTube/Twitch
    );
''')

# Tabela de Apostas
cursor.execute('''
    CREATE TABLE apostas (
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

# Tabela de Jogadores (Com Stats e Bio)
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
        bio TEXT
    );
''')

# Tabela de Notícias
cursor.execute('''
    CREATE TABLE noticias (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        titulo TEXT NOT NULL,
        resumo TEXT,
        conteudo TEXT,
        imagem_capa TEXT,
        autor TEXT DEFAULT 'Admin',
        data_postagem DATETIME DEFAULT CURRENT_TIMESTAMP
    );
''')

# Tabela de Candidatos (Peneira)
cursor.execute('''
    CREATE TABLE candidatos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        usuario_id INTEGER,
        nick_jogo TEXT,
        rank_atual TEXT,
        discord TEXT,
        motivo TEXT,
        data_inscricao DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(usuario_id) REFERENCES usuarios(id)
    );
''')

# ==============================================================================
# 2. INSERÇÃO DE DADOS (SEEDS)
# ==============================================================================

# --- USUÁRIOS ---
senha_admin = generate_password_hash("123456")
cursor.execute("INSERT INTO usuarios (nome_completo, email, senha_hash, moedas, tipo_usuario) VALUES (?, ?, ?, ?, ?)",
               ('Admin Supremo', 'admin@briza.com', senha_admin, 9999, 'admin'))
cursor.execute("INSERT INTO usuarios (nome_completo, email, senha_hash, moedas) VALUES ('João Gamer', 'joao@teste.com', ?, 1500)", (senha_admin,))
cursor.execute("INSERT INTO usuarios (nome_completo, email, senha_hash, moedas) VALUES ('Maria Pro', 'maria@teste.com', ?, 2300)", (senha_admin,))

# --- PRODUTOS (IMAGENS NOVAS) ---
cursor.execute('''
    INSERT INTO produtos (nome, descricao, preco, imagem_url, categoria) VALUES 
    ('JERSEY PRO 2025', 'Uniforme oficial de competição. Tecnologia Dry-Fit.', 119.90, '/static/img/camisaoficial.png', 'uniformes'),
    ('BASIC TEE NEON', 'Camiseta casual Oversized. Algodão Premium.', 79.90, '/static/img/informal.png', 'casual'),
    ('HOODIE KILLERS', 'Moletom tático com acabamento em neon.', 189.90, '/static/img/moleton.png', 'inverno'),
    ('BONÉ DAD HAT', 'Boné desestruturado com logo bordado.', 59.90, '/static/img/bone.png', 'acessorios'),
    ('BERMUDA ATHLETIC', 'Short esportivo. Speed surface.', 89.90, '/static/img/shot.jpg', 'casual'),
    ('CROPPED PRO FEM', 'Baby look estilo jersey. Corte atlético.', 79.90, '/static/img/cropt.png', 'uniformes')
''')

# --- PARTIDAS (COM VÍDEO) ---
cursor.execute('''
    INSERT INTO partidas (titulo, time_a, time_b, data_jogo, odd_a, odd_b, embed_url) VALUES
    ('GRANDE FINAL REGIONAL', 'Briza Killers', 'Redes FC', 'AO VIVO AGORA', 1.8, 2.2, 'https://www.youtube.com/embed/S7x5Z6w7s8s?autoplay=1&mute=1'), 
    ('SHOWMATCH DOS PROFESSORES', 'Prof. João', 'Prof. Maria', 'AMANHÃ 10:00', 5.0, 1.1, '')
''')

# --- JOGADORES (EQUIPE OFICIAL) ---
cursor.execute('''
    INSERT INTO jogadores (nickname, nome_real, funcao, jogo, foto_url, instagram, stat_mira, stat_inteligencia, stat_mecanica, mouse, main_char, bio) VALUES 
    
    ('REX', 'Juan', 'Capitão / Rush', 'Clash Royale', 'https://cdn-icons-png.flaticon.com/512/4140/4140048.png', '@juan_rex', 
    88, 95, 90, 'Logitech G Pro', 'Gigante Real', 
    'Líder nato. Especialista em leitura de elixir e contra-ataques rápidos nos momentos de pressão.'),
    
    ('PRÍNCIPE', 'Paulo Junior', 'Rei de Soledade', 'Clash Royale', 'https://cdn-icons-png.flaticon.com/512/4140/4140047.png', '@paulo_soledade', 
    80, 99, 85, 'Razer Viper', 'Príncipe', 
    'O estrategista. Joga de forma defensiva até encontrar a brecha perfeita para punir o oponente.'),
    
    ('PESTE BRANCA', 'Twilo', 'Dano Crítico', 'Brawl Stars', 'https://cdn-icons-png.flaticon.com/512/4140/4140037.png', '@twilo_peste', 
    96, 80, 92, 'HyperX Pulsefire', 'Crow', 
    'Agressividade pura. Conhecido por jogadas arriscadas que decidem campeonatos.'),
    
    ('VORTEX', 'Ernandes', 'IGL / Controle', 'CS:GO', 'https://cdn-icons-png.flaticon.com/512/4140/4140051.png', '@ernandes_vortex', 
    85, 100, 85, 'Zowie EC2', 'AWP', 
    'Mente fria. Controla o mapa e dita o ritmo da partida para o time com calls precisas.'),
    
    ('THUNDER', 'Wandson', 'Entry Fragger', 'Valorant', 'https://cdn-icons-png.flaticon.com/512/145/145867.png', '@wandson_thunder', 
    99, 75, 98, 'Razer Deathadder', 'Jett', 
    'Reflexos insanos. O primeiro a entrar no bomb e garantir a vantagem numérica.')
''')

# --- NOTÍCIAS ---
cursor.execute('''
    INSERT INTO noticias (titulo, resumo, conteudo, imagem_capa) VALUES 
    ('VITÓRIA ESMAGADORA NA FINAL', 'A Briza Killers dominou o servidor e trouxe o troféu para casa.', 'Foi uma partida intensa, mas com a estratégia do Vortex e a mira do Thunder, conseguimos fechar o mapa em 13-0. Agradecemos a torcida!', 'https://cdn-icons-png.flaticon.com/512/5352/5352037.png'),
    ('NOVA COLEÇÃO NA LOJA', 'Confira os novos moletons e camisas oficiais.', 'A coleção 2025 chegou com tecnologia Dry-Fit e design cyberpunk. Membros do site tem desconto exclusivo usando os cupons do baú.', 'https://cdn-icons-png.flaticon.com/512/3081/3081072.png'),
    ('PENEIRA ABERTA: QUER SER PRO?', 'Estamos buscando novos talentos para a Academy.', 'Se você joga Clash Royale ou Valorant e tem rank alto, inscreva-se na nossa peneira.', 'https://cdn-icons-png.flaticon.com/512/1642/1642260.png')
''')

conn.commit()
conn.close()
print("✅ BANCO DE DADOS ATUALIZADO COM SUCESSO! 🚀")