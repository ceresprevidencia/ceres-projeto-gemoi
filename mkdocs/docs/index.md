# Manual do ambiente SUCON

O **SUCON** é o ambiente de relatórios da Fundação Ceres. A aplicação combina Streamlit, consultas a bases relacionais e módulos de análise para apoiar o acompanhamento de investimentos, riscos, rentabilidade, recebimentos e diligência de gestoras.

Este manual atende dois públicos:

- **usuários de negócio**, que precisam consultar os relatórios e exportar resultados;
- **desenvolvedores e operadores**, que precisam instalar, configurar, executar e manter o ambiente.

## Visão rápida

| Necessidade | Onde encontrar |
| --- | --- |
| Instalar o projeto | [Pré-requisitos e instalação](instalacao.md) |
| Configurar bancos e Google Sheets | [Configuração e segurança](configuracao.md) |
| Abrir a aplicação | [Executar o ambiente](execucao.md) |
| Entender os relatórios | [Navegação e relatórios](modulos.md) |
| Usar o fluxo de Due Diligence | [Due Diligence](due-diligence.md) |
| Gerar PDFs e visuais | [Exportações e PDFs](exportacoes.md) |
| Entender os bots auxiliares | [Projetos auxiliares](bot-monitoramento.md) |
| Consultar o ciclo de atualização | [Atualizações e releases](atualizacoes.md) |
| Alterar código com segurança | [Arquitetura](arquitetura.md) |
| Investigar falhas | [Operação e troubleshooting](operacao.md) |

!!! warning "Dados sensíveis"
    Nunca publique arquivos `.env`, credenciais do Google, tokens OAuth, senhas ou dados extraídos das bases. Use `.env.example` apenas como referência e mantenha os segredos fora do controle de versão.

## Escopo atual

A entrada da aplicação é `src/app.py`. O menu organiza as funcionalidades em Início, Enquadramento, Risco de Crédito, Risco de Mercado, Rentabilidade, Due Diligence, Exportáveis e Risco de Liquidez.

A documentação descreve o comportamento encontrado no código atual. Regras de negócio, nomes de consultas e telas devem ser atualizados junto com as mudanças do sistema.
