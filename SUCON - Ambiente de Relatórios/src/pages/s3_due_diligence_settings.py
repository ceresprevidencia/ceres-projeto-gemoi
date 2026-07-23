from __future__ import annotations

import pandas as pd
import streamlit as st
from utils.ddq_utils.etl import executar_etl
from utils.ddq_utils.crud import (
    excluir_gestoras,
    listar_gestoras,
    atualizar_gestora,
)


# ── Funções auxiliares ────────────────────────────────────────────────────────

def inicializar_estado() -> None:
    """Inicializa os estados utilizados pela página."""
    st.session_state.setdefault("gestoras_selecionadas_exclusao", [])
    st.session_state.setdefault("exclusao_concluida", False)
    st.session_state.setdefault("mensagem_exclusao", None)


def limpar_estado_exclusao() -> None:
    """Limpa os dados temporários da exclusão."""
    st.session_state["exclusao_concluida"] = False
    st.session_state["mensagem_exclusao"] = None
    st.session_state.pop("confirmacao_texto_exclusao", None)


def carregar_gestoras() -> pd.DataFrame:
    """Busca as gestoras cadastradas."""
    try:
        return listar_gestoras()
    except Exception as erro:
        st.error("Não foi possível carregar as gestoras.")
        st.exception(erro)
        return pd.DataFrame()


@st.dialog("Confirmar exclusão de gestoras", width="large")
def confirmar_exclusao(gestoras_selecionadas: list[dict]) -> None:
    """Solicita confirmação antes de excluir as gestoras."""

    if st.session_state.get("exclusao_concluida"):
        mensagem = st.session_state.get(
            "mensagem_exclusao",
            "Gestoras excluídas com sucesso.",
        )

        st.success(mensagem, icon=":material/check_circle:")
        st.info(
            "Os preenchimentos e as respostas foram preservados. "
            "Os preenchimentos vinculados às gestoras excluídas "
            "ficaram com o campo id_gestora igual a NULL."
        )

        if st.button(
            "Fechar e atualizar a página",
            type="primary",
            width="stretch",
            key="botao_fechar_exclusao",
        ):
            limpar_estado_exclusao()
            st.rerun()

        return

    quantidade = len(gestoras_selecionadas)

    st.warning(
        f"Você está prestes a excluir {quantidade} gestora(s).",
        icon=":material/warning:",
    )

    st.write("As seguintes gestoras serão excluídas:")

    dados_confirmacao = pd.DataFrame(gestoras_selecionadas)

    colunas_disponiveis = [
        coluna
        for coluna in ["id_gestora", "nome", "cnpj", "email"]
        if coluna in dados_confirmacao.columns
    ]

    st.dataframe(
        dados_confirmacao[colunas_disponiveis],
        hide_index=True,
        column_config={
            "id_gestora": st.column_config.NumberColumn("ID", format="%d"),
            "nome": st.column_config.TextColumn("Nome"),
            "cnpj": st.column_config.TextColumn("CNPJ"),
            "email": st.column_config.TextColumn("E-mail"),
        },
    )

    st.info(
        "Os preenchimentos e respostas não serão apagados. "
        "Os preenchimentos relacionados ficarão sem uma gestora vinculada."
    )

    st.write("Para confirmar, digite **EXCLUIR** no campo abaixo.")

    texto_confirmacao = st.text_input(
        "Confirmação",
        key="confirmacao_texto_exclusao",
        placeholder="Digite EXCLUIR",
    )

    confirmacao_valida = texto_confirmacao.strip() == "EXCLUIR"

    if texto_confirmacao and not confirmacao_valida:
        st.error(
            "A confirmação está incorreta. "
            "Digite exatamente EXCLUIR, em letras maiúsculas."
        )

    with st.container(horizontal=True):
        if st.button(
            "Cancelar",
            width="stretch",
            key="botao_cancelar_exclusao",
        ):
            limpar_estado_exclusao()
            st.rerun()

        excluir = st.button(
            "Excluir gestoras",
            type="primary",
            width="stretch",
            disabled=not confirmacao_valida,
            key="botao_confirmar_exclusao",
        )

    if not excluir:
        return

    ids_gestoras = [int(g["id_gestora"]) for g in gestoras_selecionadas]

    try:
        quantidade_excluida = excluir_gestoras(ids_gestoras)
    except ValueError as erro:
        st.error(str(erro))
        return
    except Exception as erro:
        st.error("Não foi possível excluir as gestoras.")
        st.exception(erro)
        return

    st.session_state["exclusao_concluida"] = True
    st.session_state["mensagem_exclusao"] = (
        f"{quantidade_excluida} gestora(s) excluída(s) com sucesso."
    )

    st.rerun()


