import requests as rq
import pandas as pd

def nettoyer_colonnes(df,
                      colonnes
                      ):
    """
    Nettoie les colonnes spécifiées dans un DataFrame :
    - Convertit en chaîne de caractères.
    - Supprime '.0' et 'nan'.
    - Remplace les valeurs manquantes par une chaîne vide.

    Args:
        df (pd.DataFrame): Le DataFrame à nettoyer.
        colonnes (list): Liste des noms des colonnes à traiter.

    Returns:
        pd.DataFrame: Le DataFrame avec les colonnes nettoyées.
    """
    for col in colonnes:
        df[col] = df[col].astype('string')
        df[col] = df[col].str.replace('.0', '', regex=False)
        df[col] = df[col].str.replace('nan', '', regex=False)
        df[col] = df[col].fillna('')
    return df

def check_abbreviation(adresse, abbreviations):
    """
    Fonction qui vérifie si le premier mot de l'adresse est une abréviation.
    Si c'est le cas, elle sépare l'adresse en deux parties : l'abréviation et le reste de l'adresse.
    
    Arguments :
    adresse (str) : L'adresse à vérifier.
    abbreviations (list) : Liste des abréviations à vérifier.
    
    Retourne :
    tuple : Le premier mot (abréviation ou espace) et le reste de l'adresse (nom_voie).
    """
    # Initialiser les valeurs par défaut
    first_word = ' '
    nom_voie = ''
    
    if isinstance(adresse, str) and adresse.strip():
        # Extraire la première partie avant l'espace
        parts = adresse.split(' ')
        first_word = parts[0]
        
        # Vérifier si la première partie est une abréviation
        if first_word in abbreviations:
            nom_voie = ' '.join(parts[1:])  # Reste de l'adresse après l'abréviation
        else:
            nom_voie = adresse  # L'adresse complète si ce n'est pas une abréviation
            first_word = ' '  # Remplacer le premier mot par un espace
    return first_word, nom_voie
