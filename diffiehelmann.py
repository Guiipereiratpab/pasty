import random

# --- Funções Auxiliares Matemáticas ---

def is_prime(num):
    """Verifica se um número é primo."""
    if num < 2:
        return False
    for i in range(2, int(num**0.5) + 1):
        if num % i == 0:
            return False
    return True

def generate_prime(min_val=100, max_val=1000):
    """Gera um número primo aleatório dentro de um intervalo."""
    primes = [i for i in range(min_val, max_val) if is_prime(i)]
    return random.choice(primes)

def get_prime_factors(num):
    """Encontra os fatores primos de um número."""
    factors = set()
    d = 2
    while d * d <= num:
        while (num % d) == 0:
            factors.add(d)
            num //= d
        d += 1
    if num > 1:
        factors.add(num)
    return factors

def find_generator(p):
    """Encontra uma raiz primitiva (Gerador G) para o primo p."""
    if p == 2:
        return 1
    p_minus_1 = p - 1
    factors = get_prime_factors(p_minus_1)
    
    for g in range(2, p):
        is_generator = True
        for factor in factors:
            # Se g^((p-1)/fator) mod p == 1, então não é raiz primitiva
            if pow(g, p_minus_1 // factor, p) == 1:
                is_generator = False
                break
        if is_generator:
            return g
    return None

# --- Algoritmo Diffie-Hellman ---

print("=== Troca de Chaves Diffie-Hellman ===")

# 1. Recebe as senhas (chaves privadas) de A e B
senha_a = int(input("Digite a senha (chave privada) da pessoa A: "))
senha_b = int(input("Digite a senha (chave privada) da pessoa B: "))

# 2. O programa gera N (Primo) e G (Gerador)
N = generate_prime(100, 1000) # Usando primos pequenos para demonstração
G = find_generator(N)

print("\n--- Parâmetros Públicos Gerados ---")
print(f"Módulo Primo (N): {N}")
print(f"Base/Gerador (G): {G}")

# 3. Cálculo das chaves públicas (o que trafega na rede)
# Fórmula: Chave Pública = (G ^ chave_privada) mod N
pub_a = pow(G, senha_a, N)
pub_b = pow(G, senha_b, N)

print("\n--- Chaves Públicas (Compartilhadas na rede) ---")
print(f"Chave Pública de A: {pub_a}")
print(f"Chave Pública de B: {pub_b}")

# 4. Cálculo da chave secreta compartilhada
# Fórmula: Chave Compartilhada = (Chave_Publica_Recebida ^ própria_chave_privada) mod N
chave_secreta_a = pow(pub_b, senha_a, N)
chave_secreta_b = pow(pub_a, senha_b, N)

print("\n--- Resultados Finais ---")
print(f"Senha original (Chave Privada) de A: {senha_a}")
print(f"Senha original (Chave Privada) de B: {senha_b}")

if chave_secreta_a == chave_secreta_b:
    print(f"\nSucesso! A chave compartilhada gerada é idêntica para ambos: {chave_secreta_a}")
else:
    print("\nErro: As chaves geradas não coincidem.")