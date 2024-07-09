from connect_database import driver
from usuario import input_with_cancel

def create_produto():
    print("\nInserindo um novo produto")
    nome = input_with_cancel("Nome do produto: ")
    if nome is None:
        return
 

    while True:
        try:
            preco = float(input_with_cancel("Preço: "))
            if preco < 0:
                raise ValueError("Preço não pode ser negativo.")
            break
        except ValueError as e:
            print(f"Erro: {e}. Tente novamente.")

    with driver.session() as session:
        session.write_transaction(_create_produto_tx, nome, preco)
        print("Produto inserido com sucesso!")

def _create_produto_tx(tx, nome, preco):
    query = """
        CREATE (p:Produto {nome: $nome, preco: $preco})
        """
    tx.run(query, nome=nome,  preco=preco)

def read_produto(nome=None):
    with driver.session() as session:
        if nome:
            result = session.run(
                "MATCH (p:Produto {nome: $nome}) RETURN p", nome=nome
            )
            for record in result:
                print(record["p"])
        else:
            result = session.run("MATCH (p:Produto) RETURN p")
            produtos = [record["p"] for record in result]

            if not produtos:
                print("Nenhum produto encontrado.")
                return

            print("Produtos disponíveis:")
            for i, produto in enumerate(produtos, start=1):
                print(f"{i}. Nome: {produto['nome']}")

            while True:
                try:
                    index = int(input("Digite o número do produto para ver detalhes: ")) - 1
                    if 0 <= index < len(produtos):
                        produto_selecionado = produtos[index]
                        print("\nDetalhes do Produto:")
                        for chave, valor in produto_selecionado.items():
                            print(f"{chave}: {valor}")
                        break
                    else:
                        print("Índice inválido. Tente novamente.")
                except ValueError:
                    print("Entrada inválida. Digite um número.")