from connect_database import driver
from CRUDusuario import create_usuario
from datetime import datetime
from CRUDusuario import input_with_cancel

def list_produtos_indexados(driver):  
    with driver.session() as session:
        result = session.run("MATCH (p:Produto) RETURN p")
        produtos = [record["p"] for record in result]

        if not produtos:
            print("Nenhum produto encontrado.")
            return None

        print("Produtos disponíveis:")
        for i, produto in enumerate(produtos, start=1):
            print(f"{i}. Nome: {produto['nome']}, Preço: {produto['preco']}")

        while True:
            try:
                index = int(input("Digite o número do produto que deseja: ")) - 1
                if 0 <= index < len(produtos):
                    return produtos[index]  
                else:
                    print("Índice inválido. Tente novamente.")
            except ValueError:
                print("Entrada inválida. Digite um número.")

def cadastrar_endereco(tipo_pessoa, cpf_cnpj):
    print("\nCadastro de novo endereço:")
    rua = input_with_cancel("Rua: ")
    if rua is None:
        return
    numero = input_with_cancel("Número: ")
    if numero is None:
        return
    bairro = input_with_cancel("Bairro: ")
    if bairro is None:
        return
    cidade = input_with_cancel("Cidade: ")
    if cidade is None:
        return
    estado = input_with_cancel("Estado: ")
    if estado is None:
        return
    cep = input_with_cancel("CEP: ")
    if cep is None:
        return

    with driver.session() as session:
        session.write_transaction(
            _create_endereco_tx, tipo_pessoa, cpf_cnpj, rua, numero, bairro, cidade, estado, cep
        )
        print("Endereço cadastrado com sucesso!")

def _create_endereco_tx(tx, tipo_pessoa, cpf_cnpj, rua, numero, bairro, cidade, estado, cep):    
    label_pessoa = "Usuario" if tipo_pessoa == "usuario" else "Vendedor"
    
    query = f"""
        MATCH (p:{label_pessoa} {{cpf: $cpf_cnpj}})
        CREATE (e:Endereco {{rua: $rua, numero: $numero, bairro: $bairro, cidade: $cidade, estado: $estado, cep: $cep}})
        CREATE (p)-[:RESIDE_EM]->(e)
        """
    tx.run(query, cpf_cnpj=cpf_cnpj, rua=rua, numero=numero, bairro=bairro, cidade=cidade, estado=estado, cep=cep)

