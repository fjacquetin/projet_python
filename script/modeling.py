import numpy as np
import pandas as pd
import statsmodels.api as sm
from geopy.distance import geodesic
import math


def get_transactions_info(transactions):
    # Calcul des informations
    info = {
        'Nombre de transactions': len(transactions),
        'Part d\'appartements': (transactions['type_local'] == 'Appartement').mean(),
        'Prix moyen au mètre carré des appartements': transactions[transactions['type_local'] == 'Appartement']['prix_m2'].mean(),
        'Prix moyen au mètre carré des maisons': transactions[transactions['type_local'] == 'Maison']['prix_m2'].mean(),
        'Modalité la plus présente de classe_bilan_dpe': transactions['classe_bilan_dpe'].mode()[0],
        'Modalité la plus présente de période_construction_dpe': (
            transactions['periode_construction_dpe'].mode()[0]
        ),
        'Part des transactions avec un terrain': (transactions['terrain'] == 1).mean(),
        'Part des transactions avec une dépendance': (transactions['dependance'] == 1).mean(),
        'Part des transactions en ZI': (transactions['zone_inondable'] == 1).mean(),
        'Part des transactions en ZI et risque fort': (
            (transactions['zone_inondable'] == 1) & (transactions['code_scenario'] == '01For')).mean(),
        'Part des transactions en ZI en aléa de submersion de marine': (
            (transactions['libelle_type_inondation'] == 'submersion marine') & (transactions['zone_inondable'] == 1)
        ).mean()
    }
    
    # Fonction pour arrondir et formater les valeurs
    def format_value(value, is_percentage=False):
        if isinstance(value, str):  # Si c'est une chaîne (modalité), on ne modifie pas
            return value
        if is_percentage:  # Si c'est un pourcentage, on multiplie par 100, arrondit et affiche sans décimale
            return f"{round(value * 100)}%"  # Affichage sans décimales
        return round(value)  # Sinon, on arrondit à l'unité (sans décimales)

    # Appliquer la fonction de formatage à chaque valeur du dictionnaire
    formatted_info = {
        key: format_value(value, is_percentage=('Part' in key))
        for key, value in info.items()
    }

    # Convertir en DataFrame pour un affichage structuré sans trier
    info_df = pd.DataFrame(list(formatted_info.items()), columns=['Info', 'Valeur'])

    return info_df


def distance_minimale(lat1, lon1, liste_coords):
    """
    Calcule la distance minimale entre un point donné et une liste de coordonnées géographiques.
    
    Args:
        lat1, lon1: Coordonnées (latitude et longitude) du point de référence en degrés.
        liste_coords: Liste de tuples contenant des coordonnées (latitude, longitude).
    
    Returns:
        Distance minimale en kilomètres ou None si la liste est vide ou si lat1/lon1 sont invalides.
    """
    
    # Vérifier si lat1 ou lon1 sont NaN
    if math.isnan(lat1) or math.isnan(lon1):
        return None

    if not liste_coords:  # Vérifie si la liste est vide
        return None

    # Calcul de la distance minimale en utilisant geodesic
    return min(
        geodesic((lat1, lon1), (lat, lon)).kilometers for lat, lon in liste_coords
    )
    

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


def construire_modele_regression(df, colonnes_explicatives, colonne_dependante = "log_prix_m2"):
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
        tableau.rename(columns={col: f"{prefixe} - M{i+1}"}, inplace=True)
    
    # Supprimer les titres des colonnes contenant "pvalue"
    tableau = tableau.rename(columns={col: "" for col in tableau.columns if "pvalue" in col})
    
    return tableau


