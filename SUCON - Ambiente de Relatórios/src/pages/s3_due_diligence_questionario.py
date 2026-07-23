import streamlit as st
from utils.ddq_utils.crud import (
    listar_respostas,
    listar_gestoras,
    buscar_gestora,
    inserir_gestora,
    listar_preenchimentos,
    atualizar_resposta,
    listar_gestoras_preenchimento,
    CnpjDuplicadoError
)


@st.dialog("Editar resposta", on_dismiss='rerun')
def editar_resposta(
    id_resposta: str,
    pergunta: str,
    resposta_atual: str | None,
) -> None:
    """Exibe o diálogo para alterar uma resposta."""

    st.write(f"**Pergunta:** {pergunta}")

    nova_resposta = st.text_area(
        "Resposta",
        value=resposta_atual or "",
        key=f"editar_resposta_{id_resposta}",
    )

    st.write(
        "Para confirmar a alteração, digite "
        "**ALTERAR** no campo abaixo."
    )

    texto_confirmacao = st.text_input(
        "Confirmação",
        key=f"confirmacao_alteracao_{id_resposta}",
        placeholder="Digite ALTERAR",
    )

    confirmacao_valida = (
        texto_confirmacao.strip() == "ALTERAR"
    )

    if texto_confirmacao and not confirmacao_valida:
        st.error(
            "A confirmação está incorreta. "
            "Digite exatamente ALTERAR, em letras maiúsculas."
        )

    salvar = st.button(
        "Salvar alteração",
        type="primary",
        icon=":material/save:",
        use_container_width=True,
        disabled=not confirmacao_valida,
        key=f"salvar_resposta_{id_resposta}",
    )

    if not salvar:
        return

    nova_resposta = nova_resposta.strip()

    if not nova_resposta:
        st.error("A resposta não pode ficar vazia.")
        return

    if nova_resposta == (resposta_atual or "").strip():
        st.info("Nenhuma alteração foi identificada.")
        return

    try:
        atualizar_resposta(
            id_resposta=id_resposta,
            nova_resposta=nova_resposta,
        )

        st.success(
            "Resposta atualizada com sucesso!",
        )

        st.session_state["resposta_atualizada"] = True

    except ValueError as erro:
        st.error(str(erro))

    except Exception as erro:
        st.error("Não foi possível atualizar a resposta.")
        st.exception(erro)



id_gestora = st.query_params.get("id_gestora")
id_preenchimento = st.query_params.get("id_preenchimento")
status_vencimento = st.query_params.get("status_vencimento")
data_vencimento = st.query_params.get("data_vencimento")


#Dataframe com infos gerais da gestora
preenchimentos_df = listar_gestoras_preenchimento()
gestoras_selecionada_preenchimento = preenchimentos_df[preenchimentos_df["id_gestora"] == int(id_gestora)]


#Dataframe com respostas do ultimo questionário da gestora
gestoras_respostas_df = listar_respostas()
gestoras_selecionada_respostas = gestoras_respostas_df[gestoras_respostas_df["id_preenchimento"] == int(id_preenchimento)]


st.title(f'Análise Qualitativa do Gestor - {gestoras_selecionada_preenchimento['nome'].values[0]} - {status_vencimento}')
st.write(f"""{status_vencimento} | 
         Diligência: {gestoras_selecionada_preenchimento['data_envio'].values[0]} | 
         Vigência: {data_vencimento} | 
         CNPJ: {gestoras_selecionada_preenchimento['cnpj'].values[0]} | 
         E-mail: {gestoras_selecionada_preenchimento['email'].values[0]} | 
         Telefone: {gestoras_selecionada_preenchimento['telefone'].values[0]} 
        
         """)

with st.container():

    if st.button("Voltar", icon=":material/arrow_back:"):
            st.switch_page("pages/s3_due_diligence_hp.py")

gestoras_selecionada_respostas = gestoras_selecionada_respostas.sort_values(by='pergunta')

# Avança de 2 em 2 para criar as linhas
for i in range(len(gestoras_selecionada_respostas)):
      with st.container(border=True):
            id_resposta = gestoras_selecionada_respostas.iloc[i]['id_resposta']
            pergunta = gestoras_selecionada_respostas.iloc[i]['pergunta']
            resposta = gestoras_selecionada_respostas.iloc[i]['resposta']
            st.write(f"ID Reposta: {id_resposta}")
            st.write(f"Pergunta: {pergunta}")
            st.write(f"Resposta: {resposta}")
            
            if st.button(
                        "Editar",
                        icon=":material/edit:",
                        key=f"editar_{id_resposta}",
                    ):
                        editar_resposta(
                            id_resposta=id_resposta,
                            pergunta=pergunta,
                            resposta_atual=resposta,
                        )
                                        