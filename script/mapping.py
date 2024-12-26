import folium
from folium.plugins import HeatMap
import geopandas as gpd
from shapely.geometry import Polygon, MultiPolygon
import os
import numpy as np
from PIL import Image
import io


def extract_polygons_from_multipolygons(gdf):
    """
    Transforme un GeoDataFrame en un nouveau GeoDataFrame contenant uniquement des Polygons.
    Les MultiPolygons sont décomposés en plusieurs Polygons, chacun étant associé à son 'id_tri'.

    Parameters:
        gdf (GeoDataFrame): Un GeoDataFrame contenant au minimum les colonnes 'id_tri' et 'geometry'.

    Returns:
        GeoDataFrame: Un nouveau GeoDataFrame avec uniquement des Polygons.
    """
    # Liste pour stocker les nouvelles lignes du GeoDataFrame
    polygons_data = []

    for _, row in gdf.iterrows():
        geom = row['geometry']
        if isinstance(geom, Polygon):
            # Ajouter le Polygon directement
            polygons_data.append({'id_tri': row['id_tri'], 'geometry': geom})
        elif isinstance(geom, MultiPolygon):
            # Décomposer le MultiPolygon en Polygons
            for poly in geom.geoms:
                polygons_data.append({'id_tri': row['id_tri'], 'geometry': poly})

    # Créer un nouveau GeoDataFrame à partir des Polygons
    return gpd.GeoDataFrame(polygons_data, crs=gdf.crs)


def plot_polygons_on_map(m, geo_data, color='blue', weight=2, fill=False):
    """
    Affiche les polygones d'un GeoDataFrame sur une carte Folium.

    Parameters:
        m (folium.Map): Carte Folium sur laquelle ajouter les polygones.
        geo_data (GeoDataFrame): GeoDataFrame contenant une colonne 'geometry' avec des polygones.
        color (str): Couleur des contours des polygones. Par défaut 'blue'.
        weight (int): Épaisseur des contours des polygones. Par défaut 2.
        fill (bool): Indique si les polygones doivent être remplis de couleur. Par défaut False.

    Returns:
        folium.Map: Carte Folium avec les polygones ajoutés.
    """
    # Vérifier si le GeoDataFrame est vide
    if geo_data.empty:
        print("Le GeoDataFrame est vide. Aucun polygone à afficher.")
        return m

    # Extraire uniquement les polygones du GeoDataFrame
    gdf_tri = extract_polygons_from_multipolygons(geo_data)
    gdf_tri = gdf_tri[['geometry']]

    for geom in gdf_tri['geometry']:
        if isinstance(geom, Polygon):
            # Ajouter un Polygon
            coords = [(y, x) for x, y in geom.exterior.coords]  # Extraire les coordonnées (lat, long)
            folium.Polygon(
                locations=coords,
                color=color,
                weight=weight,
                fill=fill
            ).add_to(m)
        elif isinstance(geom, MultiPolygon):
            # Parcourir chaque Polygon dans le MultiPolygon
            for poly in geom.geoms:
                coords = [(y, x) for x, y in poly.exterior.coords]
                folium.Polygon(
                    locations=coords,
                    color=color,
                    weight=weight,
                    fill=fill
                ).add_to(m)

    return m