# Vecteurs ajoutés
ordre_variables_app = [
    'Observations',
    'R² ajusté',
    'const',
    'zone_inondable',
    'zone_inondable x debordement',
    'scenario_04Fai',
    'scenario_02Moy_03Mcc',
    'scenario_01For',
    'log_distance_centre_ville',
    'log_distance_min_beach',
    'log_distance_min_station',
    'log_surface_reelle_bati',
    'nombre_pieces_principales',
    'terrain',
    'dependance',
    'periode_construction_dpe_1948-1974',
    'periode_construction_dpe_1975-1988',
    'periode_construction_dpe_1989-2000',
    'periode_construction_dpe_2001-2012',
    'periode_construction_dpe_après 2013',
    'dpe_D',
    'dpe_C',
    'dpe_B',
    'dpe_A',
    'population_10000-20000',
    'population_plus_20000',
]


ordre_variables_mai = [
    'Observations',
    'R² ajusté',
    'const',
    'zone_inondable',
    'zone_inondable x debordement',
    'scenario_04Fai',
    'scenario_02Moy_03Mcc',
    'scenario_01For',
    'log_distance_centre_ville',
    'log_distance_min_beach',
    'log_distance_min_station',
    'log_surface_reelle_bati',
    'nombre_pieces_principales',
    'terrain',
    'dependance',
    'periode_construction_dpe_1948-1974',
    'periode_construction_dpe_1975-1988',
    'periode_construction_dpe_1989-2000',
    'periode_construction_dpe_2001-2012',
    'periode_construction_dpe_après 2013',
    'dpe_D',
    'dpe_C',
    'dpe_B',
    'dpe_A',
    'population_10000-20000',
    'population_plus_20000'
]


def nettoyer_coordinates(coords):
    """
    Cette fonction permet de nettoyer une valeur de coordonnées en fonction de son type.

    Arguments:
    coords : Peut être de type liste, flottant ou None.
        - Si `coords` est déjà une liste, elle est retournée telle quelle.
        - Si `coords` est un nombre flottant ou `None`, la fonction retourne `None`.
        - Dans tous les autres cas, la valeur de `coords` est retournée sans modification.

    Retour:
    - Une liste si `coords` est une liste.
    - `None` si `coords` est un nombre flottant ou `None`.
    - La valeur originale de `coords` si elle est valide et ne correspond à aucun des cas précédents.

    Exemple:
    >>> nettoyer_coordinates([1.0, 2.0, 3.0])
    [1.0, 2.0, 3.0]

    >>> nettoyer_coordinates(None)
    None

    >>> nettoyer_coordinates(5.5)
    None
    """
    if isinstance(coords, list):  # Si c'est déjà une liste, la garder
        return coords
    if isinstance(coords, float) or coords is None:  # Si c'est un NaN ou autre, retourner None
        return None
    return coords  # Par défaut, retourner la valeur initiale (si elle est correcte)


