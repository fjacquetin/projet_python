from concurrent.futures import ThreadPoolExecutor
import requests as rq
import pandas as pd
import ast as ast
from shapely.geometry import Point

def fetch_coordinates(index, address, root, key):
    """
    Effectue une requête pour récupérer les coordonnées d'une adresse.
    
    Args:
        index (int): L'index de la ligne.
        address (str): L'adresse à géolocaliser.
        root (str): URL de base de l'API.
        key (str): Clé de requête pour l'API.
    
    Returns:
        tuple: Index, latitude, longitude (ou None si une erreur survient).
    """
    try:
        req = rq.get(f'{root}{key}{address}')
        if req.status_code == 200:
            response_data = pd.json_normalize(req.json()['features'])
            data = response_data.iloc[0]  # Prend le premier résultat
            latitude = data['geometry.coordinates'][1]  # Latitude
            longitude = data['geometry.coordinates'][0]  # Longitude
            return index, latitude, longitude
        else:
            print(f"Erreur de requête pour l'adresse : {address}, statut : {req.status_code}")
    except Exception:
        return index, None, None

def geolocaliser_actifs(df,
                        colonne_adresse,
                        colonne_latitude,
                        colonne_longitude,
                        root='https://api-adresse.data.gouv.fr/search/',
                        key='?q=',
                        max_workers=10):
    """
    Remplit les colonnes latitude et longitude manquantes en interrogeant l'API Adresse de data.gouv.fr.
    Avec parallélisation des requêtes.
    
    Args:
        df (pd.DataFrame): Le DataFrame contenant les adresses.
        colonne_adresse (str): Nom de la colonne contenant les adresses.
        colonne_latitude (str): Nom de la colonne pour la latitude.
        colonne_longitude (str): Nom de la colonne pour la longitude.
        root (str): URL de base de l'API (par défaut : API Adresse de data.gouv.fr).
        key (str): Clé de requête pour l'API (par défaut : '?q=').
        max_workers (int): Nombre maximum de threads parallèles.
    
    Returns:
        pd.DataFrame: Le DataFrame avec les colonnes latitude et longitude mises à jour.
    """
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(fetch_coordinates, index, row[colonne_adresse], root, key): index
            for index, row in df.iterrows()
        }
        for future in futures:
            index, latitude, longitude = future.result()
            if latitude is not None and longitude is not None:
                df.at[index, colonne_latitude] = latitude
                df.at[index, colonne_longitude] = longitude

    return df

# Fonction pour vérifier si le point est dans le polygone de la commune
def verifier_dans_polygone(latitude, longitude, geometry):
    """
    Vérifie si un point (latitude, longitude) est dans un polygone.
    
    Args:
        latitude (float): Latitude du point.
        longitude (float): Longitude du point.
        geometry (shapely.geometry.Polygon): Polygone représentant la commune.
        
    Returns:
        bool: True si le point est dans le polygone, False sinon.
    """
    point = Point(longitude, latitude)  # Crée un objet Point avec les coordonnées
    return geometry.contains(point)  # Vérifie si le point est dans le polygone

