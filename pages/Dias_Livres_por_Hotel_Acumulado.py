import streamlit as st
import mysql.connector
import decimal
import pandas as pd
from st_aggrid import AgGrid, GridOptionsBuilder
from datetime import date, timedelta

st.set_page_config(layout='wide')

st.title('Dias Livres por Hotel Acumulado - João Pessoa')

st.divider()

def gerar_df_phoenix(vw_name, base_luck):
    # Parametros de Login AWS
    config = {
    'user': 'user_automation_jpa',
    'password': 'luck_jpa_2024',
    'host': 'comeia.cixat7j68g0n.us-east-1.rds.amazonaws.com',
    'database': base_luck
    }
    # Conexão as Views
    conexao = mysql.connector.connect(**config)
    cursor = conexao.cursor()

    request_name = f'SELECT * FROM {vw_name}'

    # Script MySql para requests
    cursor.execute(
        request_name
    )
    # Coloca o request em uma variavel
    resultado = cursor.fetchall()
    # Busca apenas o cabecalhos do Banco
    cabecalho = [desc[0] for desc in cursor.description]

    # Fecha a conexão
    cursor.close()
    conexao.close()

    # Coloca em um dataframe e muda o tipo de decimal para float
    df = pd.DataFrame(resultado, columns=cabecalho)
    df = df.applymap(lambda x: float(x) if isinstance(x, decimal.Decimal) else x)
    return df

def puxar_dados_phoenix():

    st.session_state.df_router = gerar_df_phoenix('vw_router', 'test_phoenix_joao_pessoa')

    st.session_state.df_router = st.session_state.df_router[(st.session_state.df_router['Servico'] != 'FAZER CONTATO - SEM TRF IN ') & 
                                                            (st.session_state.df_router['Servico'] != 'GUIA BASE NOTURNO') & 
                                                            (st.session_state.df_router['Servico'] != 'GUIA BASE DIURNO ')].reset_index(drop=True)

    st.session_state.df_router['Reserva Mae'] = st.session_state.df_router['Reserva'].str[:10]  

    lista_combos = ['COMBO FLEXÍVEL 2 PASSEIOS', 'COMBO FLEXÍVEL 3 PASSEIOS', 'COMBO FLEXÍVEL 4 PASSEIOS']

    st.session_state.df_router['n_servicos'] = 1

    st.session_state.df_router.loc[st.session_state.df_router['Servico']==lista_combos[0], 'n_servicos'] = 2

    st.session_state.df_router.loc[st.session_state.df_router['Servico']==lista_combos[1], 'n_servicos'] = 3

    st.session_state.df_router.loc[st.session_state.df_router['Servico']==lista_combos[2], 'n_servicos'] = 4

def calcular_media_estadia():

    df_in_geral = st.session_state.df_router[(st.session_state.df_router['Tipo de Servico']=='IN') & (st.session_state.df_router['Status do Servico']!='CANCELADO') & (st.session_state.df_router['Status da Reserva']!='CANCELADO') & 
                                             (st.session_state.df_router['Status da Reserva']!='PENDENCIA DE IMPORTAÇÃO')].reset_index(drop=True)

    df_out_geral = st.session_state.df_router[(st.session_state.df_router['Tipo de Servico']=='OUT') & (st.session_state.df_router['Status do Servico']!='CANCELADO') & (st.session_state.df_router['Status da Reserva']!='CANCELADO') & 
                                              (st.session_state.df_router['Status da Reserva']!='PENDENCIA DE IMPORTAÇÃO')].reset_index(drop=True)

    df_in_out_geral = pd.merge(df_in_geral[['Reserva Mae', 'Servico', 'Voo', 'Data Execucao']], df_out_geral[['Reserva Mae', 'Data Execucao']], on='Reserva Mae', how='left')

    df_in_out_geral = df_in_out_geral.rename(columns={'Data Execucao_x': 'Data IN', 'Data Execucao_y': 'Data OUT', 'Voo': 'Voo IN'})

    df_in_out_geral = df_in_out_geral[~pd.isna(df_in_out_geral['Data OUT'])].reset_index(drop=True)

    df_in_out_geral['Data IN'] = pd.to_datetime(df_in_out_geral['Data IN'])
    df_in_out_geral['Data OUT'] = pd.to_datetime(df_in_out_geral['Data OUT'])

    df_in_out_geral['Dias Estadia'] = (df_in_out_geral['Data OUT'] - df_in_out_geral['Data IN']).dt.days

    df_in_out_geral['Dias Estadia'] = df_in_out_geral['Dias Estadia'].astype(int)

    df_in_out_geral = df_in_out_geral[(df_in_out_geral['Dias Estadia']>0) & (df_in_out_geral['Voo IN']!='XX - 9999') & ~(pd.isna(df_in_out_geral['Voo IN']))].reset_index(drop=True)

    media_estadia = round(df_in_out_geral['Dias Estadia'].mean(), 0)

    return media_estadia

if not 'df_router' in st.session_state:

    puxar_dados_phoenix()

row1 = st.columns(2)

row2 = st.columns(1)

with row1[0]:

    atualizar_phoenix = st.button('Atualizar Dados Phoenix')

    if atualizar_phoenix:

        puxar_dados_phoenix()

with row1[0]:

    container_datas = st.container(border=True)

    container_datas.subheader('Data Limite - IN')

    data_limite = container_datas.date_input('Data Limite', value=date.today() - timedelta(days=1) ,format='DD/MM/YYYY', key='data_limite')