def traiter_resultats(modele_app1, modele_app2, modele_app3, modele_app4, modele_mai1, modele_mai2, modele_mai3, modele_mai4):
    """
    Fonction pour traiter les résultats des modèles d'appartements et de maisons en plusieurs étapes.
    
    Cette fonction effectue les opérations suivantes :
    - Extraction des résultats pour les modèles d'appartements et de maisons.
    - Filtrage des variables associées à chaque résultat.
    - Fusion des résultats en un seul tableau pour les appartements et un autre pour les maisons.
    - Traitement des coefficients et des p-values (conversion en numérique, arrondi, ajout d'étoiles aux p-values).
    - Réorganisation des lignes dans les tableaux résultants.
    - Renommage des colonnes pour les distinguer entre appartements et maisons.
    
    Arguments :
    modele_app1, modele_app2, modele_app3, modele_app4 : modèles pour les appartements (4 modèles)
    modele_mai1, modele_mai2, modele_mai3, modele_mai4 : modèles pour les maisons (4 modèles)
    
    Retourne :
    tuple : (tableau_app, tableau_mai) où chaque tableau est un DataFrame contenant les résultats traités
    pour les appartements et les maisons respectivement.
    """
    
    # Extraction des résultats pour les modèles appartements
    resultats_app1 = extraire_resultats_modele(modele_app1, "A.1")
    resultats_app2 = extraire_resultats_modele(modele_app2, "A.2")
    resultats_app3 = extraire_resultats_modele(modele_app3, "A.3")
    resultats_app4 = extraire_resultats_modele(modele_app4, "A.4")

    # Extraction des résultats pour les modèles maisons
    resultats_mai1 = extraire_resultats_modele(modele_mai1, "M.1")
    resultats_mai2 = extraire_resultats_modele(modele_mai2, "M.2")
    resultats_mai3 = extraire_resultats_modele(modele_mai3, "M.3")
    resultats_mai4 = extraire_resultats_modele(modele_mai4, "M.4")

    # Retirer les coefficients associés aux communes pour davantage de lisibilité
    resultats_app1 = filtrer_variables(resultats_app1)
    resultats_app2 = filtrer_variables(resultats_app2)
    resultats_app3 = filtrer_variables(resultats_app3)
    resultats_app4 = filtrer_variables(resultats_app4)

    resultats_mai1 = filtrer_variables(resultats_mai1)
    resultats_mai2 = filtrer_variables(resultats_mai2)
    resultats_mai3 = filtrer_variables(resultats_mai3)
    resultats_mai4 = filtrer_variables(resultats_mai4)

    # Effectuer les jointures sur la colonne 'variable' pour les appartements puis les maisons
    tableau_app = resultats_app1.merge(resultats_app2, on="variable", how="outer")
    tableau_app = tableau_app.merge(resultats_app3, on="variable", how="outer")
    tableau_app = tableau_app.merge(resultats_app4, on="variable", how="outer")

    tableau_mai = resultats_mai1.merge(resultats_mai2, on="variable", how="outer")
    tableau_mai = tableau_mai.merge(resultats_mai3, on="variable", how="outer")
    tableau_mai = tableau_mai.merge(resultats_mai4, on="variable", how="outer")

    # Sélectionner les colonnes des coefficients pour les appartements et les maisons
    coef_columns_app = [col for col in tableau_app.columns if "_coef" in col]
    coef_columns_mai = [col for col in tableau_mai.columns if "_coef" in col]

    # Convertir en float et arrondir les coefficients
    tableau_app[coef_columns_app] = tableau_app[coef_columns_app].apply(pd.to_numeric, errors='coerce')
    tableau_mai[coef_columns_mai] = tableau_mai[coef_columns_mai].apply(pd.to_numeric, errors='coerce')

    # Appliquer l'arrondi et ajouter des étoiles aux p-values pour les appartements et les maisons
    model_ids_app = [col.split("_")[0] for col in tableau_app.columns if "_pvalue" in col]
    model_ids_mai = [col.split("_")[0] for col in tableau_mai.columns if "_pvalue" in col]

    tableau_app = arrondir_pvalue_ajouter_etoiles(tableau_app, model_ids_app)
    tableau_mai = arrondir_pvalue_ajouter_etoiles(tableau_mai, model_ids_mai)

    # Réorganiser les lignes pour les deux tableaux (appartements et maisons)
    tableau_app = reordonner_lignes(tableau_app, ordre_variables_app)
    tableau_mai = reordonner_lignes(tableau_mai, ordre_variables_mai)

    # Appliquer le renommage des colonnes pour chaque tableau
    tableau_app = renommer_coef_colonnes(tableau_app, "Appart")
    tableau_mai = renommer_coef_colonnes(tableau_mai, "Maison")

    app_columns = [col for col in tableau_app.columns if col.startswith("App")]
    mai_columns = [col for col in tableau_mai.columns if col.startswith("Mai")]

    # Arrondir les valeurs dans ces colonnes à 4 chiffres après la virgule
    tableau_app[app_columns] = tableau_app[app_columns].round(4)
    tableau_app[app_columns] = tableau_app[app_columns].applymap(lambda x: f"{x:.4f}".rstrip('0').rstrip('.'))

    tableau_mai[mai_columns] = tableau_mai[mai_columns].round(4)
    tableau_mai[mai_columns] = tableau_mai[mai_columns].applymap(lambda x: f"{x:.4f}".rstrip('0').rstrip('.'))

    # Retourner les deux tableaux traités
    return tableau_app, tableau_mai


