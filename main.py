import asyncio
import random 
from datetime import datetime, timedelta
from typing import List, Optional

from fastapi import FastAPI, Depends, HTTPException, status, Security
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel, Field
from sqlalchemy import create_engine, Column, Integer, String, Float, ForeignKey, Boolean
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from passlib.context import CryptContext
from jose import JWTError, jwt
from faker import Faker
from pydantic import BaseModel, Field
from fastapi import HTTPException
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware




# ==========================================
# CONFIGURAÇÕES DE SEGURANÇA E BANCO DE DADOS
# ==========================================
SECRET_KEY = "sua_chave_super_secreta_em_producao_use_variavel_de_ambiente"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Banco de dados SQLite (em produção use PostgreSQL)
SQLALCHEMY_DATABASE_URL = "sqlite:///./ecommerce_seguro_v4.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()
fake = Faker('pt_BR')

# ==========================================
# MODELOS DE BANCO DE DADOS (ORM)
# ==========================================
class UserDB(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    # Dados sensíveis (Em produção, CPF e Cartão devem ser criptografados em repouso - AES-GCM)
    full_name = Column(String)
    cpf = Column(String, unique=True)
    address = Column(String)
    phone = Column(String)
    credit_card = Column(String) 

class ProductDB(Base):
    __tablename__ = "products"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    price = Column(Float)
    stock = Column(Integer)
    image_url = Column(String, nullable=True) 

class OrderDB(Base):
    __tablename__ = "orders"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    product_id = Column(Integer, ForeignKey("products.id"))
    status = Column(String, default="Aguardando Pagamento") # Aguardando, Em Transporte, Entregue

Base.metadata.create_all(bind=engine)

# ==========================================
# SCHEMAS DE VALIDAÇÃO (PYDANTIC - OWASP A03)
# ==========================================
class UserCreate(BaseModel):
    username: str
    # Exige no mínimo 8 caracteres
    password: str = Field(..., min_length=8)
    full_name: str
    # Exige exatamente 11 caracteres numéricos (0 a 9)
    cpf: str = Field(..., min_length=11, max_length=11, pattern=r'^\d{11}$')
    address: str
    phone: str
    credit_card: str

class UserResponse(BaseModel):
    username: str
    full_name: str
    # Omitindo propositalmente senha, CPF completo e cartão de crédito na resposta (Data Masking)
    class Config:
        orm_mode = True

class UserCreate(BaseModel):
    username: str
    password: str
    full_name: str
    cpf: str = Field(..., max_length=14)
    address: str
    phone: str
    credit_card: str

class ProductCreate(BaseModel):
    name: str
    price: float = Field(..., gt=0)
    stock: int = Field(..., ge=0)

# ==========================================
# UTILITÁRIOS DE SEGURANÇA
# ==========================================
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Credenciais inválidas",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    user = db.query(UserDB).filter(UserDB.username == username).first()
    if user is None:
        raise credentials_exception
    return user

# ==========================================
# TAREFA EM SEGUNDO PLANO: GERADOR DE USUÁRIOS
# ==========================================
app = FastAPI(title="Secure E-commerce API")
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Secure E-commerce API")

# Libera o navegador para acessar a API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
generator_state = {"is_active": False}

async def generate_users_loop():
    while True:
        if generator_state.get("is_active"):
            db = SessionLocal()
            try:
                # ==========================================
                # 1. CRIAÇÃO DO USUÁRIO
                # ==========================================
                fake_user = UserDB(
                    username=fake.user_name() + str(fake.random_int(1, 9999)),
                    hashed_password=get_password_hash("SenhaForte@123"),
                    full_name=fake.name(),
                    cpf=fake.cpf(),
                    address=fake.address(),
                    phone=fake.phone_number(),
                    credit_card=fake.credit_card_number()
                )
                db.add(fake_user)
                db.commit()
                db.refresh(fake_user)
                
                # 1.1 Imprime a criação do usuário
                hora_atual = datetime.now().strftime('%H:%M:%S')
                print(f"[{hora_atual}] 👤 Novo usuário criado: {fake_user.username}")
                
                # ==========================================
                # 2. COMPRA AUTOMÁTICA ALEATÓRIA
                # ==========================================
                produtos_disponiveis = db.query(ProductDB).filter(ProductDB.stock > 0).all()
                
                if produtos_disponiveis:
                    produto_escolhido = random.choice(produtos_disponiveis)
                    
                    produto_escolhido.stock -= 1
                    
                    novo_pedido = OrderDB(
                        user_id=fake_user.id,
                        product_id=produto_escolhido.id,
                        status=f"Em Transporte para: {fake_user.address}"
                    )
                    db.add(novo_pedido)
                    db.commit()
                    
                    # 2.1 Imprime a realização da compra
                    hora_atual = datetime.now().strftime('%H:%M:%S')
                    print(f"[{hora_atual}] 🛒 Compra realizada: {fake_user.username} comprou '{produto_escolhido.name}'")
                else:
                    hora_atual = datetime.now().strftime('%H:%M:%S')
                    print(f"[{hora_atual}] ⚠️ Compra ignorada: A loja está sem estoque.")
                    
            except Exception as e:
                db.rollback()
                hora_atual = datetime.now().strftime('%H:%M:%S')
                print(f"[{hora_atual}] ❌ Erro no gerador: {e}")
            finally:
                db.close()
        
        await asyncio.sleep(60)
@app.on_event("startup")
async def startup_event():
    db = SessionLocal()
    if not db.query(ProductDB).first():
        produtos_iniciais = [
            ProductDB(
                name="Notebook Seguro X1", 
                price=4500.00, 
                stock=500,
                image_url="https://p1-ofp.static.pub//fes/cms/2024/07/05/5zlebnmd2r6qoijtnbdue8c59529q2840002.png?width=328&height=328"
            ),
            ProductDB(
                name="CD Álbum Dookie - Green Day 1994", 
                price=85.00, 
                stock=500,
                image_url="https://encrypted-tbn3.gstatic.com/licensed-image?q=tbn:ANd9GcSSOGDvCKBM8Z3x_gYEyjXatSckvy70pMh7RWQN0MeOHMFAaOIR7mppoUQsZaF4qeNnA9UctLJhqgzOexI"
            ),
            ProductDB(
                name="Tênis Nike Air Jordan I", 
                price=1200.00, 
                stock=500,
                image_url="https://encrypted-tbn1.gstatic.com/licensed-image?q=tbn:ANd9GcR45Ht-V8RPwDvjDQHaGpVPjiZE4Z7oOWteLLpDnsgETZNqH9Zk9sljp7j57fVAZsH6dHjhfbk0sSAAJTY"
            ),
            ProductDB(
                name="Guitarra Jagstang Superfoda 6 cordas", 
                price=8500.00, 
                stock=500,
                image_url="https://encrypted-tbn0.gstatic.com/licensed-image?q=tbn:ANd9GcRbR44M-Ww4FTdcS4ZGfvES3oRZdLzzmkOeiuX44Tq3PcuZtBo9U9q35e0ISgNJOmIHGN779K-Hb99rhZI"
            )
        ]
        db.add_all(produtos_iniciais)
        db.commit()
    db.close()
    asyncio.create_task(generate_users_loop())
    
    # Inicia a tarefa de background
    asyncio.create_task(generate_users_loop())

# ==========================================
# ROTAS DA API
# ==========================================

# 1. CONTROLE DO GERADOR DE USUÁRIOS
@app.post("/api/generator/toggle")
def toggle_generator():
    """Liga ou desliga a geração de 1 usuário por minuto."""
    generator_state["is_active"] = not generator_state["is_active"]
    status_str = "Ligado" if generator_state["is_active"] else "Desligado"
    return {"message": f"Gerador de usuários {status_str}"}

# 2. SISTEMA DE LOGIN (AUTENTICAÇÃO)
@app.post("/token")
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(UserDB).filter(UserDB.username == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        # OWASP: Mensagem genérica para não revelar se o erro foi no usuário ou na senha
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuário ou senha incorretos",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/signup")
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    # Verifica se username ou CPF já existem
    if db.query(UserDB).filter(UserDB.username == user.username).first():
        raise HTTPException(status_code=400, detail="Nome de usuário já em uso")
    if db.query(UserDB).filter(UserDB.cpf == user.cpf).first():
        raise HTTPException(status_code=400, detail="CPF já cadastrado")
    
    # Salva o novo usuário com a senha criptografada
    novo_usuario = UserDB(
        username=user.username,
        hashed_password=get_password_hash(user.password),
        full_name=user.full_name,
        cpf=user.cpf,
        address=user.address,
        phone=user.phone,
        credit_card=user.credit_card
    )
    db.add(novo_usuario)
    db.commit()
    return {"message": "Usuário cadastrado com sucesso! Você já pode fazer login."}

# 3. PRODUTOS E COMPRAS (E-COMMERCE)
@app.get("/products")
def list_products(db: Session = Depends(get_db)):
    return db.query(ProductDB).all()

@app.post("/buy/{product_id}")
def buy_product(product_id: int, current_user: UserDB = Depends(get_current_user), db: Session = Depends(get_db)):
    product = db.query(ProductDB).filter(ProductDB.id == product_id).first()
    
    if not product:
        raise HTTPException(status_code=404, detail="Produto não encontrado")
    if product.stock <= 0:
        raise HTTPException(status_code=400, detail="Produto fora de estoque")
    
    # Processa a "compra" (reduz estoque)
    product.stock -= 1
    
    # Cria o pedido e define status de entrega
    order = OrderDB(
        user_id=current_user.id,
        product_id=product.id,
        status="Em Transporte para: " + current_user.address # Simula sistema de entrega
    )
    db.add(order)
    db.commit()
    db.refresh(order)
    
    return {
        "message": "Compra aprovada no cartão de final " + current_user.credit_card[-4:], 
        "order_id": order.id,
        "status_entrega": order.status
    }

# Rota para ver os próprios pedidos (Broken Access Control mitigado pelo JWT)
@app.get("/my-orders")
def my_orders(current_user: UserDB = Depends(get_current_user), db: Session = Depends(get_db)):
    orders = db.query(OrderDB).filter(OrderDB.user_id == current_user.id).all()
    return orders

@app.get("/admin/dump")
def dump_database(db: Session = Depends(get_db)):
    usuarios = [{"id": u.id, "usuario": u.username, "cpf": u.cpf} for u in db.query(UserDB).all()]
    produtos = [{"id": p.id, "nome": p.name, "estoque": p.stock} for p in db.query(ProductDB).all()]
    pedidos = [{"id": o.id, "status": o.status} for o in db.query(OrderDB).all()]
    
    return {
        "usuarios": usuarios,
        "produtos": produtos,
        "pedidos": pedidos
    }

async def compras_aleatorias_usuarios_antigos():
    while True:
        # Sorteia um tempo de espera entre 60 (1 min) e 180 segundos (3 min)
        tempo_espera = random.randint(60, 180)
        await asyncio.sleep(tempo_espera)
        
        # Abre a conexão com o banco
        db = SessionLocal()
        try:
            # Busca todos os usuários e produtos disponíveis
            usuarios = db.query(UserDB).all()
            produtos = db.query(ProductDB).filter(ProductDB.stock > 0).all()
            
            # Se houver usuários e produtos em estoque, faz a compra
            if usuarios and produtos:
                comprador = random.choice(usuarios)
                produto = random.choice(produtos)
                
                # Deduz do estoque
                produto.stock -= 1
                
                # Registra o pedido
                novo_pedido = OrderDB(
                    user_id=comprador.id,
                    product_id=produto.id,
                    status="Aprovado"
                )
                
                db.add(novo_pedido)
                db.commit()
                
                print(f"🛒 [AUTO] {comprador.username} comprou {produto.name}!")
        except Exception as e:
            print(f"Erro na compra automática: {e}")
        finally:
            db.close() # Fecha a conexão para não travar o banco


@app.on_event("startup")
async def iniciar_compras_background():
    # Cria a tarefa rodando em paralelo sem travar a API
    asyncio.create_task(compras_aleatorias_usuarios_antigos())
    print("🤖 Robô de compras aleatórias ativado!")
