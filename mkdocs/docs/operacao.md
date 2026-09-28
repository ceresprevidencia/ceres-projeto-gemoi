# Operação e troubleshooting

## Diagnóstico rápido

| Sintoma | Verificações |
| --- | --- |
| Aplicação não inicia | ambiente virtual ativo, dependências instaladas e `src/app.py` como entrada |
| Credenciais não configuradas | `.env` na raiz, nomes das variáveis e ausência de espaços indevidos |
| Erro Oracle | rede, host/porta/service name, usuário e senha |
| Erro SQL Server | Driver ODBC 18, servidor, banco e permissões |
| Tela sem dados | data selecionada, filtros e disponibilidade na origem |
| PDF sem logo/fonte | caminhos em `images/` e `fonts/` |
| Due Diligence sem respostas | credenciais Google, planilha, CNPJ e execução da ETL |
| Bot sem alertas | variáveis de API/webhook, histórico local, rede e execução da etapa correta |

## Logs e reprodução

Reproduza a falha com a menor combinação de filtros possível. Registre:

- data e hora;
- página e filtros usados;
- mensagem completa do erro;
- origem consultada;
- se o problema ocorre para todos os usuários ou apenas para um contexto.

Não inclua senha, token, CNPJ ou dados financeiros reais no chamado.

## Ciclo de atualização

O ciclo regular de atualização do ambiente e dos projetos auxiliares ocorre **às quartas-feiras**. Essa janela deve concentrar alterações planejadas, atualização de dependências, revisão de consultas e publicação da documentação.

### Hotfix

Hotfixes podem ser liberados em qualquer dia quando houver correção de falha, indisponibilidade, risco operacional ou necessidade urgente de negócio. O hotfix deve:

- registrar o problema e o impacto;
- alterar o menor escopo possível;
- passar pela validação técnica disponível;
- atualizar a documentação quando mudar comportamento ou configuração;
- ser comunicado aos usuários e operadores afetados.

## Validações do projeto

Para validar a documentação:

```powershell
cd mkdocs
mkdocs build --strict
```

Para verificar importações e sintaxe de um módulo Python específico, use o interpretador do ambiente virtual e um teste focado. A execução completa do Streamlit depende de rede, drivers, credenciais e disponibilidade das bases.

## Manutenção do manual

- mantenha a navegação em `mkdocs/mkdocs.yml` sincronizada com os arquivos em `mkdocs/docs/`;
- use nomes de arquivo em minúsculas e com hífens;
- execute o build estrito antes de publicar;
- registre comandos que mudarem com o processo de instalação;
- atualize as páginas quando nomes de menus, filtros ou fontes de dados mudarem.
