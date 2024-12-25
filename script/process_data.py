import requests
import pandas as pd
import os
import gzip
import shutil
import re
import zipfile
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np


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
        reponse = requests.get(url)
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

    except requests.exceptions.RequestException as e:
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


def process_population_data(url, zip_path="ensemble.zip", extracted_folder="ensemble"):
    """
    Télécharge un fichier ZIP, extrait son contenu et charge un fichier CSV spécifique dans un DataFrame.
    
    Args:
        url (str): L'URL du fichier ZIP à télécharger.
        zip_path (str, optional): Le chemin pour enregistrer le fichier ZIP téléchargé. Par défaut "ensemble.zip".
        extracted_folder (str, optional): Le dossier où extraire les fichiers ZIP. Par défaut "ensemble".

    Returns:
        pd.DataFrame: DataFrame contenant les colonnes 'code_commune' et 'Population'.
    """
    # Télécharger le fichier ZIP
    response = requests.get(url)
    with open(zip_path, 'wb') as file:
        file.write(response.content)

    # Dézipper le fichier ZIP
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(extracted_folder)

    # Charger le fichier CSV dans un DataFrame
    csv_path = os.path.join(extracted_folder, "donnees_communes.csv")
    df_pop = pd.read_csv(csv_path, sep=";", encoding="utf8")

    # Nettoyer les colonnes et renommer
    df_pop = df_pop[['COM', "PMUN"]].rename(columns={'COM': 'code_commune',
                                                       'PMUN': 'Population'})

    # Nettoyage des fichiers temporaires
    os.remove(zip_path)
    shutil.rmtree(extracted_folder)

    return df_pop


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
    
    # Trier les communes par population décroissante et sélectionner les 10 plus peuplées
    result_table = mean_by_zone.sort_values(by='Population', ascending=False).head(10)
    
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
    return (result_table)


def plot_ecart_prix(result_table,type):
    """
    Génère un graphique à barres côte à côte pour visualiser les prix non inondables et inondables
    pour les 10 communes les plus peuplées.

    Args:
        result_table (pd.DataFrame): DataFrame contenant les résultats de l'analyse des prix par zone.
    """
    # Création d'une nouvelle figure
    plt.figure(figsize=(12, 6))

    # Initialiser les positions des barres (utilisation d'un petit écart pour les mettre côte à côte)
    x = np.arange(len(result_table))  # Position des communes
    width = 0.35  # Largeur des barres

    if result_table['prix_moyen_non_inondable'].dtype == 'object':
        result_table['prix_moyen_non_inondable'] = result_table['prix_moyen_non_inondable'].str.replace(' ', '').astype(float)

    if result_table['prix_moyen_inondable'].dtype == 'object':
        result_table['prix_moyen_inondable'] = result_table['prix_moyen_inondable'].str.replace(' ', '').astype(float)

    # Tracer les barres pour les prix non inondables et inondables
    plt.bar(x - width/2, result_table['prix_moyen_non_inondable'], width, label='Non Inondable', color='skyblue')
    plt.bar(x + width/2, result_table['prix_moyen_inondable'], width, label='Inondable', color='coral')

    # Ajouter des labels et un titre
    plt.title(f'Prix au mètre carré par commune ({type} - Non Inondable vs Inondable)', fontsize=16)
    plt.xlabel('Commune', fontsize=14)
    plt.ylabel('Prix du m2 (en €)', fontsize=14)

    # Rotation des étiquettes sur l'axe des x pour une meilleure lisibilité
    plt.xticks(x, result_table['nom_commune'], rotation=45, ha='right')

    # Ajouter une légende
    plt.legend()

    # Ajuster les limites de l'axe des y pour bien visualiser les barres
    plt.tight_layout()

    # Afficher le graphique
    plt.show()
    

