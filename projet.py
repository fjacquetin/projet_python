#!/usr/bin/env python
# coding: utf-8

# In[1]:


## La version de python utilisée est 3.12.7

get_ipython().system('pip install -r requirements.txt -q')


# In[2]:


import pandas as pd
import requests as rq
import lxml as lxml
from bs4 import BeautifulSoup
import io as io
import math
import gzip
import shutil
import os
import geopandas as gpd
import matplotlib.pyplot as plt
import folium
import json
from pandasgui import show
import numpy as np
from io import BytesIO
from folium.plugins import HeatMap

from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut


# In[3]:


pd.set_option('display.max_columns', None)  # Afficher toutes les colonnes
pd.set_option('display.max_rows', None)     # Afficher toutes les lignes
pd.set_option('display.max_colwidth', None) # Afficher la largeur de colonne sans tronquer
pd.set_option('display.width', None) 


# In[4]:


# url = "https://static.data.gouv.fr/resources/demandes-de-valeurs-foncieres/20241008-071041/valeursfoncieres-2023.txt.zip"

url = "https://files.data.gouv.fr/geo-dvf/latest/csv/2023/full.csv.gz"
# Envoyer une requête HTTP pour obtenir le fichier CSV

downloaded_file = "full.csv.gz"
response = rq.get(url)

with open(downloaded_file, 'wb') as file:
    file.write(response.content)

# Décompresser le fichier
with gzip.open(downloaded_file, 'rb') as f_in:
    with open("full.csv", 'wb') as f_out:
        shutil.copyfileobj(f_in, f_out)

# Charger le fichier CSV dans un DataFrame
df = pd.read_csv("full.csv")

## Affiche la première ligne et et toutes les variables
premiere_ligne = df.iloc[0:9].T
print(premiere_ligne)

# Optionnel : supprimer le fichier compressé après décompression
os.remove("full.csv.gz")
os.remove("full.csv")


# In[5]:


# Création d'un DataFrame avec les noms des colonnes et leurs types
column_types = pd.DataFrame({
    'Nom de la colonne': df.columns,
    'Type': df.dtypes
})

# Affichage du DataFrame avec les noms de colonnes et leurs types
print(column_types)

# Nombre total de transactions réalisées en France
total_transactions = df.shape[0]

# Nombre de transactions manquantes dans la colonne 'valeur_fonciere'
nan_transactions = df['valeur_fonciere'].isna().sum()

# Calcul du pourcentage de valeurs manquantes
pourcentage_nan = (nan_transactions / total_transactions) * 100

# Affichage de la phrase
print(f"En 2023, il y a {pourcentage_nan:.2f}% des {total_transactions} transactions réalisées en France qui ne sont pas renseignées dans la base DVF.")


# In[6]:


## Première opération : alléger le dataset

