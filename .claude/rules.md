# ⚙️ REGRAS DE OPERAÇÃO

## Comunicação
- Respostas curtas e diretas. Sem introduções, sem resumos no final.
- Não repita o que foi pedido antes de responder.
- Sem elogios ao prompt ("Ótima pergunta!", "Claro!", etc).
- Se a tarefa for clara, execute. Só pergunte se houver ambiguidade real que bloqueie a execução.
- Prefira tópicos curtos a parágrafos longos.

## Código
- Entregue código funcional e completo. Sem placeholders como `# TODO` ou `...adicione aqui`.
- Se um arquivo já existe, edite apenas o trecho necessário. Não reescreva o arquivo inteiro.
- Siga o padrão já estabelecido no projeto. Não mude estilo sem ser pedido.
- Imports sempre no topo. Sem imports duplicados.

## Comentários no Código
- Toda função deve ter um comentário explicando o que ela faz, seus parâmetros e o que retorna.
- Blocos de lógica não óbvia devem ter uma linha explicando o porquê, não apenas o quê.
- Classes devem ter um comentário descrevendo sua responsabilidade.
- Variáveis com nomes abreviados ou valores "mágicos" devem ter comentário inline.
- Em rotas/endpoints, comentar qual a finalidade, método HTTP e se requer autenticação.
- Exemplo do padrão esperado em Python:
```python
def verificar_token(token: str) -> bool:
    """
    Valida se o token JWT ainda é válido e não foi revogado.

    Args:
        token: string do JWT recebido no header Authorization.

    Returns:
        True se o token for válido, False caso contrário.
    """
    # Tokens revogados são armazenados em cache para evitar consulta ao banco em toda requisição
    if cache.get(f"revogado:{token}"):
        return False
    ...
```

## Decisões
- Se houver mais de uma abordagem válida, apresente no máximo 2 opções em 1 linha cada e pergunte qual seguir.
- Se uma decisão for irrelevante para o resultado final, escolha a mais simples e siga em frente.
- Não antecipe refatorações ou melhorias que não foram pedidas.

## Entregas
- Um arquivo por vez, na ordem pedida.
- Mostre o caminho completo do arquivo antes do bloco de código.
- Ao terminar todos os itens pedidos, liste em até 5 bullets o que vem a seguir — nada mais.

## Erros
- Se identificar um erro no que foi pedido, aponte em uma linha e pergunte como prosseguir.
- Não corrija silenciosamente algo fora do escopo da tarefa atual.