def realizar_compra(cpf_usuario, driver):
    print("Realizando compra:")

    with driver.session() as session:
        # Verificar se o usuário existe e obter seus endereços
        result = session.run(
            """
            MATCH (u:Usuario {cpf: $cpf})-[:RESIDE_EM]->(e:Endereco)
            RETURN u, COLLECT(e) AS enderecos
            """,
            cpf=cpf_usuario
        )
        usuario_data = result.single()

        if not usuario_data:
            print("Usuário não encontrado. Deseja realizar o cadastro? (S/N)")
            resposta = input().upper()
            if resposta == 'S':
                cpf_usuario = create_usuario()
                if cpf_usuario is None:
                    print("Cadastro cancelado.")
                    return
                
                usuario_data = session.run(
                    """
                    MATCH (u:Usuario {cpf: $cpf})-[:RESIDE_EM]->(e:Endereco)
                    RETURN u, COLLECT(e) AS enderecos
                    """,
                    cpf=cpf_usuario
                ).single()
                if not usuario_data:
                    print("Erro ao buscar usuário após cadastro.")
                    return
            else:
                print("Não é possível continuar com a compra sem um usuário cadastrado.")
                return

        usuario = usuario_data["u"]
        enderecos = usuario_data["enderecos"]

        carrinho = []
        produtos = list(session.run("MATCH (p:Produto) RETURN p"))

        if not produtos:
            print("Nenhum produto encontrado.")
            return

        print("Lista de produtos disponíveis:")
        for i, record in enumerate(produtos, start=1):
            produto = record["p"]
            print(f"{i}. Nome: {produto['nome']}, Preço: {produto['preco']}")

        while True:
            id_produto = input("\nDigite o número do produto que deseja adicionar ao carrinho (ou 'C' para concluir): ")
            if id_produto.upper() == 'C':
                break

            try:
                id_produto = int(id_produto)
                if 1 <= id_produto <= len(produtos):
                    produto = produtos[id_produto - 1]["p"]
                    carrinho.append(produto)
                    print(f"Produto '{produto['nome']}' adicionado ao carrinho.")
                else:
                    raise ValueError
            except ValueError:
                print("Erro: Produto inválido. Digite um número válido.")

        if not carrinho:
            print("Nenhum produto adicionado ao carrinho.")
            return

        total = sum(float(produto["preco"]) for produto in carrinho)
        print(f"\nValor total do carrinho: R${total:.2f}")

        confirmar = input("\nDeseja confirmar a compra (S/N)? ").upper()
        if confirmar != "S":
            print("Compra cancelada.")
            return carrinho

        novo_endereco_cadastrado = False
        while not enderecos:  # Repete até ter um endereço válido
            print("Nenhum endereço cadastrado. Deseja cadastrar um novo endereço? (S/N)")
            resposta = input().upper()
            if resposta == 'S':
                endereco_entrega = cadastrar_endereco("usuario", cpf_usuario)
                if endereco_entrega is None:
                    print("Cadastro de endereço cancelado.")
                    return
                enderecos = [endereco_entrega]  # Atualiza a lista de endereços
                novo_endereco_cadastrado = True
            else:
                print("Não é possível continuar com a compra sem um endereço de entrega.")
                return

        if not novo_endereco_cadastrado:  # Só executa se NÃO tiver cadastrado um novo endereço
            print("\nSelecione o endereço de entrega:")
            for i, endereco in enumerate(enderecos, start=1):
                print(f"{i} - {endereco['rua']}, {endereco['numero']}, {endereco['bairro']}, {endereco['cidade']}, {endereco['estado']}, CEP: {endereco['cep']}")

            while True:
                endereco_selecionado = input("Digite o número do endereço selecionado: ")
                try:
                    endereco_selecionado = int(endereco_selecionado)
                    if 1 <= endereco_selecionado <= len(enderecos):
                        endereco_entrega = enderecos[endereco_selecionado - 1]
                        break
                    else:
                        print("Número de endereço inválido.")
                except ValueError:
                    print("Entrada inválida. Digite um número válido.")

        data_hora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        session.write_transaction(_create_compra_tx, cpf_usuario, carrinho, endereco_entrega, total, data_hora)
        print("Compra realizada com sucesso!")


def _create_compra_tx(tx, cpf_usuario, produtos, endereco_entrega, total, data_hora):
   
    produtos_dict = [{'id': produto.id, 'nome': produto['nome'], 'preco': produto['preco']} for produto in produtos]
    endereco_entrega_dict = {prop: endereco_entrega[prop] for prop in endereco_entrega.keys()}

    query = """
        MATCH (u:Usuario {cpf: $cpf_usuario})
        CREATE (c:Compra {data_hora: $data_hora, valor_total: $total})
        CREATE (u)-[:COMPROU]->(c)
        WITH c
        UNWIND $produtos AS produto
        MATCH (p:Produto {nome: produto.nome})
        CREATE (c)-[:CONTEM {quantidade: 1}]->(p) 
        WITH c
        CREATE (e:Endereco {rua: $endereco_entrega.rua, numero: $endereco_entrega.numero, bairro: $endereco_entrega.bairro, cidade: $endereco_entrega.cidade, estado: $endereco_entrega.estado, cep: $endereco_entrega.cep})
        CREATE (c)-[:ENTREGUE_EM]->(e)
        """
    
    tx.run(query, cpf_usuario=cpf_usuario, produtos=produtos_dict, endereco_entrega=endereco_entrega_dict, total=total, data_hora=data_hora)

def ver_compras_realizadas(cpf_usuario):
    with driver.session() as session:
        result = session.run(
            """
            MATCH (u:Usuario {cpf: $cpf_usuario})-[:COMPROU]->(c:Compra)-[:CONTEM]->(p:Produto)
            RETURN c, COLLECT(p) AS produtos
            """, cpf_usuario=cpf_usuario
        )

        for record in result:
            compra = record["c"]
            produtos = record["produtos"]
            print("\nCompra:")
            print(f"  Data e Hora: {compra['data_hora']}")
            print(f"  Valor Total: R${compra['valor_total']:.2f}")
            print("  Produtos:")
            for produto in produtos:
                print(f"    - {produto['nome']}: R${produto['preco']:.2f}")