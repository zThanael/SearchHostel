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

# Get the credencial - Secrets
string_connection = st.secrets['string_connection']
connection = create_engine(string_connection)

st.write(string_connection)