import folium
from folium.plugins import HeatMap
import pandas as pd
import geopandas as gpd
from shapely.geometry import Polygon
from pyproj import Transformer
from IPython.display import IFrame
import os
from IPython.display import display
from IPython.display import display
import folium

def create_map_for_commune(df_geolocalisees3, df_centres, commune_name):
    # Filtrer les transactions uniquement pour la commune spécifiée
    df_commune = df_geolocalisees3[df_geolocalisees3['communeName'] == commune_name]

    # Obtenir les coordonnées du centre de la commune à partir du DataFrame df_centres
    coordinates = df_centres[df_centres['nom'] == commune_name][['latitude', 'longitude']].values.flatten()
    if coordinates.size == 0:
        print(f"Commune {commune_name} non trouvée dans le DataFrame df_centres.")
        return None
    
    # Créer une carte centrée sur la commune
    carte_commune = folium.Map(location=coordinates, zoom_start=13)

    # Ajouter des markers pour chaque transaction avec le prix par m²
    for _, row in df_commune.iterrows():
        if pd.notnull(row['latitude']) and pd.notnull(row['longitude']) and pd.notnull(row['prix_m2']):
            # Ajouter un marker avec le prix dans le popup
            folium.Marker(
                location=[row['latitude'], row['longitude']],
                popup=f"Prix/m² : {row['prix_m2']:.0f} €/m²"  # Affichage du prix arrondi à l'unité
            ).add_to(carte_commune)
            
            # Ajouter un Label pour afficher le prix directement sur la carte
            folium.Marker(
                location=[row['latitude'], row['longitude']],
                icon=folium.DivIcon(html=f'<div style="font-size: 8px; color: blue; font-weight: bold;">{round(row["prix_m2"]):.0f} €/m²</div>')  # Affichage du prix arrondi à l'unité avec une police plus petite
            ).add_to(carte_commune)

    # Afficher la carte
    return carte_commune


def create_heatmap_for_commune(df_geolocalisees3, commune_name):
    # Filtrer les transactions uniquement pour la commune spécifiée
    df_commune = df_geolocalisees3[df_geolocalisees3['communeName'] == commune_name]

    # Obtenir les coordonnées du centre de la commune à partir du DataFrame df_centres
    coordinates = df_centres[df_centres['nom'] == commune_name][['latitude', 'longitude']].values.flatten()
    if coordinates.size == 0:
        print(f"Commune {commune_name} non trouvée dans le DataFrame df_centres.")
        return None
    
    # Créer une carte centrée sur la commune
    carte_commune = folium.Map(location=coordinates, zoom_start=13)

    # Calculer le prix minimum et maximum pour les gradients de couleur
    prix_min = df_commune['prix_m2'].min()
    prix_max = df_commune['prix_m2'].max()

    # Ajouter une couche de HeatMap pour visualiser la distribution des prix
    heat_data = [[row['latitude'], row['longitude'], row['prix_m2']] for _, row in df_commune.iterrows() if pd.notnull(row['latitude']) and pd.notnull(row['longitude']) and pd.notnull(row['prix_m2'])]
    
    # Ajouter la heatmap
    HeatMap(heat_data, min_opacity=0.2, max_val=prix_max, radius=15, blur=30, gradient={0.2: 'blue', 0.4: 'lime', 0.6: 'yellow', 0.8: 'orange', 1: 'red'}).add_to(carte_commune)

    # Afficher la carte
    return carte_commune

# Créer un transformer pour convertir les coordonnées (Lambert-93 -> Latitude/Longitude)
transformer = Transformer.from_crs("EPSG:2154", "EPSG:4326", always_xy=True)

# Fonction de transformation des coordonnées
def transform_coordinates(x, y):
    lon, lat = transformer.transform(x, y)  # Lambert-93 vers WGS84
    return lat, lon  # Retourne sous forme (latitude, longitude)

# Fonction pour créer une carte
def create_map(gdf, commune_name, price_data, identifiant_tri, beach_coordinates):
    # Filtrer les données de `gdf` pour la commune via `identifiant_tri`
    commune_data = gdf[gdf['id_tri'] == identifiant_tri]
    
    # Vérifier si les données sont présentes pour l'identifiant
    if commune_data.empty:
        return None

    # Extraire les coordonnées de la mairie via `price_data`
    price_data_commune = price_data[price_data['nom_commune'] == commune_name]
    if price_data_commune.empty:
        return None
    
    latitude_centre = price_data_commune['latitude_centre'].iloc[0]
    longitude_centre = price_data_commune['longitude_centre'].iloc[0]

    # Vérifier si les coordonnées de la mairie ne sont pas NaN
    if pd.isna(latitude_centre) or pd.isna(longitude_centre):
        return None

    # Créer une carte centrée sur la mairie
    m = folium.Map(location=[latitude_centre, longitude_centre], zoom_start=12)
    
    # Ajouter les polygones inondables sans remplissage de couleur
    for _, row in commune_data.iterrows():
        if isinstance(row['geometry'], Polygon):
            coordinates = [(x, y) for x, y in row['geometry'].exterior.coords]
            transformed_coords = [transform_coordinates(x, y) for x, y in coordinates]
            folium.Polygon(
                locations=transformed_coords,
                color='blue',  # Garder le contour bleu
                weight=2,
                fill=False,  # Pas de remplissage
            ).add_to(m)
    
    # Ajouter une heatmap des prix
    price_data_commune = price_data_commune.dropna(subset=['latitude', 'longitude', 'prix_m2'])
    heat_data = price_data_commune[['latitude', 'longitude', 'prix_m2']].values.tolist()
    
    if heat_data:
        HeatMap(heat_data, radius=10).add_to(m)

    # Ajouter un seul point par plage avec une icône simplifiée, rouge et plus grande
    for coord in beach_coordinates:
        # Vérifier si l'objet coord contient des attributs lat, lon
        if isinstance(coord, tuple) and len(coord) == 2:
            lat, lon = coord  # extraire latitude et longitude
            folium.Marker(
                location=[lat, lon],
                icon=folium.Icon(color='red', icon='info-sign', icon_size=(30, 30))  # Icône rouge et plus grande
            ).add_to(m)

    return m