def create_map(commune_name, price_data, communes_coordinates, gdf, zoom=14, latitude_add=0, longitude_add=0):
    """
    Crée une carte Folium avec :
    - Les polygones inondables
    - Une heatmap des prix
    - Des marqueurs pour les plages, la mairie, le port et les stations.
    - Une légende dynamique des prix immobiliers en fonction des déciles.

    Parameters:
        commune_name (str): Nom de la commune à traiter.
        price_data (DataFrame): Données des prix contenant `nom_commune`, `latitude`, `longitude`, `prix_m2`.
        communes_coordinates (DataFrame): Coordonnées géographiques des communes, avec des informations supplémentaires.
        gdf (GeoDataFrame): Données géographiques contenant des polygones.
        zoom (int, optional): Niveau de zoom initial de la carte. Par défaut 14.
        latitude_add (float, optional): Décalage en latitude. Par défaut 0.
        longitude_add (float, optional): Décalage en longitude. Par défaut 0.

    Returns:
        folium.Map: La carte générée ou None si les données sont manquantes.
    """

    # Extraire les données pour la commune spécifiée
    commune_row = communes_coordinates[communes_coordinates['nom_commune'] == commune_name]
    price_data_commune = price_data[price_data['nom_commune'] == commune_name]

    if commune_row.empty or price_data_commune.empty:
        return None
    
    identifiant_tri = price_data_commune['identifiant_tri'].dropna().iloc[0]
    commune_data = gdf[gdf['id_tri'] == identifiant_tri]

    # Vérifier si commune_data est vide
    if commune_data.empty:
        return None

    # Extraction des coordonnées supplémentaires
    beach_coordinates = commune_row.get('beach_coordinates', []).iloc[0]  
    station_coordinates = commune_row.get('station', []) .iloc[0] 
    latitude_mairie = commune_row['latitude_mairie'].iloc[0]
    longitude_mairie = commune_row['longitude_mairie'].iloc[0]
    latitude_port = commune_row['latitude_port'].iloc[0]
    longitude_port = commune_row['longitude_port'].iloc[0]

    # Extraire les données de prix pour la commune

    latitude_centre = (
        commune_row['latitude_centre'].iloc[0] + latitude_add
        if not commune_row.empty else 46.603354 + latitude_add
    )
    longitude_centre = (
        commune_row['longitude_centre'].iloc[0] + longitude_add
        if not commune_row.empty else 1.888334 + longitude_add
    )

    # Créer la carte centrée sur la commune avec le niveau de zoom spécifié
    m = folium.Map(location=[latitude_centre, longitude_centre], zoom_start=zoom)

    # Ajouter les polygones inondables
    plot_polygons_on_map(m, commune_data, color='blue', weight=2, fill=False)

    # Extraire les prix pour les déciles
    price_data_commune = price_data_commune.dropna(subset=['latitude', 'longitude', 'prix_m2'])
    
    # Calcul des déciles arrondis à l'unité
    first_decile = round(np.percentile(price_data_commune['prix_m2'], 10))
    median = round(np.percentile(price_data_commune['prix_m2'], 50))
    ninth_decile = round(np.percentile(price_data_commune['prix_m2'], 90))

    # Formatage avec séparateur de milliers
    first_decile = f"{first_decile:,.0f}".replace(",", " ")
    median = f"{median:,.0f}".replace(",", " ")
    ninth_decile = f"{ninth_decile:,.0f}".replace(",", " ")

    # Ajouter la heatmap des prix (sans gradient personnalisé)
    heat_data = price_data_commune[['latitude', 'longitude', 'prix_m2']].values.tolist()
    if heat_data:
        heatmap = HeatMap(heat_data, radius=10)
        heatmap.add_to(m)

    # Ajouter une légende avec les déciles
    legend_html = f"""
    <div style="position: fixed; 
            bottom: 50px; left: 50px; width: 200px; height: 140px; 
            background-color: white; border: 2px solid black; 
            padding: 10px; font-size: 12px; z-index: 9999; 
            box-shadow: 3px 3px 3px rgba(0, 0, 0, 0.3);">
    <b>{commune_name}</b><br>
    <i style="width: 20px; height: 10px; display: inline-block;"></i> 1er décile : {first_decile}€<br>
    <i style="width: 20px; height: 10px; display: inline-block;"></i> Médiane : {median}€<br>
    <i style="width: 20px; height: 10px; display: inline-block;"></i> 9ème décile : {ninth_decile}€
    </div>
    """
    m.get_root().html.add_child(folium.Element(legend_html))

    # Ajouter des marqueurs pour les plages
    add_markers_from_list(m, beach_coordinates, color='green', icon='info-sign', tooltip="Plage")

    # Ajouter un marker pour la mairie
    if not np.isnan(latitude_mairie) and not np.isnan(longitude_mairie):
        add_marker(m, latitude_mairie, longitude_mairie, color='red', icon='home', tooltip="Mairie")

    # Ajouter un marker pour le port
    if not np.isnan(latitude_port) and not np.isnan(longitude_port):
        add_marker(m, latitude_port, longitude_port, color='purple', icon='home', tooltip="Port")

    # Ajouter des marqueurs pour les stations
    add_markers_from_list(m, station_coordinates, color='blue', icon='info-sign', tooltip="Station")

    return m


