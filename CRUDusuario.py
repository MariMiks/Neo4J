from connect_database import driver

def input_with_cancel(prompt, cancel_keyword="CANCELAR", cancel_on_n_for_specific_prompt=False):
    resposta = input(f"{prompt} (digite {cancel_keyword} para abortar): ")
    if resposta.upper() == cancel_keyword:
        print("Operação cancelada.")
        return None
    if cancel_on_n_for_specific_prompt and resposta.upper() == 'N':
        return resposta
    return resposta

def create_usuario():
    print("\nInserindo um novo usuário")
    nome = input_with_cancel("Nome")
    if nome is None:
        return

    sobrenome = input_with_cancel("Sobrenome")
    if sobrenome is None:
        return

    cpf = input_with_cancel("CPF")
    if cpf is None or cpf.strip() == "":
        print("CPF é obrigatório.")
        return
    
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
            _create_usuario_tx, nome, sobrenome, cpf, enderecos
        )
        print("Usuário inserido com sucesso!")
    return cpf

def _create_usuario_tx(tx, nome, sobrenome, cpf, enderecos):
    query = """
        CREATE (u:Usuario {nome: $nome, sobrenome: $sobrenome, cpf: $cpf})
        WITH u
        UNWIND $enderecos AS endereco
        CREATE (e:Endereco {rua: endereco.rua, num: endereco.num, bairro: endereco.bairro, 
                            cidade: endereco.cidade, estado: endereco.estado, cep: endereco.cep})
        CREATE (u)-[:RESIDE_EM]->(e)
        """
    tx.run(query, nome=nome, sobrenome=sobrenome, cpf=cpf, enderecos=enderecos)


def read_usuario(cpf=None):
    with driver.session() as session:
        if cpf:
            
            result = session.run(
                """
                MATCH (u:Usuario {cpf: $cpf})-[:RESIDE_EM]->(e:Endereco)
                RETURN u, COLLECT(e) AS enderecos
                """, cpf=cpf
            )
            for record in result:
                usuario = record["u"]
                enderecos = record["enderecos"]
                print("\nDetalhes do Usuário:")
                for chave, valor in usuario.items():
                    print(f"{chave}: {valor}")
                print("Endereços:")
                for endereco in enderecos:
                    for chave, valor in endereco.items():
                        print(f"  {chave}: {valor}")
        else:
            
            result = session.run(
                """
                MATCH (u:Usuario)-[:RESIDE_EM]->(e:Endereco)
                RETURN u, COLLECT(e) AS enderecos
                """
            )
            usuarios = [{"usuario": record["u"], "enderecos": record["enderecos"]} for record in result]

            if not usuarios:
                print("Nenhum usuário encontrado.")
                return

            print("Usuários disponíveis:")
            for i, data in enumerate(usuarios, start=1):
                print(f"{i}. Nome: {data['usuario']['nome']}")  

            while True:
                try:
                    index = int(input("Digite o número do usuário para ver detalhes: ")) - 1
                    if 0 <= index < len(usuarios):
                        usuario_selecionado = usuarios[index]['usuario']
                        enderecos_selecionados = usuarios[index]['enderecos']
                        print("\nDetalhes do Usuário:")
                        for chave, valor in usuario_selecionado.items():
                            print(f"{chave}: {valor}")
                        print("Endereços:")
                        for endereco in enderecos_selecionados:
                            for chave, valor in endereco.items():
                                print(f"  {chave}: {valor}")
                        break
                    else:
                        print("Índice inválido. Tente novamente.")
                except ValueError:
                    print("Entrada inválida. Digite um número.")