# Fonction pour sauvegarder une carte
def save_map(commune_name, map_obj):
    # Créer le répertoire "maps" s'il n'existe pas
    os.makedirs('maps', exist_ok=True)
    
    # Sauvegarder la carte dans un fichier HTML
    file_name = f'maps/{commune_name}_map.html'
    map_obj.save(file_name)
    return file_name

# Fonction pour générer et enregistrer les cartes pour plusieurs communes
def generate_and_save_maps(gdf, price_data, tri_by_commune, unique_beach_coordinates_df):
    maps = {}
    for _, row in tri_by_commune.iterrows():
        commune_name = row['nom_commune']
        identifiant_tri = row['identifiant_tri']
        
        # Extraire les coordonnées des plages pour la commune depuis 'unique_beach_coordinates_df'
        beach_coordinates = unique_beach_coordinates_df[unique_beach_coordinates_df['nom_commune'] == commune_name]['beach_coordinates']

        if beach_coordinates.size > 0:
            beach_coordinates = beach_coordinates.iloc[0]  # Liste de tuples (latitude, longitude)
        
        # Créer une carte pour chaque commune
        m = create_map(gdf, commune_name, price_data, identifiant_tri, beach_coordinates)
        if m:
            # Sauvegarder la carte et l'ajouter au dictionnaire maps
            file_name = save_map(commune_name, m)
            maps[commune_name] = file_name

    return maps



def display_map_in_notebook(commune_name, gdf, price_data, tri_by_commune, unique_beach_coordinates_df,zoom=14,lat_sup=0,long_sup=0):
    # Extraire les données nécessaires de tri_by_commune pour la commune
    row = tri_by_commune[tri_by_commune['nom_commune'] == commune_name].iloc[0]
    identifiant_tri = row['identifiant_tri']
    
    # Extraire les coordonnées des plages pour la commune
    beach_coordinates = unique_beach_coordinates_df[unique_beach_coordinates_df['nom_commune'] == commune_name]['beach_coordinates']
    
    if beach_coordinates.size > 0:
        beach_coordinates = beach_coordinates.iloc[0]  # Liste de tuples (latitude, longitude)
    
    # Créer une carte centrée sur la commune avec des coordonnées par défaut si nécessaires
    price_data_commune = price_data[price_data['nom_commune'] == commune_name]
    latitude_centre = price_data_commune['latitude_centre'].iloc[0] if not price_data_commune.empty else 46.603354
    longitude_centre = price_data_commune['longitude_centre'].iloc[0] if not price_data_commune.empty else 1.888334

    # Créer une carte avec un zoom élevé pour se concentrer sur la commune
    m = folium.Map(location=[latitude_centre + lat_sup, longitude_centre + long_sup], zoom_start=zoom)  # Augmenter le zoom pour un niveau plus précis

    # Ajouter les polygones inondables sans remplissage de couleur
    commune_data = gdf[gdf['id_tri'] == identifiant_tri]
    for _, row in commune_data.iterrows():
        if isinstance(row['geometry'], Polygon):
            coordinates = [(x, y) for x, y in row['geometry'].exterior.coords]
            transformed_coords = [transform_coordinates(x, y) for x, y in coordinates]
            folium.Polygon(
                locations=transformed_coords,
                color='blue',
                weight=2,
                fill=False,
            ).add_to(m)
    
    # Ajouter la heatmap des prix
    price_data_commune = price_data_commune.dropna(subset=['latitude', 'longitude', 'prix_m2'])
    heat_data = price_data_commune[['latitude', 'longitude', 'prix_m2']].values.tolist()
    
    if heat_data:
        HeatMap(heat_data, radius=10).add_to(m)

    # Ajouter des markers pour les plages
    for coord in beach_coordinates:
        if isinstance(coord, tuple) and len(coord) == 2:
            lat, lon = coord
            folium.Marker(
                location=[lat, lon],
                icon=folium.Icon(color='red', icon='info-sign', icon_size=(30, 30))
            ).add_to(m)

    # Afficher la carte directement dans le notebook
    display(m)

# Fonction de conversion forcée pour transformer les coordonnées sous forme de liste de tuples (latitude, longitude)
def force_convert_to_tuple_list(beach_coordinates):
    try:
        # Si c'est déjà une liste, la convertir en liste de tuples
        if isinstance(beach_coordinates, list):
            # Convertir chaque élément de la liste en tuple (latitude, longitude)
            return [(float(coord[0]), float(coord[1])) for coord in beach_coordinates]

        # Si c'est une chaîne représentant une liste, on évalue la chaîne en une liste de tuples
        elif isinstance(beach_coordinates, str):
            coords = eval(beach_coordinates)  # Utilisation de eval avec prudence
            return [(float(coord[0]), float(coord[1])) for coord in coords]
        
        # Si c'est un tuple contenant deux éléments (latitude, longitude), on le convertit en liste
        elif isinstance(beach_coordinates, tuple) and len(beach_coordinates) == 2:
            return [(float(beach_coordinates[0]), float(beach_coordinates[1]))]
        
        # Si la donnée n'est pas dans un format attendu, retourner une liste vide
        else:
            return []

    except Exception:
        return []