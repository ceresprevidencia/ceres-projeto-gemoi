# Pré-requisitos e instalação

## Pré-requisitos

- Windows com Python `>=3.13,<4.0`;
- acesso às fontes de dados utilizadas pelo ambiente;
- Driver ODBC 18 para SQL Server, quando a instalação usar SQL Server;
- acesso de rede ao Oracle e ao SQL Server;
- credenciais autorizadas para o banco e, quando necessário, para o Google Sheets.

## Instalar o ambiente da aplicação

Na raiz de `SUCON - Ambiente de Relatórios`:

```powershell
py -3.13 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

O projeto também possui `pyproject.toml` e `poetry.lock`. Em equipes que usam Poetry, a instalação pode ser feita com:

```powershell
poetry install
poetry run streamlit run src/app.py
```

Escolha um único gerenciador para o ambiente local e mantenha o lockfile correspondente atualizado.

## Instalar a documentação

A documentação é independente do runtime da aplicação. Dentro da pasta `mkdocs`:

```powershell
cd mkdocs
python -m pip install -r requirements.txt
```

O comando deve ser executado no mesmo ambiente Python usado pelo `mkdocs`. Se o shell estiver usando um ambiente virtual, confirme com `python -c "import sys; print(sys.executable)"` antes da instalação.

## Validar a instalação

```powershell
mkdocs build --strict
```

O comando gera o site estático em `mkdocs/site/`. Essa pasta é artefato de build e não deve ser editada manualmente.