colonnes_a_supprimer = ['ancien_code_commune',
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

df.drop(columns=colonnes_a_supprimer, inplace=True)


# In[7]:


# 2ème opération (filtre) : Supprimer toutes les transactions NaN
df = df.dropna(subset=['valeur_fonciere'])

print(df['valeur_fonciere'].isna().sum())


# In[8]:


# 3ème opération : conversion des adresses en string

print(df['adresse_numero'].dtype)
print(df['adresse_nom_voie'].dtype)
print(df['code_postal'].dtype)
print(df['nom_commune'].dtype)

df['adresse_numero'] = df['adresse_numero'].astype('string')
df['adresse_numero'] = df['adresse_numero'].str.replace('.0', '', regex=False)
df['adresse_numero'] = df['adresse_numero'].str.replace('nan', '', regex=False)
df['adresse_numero'] = df['adresse_numero'].fillna('')


# Ajouter un 0 devant si le code postal a 4 caractères
df['code_postal'] = df['code_postal'].astype('string')
df['code_postal'] = df['code_postal'].str.replace('.0', '', regex=False)
df['code_postal'] = df['code_postal'].str.replace('nan', '', regex=False)
df['code_postal'] = df['code_postal'].fillna('')

# Convertir la colonne 'code_commune' en type string
df['code_commune'] = df['code_commune'].astype('string')

# Ajouter un '0' au début si la chaîne a 4 caractères
df['code_commune'] = df['code_commune'].apply(lambda x: x.zfill(5) if len(x) == 4 else x)

# Vérifier les résultats
print(df['code_commune'].head())


# In[9]:


# 4ème opération (si besoin de géolocalisation) : Compléter par le type de voie

voie = pd.read_csv('voie.csv',sep=";")
print(voie.head())

# Liste des abréviations de types de voie
abbreviations = voie['abreviation'].tolist()

# Fonction pour extraire et vérifier la première chaîne avant le premier espace
def check_abbreviation(adresse):
    if isinstance(adresse, str):
        # Extraire la première partie avant l'espace
        parts = adresse.split(' ')
        first_word = parts[0]
        # Vérifier si elle appartient à la liste des abréviations
        if first_word in abbreviations:
            # Si le premier mot est une abréviation, extraire le reste de l'adresse
            nom_voie = ' '.join(parts[1:])  # Tout ce qui suit le premier mot
        else:
            # Si ce n'est pas une abréviation, mettre tout l'adresse dans nom_voie
            nom_voie = adresse
            first_word = ' '  # Remplacer par un espace pour le premier mot
    else:
        first_word = ' '
        nom_voie = ''
    
    return first_word, nom_voie

# Appliquer la fonction à la colonne 'adresse_nom_voie'
result = df['adresse_nom_voie'].apply(check_abbreviation)

# Décomposer les résultats dans les colonnes 'type_voie' et 'nom_voie'
df['type_voie'] = result.apply(lambda x: x[0])  # Prend le premier élément
df['nom_voie'] = result.apply(lambda x: x[1])   # Prend le deuxième élément

df = df.merge(voie,left_on=['type_voie'],right_on=['abreviation'])


# In[10]:


## 5ème : Réécriture de l'adresse

df['Adresse'] = df['adresse_numero'] + ' ' + df['type_voie_complet'] + ' ' + df['nom_voie'] + ' ' + df['code_postal'] + ' ' + df['nom_commune']

print(df['Adresse'].head())


# In[11]:


# Nombre total de lignes dans df_geolocalisees2
nb_lignes_total = len(df)
print(f"Nombre total de lignes dans df_geolocalisees2 : {nb_lignes_total}")

# Compter les modalités de 'nature_mutation' et calculer les pourcentages
modalites_nature_mutation = df['nature_mutation'].value_counts()
modalites_nature_mutation_percent = (modalites_nature_mutation / nb_lignes_total * 100).round(1)

# Combiner les valeurs et les pourcentages dans un DataFrame
tableau_nature_mutation = pd.DataFrame({
    'Nombre de transactions': modalites_nature_mutation,
    'Pourcentage (%)': modalites_nature_mutation_percent
})

# Afficher le tableau
print("\nTableau des modalités de 'nature_mutation' avec pourcentages :")
print(tableau_nature_mutation)


# In[12]:


# Filtre : on ne conserve que les ventes
df = df[df['nature_mutation']=='Vente']


# In[13]:


# Combien de transactions ne sont pas géolocalisées ?

# Nombre total de transactions renseignées (celles qui ont des valeurs dans 'latitude' et 'longitude')
total_transactions_renseignees = df.shape[0]

# Nombre de lignes où 'latitude' ou 'longitude' est manquant (sans double compte)
non_geolocalisees = df[df['latitude'].isna() | df['longitude'].isna()].shape[0]

# Calcul du pourcentage de transactions non géolocalisées
pourcentage_non_geolocalisees = (non_geolocalisees / total_transactions_renseignees) * 100

# Affichage de la phrase
print(f"Sur les {total_transactions_renseignees} transactions renseignées, {pourcentage_non_geolocalisees:.2f}% ne sont pas géolocalisées.")


# In[14]:


# # Filtrer pour ne garder que les transactions géolocalisées (celles où latitude et longitude sont renseignées)
df_geolocalisees = df
# df_geolocalisees = df.dropna(subset=['latitude', 'longitude'])

# print(total_transactions_renseignees)
# print(df_geolocalisees.shape[0])


# In[15]:


# Charger les données des codes de région
region = pd.read_csv('code_region.csv', sep=';')
print(region['departmentCode'].dtype)
print(df_geolocalisees['code_departement'].dtype)

# Afficher les premières lignes pour vérifier
print(region.head())

# Vérifier le type de la colonne 'departmentCode'
print(f"Type de la colonne 'departmentCode': {region['departmentCode'].dtype}")

# Vérifier les modalités (valeurs uniques) de 'departmentCode'
print("Modalités de 'departmentCode':")
print(region['departmentCode'].unique())
print(df_geolocalisees['code_departement'].unique())


# In[16]:


region['departmentCode'] = region['departmentCode'].astype(str)
df_geolocalisees['code_departement'] = df_geolocalisees['code_departement'].astype(str)

print(region['departmentCode'].unique())
print(df_geolocalisees['code_departement'].unique())


# In[17]:


# Fusionner df_geolocalisees avec les codes de région
df_geolocalisees = df_geolocalisees.merge(region, left_on=["code_departement"], right_on=['departmentCode'], how='left')

# Compter le nombre de transactions par région
transactions_par_region = df_geolocalisees.groupby('regionName').size()

# Calculer le total des transactions
total_transactions = transactions_par_region.sum()

# Calculer la part de chaque région dans le total des transactions
part_region = (transactions_par_region / total_transactions) * 100

# Créer un DataFrame avec les résultats
tableau_regions = pd.DataFrame({
    'Nombre de transactions': transactions_par_region,
    'Part du total (%)': part_region
})

# Afficher le tableau des régions
print(tableau_regions)


# In[18]:


# Retirer les Départements et Régions Outre-Mer
df_geolocalisees = df_geolocalisees[~df_geolocalisees['regionName'].isin(['Guyane', 'Martinique', 'Guadeloupe', 'La Réunion', 'Mayotte'])]


# In[19]:


# Création d'un DataFrame avec les noms des colonnes et leurs types
column_types = pd.DataFrame({
    'Nom de la colonne': df_geolocalisees.columns,
    'Type': df_geolocalisees.dtypes
})

# Affichage du DataFrame avec les noms de colonnes et leurs types
print(column_types)

print(df_geolocalisees.head())


# In[20]:


# Créer les colonnes conditionnelles
df_geolocalisees['pieces_sup_0'] = df_geolocalisees['nombre_pieces_principales'] > 0
df_geolocalisees['surface_renseignée'] = df_geolocalisees['surface_reelle_bati'].notna()

# Calculer la répartition des pièces > 0 par type de bien
repartition_pieces = pd.crosstab(index=df_geolocalisees['type_local'], 
                                 columns=df_geolocalisees['pieces_sup_0'], 
                                 normalize='index') * 100

# Calculer la répartition des surfaces renseignées par type de bien
repartition_surface = pd.crosstab(index=df_geolocalisees['type_local'], 
                                  columns=df_geolocalisees['surface_renseignée'], 
                                  normalize='index') * 100

# Renommer les colonnes pour chaque répartition
repartition_pieces.columns = ['Pas de pièces > 0', 'Pièces > 0']
repartition_surface.columns = ['Surface manquante', 'Surface renseignée']

# Fusionner les deux tables en une seule
repartition_combined = pd.concat([repartition_pieces, repartition_surface], axis=1)

# Arrondir et ajouter le signe %
repartition_combined = repartition_combined.round(1).astype(str) + '%'

# Afficher le tableau combiné
print(repartition_combined)


# In[21]:


# One ne garde donc que les maisons et les appartements

df_geolocalisees2 = df_geolocalisees[df_geolocalisees['type_local'].isin(['Maison', 'Appartement'])]

total_transactions = df_geolocalisees.shape[0]
total_transactions2 = df_geolocalisees2.shape[0]

# Calcul du nombre d'appartements et de maisons dans ce sous-ensemble
appartements = df_geolocalisees2[df_geolocalisees['type_local'] == 'Appartement'].shape[0]
maisons = df_geolocalisees2[df_geolocalisees['type_local'] == 'Maison'].shape[0]

# Calcul des pourcentages
pourcentage = total_transactions2/total_transactions * 100
pourcentage_appartements = (appartements / total_transactions2) * 100
pourcentage_maisons = (maisons / total_transactions2) * 100

# Générer la phrase
phrase = f"Sur les {total_transactions} transactions renseignées et géolocalisées, on ne conserve que {total_transactions2} (soit {pourcentage:.1f}%)" \
         f"transactions représentant {pourcentage_appartements:.1f}% d'appartements et {pourcentage_maisons:.1f}% de maisons."

# Afficher la phrase
print(phrase)


# In[22]:


# Vérifier si la surface est renseignée dans la colonne 'surface_reelle_bati'
surface_renseignée = df_geolocalisees2['surface_reelle_bati'].notna().sum()

# Calcul du nombre total de lignes dans le DataFrame
total_lignes = df_geolocalisees2.shape[0]

# Calcul du pourcentage de valeurs renseignées
pourcentage_surface_renseignée = (surface_renseignée / total_lignes) * 100

# Afficher le résultat
print(f"Pourcentage de lignes avec surface renseignée : {pourcentage_surface_renseignée:.1f}%")


# In[23]:


# Pour l'instant, on ne garde que les appartements
df_geolocalisees2 = df_geolocalisees2[df_geolocalisees2['type_local'] == 'Appartement']


# In[24]:


# Calcule le prix moyen par mètre carré
df_geolocalisees2['prix_m2'] = df_geolocalisees2['valeur_fonciere']/df_geolocalisees2['surface_reelle_bati']


# In[25]:


# Problème : certains terrains sont déclarés en habitation
# Filtrer les lignes où 'nature_culture' n'est pas NaN
df_filtered = df_geolocalisees2[df_geolocalisees2['nature_culture'].notna()]

# Sélectionner uniquement les colonnes désirées
df_filtered = df_filtered[['type_local','valeur_fonciere','nature_culture', 'surface_reelle_bati', 'surface_terrain', 'prix_m2']]

# Afficher les 10 premières lignes
print(df_filtered.head(10))

df_geolocalisees2 = df_geolocalisees2[df_geolocalisees2['nature_culture'].isna()]


# In[26]:


# Une partie des transactions sont en doublon

# Compter les doublons en fonction des colonnes spécifiées
nb_doublons = df_geolocalisees2.duplicated(subset=['adresse_nom_voie', 'code_postal', 'surface_reelle_bati', 'valeur_fonciere']).sum()
print(f"Nombre de doublons : {nb_doublons}")

# Supprimer les doublons en gardant la première occurrence
df_geolocalisees2 = df_geolocalisees2.drop_duplicates(subset=['adresse_nom_voie', 'code_postal', 'surface_reelle_bati', 'valeur_fonciere'], keep='first')

# Vérifier le nouveau nombre de lignes
print(f"Nombre de lignes après suppression des doublons : {len(df_geolocalisees2)}")


# In[27]:


# Calcul de la moyenne des prix totale en fonction de la surface
prix_moyen_m2 = df_geolocalisees2['valeur_fonciere'].sum() / df_geolocalisees2['surface_reelle_bati'].sum()
print(f"Moyenne totale des prix en fonction de la surface : {prix_moyen_m2:.2f} €")

# Calcul de la moyenne des prix par région
prix_moyen_region = df_geolocalisees2.groupby('regionName')['valeur_fonciere'].sum() / df_geolocalisees2.groupby('regionName')['surface_reelle_bati'].sum()

# Calcul de la moyenne des prix par type d'appartement en fonction de la surface
prix_moyen_type = df_geolocalisees2.groupby('type_local')['valeur_fonciere'].sum() / df_geolocalisees2.groupby('type_local')['surface_reelle_bati'].sum()

# Calcul du nombre de transactions par région
nb_transactions_region = df_geolocalisees2.groupby('regionName').size()

# Calcul du pourcentage d'appartements et de maisons par région
nb_transactions_appart = df_geolocalisees2[df_geolocalisees2['type_local'] == "Appartement"].groupby('regionName').size()
nb_transactions_maison = df_geolocalisees2[df_geolocalisees2['type_local'] == "Maison"].groupby('regionName').size()

# Calculer le pourcentage pour chaque type par région
pourcentage_appart = (nb_transactions_appart / nb_transactions_region * 100).fillna(0)
pourcentage_maison = (nb_transactions_maison / nb_transactions_region * 100).fillna(0)

# Combiner toutes les informations dans un DataFrame final
stats_region = pd.DataFrame({
    'prix_moyen_region': prix_moyen_region,
    'nb_transactions': nb_transactions_region,
    'pourcentage_appart': pourcentage_appart,
    'pourcentage_maison': pourcentage_maison
}).reset_index()

# Afficher le tableau final
print(stats_region)
# Afficher les tableaux de moyennes
print("\nMoyenne des prix par région en fonction de la surface :")
print(prix_moyen_region)

print("\nMoyenne des prix par type d'appartement en fonction de la surface :")
print(prix_moyen_type)


# In[28]:


# URL du fichier GeoJSON des régions de France
url_region = "https://france-geojson.gregoiredavid.fr/repo/regions.geojson"

# Récupérer le fichier GeoJSON des régions de France
response = rq.get(url_region)
regions_geojson = response.json()

# Créer une liste pour stocker les noms des régions
region_names = []

# Extraire les noms des régions depuis les propriétés de chaque feature
for feature in regions_geojson['features']:
    region_name = feature['properties']['nom']
    region_names.append(region_name)

# Créer un DataFrame avec les noms des régions
df_regions = pd.DataFrame(region_names, columns=['regionName'])
    
# Afficher le DataFrame
print(df_regions)

 # Afficher les modalités de la colonne 'regionName'
modalites_region = df_geolocalisees2['regionName'].value_counts().reset_index()

modalites_region = pd.DataFrame(modalites_region[['regionName']])
# Affichage
print(modalites_region)


# In[29]:


# Charger le fichier GeoJSON dans un GeoDataFrame
gdf_regions = gpd.GeoDataFrame.from_features(regions_geojson['features'])

# Afficher un aperçu des données
print(gdf_regions[['nom']])

# Tracer la carte
fig, ax = plt.subplots(figsize=(10, 10))
gdf_regions.plot(ax=ax, color="lightblue", edgecolor="black")
ax.set_title("Carte des Régions de France")
plt.show()


# In[30]:


# URL du fichier GeoJSON des départements de France
url_departement = "https://france-geojson.gregoiredavid.fr/repo/departements.geojson"

# Récupérer le fichier GeoJSON des départements de France
response = rq.get(url_departement)
departements_geojson = response.json()

# Créer une liste pour stocker les noms des départements
departement_names = []

# Extraire les noms des départements depuis les propriétés de chaque feature
for feature in departements_geojson['features']:
    departement_name = feature['properties']['nom']
    departement_names.append(departement_name)

# Créer un DataFrame avec les noms des départements
df_departements = pd.DataFrame(departement_names, columns=['departementName'])
    
# Afficher le DataFrame
print(df_departements)


# In[31]:


# Charger les données des codes de région
dep = pd.read_csv('code_region.csv', sep=';')
print(region['departmentName'].dtype)
print(df_geolocalisees2['departmentName'].dtype)


# Vérifier le type de la colonne 'departmentCode'
print(f"Type de la colonne 'departmentCode': {dep['departmentName'].dtype}")

# Vérifier les modalités (valeurs uniques) de 'departmentCode'
print("Modalités de 'departmentCode':")
print(dep['departmentName'].unique())
print(df_geolocalisees2['departmentName'].unique())


# In[32]:


# Créer une carte centrée sur la France
carte = folium.Map(location=[46.603354, 1.888334], zoom_start=6)

# Ajouter la couche choroplétique pour les régions
folium.Choropleth(
    geo_data=regions_geojson,
    name="Régions de France",
    fill_color="YlGnBu",  # Palette de couleurs
    fill_opacity=0.7,
    line_opacity=0.2,
    legend_name="Régions de France",
).add_to(carte)

# Afficher la carte
carte


# In[33]:


# Charger le fichier GeoJSON dans un GeoDataFrame
gdf_regions = gpd.GeoDataFrame.from_features(regions_geojson['features'])

# Calculer le prix moyen par région
prix_moyen_region = df_geolocalisees2.groupby('regionName')['valeur_fonciere'].sum() / df_geolocalisees2.groupby('regionName')['surface_reelle_bati'].sum()
prix_moyen_region = prix_moyen_region.reset_index()
prix_moyen_region.columns = ['nom', 'prix_moyen']

# Fusionner les données de prix avec les données géographiques
gdf_regions = gdf_regions.merge(prix_moyen_region, on='nom', how='left')

# Créer une carte centrée sur la France
carte = folium.Map(location=[46.603354, 1.888334], zoom_start=6)

# Ajouter la couche choroplétique pour les régions
choropleth = folium.Choropleth(
    geo_data=regions_geojson,
    name="Régions de France",
    fill_color="YlGnBu",  # Palette de couleurs
    fill_opacity=0.7,
    line_opacity=0.2,
    legend_name="Prix moyen par région",
    data=prix_moyen_region,
    columns=['nom', 'prix_moyen'],
    key_on="feature.properties.nom",
).add_to(carte)

# Ajouter des popups pour afficher le nom de la région et le prix moyen
for _, row in gdf_regions.iterrows():
    folium.Marker(
        location=[row['geometry'].centroid.y, row['geometry'].centroid.x],
        popup=f"Région : {row['nom']}<br>Prix moyen : {row['prix_moyen']:.2f} €/m²",
    ).add_to(carte)

# Afficher la carte
carte


# In[34]:


# Charger le fichier GeoJSON des départements
url_departement = "https://france-geojson.gregoiredavid.fr/repo/departements.geojson"
response = rq.get(url_departement)
departements_geojson = response.json()

# Charger le GeoJSON dans un GeoDataFrame
gdf_departements = gpd.GeoDataFrame.from_features(departements_geojson['features'])

# Calculer le prix moyen par département
prix_moyen_departement = df_geolocalisees2.groupby('departmentName')['valeur_fonciere'].sum() / df_geolocalisees2.groupby('departmentName')['surface_reelle_bati'].sum()
prix_moyen_departement = prix_moyen_departement.reset_index()
prix_moyen_departement.columns = ['nom', 'prix_moyen']

# En particulier, la base DVF ne contient pas de mutation en Haut-Rhin, Bas-Rhin, Moselle
prix_moyen_departement = prix_moyen_departement.dropna(subset=['prix_moyen'])

# Fusionner les données de prix avec les données géographiques des départements
gdf_departements = gdf_departements.merge(prix_moyen_departement, on='nom', how='left')

# Créer une carte centrée sur la France
carte_departements = folium.Map(location=[46.603354, 1.888334], zoom_start=6)

# Ajouter la couche choroplétique pour les départements, en excluant ceux sans prix moyen
choropleth_departements = folium.Choropleth(
    geo_data=departements_geojson,
    name="Départements de France",
    fill_color="YlGnBu",  # Palette de couleurs
    fill_opacity=0.7,
    line_opacity=0.2,
    legend_name="Prix moyen par département",
    data=prix_moyen_departement,
    columns=['nom', 'prix_moyen'],
    key_on="feature.properties.nom",
    # Ne pas colorier les départements avec NaN dans le prix_moyen
    nan_fill_color="lightgrey"  # Couleur de remplissage pour les départements sans prix moyen
).add_to(carte_departements)

# Ajouter des popups pour afficher le nom du département et le prix moyen
for _, row in gdf_departements.iterrows():
    if pd.notna(row['prix_moyen']):  # Ne pas ajouter de popup pour les départements sans prix moyen
        folium.Marker(
            location=[row['geometry'].centroid.y, row['geometry'].centroid.x],
            popup=f"Département : {row['nom']}<br>Prix moyen : {row['prix_moyen']:.2f} €/m²",
        ).add_to(carte_departements)

# Afficher la carte
carte_departements


# In[35]:


# Charger le fichier GeoJSON des communes de France depuis le lien GitHub
url_commune = 'https://raw.githubusercontent.com/gregoiredavid/france-geojson/master/communes.geojson'
response_commune = rq.get(url_commune)
communes_geojson = response_commune.json()

# Charger le GeoJSON dans un GeoDataFrame
gdf_communes = gpd.GeoDataFrame.from_features(communes_geojson['features'])

# Sélectionner les colonnes 'code' et 'nom'
code_nom = gdf_communes[['code', 'nom']]

# Renommer la colonne 'nom' en 'communeName'
code_nom = code_nom.rename(columns={'nom': 'communeName'})

# Exporter le résultat dans un fichier CSV local (UTILE SEULEMENT LA 1ère FOIS)
# code_nom.to_csv('communes_code.csv', index=False, sep=';', encoding='utf-8-sig')
# print(gdf_communes.head(10))


# In[36]:


print(df_geolocalisees2['code_commune'].head())


# In[37]:


commune = pd.read_csv('communes_code.csv', sep=';')
show(commune)
# Left_join des codes_communes avec les noms des communes geoJson
df_geolocalisees2 = df_geolocalisees2.merge(commune, left_on=["code_commune"], right_on=['code'], how='left')
df_geolocalisees2 = df_geolocalisees2.sort_values(by='code_commune', ascending=True)


# In[38]:


# URL du fichier Excel
url_cotier = 'https://comersis.com/free-download.php?f=communes_littorales_2019.xlsx&d=littoral'

# Télécharger le fichier
response = rq.get(url_cotier)

# Lire le fichier Excel dans un DataFrame
df_cotieres = pd.read_excel(BytesIO(response.content))
df_cotieres = df_cotieres[df_cotieres['Région'] != "Départements d'Outre-Mer"]


print(df_cotieres.columns)
show(df_cotieres)


# In[39]:


# Statistiques par "Motif du classement"
stats_motif = df_cotieres.groupby('Motif du classement').agg(
    nombre_communes=('Nom commune', 'nunique'),
    population_totale=('Population', 'sum')
).reset_index()

# Statistiques par "Région"
stats_region = df_cotieres.groupby('Région').agg(
    nombre_communes=('Nom commune', 'nunique'),
    population_totale=('Population', 'sum')
).reset_index()

# Afficher les résultats
print(stats_motif)
print(stats_region)


# In[40]:


# Filtrer sur le Motif du classement
df_cotieres = df_cotieres[df_cotieres['Motif du classement'] == "Commune riveraine de la mer ou d'un océan"]

print(df_cotieres.columns)
liste_cotieres = df_cotieres['Nom commune'].unique().tolist()
print(liste_cotieres[1:10])
# Statistiques par "Région" pour les communes filtrées
stats_region_filtered = df_cotieres.groupby('Région').apply(
    lambda x: pd.Series({
        'nombre_communes': x['Nom commune'].nunique(),
        'population_totale': x['Population'].sum()
    })
).reset_index()

# Afficher les résultats
print(stats_region_filtered)


# In[41]:


df_geolocalisees3 = df_geolocalisees2[df_geolocalisees2['communeName'].isin(liste_cotieres)]

# Filtrer les communes riveraines de la mer ou d'un océan
df_cotieres = df_cotieres[df_cotieres['Motif du classement'] == "Commune riveraine de la mer ou d'un océan"]

# Calculer le nombre de transactions par commune
nombre_transactions_cotieres = df_geolocalisees3.groupby('communeName').size().reset_index(name='Nombre de transactions')

show(nombre_transactions_cotieres)


# In[ ]:


# Charger le fichier GeoJSON des communes de France depuis le lien GitHub
url_commune = 'https://raw.githubusercontent.com/gregoiredavid/france-geojson/master/communes.geojson'
response_commune = rq.get(url_commune)
communes_geojson = response_commune.json()

# Charger le GeoJSON dans un GeoDataFrame
gdf_communes = gpd.GeoDataFrame.from_features(communes_geojson['features'])
gdf_communes_cotieres = gdf_communes[gdf_communes['nom'].isin(liste_cotieres)]

# Calculer les centroïdes pour chaque commune
gdf_communes_cotieres['centroid'] = gdf_communes_cotieres.geometry.centroid
gdf_communes_cotieres['latitude'] = gdf_communes_cotieres['centroid'].y
gdf_communes_cotieres['longitude'] = gdf_communes_cotieres['centroid'].x
gdf_communes_cotieres = gdf_communes_cotieres.drop(columns=['centroid'])
df_centres = gdf_communes_cotieres[['nom', 'latitude', 'longitude']]

liste_commune = gdf_communes_cotieres['nom'].to_list()
show(gdf_communes_cotieres)


# In[43]:


# Calculer le prix moyen par commune
prix_moyen_commune = df_geolocalisees3.groupby('communeName').sum()['valeur_fonciere'] / df_geolocalisees3.groupby('communeName').sum()['surface_reelle_bati']
prix_moyen_commune = prix_moyen_commune.reset_index()
prix_moyen_commune.columns = ['nom', 'prix_moyen']

nombre_transactions_commune = df_geolocalisees3.groupby('communeName').size()

nombre_transactions_commune_cotieres = nombre_transactions_commune[nombre_transactions_commune.index.isin(liste_cotieres)]

# Filtrer le DataFrame prix_moyen_commune pour ne garder que les communes présentes dans liste_commune_totale
prix_moyen_commune_filtre = prix_moyen_commune[prix_moyen_commune['nom'].isin(liste_cotieres)]

# Fusionner les données de prix avec les données géographiques des communes
gdf_communes = gdf_communes.merge(prix_moyen_commune_filtre, on='nom', how='left')

# Créer une carte centrée sur la France
carte = folium.Map(location=[46.603354, 1.888334], zoom_start=6)

# Ajouter la couche choroplétique pour les communes
choropleth = folium.Choropleth(
    geo_data=communes_geojson,
    name="Communes de France",
    fill_color="YlGnBu",  # Palette de couleurs
    fill_opacity=0.7,
    line_opacity=0.2,
    legend_name="Prix moyen par commune",
    data=prix_moyen_commune_filtre,
    columns=['nom', 'prix_moyen'],
    key_on="feature.properties.nom",
    nan_fill_color=None,  # Spécifie qu'il ne faut pas colorier les communes sans données

).add_to(carte)

# Ajouter des popups pour afficher le nom de la commune et le prix moyen
for _, row in gdf_communes.iterrows():
    if pd.notnull(row['prix_moyen']):
        folium.Marker(
            location=[row['geometry'].centroid.y, row['geometry'].centroid.x],
            popup=f"Commune : {row['nom']}<br>Prix moyen : {row['prix_moyen']:.2f} €/m²",
        ).add_to(carte)

# Afficher la carte
carte


# In[61]:


# Création de la variable adresse_py en remplaçant les espaces par des "+"
df_geolocalisees3['adresse_py'] = df_geolocalisees3['Adresse'].str.replace(' ', '+', regex=True)
df_missing = df_geolocalisees3[df_geolocalisees3['latitude'].isna()]
df_missing = df_missing.drop(columns=['latitude', 'longitude'])
show(df_geolocalisees3.head())


# In[56]:


root = 'https://api-adresse.data.gouv.fr/search/'
key = '?q='

# Boucle pour remplir les coordonnées manquantes
for index, row in df_missing.iterrows():
    address = row['adresse_py']
    req = rq.get(f'{root}{key}{address}')
    
    if req.status_code == 200:
        try:
            # Récupère les informations de latitude et longitude
            df = pd.json_normalize(req.json()['features'])
            data = df.iloc[0]  # Prend le premier résultat
            
            # Affecte la latitude et la longitude au DataFrame d'origine
            df_missing.at[index, 'latitude'] = data['geometry.coordinates'][1]  # df.x
            df_missing.at[index, 'longitude'] = data['geometry.coordinates'][0]  # df.y
        except IndexError:
            print(f"Aucune donnée trouvée pour l'adresse : {address}")
    else:
        print(f"Erreur de requête pour l'adresse : {address}, statut : {req.status_code}")

# Vérification des coordonnées ajoutées
df_missing.head()

show(df_missing)


# In[57]:


# Concatène les DataFrames en réinitialisant l'index
df_final = pd.concat([df_geolocalisees3, df_missing], ignore_index=True)

# Affiche le DataFrame final pour vérifier la concaténation

print(df_geolocalisees3.shape)
print(df_missing.shape)
print(df_final.shape)


# In[63]:


# Liste des communes
liste_communes = ['Paris', 'Marseille', 'Lyon', 'Toulouse', 'Nice']  # Exemple de liste de communes

# Créer un DataFrame vide avec les colonnes nécessaires
df_communes = pd.DataFrame(liste_communes, columns=['communeName'])
df_communes['latitude'] = None
df_communes['longitude'] = None

# Définir l'URL de base et la clé pour la requête
root = 'https://api-adresse.data.gouv.fr/search/'
key = '?q='

# Boucle pour remplir les coordonnées des mairies
for index, row in df_communes.iterrows():
    commune_name = row['communeName']
    address = f'Mairie+de+{commune_name}'  # Format de l'adresse à rechercher
    
    req = rq.get(f'{root}{key}{address}')
    
    if req.status_code == 200:
        try:
            # Récupère les informations de latitude et longitude
            df_result = pd.json_normalize(req.json()['features'])
            data = df_result.iloc[0]  # Prend le premier résultat
            
            # Affecte la latitude et la longitude au DataFrame d'origine
            df_communes.at[index, 'latitude_mairie'] = data['geometry.coordinates'][1]  # Latitude
            df_communes.at[index, 'longitude_mairie'] = data['geometry.coordinates'][0]  # Longitude
        except IndexError:
            print(f"Aucune donnée trouvée pour la commune : {commune_name}")
    else:
        print(f"Erreur de requête pour la commune : {commune_name}, statut : {req.status_code}")

# Vérification des coordonnées ajoutées
print(df_communes.head())


# In[ ]:


# Effectuer un left join entre df_final et df_communes
df_final = pd.merge(df_final, df_communes, how='left', left_on='communeName', right_on='communeName')

# Vérification du résultat
print(df_final.head())


# In[ ]:


def create_map_for_commune(df_geolocalisees3, df_centres, commune_name):
    # Filtrer les transactions uniquement pour la commune spécifiée
    df_commune = df_geolocalisees3[df_geolocalisees3['communeName'] == commune_name]

    # Obtenir les coordonnées du centre de la commune à partir du DataFrame df_centres
    coordinates = df_centres[df_centres['nom'] == commune_name][['latitude', 'longitude']].values.flatten()
    if coordinates.size == 0:
        print(f"Commune {commune_name} non trouvée dans le DataFrame df_centres.")
        return None
    
    # Créer une carte centrée sur la commune
    carte_commune = folium.Map(location=coordinates, zoom_start=13)

    # Ajouter des markers pour chaque transaction avec le prix par m²
    for _, row in df_commune.iterrows():
        if pd.notnull(row['latitude']) and pd.notnull(row['longitude']) and pd.notnull(row['prix_m2']):
            # Ajouter un marker avec le prix dans le popup
            folium.Marker(
                location=[row['latitude'], row['longitude']],
                popup=f"Prix/m² : {row['prix_m2']:.0f} €/m²"  # Affichage du prix arrondi à l'unité
            ).add_to(carte_commune)
            
            # Ajouter un Label pour afficher le prix directement sur la carte
            folium.Marker(
                location=[row['latitude'], row['longitude']],
                icon=folium.DivIcon(html=f'<div style="font-size: 8px; color: blue; font-weight: bold;">{round(row["prix_m2"]):.0f} €/m²</div>')  # Affichage du prix arrondi à l'unité avec une police plus petite
            ).add_to(carte_commune)

    # Afficher la carte
    return carte_commune

# Exemple d'utilisation pour la commune "Biarritz"
map = create_map_for_commune(df_geolocalisees3, df_centres, 'Biarritz')
map


# In[ ]:


import folium
from folium.plugins import HeatMap

def create_heatmap_for_commune(df_geolocalisees3, commune_name):
    # Filtrer les transactions uniquement pour la commune spécifiée
    df_commune = df_geolocalisees3[df_geolocalisees3['communeName'] == commune_name]

    # Obtenir les coordonnées du centre de la commune à partir du DataFrame df_centres
    coordinates = df_centres[df_centres['nom'] == commune_name][['latitude', 'longitude']].values.flatten()
    if coordinates.size == 0:
        print(f"Commune {commune_name} non trouvée dans le DataFrame df_centres.")
        return None
    
    # Créer une carte centrée sur la commune
    carte_commune = folium.Map(location=coordinates, zoom_start=13)

    # Calculer le prix minimum et maximum pour les gradients de couleur
    prix_min = df_commune['prix_m2'].min()
    prix_max = df_commune['prix_m2'].max()

    # Ajouter une couche de HeatMap pour visualiser la distribution des prix
    heat_data = [[row['latitude'], row['longitude'], row['prix_m2']] for _, row in df_commune.iterrows() if pd.notnull(row['latitude']) and pd.notnull(row['longitude']) and pd.notnull(row['prix_m2'])]
    
    # Ajouter la heatmap
    HeatMap(heat_data, min_opacity=0.2, max_val=prix_max, radius=15, blur=30, gradient={0.2: 'blue', 0.4: 'lime', 0.6: 'yellow', 0.8: 'orange', 1: 'red'}).add_to(carte_commune)

    # Afficher la carte
    return carte_commune

# Exemple d'utilisation pour la commune "Bandol"
heatmap = create_heatmap_for_commune(df_geolocalisees3, 'Bandol')
heatmap

