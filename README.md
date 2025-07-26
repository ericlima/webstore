# Portal de Vendas FastAPI + Bootstrap

Este projeto é um portal de vendas simples feito com FastAPI, Jinja2, Bootstrap e SQLite.

## Funcionalidades
- Exibição de produtos em grade (NxN)
- Carrinho de compras
- Cadastro de cliente (nome, morada, telefone, email)
- Banco de dados SQLite
- Interface responsiva com Bootstrap

## Como rodar

1. Clone o repositório e acesse a pasta do projeto:
   ```bash
   cd fast_html_store
   ```
2. Crie e ative o ambiente virtual:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```
3. Instale as dependências:
   ```bash
   pip install -r requirements.txt
   ```
4. Rode o servidor:
   ```bash
   uvicorn main:app --reload
   ```
5. Acesse em [http://localhost:8000](http://localhost:8000)

## Estrutura
- `main.py`: Código principal FastAPI
- `templates/`: HTMLs Jinja2
- `static/`: Arquivos estáticos (imagens, CSS)
- `requirements.txt`: Dependências

## Observações
- Para adicionar produtos, insira registros na tabela `products` do banco SQLite (`store.db`).
- O Bootstrap é carregado via CDN. 