def renderizar_lista_exclusao(gestoras: pd.DataFrame) -> None:
    """Exibe a listagem e permite selecionar gestoras."""

    st.subheader("Gestoras cadastradas")

    if gestoras.empty:
        st.info("Nenhuma gestora cadastrada.")
        return

    st.dataframe(
        gestoras,
        hide_index=True,
        column_config={
            "id_gestora": st.column_config.NumberColumn("ID", format="%d"),
            "nome": st.column_config.TextColumn("Nome"),
            "telefone": st.column_config.TextColumn("Telefone"),
            "email": st.column_config.TextColumn("E-mail"),
            "cnpj": st.column_config.TextColumn("CNPJ"),
            "atualizado": st.column_config.TextColumn("Atualizado em"),
        },
    )

    opcoes: dict[str, dict] = {}

    for _, linha in gestoras.iterrows():
        id_gestora = int(linha["id_gestora"])
        nome = str(linha["nome"])
        cnpj = "" if pd.isna(linha.get("cnpj")) else str(linha.get("cnpj"))

        rotulo = f"{nome} — ID {id_gestora}"
        if cnpj:
            rotulo += f" — CNPJ {cnpj}"

        opcoes[rotulo] = {
            "id_gestora": id_gestora,
            "nome": nome,
            "telefone": None if pd.isna(linha.get("telefone")) else linha.get("telefone"),
            "email": None if pd.isna(linha.get("email")) else linha.get("email"),
            "cnpj": None if pd.isna(linha.get("cnpj")) else linha.get("cnpj"),
        }

    rotulos_selecionados = st.multiselect(
        "Selecione as gestoras que deseja excluir",
        options=list(opcoes.keys()),
        placeholder="Selecione uma ou mais gestoras",
    )

    gestoras_selecionadas = [opcoes[r] for r in rotulos_selecionados]
    quantidade_selecionada = len(gestoras_selecionadas)

    if quantidade_selecionada:
        st.caption(f"{quantidade_selecionada} gestora(s) selecionada(s).")

    if st.button(
        "Excluir gestoras selecionadas",
        type="primary",
        width="stretch",
        disabled=quantidade_selecionada == 0,
        key="botao_abrir_confirmacao_exclusao",
    ):
        limpar_estado_exclusao()
        confirmar_exclusao(gestoras_selecionadas)


# ── Corpo da página ───────────────────────────────────────────────────────────

inicializar_estado()

with st.expander("Exclusão", expanded=False):
 

    st.warning(
        "Esta operação remove permanentemente o cadastro "
        "da gestora. Revise cuidadosamente a seleção.",
        icon=":material/warning:",
    )

    gestoras = carregar_gestoras()
    renderizar_lista_exclusao(gestoras)


with st.expander("ETL"):
    st.title("ETL de preenchimentos e respostas")
    st.write(
        "Importa os dados do Google Sheets e atualiza "
        "os preenchimentos e respostas no banco."
    )

    if st.button(
        "Executar ETL",
        type="primary",
        use_container_width=True,
    ):
        with st.spinner("Executando ETL..."):
            resultado = executar_etl()
            
        if not resultado.sucesso:
            st.error(
                resultado.mensagem_erro
                or "Ocorreu um erro durante a execução."
            )
            st.stop()

        st.success("ETL executada com sucesso.")

        coluna_1, coluna_2, coluna_3 = st.columns(3)

        coluna_1.metric(
            "Preenchimentos adicionados",
            resultado.preenchimentos_adicionados,
        )

        coluna_2.metric(
            "Respostas adicionadas",
            resultado.respostas_adicionadas,
        )

        coluna_3.metric(
            "Respostas atualizadas",
            resultado.respostas_atualizadas,
        )

        if resultado.cnpjs_nao_encontrados:
            st.warning(
                "Alguns CNPJs não foram encontrados no cadastro."
            )

            st.dataframe(
                pd.DataFrame(
                    {
                        "CNPJ não encontrado": sorted(
                            resultado.cnpjs_nao_encontrados
                        )
                    }
                ),
                width='stretch',
                hide_index=True,
            )

        if resultado.novos_preenchimentos:
            with st.expander("Novos preenchimentos"):
                st.dataframe(
                    pd.DataFrame(
                        resultado.novos_preenchimentos
                    ),
                    width='stretch',
                    hide_index=True,
                )

        if resultado.novas_respostas:
            with st.expander("Novas respostas"):
                st.dataframe(
                    pd.DataFrame(
                        resultado.novas_respostas
                    ),
                    width='stretch',
                    hide_index=True,
                )

        if resultado.respostas_modificadas:
            with st.expander("Respostas atualizadas"):
                st.dataframe(
                    pd.DataFrame(
                        resultado.respostas_modificadas
                    ),
                    use_container_width=True,
                    hide_index=True,
                )

with st.expander("Atualização de gestoras"):
    st.title("Alterar gestora")

    gestoras = listar_gestoras()

    if gestoras.empty:
        st.info("Nenhuma gestora cadastrada.")
        st.stop()

    gestoras = gestoras.set_index("id_gestora")

    id_gestora = st.selectbox(
        "Gestora",
        gestoras.index,
        format_func=lambda id_: gestoras.loc[id_, "nome"],
    )

    gestora = gestoras.loc[id_gestora]

    with st.form("editar_gestora", clear_on_submit=False,):
        nome = st.text_input(
            "Nome",
            value=str(gestora["nome"] or ""),
        )

        cnpj = st.text_input(
            "CNPJ",
            value=str(gestora["cnpj"] or ""),
        )

        email = st.text_input(
            "E-mail",
            value=str(gestora["email"] or ""),
        )

        opcoes = ["Ativa", "Inativa"]
        status_atual = str(gestora["status"] or "Ativa")
        status = st.selectbox(
            "Status",
            options=opcoes,
            index=opcoes.index(status_atual) if status_atual in opcoes else 0,
        )

        salvar = st.form_submit_button(
            "Salvar",
            type="primary",
        )

    if salvar:
        try:
            atualizar_gestora(
                id_gestora=int(id_gestora),
                nome=nome,
                cnpj=cnpj,
                email=email,
                status=status,

            )

            st.success("Gestora atualizada com sucesso.")
           

        except ValueError as erro:
            st.error(str(erro))

        except Exception as erro:
            st.error(f"Erro ao atualizar: {erro}")


if st.button("Voltar", icon=":material/arrow_back:"):
            st.switch_page("pages/s3_due_diligence_hp.py")
