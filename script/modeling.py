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
    X = sm.add_constant(X)
    model = sm.OLS(y, X).fit()
    
    return model

# Fonction pour extraire les résultats des modèles
def extraire_resultats_modele(modele, suffixe):
    """
    Cette fonction extrait les résultats des modèles de régression, notamment les coefficients des variables,
    les p-values, ainsi que les informations supplémentaires telles que le nombre d'observations et le R² ajusté.
    
    Les résultats sont retournés dans un DataFrame, avec un suffixe ajouté aux noms des colonnes pour distinguer
    les résultats de différents modèles.
    
    Paramètres :
    modele : objet de modèle
        Modèle de régression ajusté, par exemple un modèle OLS de statsmodels.
    suffixe : str
        Suffixe à ajouter aux colonnes de coefficients et de p-values pour identifier les résultats du modèle.
    
    Retour :
    DataFrame
        DataFrame contenant les variables, les coefficients, et les p-values pour chaque modèle.
    """
    # Extraction du nombre d'observations et du R² ajusté
    n_obs = modele.nobs  # Nombre d'observations
    r2_adj = modele.rsquared_adj  # R² ajusté
    resultats = pd.DataFrame({
        "variable": modele.params.index,
        f"{suffixe}_coef": modele.params.values,
        f"{suffixe}_pvalue": modele.pvalues.values  # Remplacer 'signif' par 'pvalue'
    })
    
    # Ajouter les informations en haut du DataFrame
    info = pd.DataFrame({
        "variable": ["Observations", "R² ajusté"],
        f"{suffixe}_coef": [int(round(n_obs)), f"{r2_adj:.4f}"],  # Convertir Observations en entier et arrondir le R² ajusté à 4 chiffres
        f"{suffixe}_pvalue": ["", ""]
    })
    
    # Fusionner l'en-tête avec les résultats
    resultats = pd.concat([info, resultats], ignore_index=True)
    return resultats


# Fonction pour arrondir les p-values et ajouter des étoiles de significativité
def arrondir_pvalue_ajouter_etoiles(resultats, model_ids):
    """
    Cette fonction arrondit les p-values pour chaque modèle spécifié, et ajoute des étoiles de significativité 
    en fonction de la valeur de la p-value.
    
    Les p-values inférieures à 0.01 obtiennent trois étoiles (***), celles inférieures à 0.05 obtiennent deux 
    étoiles (**), celles inférieures à 0.1 obtiennent une étoile (*), et les autres p-values sont affichées sans étoiles.
    
    Paramètres :
    resultats : DataFrame
        DataFrame contenant les résultats des modèles, avec des colonnes de p-values.
    model_ids : list of str
        Liste des identifiants des modèles (par exemple ["A.1", "A.2"]) pour lesquels les p-values doivent être traitées.

    Retour :
    DataFrame
        DataFrame mis à jour avec les p-values arrondies et les étoiles de significativité ajoutées.
    """
    for model_id in model_ids:
        pvalue_col = f"{model_id}_pvalue"
        
        # Convertir les p-values en float (si possible) avant l'arrondi
        resultats[pvalue_col] = pd.to_numeric(resultats[pvalue_col], errors='coerce')
        
        # Appliquer un arrondi à 3 chiffres et ajouter des étoiles de significativité
        resultats[pvalue_col] = resultats[pvalue_col].apply(
            lambda p: f"{round(p, 3)}***" if p < 0.01 else (f"{round(p, 3)}**" if p < 0.05 else (f"{round(p, 3)}*" if p < 0.1 else f"{round(p, 3)}")) if pd.notna(p) else ""
        )
        
    return resultats

# Fonction pour filtrer les variables
def filtrer_variables(resultats):
    """
    Cette fonction filtre les variables dans un DataFrame en excluant celles dont le nom commence par 'commune'.
    Cela permet d'éviter d'afficher des variables liées aux communes dans les résultats des modèles.
    
    Paramètres :
    resultats : DataFrame
        DataFrame contenant les résultats des modèles, avec une colonne 'variable' indiquant les noms des variables.
    
    Retour :
    DataFrame
        DataFrame filtré, excluant les variables liées aux communes.
    """
    return resultats[~resultats["variable"].str.startswith("commune")]

# Fonction pour réorganiser les lignes selon l'ordre des variables et ajouter une ligne vide entre R² ajusté et const
def reordonner_lignes(tableau, ordre_variables):
    """
    Cette fonction réorganise les lignes d'un DataFrame selon un ordre spécifié dans `ordre_variables`.
    Elle permet de s'assurer que les variables apparaissent dans un ordre logique pour l'analyse des résultats.
    
    Paramètres :
    tableau : DataFrame
        DataFrame contenant les résultats des modèles avec une colonne 'variable'.
    ordre_variables : list of str
        Liste des variables dans l'ordre souhaité pour l'affichage.
    
    Retour :
    DataFrame
        DataFrame réorganisé selon l'ordre des variables spécifié.
    """
    # Vérifier que toutes les variables de l'ordre sont présentes dans le DataFrame
    variables_presentes = [var for var in ordre_variables if var in tableau['variable'].values]
    
    # Trier les lignes en fonction de l'ordre des variables
    tableau_reorganise = tableau.set_index("variable").loc[variables_presentes].reset_index()
    
    # Ajouter la ligne vide entre "R² ajusté" et "const"
    # tableau_reorganise = ajouter_ligne_vide(tableau_reorganise)
    
    return tableau_reorganise

# Renommer les colonnes des coefficients avec M1, M2, M3, M4 en fonction des modèles
def renommer_coef_colonnes(tableau, prefixe):
    """
    Cette fonction renomme les colonnes des coefficients dans un DataFrame en fonction du préfixe fourni,
    en ajoutant un suffixe "M1", "M2", "M3", "M4" pour chaque modèle. De plus, elle supprime les titres des 
    colonnes contenant les p-values.
    
    Paramètres :
    tableau : DataFrame
        DataFrame contenant les résultats des modèles avec des colonnes de coefficients et de p-values.
    prefixe : str
        Préfixe à ajouter avant "M1", "M2", "M3", "M4" pour identifier chaque modèle. Par exemple, "A" ou "M".
    
    Retour :
    DataFrame
        DataFrame avec les colonnes des coefficients renommées et les colonnes des p-values sans titre.
    """
    # Renommer les colonnes des coefficients
    for i, col in enumerate([col for col in tableau.columns if "_coef" in col]):
        tableau.rename(columns={col: f"({prefixe} - M{i+1})"}, inplace=True)
    
    # Supprimer les titres des colonnes contenant "pvalue"
    tableau = tableau.rename(columns={col: "" for col in tableau.columns if "pvalue" in col})
    
    return tableau