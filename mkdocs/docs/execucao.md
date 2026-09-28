# Executar o ambiente

## Iniciar o Streamlit

Na raiz do projeto, com o ambiente virtual ativo:

```powershell
streamlit run src/app.py
```

O Streamlit exibirá a URL local, normalmente `http://localhost:8501`. A aplicação usa layout amplo e a navegação superior definida em `src/app.py`.

## Iniciar o manual

Na pasta `mkdocs`:

```powershell
mkdocs serve
```

Abra a URL informada pelo comando, normalmente `http://127.0.0.1:8000`. O servidor recarrega a documentação quando um arquivo Markdown ou a configuração muda.

## Fluxo recomendado

1. Ative a `.venv`.
2. Confirme o `.env` e o acesso às fontes de dados.
3. Execute o Streamlit.
4. Abra a página inicial e valide a data mais recente disponível.
5. Consulte o relatório desejado e confira os filtros.
6. Gere a exportação quando necessário.

## Parar os servidores

No terminal de cada servidor, pressione `Ctrl+C`.

## Execução em rede

Para disponibilizar temporariamente o Streamlit em uma interface de rede controlada:

```powershell
streamlit run src/app.py --server.address 0.0.0.0
```

Não exponha a aplicação diretamente à internet sem autenticação, controle de rede, gestão de segredos e revisão de permissões.
