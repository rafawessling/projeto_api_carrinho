from fastapi import FastAPI
from typing import List
from pydantic import BaseModel

app = FastAPI()

OK = "OK"
FALHA = "FALHA"

# Classe representando os dados do endereço do cliente
class Endereco(BaseModel):
    id: int
    rua: str
    cep: str
    cidade: str
    estado: str


# Classe representando os dados do cliente
class Usuario(BaseModel):
    id: int
    nome: str
    email: str
    senha: str
    endereco: Endereco = {}


# Classe representando a lista de endereços de um cliente
class ListaDeEnderecosDoUsuario(BaseModel):
    usuario: int
    endereco: Endereco = {}


# Classe representando os dados do produto
class Produto(BaseModel):
    id: int
    nome: str
    descricao: str
    preco: float
    

db_usuarios = {}
db_produtos = {}
db_end = {}        # enderecos_dos_usuarios
db_carrinhos = {}

#--------------------------------------------------
#Persistência e Regras
#--------------------------------------------------

def persistencia_cadastrar_usuario(usuario):
    if usuario.id in db_usuarios:
        return FALHA
    db_usuarios[usuario.id] = usuario
    return OK
  
def persistencia_listar_usuarios():
    return db_usuarios

def persistencia_pesquisar_nome_usuario(nome):
    usuarios = {}
    for key, value in db_usuarios.items():
        if db_usuarios[key].nome == nome:
            usuarios[key] = value
            
    if usuarios:
        return usuarios
    return FALHA

def persistencia_retornar_emails(dominio):
    emails = {}
    for key, _value in db_usuarios.items():
        if db_usuarios[key].email.split('@')[1].replace(".com", "") == dominio:
            emails[key] = db_usuarios[key].email
        
    if emails:
        return emails
    return FALHA

def persistencia_pesquisar_codigo_usuario(id_usuario):
    if id_usuario in db_usuarios:
        return db_usuarios[id_usuario]
    return FALHA

def persistencia_deletar_usuario(id_usuario):
    if id_usuario in db_usuarios:
        db_usuarios.pop(id_usuario)
        return OK
    return FALHA

def persistencia_criar_endereco(end):
    if end.usuario not in db_end:
        db_end[end.usuario] = [end.endereco]
    else:
        for address in db_end[end.usuario]:
            if end.endereco.id == address.id:
                return FALHA
        db_end[end.usuario].append(end.endereco)
        
    db_usuarios[end.usuario].endereco = db_end[end.usuario]
    return OK

def persistencia_listar_enderecos_usuario(id_usuario):
    if id_usuario in db_end:
        return db_end[id_usuario]
    return FALHA

def persistencia_deletar_endereco(id_endereco, id_usuario):
    if id_usuario in db_end:
        for index, end in enumerate(db_end[id_usuario]):
            if end.id == id_endereco:
                db_end[id_usuario].pop(index)
                return OK
    return FALHA

def persistencia_criar_produto(produto):
    if produto.id in db_produtos:
        return FALHA
    db_produtos[produto.id] = produto
    return OK

def persistencia_listar_produtos():
    return db_produtos

def persistencia_deletar_produto(id_produto):
    if id_produto in db_produtos:
        for _key, produtos_p_user in db_carrinhos.items():
            for index, produtos in enumerate(produtos_p_user["produtos"]):
                if id_produto in produtos:
                    produtos_p_user["preco_total"] -= db_produtos[id_produto].preco * produtos["quantidade"]
                    produtos_p_user["quantidade_de_produtos"] -= produtos["quantidade"]
                    produtos_p_user["produtos"].pop(index)
    
        db_produtos.pop(id_produto)
        return OK
    return FALHA

def persistencia_adicionar_carrinho(id_usuario, id_produto):
    # Verificar se usuario e produto existem
    if id_usuario not in db_usuarios or id_produto not in db_produtos:
        return FALHA
            
    if id_usuario not in db_carrinhos:
        # Criar carrinho
        carrinho = {
            "id_usuario": id_usuario,
            "produtos": [{id_produto: db_produtos[id_produto],
                          "quantidade": 1,
                          "preco": db_produtos[id_produto].preco}],
            "preco_total": db_produtos[id_produto].preco,
            "quantidade_de_produtos": 1
        }
        db_carrinhos[id_usuario] = carrinho
    else:
        #Adicionar outro produto ao carrinho
        inserido = 0
        produto_encontrado = 0
        for _index, produto in enumerate(db_carrinhos[id_usuario]["produtos"]):
            if id_produto in produto:
                produto_encontrado = 1
                produto["quantidade"] += 1
                produto["preco"] += db_produtos[id_produto].preco
                inserido = 1
        
        if not produto_encontrado:
            produto_dict = {
                id_produto: db_produtos[id_produto],
                "quantidade": 1,
                "preco": db_produtos[id_produto].preco
            }
            db_carrinhos[id_usuario]["produtos"].append(produto_dict)
            inserido = 1
            
        if inserido:
            db_carrinhos[id_usuario]["quantidade_de_produtos"] += 1
            db_carrinhos[id_usuario]["preco_total"] += db_produtos[id_produto].preco
            
    return OK

