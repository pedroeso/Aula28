import mysql.connector               # Driver oficial do MySQL para Python
import pandas as pd                  # Manipulação de dados (Dataframe, )
import matplotlib.pyplot as plt      # Criação de gráficos
from mysql.connector import Error    # Exceção específica do conector MySQL

# --------------------------------------------------------------------------
# Dados que serão inseridos pelo Python
# A ordem importa: primeiro as tabelas "pai", depois as "filhas"
#    cursos -> alunos -> disciplinas -> notas 
# --------------------------------------------------------------------------



# 3) Disciplinas (ids gerados: 1 a 6) — o último campo é o id_curso (FK)
disciplinas = [
    # (nome_disciplina, carga_horaria, id_curso)
    ('Lógica de Programação', 80, 1),  # id 1
    ('Banco de Dados',        60, 1),  # id 2
    ('Gestão Financeira',     60, 2),  # id 3
    ('Marketing',             40, 2),  # id 4
    ('Anatomia',              80, 3),  # id 5
    ('Farmacologia',          60, 3),  # id 6
]

# 4) Notas — cada aluno recebe nota nas disciplinas do seu curso
notas = [
    # (id_aluno, id_disciplina, nota, data_avaliacao)
    # Informática (alunos 1, 2, 5, 6, 10 | disciplinas 1 e 2)
    (1, 1, 8.5, '2026-06-30'), (1, 2, 9.0, '2026-06-30'),
    (2, 1, 7.0, '2026-06-30'), (2, 2, 6.5, '2026-06-30'),
    (5, 1, 9.5, '2026-06-30'), (5, 2, 8.0, '2026-06-30'),
    (6, 1, 6.0, '2026-06-30'), (6, 2, 7.5, '2026-06-30'),
    (10, 1, 8.0, '2026-06-30'), (10, 2, 8.5, '2026-06-30'),
    # Administração (alunos 3, 8 | disciplinas 3 e 4)
    (3, 3, 7.5, '2026-06-30'), (3, 4, 8.0, '2026-06-30'),
    (8, 3, 6.5, '2026-06-30'), (8, 4, 9.0, '2026-06-30'),
    # Enfermagem (alunos 4, 7, 9 | disciplinas 5 e 6)
    (4, 5, 9.0, '2026-06-30'), (4, 6, 8.5, '2026-06-30'),
    (7, 5, 7.0, '2026-06-30'), (7, 6, 6.0, '2026-06-30'),
    (9, 5, 8.5, '2026-06-30'), (9, 6, 9.5, '2026-06-30'),
]

try:
    # Estabelece a conexão
    conexao = mysql.connector.connect(
        host='localhost',       
        user='root',
        password='',
        database='escola'
    )

    if conexao.is_connected():
        print("Conectado com sucesso!")

        cursor = conexao.cursor()
        inserts = [
        ("disciplinas",
        "INSERT IGNORE INTO disciplinas (nome_disciplina, carga_horaria, id_curso)"
        "VALUES (%s, %s, %s)",
        disciplinas),
        ("notas",
        "INSERT IGNORE INTO notas (id_aluno, id_disciplina, nota, data_avaliacao)"
        "VALUES (%s, %s, %s, %s)",
        notas),
        ]

        # Executa na ordem: pai antes de filha
        for tabela, sql, valores in inserts:
            cursor.executemany(sql, valores)     # varios INSERTs de uma vez
            conexao.commit()                     # sem commit() nada é gravado
            print(f"{tabela}: {cursor.rowcount} linha(s) inserida(s)")


        # -------------------------------------------------------------
        # 3) Exportar os dados para um DataFrame
        # -------------------------------------------------------------
        # JOIN das 4 tabelas: cada linha = uma nota de um aluno em uma
        # disciplina, com o nome do curso

        consulta = """
            SELECT a.id_aluno, a.nome, c.nome_curso, c.turno,
                   d.nome_disciplina, n.nota, n.data_avaliacao
            FROM notas n
            INNER JOIN alunos      a ON n.id_aluno            = a.id_aluno
            INNER JOIN disciplinas d ON n.id_disciplina        = d.id_disciplina
            INNER JOIN cursos      c ON a.id_curso             = c.id_curso
            ORDER BY c.nome_curso, a.nome, d.nome_disciplina
        """

        cursor.execute(consulta)

        # fetchall() traz as linhas; cursor.column_names traz os nomes das colunas
        df = pd.DataFrame(cursor.fetchall(), columns=cursor.column_names)

        df["nota"] = df["nota"].astype(float)

        print("\nDataframe (notas + alunos + disciplinas + cursos):")
        print(df)

        # Salva em CSV ("utf-8-sig" faz o Excel abrir os acentos corretamente)
        df.to_csv("notas_alunos.csv", index=False, encoding="utf-8-sig")
        print("\nArquivo notas_alunos.csv gerado!")


except Error as e:
    print(f"Erro ao conectar ou executar: {e}")
        
finally:
    #Fecha o cursor (se foi criado)
    if 'cursor' in locals():
        try:
            cursor.close()
        except Exception:
            pass  #Se já estiver fechado ou ocorrer erro, ignora
            
            #Fecha a conexão (se foi criada e ainda está conectada)
    if 'conexao' in locals() and conexao.is_connected():
        conexao.close()
        print("Conexão encerrada.")

# -----------------------------------------------------------
# Só desenha se o DataFrame foi criado e tem dados
if 'df' in locals() and not df.empty:
    # Gráfico 1: quantos alunos há em cada curso
    # nunique() conta cada aluno uma vez só (ele aparece uma vez por nota)
    alunos_por_curso = df.groupby("nome_curso")["id_aluno"].nunique().sort_values()

    # Gráfico 2: média das notas em cada disciplina
    media_por_disciplina = df.groupby("nome_disciplina")["nota"].mean().sort_values()

    # Uma figura com dois gráficos lado a lado
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 5))

    bars1 = ax1.barh(alunos_por_curso.index, alunos_por_curso.values, color= "#2a7ab9")
    ax1.bar_label(bars1, padding=3)
    ax1.set_title("Alunos matriculados por curso")
    ax1.set_xlabel("Quantidade de alunos")
    ax1.set_xlim(0, alunos_por_curso.max() + 1)   # espaço para o rótulo

    bars2 = ax2.barh(media_por_disciplina.index, media_por_disciplina.values, color= "#2a7ab9")
    ax2.bar_label(bars2, fmt="%.2f", padding=3)
    ax2.set_title("Média das notas por disciplina")
    ax2.set_xlabel("Nota média (0 a 10)")
    ax2.set_xlim(0, 10.5)   

    plt.tight_layout()
    plt.savefig("graficos_escola.png", dpi=150)  # salva a imagem
    plt.show()