# Fonction pour rechercher les coordonnées à partir d'un mot-clé
def geolocaliser_mot_cle(df, colonne_commune, colonne_geometry, mots_cles, colonne_latitude, colonne_longitude, url_base='https://api-adresse.data.gouv.fr/search/', key='?q='):
    """
    Recherche successivement les coordonnées d'une commune en utilisant plusieurs mots-clés et vérifie si elles se trouvent dans le polygone.
    
    Args:
        df (pd.DataFrame): Le GeoDataFrame contenant les noms des communes et la colonne 'geometry'.
        colonne_commune (str): Le nom de la colonne contenant les noms des communes.
        colonne_geometry (str): Le nom de la colonne contenant les polygones géographiques.
        mots_cles (list): Liste des chaînes de recherche (par exemple, ["Hotel+de+Ville+de", "Mairie+de"]).
        colonne_latitude (str): Nom de la colonne pour la latitude
        colonne_longitude (str): Nom de la colonne pour la longitude
        url_base (str): URL de base de l'API (par défaut : API Adresse data.gouv.fr).
        key (str): Clé de requête pour l'API (par défaut : '?q=').

    Returns:
        pd.DataFrame: Le GeoDataFrame avec les colonnes latitude et longitude mises à jour (ou None si hors polygone).
    """
    # Initialiser les colonnes latitude et longitude si elles n'existent pas
    if colonne_latitude not in df.columns:
        df[colonne_latitude] = None
    if colonne_longitude not in df.columns:
        df[colonne_longitude] = None

    for index, row in df.iterrows():
        commune_name = row[colonne_commune]
        geometry = row[colonne_geometry]  # Polygone correspondant à la commune
        latitude, longitude = row[colonne_latitude], row[colonne_longitude]  # Récupérer les coordonnées existantes

        # Si les coordonnées existent déjà, passer à la commune suivante
        if latitude is not None and longitude is not None:
            continue

        # Essayer chaque mot-clé jusqu'à ce que les coordonnées soient trouvées
        for mot_cle in mots_cles:
            address = f'{mot_cle}+{commune_name}'  # Format de l'adresse à rechercher

            try:
                req = rq.get(f'{url_base}{key}{address}')
                
                if req.status_code == 200:
                    try:
                        # Récupère les informations de latitude et longitude
                        df_result = pd.json_normalize(req.json()['features'])
                        data = df_result.iloc[0]  # Prend le premier résultat

                        latitude, longitude = data['geometry.coordinates'][1], data['geometry.coordinates'][0]

                        # Si les coordonnées sont trouvées, vérifier si elles sont dans le polygone
                        if latitude is not None and longitude is not None:
                            if verifier_dans_polygone(latitude, longitude, geometry):
                                df.at[index, colonne_latitude] = latitude
                                df.at[index, colonne_longitude] = longitude
                                break  # Si trouvé, sortir de la boucle
                    except IndexError:
                        pass
                else:
                    pass
            except rq.exceptions.RequestException:
                pass

    return df


def get_townhall_coordinates(commune_name, api):
    """
    Récupère les coordonnées de la mairie d'une commune.

    Args:
        commune_name (str): Nom de la commune.
        api (overpy.Overpass): Instance de l'API Overpass.

    Returns:
        tuple: Latitude et longitude de la mairie ou (None, None) si aucune correspondance.
    """
    try:
        # Construire la requête Overpass pour la mairie
        query = f"""
        [out:json];
        area[name="{commune_name}"]->.searchArea;
        node["amenity"="townhall"](area.searchArea);
        out body;
        """
        # Exécuter la requête
        result = api.query(query)

        # Si des résultats sont trouvés, retourner les coordonnées du premier node
        if result.nodes:
            node = result.nodes[0]
            return node.lat, node.lon
        
        # Si aucune mairie trouvée
        return None, None

    except Exception:
        return None, None

    
def get_beach_coordinates(commune_name, api):
    """
    Récupère les coordonnées des plages dans une commune via l'API Overpass.

    Args:
        commune_name (str): Nom de la commune.
        api (overpy.Overpass): Instance de l'API Overpass.

    Returns:
        list[tuple]: Liste des coordonnées des plages sous forme de (latitude, longitude).
    """
    try:
        # Construire la requête Overpass
        query = f"""
        [out:json];
        area["name"="{commune_name}"]->.searchArea;
        (
        node["natural"="beach"](area.searchArea);
        node["leisure"="beach"](area.searchArea);
        node["tourism"="beach"](area.searchArea);
        node["landuse"="recreation_ground"](area.searchArea);
        );
        out body;
        """
        # Envoyer la requête
        result = api.query(query)

        # Liste pour stocker les coordonnées des plages
        beach_coordinates = []

        # Traitement des nœuds (nodes)
        if result.nodes:
            for node in result.nodes:
                beach_coordinates.append((node.lat, node.lon))

        return beach_coordinates

    except Exception:
        return []
    
