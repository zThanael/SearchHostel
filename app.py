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


string_connection = st.secrets['postgres']
connection = create_engine(string_connection)

st.write(string_connection)