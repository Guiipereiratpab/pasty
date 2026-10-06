import hashlib

def gerar_hashes_de_arquivo(nome_arquivo):
    try:
        # Abre o arquivo em modo de leitura
        with open(nome_arquivo, 'r', encoding='utf-8') as arquivo:
            # Lê as linhas e remove os espaços e quebras de linha invisíveis (como \n)
            senhas = [linha.strip() for linha in arquivo.readlines()]
        
        # Cabeçalho para a exibição dos resultados
        print(f"{'Senha Original':<20} | {'Hash MD5':<32} | {'Hash SHA1'}")
        print("-" * 100)

        for senha in senhas:
            # Ignora linhas em branco
            if not senha:
                continue
            
            # As bibliotecas de hash requerem que a string seja convertida para bytes
            senha_bytes = senha.encode('utf-8')
            
            # Gera os hashes
            md5_hash = hashlib.md5(senha_bytes).hexdigest()
            sha1_hash = hashlib.sha1(senha_bytes).hexdigest()
            
            # Exibe o resultado formatado
            print(f"{senha:<20} | {md5_hash} | {sha1_hash}")
            
    except FileNotFoundError:
        print(f"Erro: O arquivo '{nome_arquivo}' não foi encontrado.")
        print("Certifique-se de criar o arquivo e colocar as senhas nele.")

# Chamada da função
gerar_hashes_de_arquivo('piores_senhas.txt')