def persistencia_carrinho_usuario(id_usuario):
    if id_usuario not in db_carrinhos:
        return FALHA
    return db_carrinhos[id_usuario]

def persistencia_total_carrinho(id_usuario):
    if id_usuario not in db_carrinhos:
        return FALHA

    total_carrinho = {
        "valor_total": db_carrinhos[id_usuario]["preco_total"],
        "quantidade_items": db_carrinhos[id_usuario]["quantidade_de_produtos"]
    }
    
    return total_carrinho

def persistencia_deletar_carrinho_usuario(id_usuario):
    if id_usuario not in db_carrinhos:
        return FALHA
    db_carrinhos.pop(id_usuario)
    return OK

#--------------------------------------------------
#API Rest / Controlador
#--------------------------------------------------

#Seja bem vinda
@app.get("/")
async def bem_vinda():
    site = "Seja bem vinda"
    return site.replace('\n', '')

#Criar usuário
@app.post("/usuario")
async def criar_usuario(usuario: Usuario):
    usuario = persistencia_cadastrar_usuario(usuario)
    return usuario

#Extra: listar todos os usuários
@app.get("/usuario")
async def listar_usuarios():
    return persistencia_listar_usuarios()

#Pesquisar usuário pelo nome
@app.get("/usuario/search")
async def retornar_usuario_com_nome(nome: str):
    return persistencia_pesquisar_nome_usuario(nome)

#Listar e-mails com dominio igual
@app.get("/usuario/email/search")
async def retornar_emails(dominio: str):
    return persistencia_retornar_emails(dominio)

#Pesquisar usuário pelo id
@app.get("/usuario/{id_usuario}")
async def retornar_usuario(id_usuario: int):
    return persistencia_pesquisar_codigo_usuario(id_usuario)

#Deletar pelo código
@app.delete("/usuario/{id_usuario}")
async def deletar_usuario(id_usuario: int):
    return persistencia_deletar_usuario(id_usuario)

#Criar endereco
@app.post("/endereco")
async def criar_endereco(end: ListaDeEnderecosDoUsuario):
    return persistencia_criar_endereco(end)

#Listar todos os enderecos do usuário
@app.get("/usuario/{id_usuario}/endereco")
async def retornar_enderecos_do_usuario(id_usuario: int):
    return persistencia_listar_enderecos_usuario(id_usuario)

@app.delete("/usuario/{id_usuario}/endereco/{id_endereco}")
async def deletar_endereco(id_endereco: int, id_usuario: int):
    return persistencia_deletar_endereco(id_endereco, id_usuario)

#Criar produto
@app.post("/produto")
async def criar_produto(produto: Produto):
    produto = persistencia_criar_produto(produto)
    return produto

#Extra: listar todos os produtos
@app.get("/produto")
async def listar_produtos():
    return persistencia_listar_produtos()

#Deletar produto pelo código
@app.delete("/produto/{id_produto}")
async def deletar_produto(id_produto: int):
    return persistencia_deletar_produto(id_produto)

#Adicionar produto ao carrinho
@app.post("/carrinho/{id_usuario}/{id_produto}")
async def adicionar_carrinho(id_usuario: int, id_produto: int):
    return persistencia_adicionar_carrinho(id_usuario, id_produto)

#Mostrar carrinho usuario
@app.get("/carrinho/{id_usuario}")
async def retornar_carrinho(id_usuario: int):
    return persistencia_carrinho_usuario(id_usuario)

#Mostrar valor total e quantidade de itens do carrinho
@app.get("/carrinho/total/{id_usuario}")
async def retornar_total_carrinho(id_usuario: int):
    return persistencia_total_carrinho(id_usuario)

#Deletar carrinho usuario
@app.delete("/carrinho/{id_usuario}")
async def deletar_carrinho(id_usuario: int):
    return persistencia_deletar_carrinho_usuario(id_usuario)
