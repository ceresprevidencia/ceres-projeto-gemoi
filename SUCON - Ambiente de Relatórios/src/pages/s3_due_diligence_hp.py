import streamlit as st
from datetime import datetime

import pandas as pd

from utils.ddq_utils.crud import (
    listar_respostas,
    listar_gestoras,
    buscar_gestora,
    inserir_gestora,
    listar_preenchimentos,
    listar_gestoras_preenchimento,
    CnpjDuplicadoError
)

from utils.helpers import (card_geral)


st.set_page_config(layout="wide")


st.html("""
<style>
    /* Remove o padding lateral e superior do bloco principal */
    .block-container {
        padding-top: 3.8rem;
        padding-left: 0rem;
        padding-right: 0rem;
    }

    .st-key-meu-container {
        background-color: #0B2F13;
        border-radius: 0px;
        padding: 30px 20px 30px 20px;
        width: 100%;
        box-sizing: border-box;
    }
    
    /* Container do conteúdo COM padding lateral */
    .st-key-conteudo {
        padding-left: 3rem;
        padding-right: 3rem;
    }
        
</style>
""")

with st.container(key="meu-container"):
    st.html("""
        <p style="text-align:center; color:#FAFBEB; margin:0 0; font-size: clamp(20px, 3vw, 29px); font-weight:400;">
            Diligência - 
            <span style='color:#A8EC7D; font-family:"Source Serif 4",serif; font-style:italic; font-weight:600;'>
                Ceres
            </span>
        </p>
    """)



