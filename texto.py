# Define o tamanho exato de caracteres desejado
tamanho_desejado = 101891

# Cria uma string com a letra "A" repetida 101.891 vezes
texto = "A" * tamanho_desejado

# Salva o resultado em um arquivo .txt
with open("texto_teste.txt", "w", encoding="utf-8") as arquivo:
    arquivo.write(texto)

print(f"Arquivo gerado com sucesso! Tamanho: {len(texto)} caracteres.")