def prepare_columns(df, modeling):
    """
    Cette fonction prépare les colonnes du DataFrame en effectuant diverses transformations et 
    en définissant des listes de colonnes explicatives et géographiques pour une analyse ultérieure.
    
    Elle applique notamment une transformation logarithmique sur certaines variables continues 
    et génère plusieurs listes de colonnes explicatives pour différentes étapes d'un modèle.

    Parameters:
    -----------
    df : pandas.DataFrame
        Le DataFrame contenant les données à transformer.
    modeling : module
        Le module contenant la fonction `transformer_log` utilisée pour appliquer les transformations logarithmiques.

    Returns:
    --------
    df : pandas.DataFrame
        Le DataFrame avec les colonnes transformées.
    colonnes_geographiques : list
        Liste des colonnes géographiques après transformation logarithmique.
    colonnes_explicatives : list
        Liste des colonnes explicatives de base (avant ajout de certaines autres variables).
    colonnes_explicatives1 : list
        Liste des colonnes explicatives incluant les variables commençant par 'commune_'.
    colonnes_explicatives2 : list
        Liste des colonnes explicatives incluant les colonnes géographiques.
    colonnes_explicatives3 : list
        Liste des colonnes explicatives excluant 'zone_inondable' et incluant 'scenario'.
    colonnes_explicatives4 : list
        Liste des colonnes explicatives incluant l'interaction 'zone_inondable x debordement'.
    colonne_dependante : str
        La colonne dépendante (ici, la transformation logarithmique du prix au mètre carré).
    """
    
    # Liste des variables continues à transformer en log
    variables_continues = [
        "surface_reelle_bati",
        "prix_m2",
        "distance_min_beach",
        "distance_min_station",
        "distance_centre_ville"
    ]
    
    # Applique la transformation logarithmique sur les variables continues
    df = modeling.transformer_log(df, variables_continues)
    
    # Liste des colonnes géographiques après transformation logarithmique
    colonnes_geographiques = [
        "log_distance_min_beach",
        "log_distance_min_station",
        "log_distance_centre_ville"
    ]
    
    # Liste de base des colonnes explicatives
    colonnes_explicatives = [
        "zone_inondable",
        "log_surface_reelle_bati",
        "nombre_pieces_principales",
        'dependance',
        'terrain'
    ] + [
        col for col in df.columns if col.startswith('population')
    ] + [
        col for col in df.columns if col.startswith('dpe')
    ] + [
        col for col in df.columns if col.startswith('periode_construction_dpe_')
    ]
    
    # Ajoute les colonnes commençant par 'commune_' à la liste des explicatives
    colonnes_explicatives1 = colonnes_explicatives + [col for col in df.columns if col.startswith('commune_')]
    
    # Ajoute les colonnes géographiques à la liste des explicatives
    colonnes_explicatives2 = colonnes_explicatives1 + colonnes_geographiques
    
    # Liste des colonnes explicatives excluant 'zone_inondable' et incluant 'scenario'
    colonnes_explicatives3 = [col for col in colonnes_explicatives2 if col != "zone_inondable"] + [
        col for col in df.columns if col.startswith("scenario")
    ]
    
    # Liste des colonnes explicatives incluant l'interaction 'zone_inondable x debordement'
    colonnes_explicatives4 = colonnes_explicatives2 + ['zone_inondable x debordement']
    
    # Définir la colonne dépendante (log du prix au mètre carré)
    colonne_dependante = "log_prix_m2"
    
    # Retourner le DataFrame modifié et toutes les listes de colonnes créées
    return df, colonnes_geographiques, colonnes_explicatives, colonnes_explicatives1, colonnes_explicatives2, colonnes_explicatives3, colonnes_explicatives4, colonne_dependante
