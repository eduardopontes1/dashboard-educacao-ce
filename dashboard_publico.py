import pandas as pd
import plotly.express as px
import geopandas as gpd
import streamlit as st
import warnings
import os

# Ignorar avisos
warnings.filterwarnings('ignore')

# --- Nomes dos arquivos (Altere aqui se for diferente) ---
# ESTE É O ÚNICO ARQUIVO DE DADOS QUE VAMOS CARREGAR
FILE_MAPA_PUBLICO = "dados_mapa_publico.csv" 
FILE_SHAPEFILE = "CE_Municipios_2022.shp"     # O .shp que você baixou do IBGE
FILE_SAEB_IMAGE = "grafico_saeb_desempenho.png" # O gráfico que criamos no Jupyter

# --- Configuração da Página ---
st.set_page_config(
    page_title="Diagnóstico Ceará: Educação e Segurança",
    page_icon="🚨",
    layout="wide"
)

# --- Título do Painel ---
st.title("🚨 Diagnóstico de Risco: Educação e Segurança no Ceará")
st.markdown("Uma análise de data storytelling para a Bolsa Reitoral de Liderança, baseada em dados agregados da SUSEP e SAEB.")

# --- Funções de Carregamento ---
@st.cache_data
def carregar_dados_mapa(file_path):
    if not os.path.exists(file_path):
        st.error(f"Erro: O arquivo de dados do mapa ('{file_path}') não foi encontrado.")
        return pd.DataFrame()
    return pd.read_csv(file_path)

@st.cache_data
def carregar_mapa_ceara(file_path):
    if not os.path.exists(file_path):
        st.warning(f"Aviso: Shapefile do mapa ('{file_path}') não encontrado.", icon="🗺️")
        st.info(f"Para ver o mapa de calor, baixe os arquivos (.shp, .shx, .dbf) dos 'Limites dos Municípios' do Ceará no portal do IBGE (Malhas Digitais) e coloque-os nesta pasta.")
        return None
    try:
        gdf = gpd.read_file(file_path)
        gdf = gdf.rename(columns={'NM_MUN': 'Município'})
        return gdf
    except Exception as e:
        st.error(f"Erro ao carregar o shapefile do mapa: {e}")
        return None

# --- Carregar os Dados ---
contagem_municipio = carregar_dados_mapa(FILE_MAPA_PUBLICO)
gdf_ceara_base = carregar_mapa_ceara(FILE_SHAPEFILE)

# --- O Storytelling ---

# --- ATO 1: O PROBLEMA (DADOS SUSEP) ---
st.header("Ato 1: A Realidade da Segurança 📉", divider='red')

# --- KPIs (Cartões) Hard-coded ---
kpi1, kpi2, kpi3 = st.columns(3)
kpi1.metric(label="Total de Registros de Infrações (2019-2024)", value="428.414")
kpi2.metric(label="% Infratores sem Educação Básica", value="65,33%")
kpi3.metric(label="% Infratores Jovens (12-23 anos)", value="49,00%")

st.markdown("A análise dos registros da SUSEP revela que o problema da criminalidade está profundamente ligado à evasão escolar e à juventude.")

# Layout em colunas para os gráficos
col1, col2 = st.columns(2)

with col1:
    st.subheader("Perfil de Escolaridade dos Infratores")
    
    # --- DADOS HARD-CODED (Seguros) ---
    data_escolaridade = {
        'Escolaridade': [
            'Alfabetizado', 'Ensino Fundamental Incompleto', 'Ensino Fundamental Completo',
            'Não Infomada', 'Ensino Médio Completo', 'Ensino Médio Incompleto',
            'Não Alfabetizado', 'Superior Incompleto', 'Superior Completo'
        ],
        'Contagem': [158759, 81045, 56132, 51757, 34762, 22011, 18079, 3351, 2518]
    }
    df_escolaridade_plot = pd.DataFrame(data_escolaridade)
    
    fig_escolaridade = px.bar(
        df_escolaridade_plot,
        y='Escolaridade', x='Contagem', orientation='h',
        title='Escolaridade dos Infratores no Ceará', text_auto=True,
        color='Contagem', color_continuous_scale='Reds'
    )
    fig_escolaridade.update_layout(yaxis={'categoryorder':'total ascending'}, showlegend=False)
    st.plotly_chart(fig_escolaridade, use_container_width=True)

