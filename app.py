# Importação das Bibliotecas
import streamlit as st
import pandas as pd
import numpy as np
import re
from sqlalchemy import create_engine, text

# Bibliotecas para os Mapas
import plotly.express as px
import plotly.graph_objects as go
import folium
from streamlit_folium import st_folium

# Ajustes no CSS
# Remover o Header
hide_streamlit_style = """
            <style>
                /* Hide the Streamlit header and menu */
                header {visibility: hidden;}
                /* Optionally, hide the footer */
                .streamlit-footer {display: none;}
                /* Hide your specific div class, replace class name with the one you identified */
                .st-emotion-cache-uf99v8 {display: none;}
            </style>
            """

st.markdown(hide_streamlit_style, unsafe_allow_html=True)

# Remover o Espaçamento Lateral
st.markdown('''
<style>
    section.main > div {max-width:75rem}
</style>
''', unsafe_allow_html=True)

# Remover espaçamento no TOPO
# st.markdown('''
# <style> 
#     div[class^='block-container'] { padding-top: 1rem; } 
# </style> 
# ''', unsafe_allow_html=True)

# Get data in cache
@st.cache_data
def get_data():

    # Get the credencial - Secrets
    string_connection = st.secrets['string_connection']
   
    connection = create_engine(string_connection)

    # Create DataFrame
    df = pd.read_sql('''
	select
            hostel."name" 
        ,	hostel.qtd_rating 
        ,	coalesce(ratings.rating::text, '') as rating
        ,	case 
                when ratings.rating >= 4 then 'green'
                when ratings.rating >= 2.5 and ratings.rating < 4 then 'orange'
                when ratings.rating < 2.5 then 'lightred'
                else 'lightgray'
            end as color
        ,	hostel.continent 
        ,	hostel.country 
        ,	hostel.city 
        ,	hostel.latitude 
        ,	hostel.longitude 
        ,	hostel.url 
    from hostelworld_hostel hostel  
    left join hostelworld_ratings ratings
        on ratings.id_hostel = hostel.id_hostel 
    where 1=1
        and "type" = 'HOSTEL' 
    ''', connection)
    connection.dispose()

    return df


## Tela de Login

def validate_email(email):
    regex = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
    return regex.match(email)

def cred_entered():
    if validate_email(st.session_state['email'].strip()):
        st.session_state['authenticated'] = True
        
        # Inserir o Email e o acesso ao Banco
        string_connection = st.secrets['string_connection']

        # Inserir na tabela de LOG
        connection = create_engine(string_connection)
        with connection.connect() as conn:
            conn.execute(text(f'''INSERT INTO search_hostel_acessos (email) VALUES ('{st.session_state['email'].strip()}') '''))
        connection.dispose()

    else:
        st.session_state['authenticated'] = False

        if not st.session_state['email']:
            st.warning('Insira seu email')
        else: 
            st.warning('Email inválido.')

def create_login():
    st.title('Acesse o Search Hostel')
    st.text_input(label = "Email: ", value = "", key = 'email')
    st.button(label = 'Entrar',  on_click = cred_entered)

def authenticate_user(): 
    if "authenticated" not in st.session_state: 
        create_login()
    else:
        if st.session_state['authenticated']:
            return True
        else:
            create_login()
            return False


### Código de Fato.

if authenticate_user():
        
    # Get the DataFrame
    df = get_data()

    # Header da página 
    title, button_newsletter = st.columns([0.85, 0.15], gap = "large")
    with title:
        title.title('Search Hostel')

    with button_newsletter:
        button_newsletter.html('<br>')
        button_newsletter.link_button("Newsletter", "https://thanael.substack.com/", type='primary')
        button_newsletter.html('<br>')

    # Secção do MAPA
    select_continent, select_country, select_city = st.columns([0.2, 0.2, 0.2], gap = "large")

    with select_continent:
        
        # Select Continent
        continent = select_continent.selectbox(
            label = "Selecione um Continente: ",
            options = (df['continent'].sort_values().unique()),
            index = None
        )

        if continent != None:
            df = df[df['continent'] == continent]

    with select_country: 
        # Select Country
        country = select_country.selectbox(
            label = "Selecione um Pais: ",
            options = (df['country'].sort_values().unique()),
            index = None
        )

        if country != None:
            df = df[df['country'] == country]

    with select_city:

        # Select City
        city = select_city.selectbox(
            label = "Selecione uma Cidade: ",
            options = (df['city'].sort_values().unique()),
            index = None
        )

        if city != None:
            df = df[df['city'] == city]
        

        
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
            #iframe = folium.IFrame(str(row['nome']) + '<br>' + 'Avaliações: 12 ' + '<br>' + f"HostelWorld: <a href='{row['link']}'> Link </a>"),
            html = f''' <h3> {row['name']}   </h3>
            <b> Avaliações: </b> {row['qtd_rating']}<br>
            <b> Nota: </b> {row['rating']} ⭐  <br><br>
            <b> HostelWorld: </b> <a href='{row['url']}' , target="_blank"> Link </a>  '''

            iframe = folium.IFrame(html,
                                width=300,
                                height = 135
                                )

            popup = folium.Popup(iframe,
                                max_width=300)


            folium.Marker(
                [row['latitude'], row['longitude']],                                                  # Localização
                tooltip = row['name'],                                                                # Hover do Marcador
                icon=folium.Icon(color=f"{row['color']}"),    # Icone do Marcador
                popup = popup    
            ).add_to(m) 

        # Instanciar o mapa
        events = st_folium(m,  width=1300, height = 600)

    # Estilização
    def negrito(v):
            return f"font-weight: bold; text_align: center"

    def make_clickable(val):
        return '<a href="{}">Link</a>'.format(val)

    def apply_style(row):
        styles = []
        for val in row.index:
            if val not in ('color','Marcador'): 
                styles.append(f'background-color: rgba{color_mapping[row["color"]]};')
            else:
                styles.append(f'background-color: {row["color"]};')
        return styles