def get_station_coordinates(commune_name, api):
    """
    Récupère les coordonnées des gares d'une commune via l'API Overpass.
    
    Args:
        commune_name (str): Nom de la commune.
        api (overpy.Overpass): Instance de l'API Overpass.
        
    Returns:
        list[tuple]: Liste des coordonnées des gares sous forme de (latitude, longitude).
    """
    try:
        # Construire la requête Overpass pour récupérer les gares
        query = f"""
        [out:json];
        area["name"="{commune_name}"]->.searchArea;
        (
          node["railway"="station"](area.searchArea);
          node["amenity"="transport_station"](area.searchArea);
          node["railway"="halt"](area.searchArea);
          node["public_transport"="station"](area.searchArea);
        );
        out body;
        """
        # Envoyer la requête
        result = api.query(query)

        # Liste pour stocker les coordonnées des gares
        station_coordinates = []

        # Traiter les nœuds récupérés
        for node in result.nodes:
            lat, lon = node.lat, node.lon
            station_coordinates.append((lat, lon))

        # Retourner la liste des gares trouvées
        return station_coordinates if station_coordinates else [(None, None)]

    except Exception:
        return [(None, None)]
    
def get_ports(commune_name, api):
    """
    Recherche les ports dans une commune via l'API Overpass.

    Args:
        commune_name (str): Nom de la commune.
        api (overpy.Overpass): Instance de l'API Overpass.

    Returns:
        float: Latitude du port ou None si aucun port trouvé.
        float: Longitude du port ou None si aucun port trouvé.
    """
    try:
        # Construire la requête Overpass pour rechercher des ports
        query = f"""
        [out:json];
        area["name"="{commune_name}"]->.searchArea;
        (
          node["amenity"="harbor"](area.searchArea);
          way["amenity"="harbor"](area.searchArea);
          relation["amenity"="harbor"](area.searchArea);
        );
        out body;
        """
        result = api.query(query)

        # Initialisation des coordonnées à None
        latitude = None
        longitude = None

        # Traitement des nœuds (ports sous forme de nœuds)
        if result.nodes:
            # Prendre la première coordonnée du premier port trouvé
            first_node = result.nodes[0]
            latitude = first_node.lat
            longitude = first_node.lon

        # Traitement des chemins (ways) pour les ports
        if result.ways and latitude is None:
            # Calculer le centre du premier chemin de port trouvé
            way = result.ways[0]
            node_coords = [
                (node.lat, node.lon) 
                for node in way.nodes 
                if hasattr(node, "lat") and hasattr(node, "lon")
            ]
            if node_coords:
                # Calculer le centre des nœuds du port
                lat_center = sum(lat for lat, lon in node_coords) / len(node_coords)
                lon_center = sum(lon for lat, lon in node_coords) / len(node_coords)
                latitude = lat_center
                longitude = lon_center

        # Traitement des relations (ports sous forme de relations)
        if result.relations and latitude is None:
            # Calculer le centre du premier port trouvé dans une relation
            relation = result.relations[0]
            node_coords = [
                (member.lat, member.lon) 
                for member in relation.members 
                if hasattr(member, "lat") and hasattr(member, "lon")
            ]
            if node_coords:
                # Calculer le centre des membres du port
                lat_center = sum(lat for lat, lon in node_coords) / len(node_coords)
                lon_center = sum(lon for lat, lon in node_coords) / len(node_coords)
                latitude = lat_center
                longitude = lon_center

        # Si aucun port n'a été trouvé, retourner None
        if latitude is None or longitude is None:
            return None, None

        # Retourner les coordonnées du premier port trouvé
        return latitude, longitude

    except Exception:
        return None, None  # Renvoie des None en cas d'erreur

# Fonction pour traiter uniquement les lignes bien formées
def safe_convert_coordinates(value):
    try:
        parsed = ast.literal_eval(value)
        return [(float(lat), float(lon)) for lat, lon in parsed]
    except Exception:
        return value