def download_and_extract_csv(url, output_csv_path):
    """
    Télécharge un fichier compressé à partir de l'URL et le décompresse en CSV.
    """
    # Nom du fichier compressé
    downloaded_file = "downloaded_file.gz"
    
    # Envoyer la requête HTTP pour télécharger le fichier
    response = requests.get(url)
    
    # Enregistrer le fichier compressé
    with open(downloaded_file, 'wb') as file:
        file.write(response.content)
    
    # Décompresser le fichier
    with gzip.open(downloaded_file, 'rb') as f_in:
        with open(output_csv_path, 'wb') as f_out:
            shutil.copyfileobj(f_in, f_out)
    
    # Supprimer le fichier compressé après décompression
    os.remove(downloaded_file)
    
colonnes_a_supprimer_dans_dvf = ['adresse_suffixe',
                                 'code_nature_culture',
                                 'ancien_code_commune',
                                 'ancien_nom_commune',
                                 'ancien_id_parcelle',
                                 'numero_volume',
                                 'code_nature_culture_speciale',
                                 'nature_culture_speciale',
                                 'lot1_numero',
                                 'lot2_numero',
                                 'lot3_numero',
                                 'lot4_numero',
                                 'lot5_numero',
                                 'lot1_surface_carrez',
                                 'lot2_surface_carrez',
                                 'lot3_surface_carrez',
                                 'lot4_surface_carrez',
                                 'lot5_surface_carrez'
                                 ]


def compute_percentage(df, column):
    """
    Calcule les pourcentages des modalités d'une colonne spécifiée d'un DataFrame.
    Crée un DataFrame avec un titre 'Part' pour chaque modalité et ses pourcentages.
    Regroupe les None et NaN dans la catégorie 'NaN' et trie les résultats par part décroissante.
    
    Args:
        df (pd.DataFrame): Le DataFrame contenant les données.
        column (str): Le nom de la colonne pour laquelle calculer les pourcentages.

    Returns:
        pd.DataFrame: Un DataFrame contenant les modalités et leurs pourcentages formatés.
    """
    # Remplacer None et NaN par 'NaN' avant le comptage
    df[column] = df[column].fillna('NaN')
    
    # Comptage des modalités pour la colonne
    modalites = df[column].value_counts(dropna=False)
    
    # Calcul des pourcentages pour la colonne
    percent = (modalites / modalites.sum()) * 100
    
    # Arrondi à 1 chiffre après la virgule
    percent = percent.round(1)
    
    # Formatage des pourcentages en chaîne avec '%' ajouté
    percent = percent.apply(lambda x: f"{x}%")
    
    # Créer un DataFrame avec les modalités et leurs pourcentages
    result_df = pd.DataFrame({
        'Part': percent
    })
    
    # Trier par part décroissante et mettre 'NaN' en haut
    result_df['Part_value'] = modalites / modalites.sum()  # Pour le tri basé sur la valeur
    result_df = result_df.sort_values(by='Part_value', ascending=False)
    
    # Remettre la colonne 'Part_value' pour le tri, puis supprimer après le tri
    result_df = result_df.drop(columns=['Part_value'])
    
    return result_df


def plot_density(df, column, xlim=(0, 10000)):
    """
    Trace la densité des données d'une colonne d'un DataFrame.

    Args:
        df (pd.DataFrame): Le DataFrame contenant les données.
        column (str): Le nom de la colonne pour laquelle tracer la densité.
        xlim (tuple, optional): Limites de l'axe X (par défaut (0, 10000)).
    """
    # Tracer la densité de la colonne spécifiée
    plt.figure(figsize=(10, 6))
    sns.kdeplot(df[column], shade=True, color="skyblue", alpha=0.7)

    # Ajouter un titre et des labels
    plt.title(f'Densité de {column}', fontsize=16)
    plt.xlabel(column, fontsize=14)
    plt.ylabel('Densité', fontsize=14)
    plt.xlim(xlim)

    # Afficher le graphique
    plt.tight_layout()
    plt.show()