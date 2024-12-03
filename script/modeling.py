import math
import numpy as np
import pandas as pd
import statsmodels.api as sm

def distance_haversine(lat1, lon1, lat2, lon2):
    """
    Calcule la distance en kilomètres entre deux points géographiques
    (latitude, longitude) en utilisant la formule de Haversine.

    Args:
        lat1, lon1: Coordonnées (latitude et longitude) du premier point en degrés.
        lat2, lon2: Coordonnées (latitude et longitude) du second point en degrés.

    Returns:
        Distance entre les deux points en kilomètres.
    """
    # Rayon moyen de la Terre en kilomètres
    R = 6371.0

    # Convertir les degrés en radians
    lat1_rad = math.radians(lat1)
    lon1_rad = math.radians(lon1)
    lat2_rad = math.radians(lat2)
    lon2_rad = math.radians(lon2)

    # Calcul des différences
    delta_lat = lat2_rad - lat1_rad
    delta_lon = lon2_rad - lon1_rad

    # Formule de Haversine
    a = math.sin(delta_lat / 2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    distance = R * c

    return distance

def distance_minimale(lat1, lon1, liste_coords):
    """
    Calcule la distance minimale entre un point donné et une liste de coordonnées géographiques.
    
    Args:
        lat1, lon1: Coordonnées (latitude et longitude) du point de référence en degrés.
        liste_coords: Liste de tuples contenant des coordonnées (latitude, longitude).
    
    Returns:
        Distance minimale en kilomètres ou None si la liste est vide.
    """
    if not liste_coords:  # Vérifie si la liste est vide
        return None

    # Calcul de la distance minimale en utilisant la fonction `distance_haversine`
    distances = [distance_haversine(lat1, lon1, lat, lon) for lat, lon in liste_coords]
    return min(distances)

def transformer_log(df, colonnes):
    """
    Transforme les colonnes spécifiées en leur logarithme naturel et crée de nouvelles colonnes
    avec le préfixe 'log_'.

    Args:
        df (pd.DataFrame): DataFrame contenant les colonnes à transformer.
        colonnes (list): Liste des noms de colonnes à transformer.

    Returns:
        pd.DataFrame: DataFrame avec les colonnes transformées (remplace les valeurs 0 par NaN avant de prendre le log).
    """
    df = df.copy()
    for col in colonnes:
        log_col_name = f"log_{col}"  # Créer le nom de la nouvelle colonne
        df[log_col_name] = np.log(df[col].replace(0, np.nan))  # Calcul du log et ajout dans la nouvelle colonne
    return df

def construire_modele_regression(df, colonnes_explicatives, colonne_dependante):
    """
    Crée un modèle de régression linéaire à partir des données spécifiées.

    Args:
        df (pd.DataFrame): DataFrame contenant les données.
        colonnes_explicatives (list): Liste des colonnes explicatives.
        colonne_dependante (str): Nom de la colonne dépendante (variable cible).

    Returns:
        X (pd.DataFrame): Variables explicatives.
        y (pd.Series): Variable dépendante.
    """
    # Copie du DataFrame pour éviter de modifier l'original
    df = df.copy()

    # Retirer les lignes avec des valeurs manquantes dans les colonnes nécessaires
    colonnes_model = colonnes_explicatives + [colonne_dependante]
    df_clean = df.dropna(subset=colonnes_model)

    # Création des variables explicatives X
    X = df_clean[colonnes_explicatives]

    # Variable dépendante y
    y = df_clean[colonne_dependante]

    return X, y