with col2:
    st.subheader("Perfil de Idade dos Infratores")
    
    # --- DADOS HARD-CODED (Seguros) ---
    data_idade = {
        'Faixa Etária': [
            '18 até 23 anos', '12 até 17 anos', '24 até 29 anos', '30 até 35 anos',
            '36 até 41 anos', '42 até 47 anos', '48 até 53 anos', 'Não Identificada'
        ],
        'Contagem': [123224, 86706, 78689, 52128, 33124, 19956, 11654, 10568]
    }
    df_idade_plot = pd.DataFrame(data_idade)
    
    fig_idade = px.bar(
        df_idade_plot,
        x='Faixa Etária', y='Contagem',
        title='Perfil de Idade dos Infratores (Top 8 Faixas)', text_auto=True,
        color='Faixa Etária',
        color_discrete_map={'18 até 23 anos': '#FF4B4B', '12 até 17 anos': '#FF8C00'}
    )
    fig_idade.update_layout(xaxis={'categoryorder':'total descending'})
    st.plotly_chart(fig_idade, use_container_width=True)

# --- O Mapa Interativo ---
st.header("Onde o Problema se Concentra? 🗺️")

if gdf_ceara_base is not None and not contagem_municipio.empty:
    st.markdown("O mapa de calor abaixo mostra a contagem total de infrações por município, revelando os 'hotspots' de criminalidade no estado.")
    
    # Normalizar nomes para o 'merge'
    contagem_municipio['Município'] = contagem_municipio['Município'].str.upper().str.strip()
    gdf_ceara_base['Município'] = gdf_ceara_base['Município'].str.upper().str.strip()
    
    gdf_ceara_plot = gdf_ceara_base.merge(contagem_municipio, on='Município', how='left')
    gdf_ceara_plot['Contagem'] = gdf_ceara_plot['Contagem'].fillna(0)
    
    fig_mapa = px.choropleth_mapbox(
        gdf_ceara_plot,
        geojson=gdf_ceara_plot.geometry,
        locations=gdf_ceara_plot.index,
        color="Contagem",
        hover_name="Município",
        hover_data={"Contagem": True, "Município": False},
        color_continuous_scale="Reds",
        mapbox_style="carto-positron",
        center={"lat": -5.1, "lon": -39.5},
        zoom=6.5
    )
    fig_mapa.update_layout(title="Mapa de Calor: Concentração de Infrações por Município")
    st.plotly_chart(fig_mapa, use_container_width=True)

# --- ATO 2: A CAUSA RAIZ (DADOS SAEB) ---
st.header("Ato 2: A Causa Raiz 📚", divider='blue')
st.markdown("Se a evasão é o problema, por que os alunos evadem? A análise dos dados do SAEB mostra um claro abismo de desempenho e uma falha em criar perspectiva.")

try:
    st.image(FILE_SAEB_IMAGE, caption="Desempenho Médio em Matemática (SAEB) - Ceará (Público vs. Privado)")
except Exception as e:
    st.error(f"Erro ao carregar a imagem '{FILE_SAEB_IMAGE}'. Verifique se o arquivo está na pasta.")
    
st.markdown("""
**Dados do SAEB (Ensino Médio - Ceará) revelam:**
* **14%** dos alunos da rede pública já foram **reprovados**.
* **21,28%** dos alunos estão no "grupo de risco": planejam **'Somente trabalhar' (13,05%)** ou **'Não sabem' (8,23%)** o que fazer após a escola.
* Apenas **4,4%** podem se dar ao luxo de "Somente continuar estudando".
""")

# --- ATO 3: A SOLUÇÃO (SEU PROJETO) ---
st.header("Ato 3: A Intervenção 💡", divider='green')
st.markdown("### Meu projeto ataca a causa raiz, não o sintoma.")
st.markdown("Proponho uma intervenção-piloto focada em **desempenho, motivação e perspectiva de futuro**.")

c1, c2, c3 = st.columns(3)
c1.info("**1. Inspiração e Mentoria**\n* Criar um programa de mentoria com egressos da UFC de origem pública para construir 'capital cultural' e perspectiva.")
c2.info("**2. Gamificação (Reconhecimento e Incentivo)**\n* Lançar um app de quiz (ENEM/Escolar) com rankings e prêmios (tablets, etc.) para engajar pelo jogo e pela competição.")
c3.info("**3. Viabilidade (Acesso à Permanência)**\n* Divulgar ativamente os auxílios e bolsas da UFC (RU, moradia) para transformar o sonho em um plano financeiro concreto.")

st.success("Esta não é apenas uma proposta educacional. É uma **política pública de prevenção à criminalidade** baseada em evidências.")