with st.container(horizontal_alignment="center", gap=None, key="conteudo"):
    with st.container(width=1200):
        
        with st.container():
            gestoras = listar_gestoras_preenchimento()
            meses_2 = datetime.now() + pd.DateOffset(months=2)
            gestoras["data_envio"] = pd.to_datetime(gestoras["data_envio"], errors="coerce",)
            gestoras["vencimento"] = (gestoras["data_envio"] + pd.DateOffset(months=12))
            agora = pd.Timestamp.now()

            gestoras["status_vencimento"] = gestoras["vencimento"].apply(
                lambda x: (
                    "Não preenchida"
                    if pd.isna(x)
                    else "Vencido"
                    if x < agora
                    else "A vencer"
                    if x - pd.DateOffset(months=2) <= agora
                    else "Em dia"
                )
            )
        
        
            col1, col2, col3, col4, col5 = st.columns(5)

            with col1:
                qtd_gestoras = len(listar_gestoras_preenchimento())
                card_geral(
                    "Gestoras",
                    qtd_gestoras,
                    help="Gestoras cadastradas no sistema.",)
            
            with col2:
                qtd_em_dia = len(gestoras[gestoras["status_vencimento"] == "Em dia"])
               
                card_geral(
                    "Em dia",
                    qtd_em_dia,
                    help="Gestoras que enviaram o questionário e estão com o prazo de vencimento em dia.",)

            with col3:
                qtd_a_vencer = len(gestoras[gestoras["status_vencimento"] == "A vencer"])
                card_geral(
                    "A vencer",
                    qtd_a_vencer,
                    help="Gestoras que enviaram o questionário e estão com o prazo de vencimento a vencer (faltando até 2 meses).",)

            with col4:
                qtd_vencido = len(gestoras[gestoras["status_vencimento"] == "Vencido"])
                card_geral(
                    "Vencido",
                    qtd_vencido,
                    help="Gestoras que enviaram o questionário e estão com o prazo de vencimento vencido.",)

            with col5:
                qtd_sem_data = len(gestoras[gestoras["status_vencimento"] == "Não preenchida"])
                card_geral(
                    "Não respondida",
                    qtd_sem_data,
                    help="Gestoras que não responderam o questionário.",
                )

        with st.container(horizontal=True):
            c1, c2, = st.columns([0.4, 0.2])
            
            with c1:
                gestoras['status_geral'] = gestoras['status'].apply(lambda x: x.split(' ')[0].capitalize())
                opcoes_status = list(gestoras['status_geral'].unique()) + ["Todos"]
                sit_cadastral = st.selectbox("Situação cadastral",
                                             placeholder='Situação cadastral', 
                                             options=opcoes_status, key='gestora_selecionada',
                                             index=None,
                                             label_visibility="collapsed")
                if sit_cadastral:
                    if sit_cadastral != "Todos":
                        gestoras = gestoras[gestoras["status_geral"] == sit_cadastral]

            with c2:

                status = st.selectbox(
                    'Status vencimento',
                     placeholder='Status vencimento',
                     options=gestoras["status_vencimento"].unique(), 
                     key='status_selecionado',
                     index=None,
                     label_visibility="collapsed")
                if status:
                    if status != "Todos":
                        gestoras = gestoras[gestoras["status_vencimento"] == status]
                    
                        
            
            @st.dialog("Cadastrar nova gestora", on_dismiss='rerun')
            def cadastrar_gestora() -> None:
                with st.form(
                    "form_cadastro_gestora",
                    clear_on_submit=False,
                ):
                    nome = st.text_input("Nome da gestora *")
                    telefone = st.text_input("Telefone")
                    email = st.text_input("E-mail")
                    cnpj = st.text_input(
                        "CNPJ",
                        placeholder="00.000.000/0000-00",
                    )

                    salvar = st.form_submit_button(
                        "Cadastrar gestora",
                        type="primary",
                        use_container_width=True,
                    )

                if not salvar:
                    return

                if not nome.strip():
                    st.error('O campo "Nome da gestora" é obrigatório.')
                    return

                try:
                    novo_id = inserir_gestora(
                        nome=nome,
                        telefone=telefone,
                        email=email,
                        cnpj=cnpj,
                    )

                    st.success(
                        f'Gestora "{nome.strip()}" cadastrada com sucesso. '
                        f"ID: {novo_id}"
                    )

                
                except CnpjDuplicadoError as erro:
                    st.error(str(erro))

                except ValueError as erro:
                    st.error(str(erro))

                except Exception as erro:
                    st.exception(erro)



            if st.button(
                "Cadastrar nova gestora",
                use_container_width=True,
            ):
                cadastrar_gestora()
                
        
      
            if st.button("", icon=":material/settings:"):
                st.switch_page("pages/s3_due_diligence_settings.py")





        with st.container():

            col_linha = 4
            qtd_gestoras = len(gestoras)
            for i in range(0, qtd_gestoras, col_linha):
                
                with st.container():
                    cols = st.columns(col_linha)
                    for j in range(col_linha):
                        if i + j < qtd_gestoras:
                            gestora = gestoras.iloc[i + j]
                            with cols[j]:
                                if gestora['status_vencimento'] == "Não preenchida":
                                    st.subheader(gestora["nome"])
                                    st.warning(f"Gestora {gestora['nome']} não respondeu o questionário.")
                                else:
                                    st.subheader(gestora["nome"])
                                    st.write(f"Data de envio: {gestora['data_envio']}")
                                    st.write(f"Vencimento: {gestora['vencimento']}")
                                    st.write(f"Status vencimento: {gestora['status_vencimento']}")
                                    st.write(f"Telefone: {gestora['telefone']}")
                                    st.write(f"CNPJ: {gestora['cnpj']}")
                                    st.write(f"E-mail: {gestora['email']}")
                                    st.write(f"Status gestora: {gestora['status']}")
                                    if st.button("Abrir questionário", key=f"abrir_{gestora['id_gestora']}"):
                                        st.switch_page(
                                                        "pages/s3_due_diligence_questionario.py",
                                                        query_params={
                                                            "id_gestora": str(gestora["id_gestora"]),
                                                            "id_preenchimento": str(gestora["id_preenchimento"]),
                                                            "status_vencimento": str(gestora["status_vencimento"]),
                                                            "data_vencimento": str(gestora["vencimento"]),
                                                        },
                                                    )


