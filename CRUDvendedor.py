from connect_database import driver
from CRUDusuario import input_with_cancel

def create_vendedor():
    print("\nInserindo um novo vendedor")
    nome = input_with_cancel("Nome do vendedor: ")
    if nome is None: return

    sobrenome = input_with_cancel("Sobrenome do vendedor: ")
    if sobrenome is None: return

    while True:
        try:
            cpf = int(input_with_cancel("CPF: "))
            if cpf < 0:
                raise ValueError("CPF não pode ser negativo.")
            break
        except ValueError as e:
            print(f"Erro: {e}. Tente novamente.")

    while True:
        try:
            cnpj = int(input_with_cancel("CNPJ: "))
            if cnpj < 0:
                raise ValueError("CNPJ não pode ser negativo.")
            break
        except ValueError as e:
            print(f"Erro: {e}. Tente novamente.")

    enderecos = []

    while True:
        print("\nEndereço:")
        rua = input("Rua: ")
        num = input("Num: ")
        bairro = input("Bairro: ")
        cidade = input("Cidade: ")
        estado = input("Estado: ")
        cep = input("CEP: ")

        enderecos.append({
            "rua": rua,
            "num": num,
            "bairro": bairro,
            "cidade": cidade,
            "estado": estado,
            "cep": cep
        })

        adicionar_outro = input_with_cancel("Deseja adicionar outro endereço? (S/N): ", cancel_on_n_for_specific_prompt=True)
        if adicionar_outro is None:
            return  
        elif adicionar_outro.upper() != 'S':
            break 

    print(f"\n{nome} {sobrenome} - {cpf} - {enderecos}")  

    with driver.session() as session:
        session.write_transaction(
            _create_vendedor_tx, nome, sobrenome, cpf, cnpj, enderecos 
        )
        print("Vendedor inserido com sucesso!")

def _create_vendedor_tx(tx, nome, sobrenome, cpf, cnpj, enderecos):
    query = """
        CREATE (v:Vendedor {nome: $nome, sobrenome: $sobrenome, cpf: $cpf, cnpj: $cnpj})
        WITH v
        UNWIND $enderecos AS endereco
        CREATE (e:Endereco {rua: endereco.rua, num: endereco.num, bairro: endereco.bairro, 
                            cidade: endereco.cidade, estado: endereco.estado, cep: endereco.cep})
        CREATE (v)-[:RESIDE_EM]->(e)
        """
    tx.run(query, nome=nome, sobrenome=sobrenome, cpf=cpf, cnpj=cnpj, enderecos=enderecos)

def list_vendedores_indexados():
    with driver.session() as session:
        result = session.run("MATCH (v:Vendedor) RETURN v")
        vendedores = [record["v"] for record in result]

        if not vendedores:
            print("Nenhum vendedor encontrado.")
            return None

        print("Vendedores disponíveis:")
        for i, vendedor in enumerate(vendedores):
            print(f"{i+1}. Nome: {vendedor['nome']}, CPF: {vendedor['cpf']}")

        while True:
            try:
                index = int(input("Digite o número do vendedor que deseja: ")) - 1
                if 0 <= index < len(vendedores):
                    return vendedores[index]['cpf']
                else:
                    print("Índice inválido. Tente novamente.")
            except ValueError:
                print("Entrada inválida. Digite um número.")

def update_vendedor():
    cpf_vendedor = list_vendedores_indexados()
    if cpf_vendedor is None:
        return

    
    with driver.session() as session:
        result = session.run(
            "MATCH (v:Vendedor {cpf: $cpf}) RETURN v", cpf=cpf_vendedor
        )
        vendedor = result.single()["v"] if result.single() else None

    if vendedor:
        print("Dados atuais do vendedor:", vendedor)

        
        nome = input_with_cancel(f"Novo nome (ou pressione Enter para manter '{vendedor['nome']}' ): ") or vendedor['nome']
        
        while True:
            try:
                cpf = int(input_with_cancel(f"Novo cpf (ou pressione Enter para manter '{vendedor['cpf']}' ): "))
                if cpf is not None and cpf < 0:
                    raise ValueError("CPF não pode ser negativo.")
                break
            except ValueError as e:
                print(f"Erro: {e}. Tente novamente.")
        cpf = cpf if cpf is not None else vendedor['cpf']

        while True:
            try:
                cnpj = int(input_with_cancel(f"Novo cnpj (ou pressione Enter para manter '{vendedor['cnpj']}' ): "))
                if cnpj is not None and cnpj < 0:
                    raise ValueError("CNPJ não pode ser negativo.")
                break
            except ValueError as e:
                print(f"Erro: {e}. Tente novamente.")
        cnpj = cnpj if cnpj is not None else vendedor['cnpj']

        
        with driver.session() as session:
            session.write_transaction(
                _update_vendedor_tx, cpf_vendedor, nome, cpf, cnpj
            )
            print("Vendedor atualizado com sucesso!")
    else:
        print("Vendedor não encontrado.")

def _update_vendedor_tx(tx, cpf_vendedor, nome, cpf, cnpj):
    query = """
        MATCH (v:Vendedor {cpf: $cpf_vendedor})
        SET v.nome = $nome, v.cpf = $cpf, v.cnpj = $cnpj
        """
    tx.run(query, cpf_vendedor=cpf_vendedor, nome=nome, cpf=cpf, cnpj=cnpj)

def read_vendedor(cpf=None):
    with driver.session() as session:
        if cpf:
            result = session.run(
                """
                MATCH (v:Vendedor {cpf: $cpf})-[:RESIDE_EM]->(e:Endereco)
                RETURN v, COLLECT(e) AS enderecos
                """, cpf=cpf
            )
            for record in result:
                vendedor = record["v"]
                enderecos = record["enderecos"]
                print("\nDetalhes do Vendedor:")
                for chave, valor in vendedor.items():
                    print(f"{chave}: {valor}")
                print("Endereços:")
                for endereco in enderecos:
                    for chave, valor in endereco.items():
                        print(f"  {chave}: {valor}")
        else:
                result = session.run(
                    """
                    MATCH (v:Vendedor)
                    OPTIONAL MATCH (v)-[:RESIDE_EM]->(e:Endereco)
                    RETURN v, COLLECT(e) AS enderecos
                    """
                )
                vendedores = [{"vendedor": record["v"], "enderecos": record["enderecos"]} for record in result]

                if not vendedores:
                    print("Nenhum vendedor encontrado.")
                    return

                print("Vendedores disponíveis:")
                for i, data in enumerate(vendedores, start=1):
                    print(f"{i}. Nome: {data['vendedor']['nome']}")

                while True:
                    try:
                        index = int(input("Digite o número do vendedor para ver detalhes: ")) - 1
                        if 0 <= index < len(vendedores):
                            vendedor_selecionado = vendedores[index]['vendedor']
                            enderecos_selecionados = vendedores[index]['enderecos']
                            print("\nDetalhes do Vendedor:")
                            for chave, valor in vendedor_selecionado.items():
                                print(f"{chave}: {valor}")

                            if enderecos_selecionados and enderecos_selecionados[0] is not None:
                                print("Endereços:")
                                for endereco in enderecos_selecionados:
                                    for chave, valor in endereco.items():
                                        print(f"  {chave}: {valor}")
                            else:
                                print("Nenhum endereço cadastrado para este vendedor.")

                            break
                        else:
                            print("Índice inválido. Tente novamente.")
                    except ValueError:
                        print("Entrada inválida. Digite um número.")