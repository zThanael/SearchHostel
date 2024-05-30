# Importação das Bibliotecas
import streamlit as st
import pandas as pd
import numpy as np
from sqlalchemy import create_engine

# Bibliotecas para os Mapas
import plotly.express as px
import plotly.graph_objects as go
import folium
from streamlit_folium import st_folium

# Ajustes no CSS

# Remover o Espaçamento Lateral
st.markdown('''
<style>
    section.main > div {max-width:75rem}
</style>
''', unsafe_allow_html=True)

# Remover espaçamento no TOPO
st.markdown('''
<style> 
    div[class^='block-container'] { padding-top: 1rem; } 
</style> 
''', unsafe_allow_html=True)

# Get data in cache
@st.cache_data
def get_data():

    # Get the credencial - Secrets
    string_connection = st.secrets['string_connection']

    connection = create_engine(string_connection)

    # Create DataFrame
    df = pd.read_sql('''
    select * from hostelworld_hostel hh  where "type" = 'HOSTEL' --and country = 'Brazil'
    ''', connection)
    connection.dispose()

    return df

# Get the DataFrame
df = get_data()

# Criação dos marcadores que serão usados nos Mapas

# Get Colors used in Folium
colors = ['red', 'blue', 'green', 'purple', 'orange', 'darkred','lightred', 'beige', 'darkblue', 'darkgreen', 'cadetblue', 'darkpurple', 'white', 'pink', 'lightblue', 'lightgreen', 'gray', 'lightgray']

list_color = []
list_comprehension = [list_color.extend([color]*10) for color in colors]

nums = []
list_comprehension = [nums.extend(np.arange(0,10)) for i in range(len(colors))]

df_color = pd.DataFrame({'color': list_color, 'num_icon':nums})
df_color = df_color.reset_index()


# Header da página 
title, button_newsletter = st.columns([0.85, 0.15], gap = "large")
with title:
    title.title('Search Hostel')

with button_newsletter:
    button_newsletter.html('<br>')
    button_newsletter.link_button("Newsletter", "https://thanael.substack.com/", type='primary')
    button_newsletter.html('<br>')

# Secção do MAPA
selects, maps = st.columns([0.25, 0.75], gap = "large")

with selects:
    st.html('<br><br>')

    # Select Continent
    continent = selects.selectbox(
        label = "Selecione um Continente: ",
        options = (df['continent'].sort_values().unique()),
        index = None
    )

    if continent != None:
        df = df[df['continent'] == continent]

    st.html('<br>')

    # Select Country
    country = selects.selectbox(
        label = "Selecione um Pais: ",
        options = (df['country'].sort_values().unique()),
        index = None
    )

    if country != None:
        df = df[df['country'] == country]

    st.html('<br>')

    # Select City
    city = selects.selectbox(
        label = "Selecione uma Cidade: ",
        options = (df['city'].sort_values().unique()),
        index = None
    )
    st.html('<br>')

    if city != None:
        df = df[df['city'] == city]
    
with maps: 
    
    #Token 
    token = st.secrets['map_token']
    px.set_mapbox_access_token(token)

    # Se não usar o filtro de Cidade usar PLOTLY
    if city == None:
        
        # Criação do mapa com Plotly
        fig = px.scatter_mapbox(df,
                            lat='latitude',
                            lon='longitude',
                            hover_name="name",
                            zoom = 12 if city else 2.2
        )

        # Ajustar o tamanho.
        fig.update_layout(height=500, width= 800)

        # Plotar
        st.plotly_chart(fig, use_container_width=True)

    # Se usar o Filtro da Cidade usar o Folium
    else:

        # Criar colunas de cores.

        # Ordenação
        df = df.sort_values(by = 'qtd_rating', ascending = False)

        # Resetar o Index para usa-lo no Merge
        df = df.reset_index()

        # Juntar ao DataFrame de marcadores (df_color)
        df = df.merge(df_color[['color','num_icon']], how='left', left_index=True, right_index=True)

        # Configuração inicial do Mapa - Localização
        lat_avg = df['latitude'].mean()
        lon_avg = df['longitude'].mean()

        # Criação do Mapa
        m = folium.Map(
            location = [lat_avg, lon_avg],
            zoom_start = 10
        )

        # Definição dos Marcadores
        for _, row in df.iterrows():
            # Criação do Marcador
            folium.Marker(
                [row['latitude'], row['longitude']],                                                  # Localização
                tooltip = row['name'],                                                                # Hover do Marcador
                icon=folium.Icon(icon=f"{row['num_icon']}", prefix='fa', color=f"{row['color']}")     # Icone do Marcador
            ).add_to(m) 

        # Instanciar o mapa
        events = st_folium(m,  width=800, height = 500)