df_in = st.session_state.df_router[(st.session_state.df_router['Data Execucao'] <= data_limite) & (st.session_state.df_router['Tipo de Servico']=='IN') & 
                                   (st.session_state.df_router['Status do Servico']!='CANCELADO') & (st.session_state.df_router['Status da Reserva']!='CANCELADO') & 
                                   (st.session_state.df_router['Status da Reserva']!='PENDENCIA DE IMPORTAÇÃO')].reset_index(drop=True)

media_estadia = calcular_media_estadia()

lista_reservas_in = df_in['Reserva Mae'].unique().tolist()

df_out = st.session_state.df_router[(st.session_state.df_router['Tipo de Servico']=='OUT') & (st.session_state.df_router['Status do Servico']!='CANCELADO') & (st.session_state.df_router['Status da Reserva']!='CANCELADO') & 
                                    (st.session_state.df_router['Status da Reserva']!='PENDENCIA DE IMPORTAÇÃO') & (st.session_state.df_router['Reserva Mae'].isin(lista_reservas_in))].reset_index(drop=True)

df_in_out = pd.merge(df_in[['Reserva Mae', 'Est Destino', 'Cliente', 'Telefone Cliente', 'Data Execucao']], df_out[['Reserva Mae', 'Data Execucao']], on='Reserva Mae', how='left')

df_in_out = df_in_out.rename(columns={'Data Execucao_x': 'Data IN', 'Data Execucao_y': 'Data OUT'})

df_in_out.loc[pd.isna(df_in_out['Data OUT']), 'Data OUT'] = df_in_out['Data IN'] + timedelta(days=media_estadia)

df_in_out_na_base = df_in_out[df_in_out['Data OUT']>=date.today() + timedelta(days=2)].reset_index(drop=True)

df_tour_transfer = st.session_state.df_router[((st.session_state.df_router['Tipo de Servico']=='TOUR') | (st.session_state.df_router['Tipo de Servico']=='TRANSFER')) & (st.session_state.df_router['Status do Servico']!='CANCELADO') & 
                                              (st.session_state.df_router['Status da Reserva']!='CANCELADO') & (st.session_state.df_router['Status da Reserva']!='PENDENCIA DE IMPORTAÇÃO') & 
                                              (st.session_state.df_router['Reserva Mae'].isin(lista_reservas_in))].reset_index(drop=True)

df_tour_transfer_group = df_tour_transfer.groupby(['Data Execucao', 'Reserva Mae'])['n_servicos'].sum().reset_index()

df_tour_transfer_group = df_tour_transfer_group.groupby(['Reserva Mae'])['n_servicos'].sum().reset_index()

df_tour_transfer_group = df_tour_transfer_group.rename(columns={'n_servicos': 'Qtd. Servicos'})

df_in_out_na_base = pd.merge(df_in_out_na_base, df_tour_transfer_group, on='Reserva Mae', how='left')

df_in_out_na_base['Data IN'] = pd.to_datetime(df_in_out_na_base['Data IN'])
df_in_out_na_base['Data OUT'] = pd.to_datetime(df_in_out_na_base['Data OUT'])

df_in_out_na_base['Qtd. Servicos'] = df_in_out_na_base['Qtd. Servicos'].fillna(0)

df_in_out_na_base['Dias Estadia'] = (df_in_out_na_base['Data OUT'] - df_in_out_na_base['Data IN']).dt.days

df_in_out_na_base['Dias Estadia'] = df_in_out_na_base['Dias Estadia'].astype(int)

df_in_out_na_base['Dias Estadia'] = df_in_out_na_base['Dias Estadia']-1

df_in_out_na_base['Dias Livres'] = df_in_out_na_base['Dias Estadia']-df_in_out_na_base['Qtd. Servicos']

df_final = df_in_out_na_base.groupby('Est Destino').agg({'Dias Livres': 'sum'}).reset_index()

df_final = df_final.sort_values(by=['Dias Livres'], ascending=False).reset_index(drop=True)

gb = GridOptionsBuilder.from_dataframe(df_final)
gb.configure_selection('multiple', use_checkbox=True)
gb.configure_grid_options(domLayout='autoHeight')
gb.configure_grid_options(domLayout='autoWidth')
gridOptions = gb.build()

with row1[1]:

    grid_response = AgGrid(df_final, gridOptions=gridOptions, enable_enterprise_modules=False, fit_columns_on_grid_load=True)

selected_rows = grid_response['selected_rows']

if selected_rows is not None and len(selected_rows)>0:

    df_ref = df_in_out_na_base[df_in_out_na_base['Est Destino'].isin(selected_rows['Est Destino'].unique().tolist())].reset_index(drop=True)

    total_dias_livres = df_ref['Dias Livres'].sum()

    with row1[1]:

        st.subheader(f'Total de dias livres dos hoteis selecionados = {int(total_dias_livres)}')

    df_ref['Data IN'] = pd.to_datetime(df_ref['Data IN']).dt.date

    df_ref['Data OUT'] = pd.to_datetime(df_ref['Data OUT']).dt.date

    with row2[0]:

        container_dataframe = st.container()

        container_dataframe.dataframe(df_ref[['Reserva Mae', 'Cliente', 'Telefone Cliente', 'Est Destino', 'Data IN', 'Data OUT', 'Qtd. Servicos', 'Dias Estadia', 
                                              'Dias Livres']].sort_values(by='Est Destino'), hide_index=True, use_container_width=True)