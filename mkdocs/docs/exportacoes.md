# Exportações e PDFs

## PDFs

O módulo `src/utils/gerar_pdf.py` centraliza a geração dos relatórios PDF:

- enquadramento diário;
- limites operacionais;
- risco de mercado dos planos.

Os PDFs usam A4 em paisagem, identidade visual da Ceres, tabelas formatadas e a fonte Figtree quando os arquivos locais estão disponíveis. Na ausência da fonte, o módulo usa Helvetica/Times como fallback.

### Boas práticas

- confira o plano, regime e data antes de baixar;
- abra o PDF e valide o número de páginas e o rodapé;
- preserve o nome de arquivo com a data de posição;
- não compartilhe o arquivo fora do público autorizado.

## Central de Exportáveis

A página **Exportáveis** registra os visuais disponíveis em `src/pages/s5_exportaveis.py`. Atualmente o módulo RRAS é exposto pela função `renderizar_rras` em `src/modulos_exportaveis/rras.py`.

O RRAS apresenta por plano a posição, VaR em reais e percentual, limite e status. A exportação utiliza dados de risco de mercado e a fonte Figtree local.

## Adicionar uma nova exportação

1. Crie o renderizador em `src/modulos_exportaveis/`.
2. Mantenha o renderizador responsável apenas por preparar e exibir seu visual.
3. Registre a função no dicionário `visuais_disponiveis`.
4. Valide o caso sem dados e o caso com dados.
5. Confira se a fonte e os assets usados existem em uma instalação limpa.
6. Atualize este capítulo com o novo visual.
