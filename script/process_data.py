import requests as rq
import pandas as pd
import os
import gzip
import shutil

def telecharger_et_decompresser(url, fichier_destination):
    """
    Télécharge un fichier compressé depuis une URL, puis le décompresse
    dans un fichier de destination.

    Arguments :
    url -- URL du fichier à télécharger
    fichier_destination -- Chemin où le fichier décompressé sera sauvegardé
    """
    try:
        # Télécharger le fichier compressé
        reponse = rq.get(url)
        reponse.raise_for_status()  # Vérifie si la requête a réussi
        nom_compression = fichier_destination + ".gz"
        
        with open(nom_compression, 'wb') as fichier:
            fichier.write(reponse.content)
        print(f"Le fichier a été téléchargé sous : {nom_compression}")

        # Décompresser le fichier téléchargé
        with gzip.open(nom_compression, 'rb') as f_in:
            with open(fichier_destination, 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)
        print(f"Le fichier a été décompressé sous : {fichier_destination}")

    except rq.exceptions.RequestException as e:
        print(f"Erreur lors du téléchargement du fichier : {e}")
    except Exception as e:
        print(f"Une erreur est survenue : {e}")
    finally:
        # Supprimer le fichier compressé après décompression
        if os.path.exists(nom_compression):
            os.remove(nom_compression)
            print(f"Le fichier compressé {nom_compression} a été supprimé.")

# Fonction pour traiter un fichier et ajouter à la liste des DataFrames
def traiter_fichier(annee, base_url, colonnes_a_supprimer):
    """
    Télécharge, décompresse et traite un fichier CSV pour une année donnée.
    Charge ensuite le fichier dans un DataFrame, supprime les colonnes spécifiées
    et supprime le fichier CSV après traitement.

    Arguments :
    annee -- Année pour laquelle le fichier doit être traité
    base_url -- URL de base avec un format pour l'année
    colonnes_a_supprimer -- Liste des colonnes à supprimer du DataFrame

    Retourne :
    df -- DataFrame après traitement
    """
    print(f"Téléchargement et traitement de l'année {annee}...")
    fichier_csv = f"full_{annee}.csv"
    url = base_url.format(year=annee)
    
    # Télécharger et décompresser le fichier
    telecharger_et_decompresser(url, fichier_csv)
    
    # Charger le fichier dans un DataFrame
    df = pd.read_csv(fichier_csv, encoding="utf-8")
    
    # Supprimer les colonnes inutiles
    df.drop(columns=colonnes_a_supprimer, inplace=True)
    
    # Supprimer le fichier CSV après traitement
    os.remove(fichier_csv)
    
    return df

# Fonction pour convertir les colonnes en chaîne de caractères
def convertir_en_str(df, colonnes):
    """
    Convertit les colonnes spécifiées d'un DataFrame en chaînes de caractères
    en remplaçant les valeurs manquantes par des chaînes vides.

    Arguments :
    df -- DataFrame à traiter
    colonnes -- Liste des colonnes à convertir

    Retourne :
    df -- DataFrame avec les colonnes converties
    """
    for col in colonnes:
        # Remplacer les valeurs manquantes par des chaînes vides et convertir en str
        df[col] = df[col].fillna('').astype(str)
    return df

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
