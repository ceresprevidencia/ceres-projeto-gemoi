# Atualizações e releases

## Ciclo regular

O ciclo regular de atualização do ambiente SUCON e dos projetos auxiliares ocorre **às quartas-feiras**. A janela deve ser usada para:

- publicar melhorias planejadas;
- atualizar dependências;
- revisar consultas e feeds;
- atualizar regras de classificação;
- atualizar o manual;
- executar as validações técnicas e funcionais.

## Hotfix em qualquer dia

Um hotfix pode ser liberado em qualquer dia quando corrigir uma falha que afete disponibilidade, dados, alertas, segurança ou uma operação crítica. A urgência não elimina a rastreabilidade.

Checklist mínimo:

1. Registrar problema, impacto e responsável.
2. Aplicar a menor alteração necessária.
3. Validar o código e o fluxo afetado.
4. Confirmar que não há credenciais ou dados reais no diff.
5. Atualizar a documentação se houver mudança de comportamento.
6. Comunicar a liberação aos usuários e operadores.
7. Registrar o que deve ser incorporado ao próximo ciclo de quarta-feira.

## Validação do manual

Na raiz do repositório:

```powershell
cd mkdocs
python -m pip install -r requirements.txt
python -m mkdocs build --strict
```

O site gerado fica em `mkdocs/site/` e não deve ser editado manualmente.
