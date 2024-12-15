import requests as rq
import pandas as pd
import os
import gzip
import shutil
import re

def fix_coordinates_format(coord_str):
    """
    Transforme une chaîne contenant une liste de tuples de Decimal
    en une liste de tuples de float, en ignorant les erreurs.
    """
    if isinstance(coord_str, str):
        # Nettoyer la chaîne en remplaçant 'Decimal' par les valeurs brutes
        clean_str = re.sub(r"Decimal\('([\d\.\-]+)'\)", r"\1", coord_str)
        try:
            # Évaluer la chaîne nettoyée comme une liste de tuples
            parsed_list = eval(clean_str)
            if isinstance(parsed_list, list):
                # Convertir chaque tuple en float
                return [
                    (float(lat), float(lon)) 
                    for lat, lon in parsed_list 
                    if lat is not None and lon is not None
                ]
        except (ValueError, SyntaxError, TypeError) as e:
            print(f"Erreur lors de l'analyse : {coord_str} -> {e}")
            return None  # Retourner None en cas d'échec
    elif isinstance(coord_str, list):
        # Si c'est déjà une liste, vérifier et convertir
        try:
            return [
                (float(lat), float(lon)) 
                for lat, lon in coord_str 
                if lat is not None and lon is not None
            ]
        except TypeError as e:
            print(f"Erreur de conversion : {coord_str} -> {e}")
            return None
    else:
        print(f"Type inattendu : {type(coord_str)}")
        return None
    
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

def produce_stats(filtered_data, output_file):
    """
    Analyse les données des transactions immobilières pour calculer des statistiques 
    par commune et par zone inondable, en se concentrant sur les 20 communes les plus peuplées.

    Args:
        filtered_data (pd.DataFrame): DataFrame contenant les données filtrées avec les colonnes suivantes :
            - 'nom_commune': Nom des communes.
            - 'zone_inondable': Indicateur binaire (1 si en zone inondable, 0 sinon).
            - 'prix_m2': Prix au mètre carré des transactions.
            - 'Population': Population de chaque commune.
        output_file (str): Chemin du fichier CSV dans lequel exporter les résultats.

    Returns:
        pd.io.formats.style.Styler: Un objet Styler pour afficher le tableau formaté dans un notebook.

    Étapes principales :
        1. Calcul du prix moyen au mètre carré par commune et par zone inondable.
        2. Calcul du prix moyen total par commune, ainsi que la différence relative en % entre zones inondables et non-inondables.
        3. Ajout des colonnes pour :
            - Nombre total de transactions.
            - Proportion de transactions en zone inondable.
        4. Ajout de la population par commune.
        5. Tri des communes par population décroissante et sélection des 20 premières.
        6. Export du résultat en fichier CSV.
        7. Formatage des données (séparateurs de milliers, pourcentage, etc.) pour une présentation claire.
    """
    # Calcul du prix moyen par commune et par zone inondable
    mean_by_zone = (
        filtered_data
        .groupby(['nom_commune', 'zone_inondable'])['prix_m2']
        .mean()
        .unstack(fill_value=0)  # Remplace NaN par 0
    )
    
    # Calcul du prix moyen total par commune
    mean_total = (
        filtered_data
        .groupby('nom_commune')['prix_m2']
        .mean()
    )
    
    # Renommer les colonnes pour les prix moyens par zone
    mean_by_zone = mean_by_zone.rename(columns={0: 'prix_moyen_non_inondable', 1: 'prix_moyen_inondable'})
    
    # Calcul de la différence relative en %
    mean_by_zone['écart'] = (
        (mean_by_zone['prix_moyen_inondable'] - mean_by_zone['prix_moyen_non_inondable']) / mean_by_zone['prix_moyen_non_inondable'] * 100
    )
    
    # Ajouter le nombre total de transactions par commune (nb_transactions)
    nb_transactions = filtered_data.groupby('nom_commune').size()
    
    # Ajouter le nombre de transactions inondables par commune
    nb_inondable = filtered_data[filtered_data['zone_inondable'] == 1].groupby('nom_commune').size()
    
    # Calculer la proportion de transactions inondables par commune (part_inondable)
    part_inondable = nb_inondable / nb_transactions * 100
    
    # Joindre les nouvelles colonnes au DataFrame 'mean_by_zone'
    mean_by_zone['nb_transactions'] = nb_transactions
    mean_by_zone['part_inondable'] = part_inondable
    
    # Ajouter la population par commune
    population_data = filtered_data.groupby('nom_commune')['Population'].max()
    mean_by_zone = mean_by_zone.join(population_data, on='nom_commune')
    
    # Trier les communes par population décroissante et sélectionner les 20 plus peuplées
    result_table = mean_by_zone.sort_values(by='Population', ascending=False).head(20)
    
    # Exporter le DataFrame final en CSV
    result_table.to_csv(output_file, encoding='utf-8-sig', sep=";", decimal=",", index=True)
    
    # Ajouter la colonne 'nom_commune' comme première colonne
    result_table = result_table.reset_index()

    # Réorganiser les colonnes pour mettre 'Population' en deuxième position
    cols = ['nom_commune', 'Population', 'prix_moyen_non_inondable', 'prix_moyen_inondable', 
            'écart', 'nb_transactions', 'part_inondable']
    result_table = result_table[cols]

    # Formatage des nombres avec séparateurs de milliers (espaces)
    result_table['prix_moyen_non_inondable'] = result_table['prix_moyen_non_inondable'].apply(lambda x: f"{x:,.0f}".replace(',', ' '))
    result_table['prix_moyen_inondable'] = result_table['prix_moyen_inondable'].apply(lambda x: f"{x:,.0f}".replace(',', ' '))
    result_table['écart'] = result_table['écart'].apply(lambda x: f"{x:,.1f}%".replace(',', ' '))
    result_table['nb_transactions'] = result_table['nb_transactions'].apply(lambda x: f"{x:,.0f}".replace(',', ' '))
    result_table['part_inondable'] = result_table['part_inondable'].apply(lambda x: f"{x:,.1f}%".replace(',', ' '))
    result_table['Population'] = result_table['Population'].apply(lambda x: f"{x:,.0f}".replace(',', ' '))

    # Retourner le tableau stylé
    return (
        result_table
        .style
        .hide(axis="index")  # Supprime l'index
        .set_caption(f"Top 20 des communes les plus peuplées - {output_file.split('/')[-1]}")
    )
