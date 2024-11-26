import requests as rq
import pandas as pd

def geolocaliser_actifs(df,
                        colonne_adresse,
                        colonne_latitude,
                        colonne_longitude,
                        root='https://api-adresse.data.gouv.fr/search/',
                        key='?q='
                        ):
    """
    Remplit les colonnes latitude et longitude manquantes en interrogeant l'API Adresse de data.gouv.fr.
    
    Args:
        df (pd.DataFrame): Le DataFrame contenant les adresses.
        colonne_adresse (str): Nom de la colonne contenant les adresses.
        colonne_latitude (str): Nom de la colonne pour la latitude.
        colonne_longitude (str): Nom de la colonne pour la longitude.
        root (str): URL de base de l'API (par défaut : API Adresse de data.gouv.fr).
        key (str): Clé de requête pour l'API (par défaut : '?q=').
    
    Returns:
        pd.DataFrame: Le DataFrame avec les colonnes latitude et longitude mises à jour.
    """
    for index, row in df.iterrows():
        address = row[colonne_adresse]
        req = rq.get(f'{root}{key}{address}')
        
        if req.status_code == 200:
            try:
                # Récupérer les informations de latitude et longitude
                response_data = pd.json_normalize(req.json()['features'])
                data = response_data.iloc[0]  # Prend le premier résultat
                
                # Mise à jour des colonnes latitude et longitude
                df.at[index, colonne_latitude] = data['geometry.coordinates'][1]  # Latitude
                df.at[index, colonne_longitude] = data['geometry.coordinates'][0]  # Longitude
            except IndexError:
                print(f"Aucune donnée trouvée pour l'adresse : {address}")
        else:
            print(f"Erreur de requête pour l'adresse : {address}, statut : {req.status_code}")
    return df

def geolocaliser_mairies(df, colonne_commune, colonne_latitude='latitude_mairie', colonne_longitude='longitude_mairie', url_base='https://api-adresse.data.gouv.fr/search/', key='?q='):
    """
    Récupère les coordonnées (latitude et longitude) des mairies des communes spécifiées dans un DataFrame.

    Args:
        df (pd.DataFrame): Le DataFrame contenant les noms des communes.
        colonne_commune (str): Le nom de la colonne contenant les noms des communes.
        colonne_latitude (str): Nom de la colonne pour la latitude (par défaut : 'latitude_mairie').
        colonne_longitude (str): Nom de la colonne pour la longitude (par défaut : 'longitude_mairie').
        url_base (str): URL de base de l'API (par défaut : API Adresse data.gouv.fr).
        key (str): Clé de requête pour l'API (par défaut : '?q=').

    Returns:
        pd.DataFrame: Le DataFrame avec les colonnes latitude et longitude mises à jour.
    """
    # Initialiser les colonnes latitude et longitude si elles n'existent pas
    if colonne_latitude not in df.columns:
        df[colonne_latitude] = None
    if colonne_longitude not in df.columns:
        df[colonne_longitude] = None

    for index, row in df.iterrows():
        commune_name = row[colonne_commune]
        address = f'Mairie+de+{commune_name}'  # Format de l'adresse à rechercher
        
        try:
            req = rq.get(f'{url_base}{key}{address}')
            
            if req.status_code == 200:
                try:
                    # Récupère les informations de latitude et longitude
                    df_result = pd.json_normalize(req.json()['features'])
                    data = df_result.iloc[0]  # Prend le premier résultat

                    # Mise à jour des coordonnées dans le DataFrame
                    df.at[index, colonne_latitude] = data['geometry.coordinates'][1]  # Latitude
                    df.at[index, colonne_longitude] = data['geometry.coordinates'][0]  # Longitude
                except IndexError:
                    print(f"Aucune donnée trouvée pour la commune : {commune_name}")
            else:
                print(f"Erreur de requête pour la commune : {commune_name}, statut : {req.status_code}")
        except rq.exceptions.RequestException as e:
            print(f"Erreur de connexion pour la commune : {commune_name}. Détails : {e}")

    return df