# Fonction pour sauvegarder une carte
def save_map(commune_name, map_obj):
    # Créer le répertoire "maps" s'il n'existe pas
    os.makedirs('maps', exist_ok=True)
    
    # Sauvegarder la carte dans un fichier HTML
    file_name = f'maps/{commune_name}_map.html'
    map_obj.save(file_name)
    return file_name

def generate_and_save_maps(price_data, communes_coordinates, gdf):
    """
    Génère et sauvegarde des cartes pour chaque commune.

    Args:
        price_data (pd.DataFrame): Les données de prix associées aux communes.
        communes_coordinates (pd.DataFrame): Les coordonnées des communes.
        gdf (gpd.GeoDataFrame): Le GeoDataFrame contenant les données géospatiales.

    Returns:
        dict: Un dictionnaire associant le nom de chaque commune au chemin du fichier de la carte générée.
    """
    maps = {}

    for _, row in communes_coordinates.iterrows():
        # Récupérer le nom de la commune
        commune_name = row['nom_commune']

        # Vérifier si des données de prix existent pour cette commune
        if price_data[price_data['nom_commune'] == commune_name].empty:
            m = None # Arrête complètement l'exécution de la fonction
        else:
            # Générer une carte pour la commune
            m = create_map(commune_name, price_data, communes_coordinates, gdf)

        # Vérifier si la carte a bien été générée
        if m is not None:
            # Sauvegarder la carte et ajouter le chemin au dictionnaire
            file_name = save_map(commune_name, m)
            maps[commune_name] = file_name

    return None


# Fonction pour ajouter un seul marker
def add_marker(m, lat, lon, color, icon, tooltip=None):
    folium.Marker(
        location=[lat, lon],
        icon=folium.Icon(color=color, icon=icon, icon_size=(30, 30)),
        tooltip=tooltip
    ).add_to(m)


# Fonction pour ajouter une liste de markers
def add_markers_from_list(m, coordinates, color, icon, tooltip):
    for coord in coordinates:
        if isinstance(coord, tuple) and len(coord) == 2:
            lat, lon = coord
            add_marker(m, lat, lon, color, icon, tooltip)
       

def display_map_in_notebook(commune_name, price_data, communes_coordinates, gdf, zoom=14, latitude_add=0, longitude_add=0):
    """
    Affiche une capture d'écran d'une carte Folium dans un notebook Jupyter.
    
    Args:
        commune_name (str): Nom de la commune.
        price_data (pd.DataFrame): Données de prix.
        communes_coordinates (pd.DataFrame): Coordonnées des communes.
        gdf (GeoDataFrame): GeoDataFrame contenant les données géographiques.
        zoom (int, optional): Niveau de zoom de la carte. Default à 14.
        latitude_add (float, optional): Ajustement de latitude. Default à 0.
        longitude_add (float, optional): Ajustement de longitude. Default à 0.
    
    Returns:
        Image: Une image PIL affichant la carte.
    """
    # Créer la carte Folium
    m = create_map(commune_name, price_data, communes_coordinates, gdf, zoom, latitude_add, longitude_add)
    
    # Générer l'image de la carte avec un niveau de détail de 10
    img_data = m._to_png(5)
    
    # Convertir l'image PNG en image PIL
    img = Image.open(io.BytesIO(img_data))
    
    # Sauvegarder l'image si nécessaire
    img.save(f"maps/{commune_name}.png")
    
    # Retourner l'image PIL
    return img


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