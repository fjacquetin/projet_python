
#module de récupération des données

import requests as rq
import geopandas as gpd
import pandas as pd
import os
import matplotlib.pyplot as plt
from shapely import wkt

import folium

#modules pour accélérer le téléchargement des zones inondables
import aiohttp
import asyncio
import zipfile

import glob

async def telechargement_fichier(url, nom_fichier):
    """
        fonction de téléchargement

        url (str): url de téléchargement
        nom_fichier (str): nom de fichier destination

    """
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as reponse:
            if reponse.status == 200:
                with open(nom_fichier, 'wb') as f:
                    f.write(await reponse.read())
                print(f"Téléchargement de {nom_fichier} terminé avec succès !")
            else:
                print(f"Erreur lors du téléchargement. Code HTTP : {reponse.status}")

def extraction_suppression_zip(fichier_zip, dossier_destination):
    """
        Fonction d'extraction du fichier zip des zones inondables

        fichier_zip (str): fichier zip
        dossier_destination (str): dossier destination
    """
    try:
        with zipfile.ZipFile(fichier_zip, 'r') as zip_ref:
            zip_ref.extractall(dossier_destination)
        print(f"fichier ZIP extrait {dossier_destination}")
        
        os.remove(fichier_zip)
        print(f"le fichier ZIP {fichier_zip} a été supprimmé.")
    
    except Exception as e:
        print(f"une erreur est apparue: {e}")


def get_communes_france(url_communes='https://raw.githubusercontent.com/gregoiredavid/france-geojson/master/communes.geojson', fichier_sortie_communes_france = 'projet_python/data/communes_france/communes_france.shp'):

    """
        fonction de téléchargement des communes françaises à partir d'un fichier geojson
        et export dans un fichier shp

        url_communes (str): localisation fichier des communes en geojson
        sortie_fichier_communes_france_shp (str): localisation fichier de sortie des communes en shapefile
    """

    print("récupération des communes francaises")

    response_commune = rq.get(url_communes)
    communes_geojson = response_commune.json()

    # Charger le GeoJSON dans un GeoDataFrame
    gdf_communes = gpd.GeoDataFrame.from_features(communes_geojson['features'])
    
    print(gdf_communes)

    #reprojection en Lambert 93
    gdf_communes = gdf_communes.set_crs(epsg=4326)
    gdf_communes = gdf_communes.to_crs(epsg=2154)

    #export des communes en Shapefile
    gdf_communes.to_file(fichier_sortie_communes_france)

def get_communes_cotieres(fichier_communes_france = "projet_python/data/communes_france/communes_france.shp", fichier_trait_de_cote = "projet_python/data/trait_de_cote/TCH_FRA_V2/Shapefile/TCH.shp",\
     fichier_sortie_communes_cotieres="projet_python/data/communes_cotieres/communes_cotieres.shp"):
    """
        Fonction de récupération des communes cotières en France à partir d'une jointure spatiale
    
        fichier_communes_france (str): localisation fichier des communes shp
        fichier_trait_de_cote (str): localisation fichier trait de cote shp
        fichier_sortie_communes_cotieres (str): localisation fichier communes cotieres shp
    """

    print("récupération des communes cotieres")

    #chargement des communes et du trait de côte
    gdf_communes = gpd.read_file(fichier_communes_france)
    gdf_trait_cote = gpd.read_file(fichier_trait_de_cote)

    #jointure spatiale pour récupérer les communes cotières
    gdf_communes_cotieres = gpd.sjoin(gdf_communes, gdf_trait_cote, how='inner', predicate='intersects')

    gdf_communes_cotieres.to_file(fichier_sortie_communes_cotieres)


def show_communes_cotieres(fichier_communes_cotieres_csv = "projet_python/data/communes_cotieres.csv", fichier_communes_cotieres_shp = "projet_python/data/communes_cotieres/communes_cotieres.shp",\
     communes_cotieres_shp_map = 'projet_python/data/map_communes_cotieres.html', communes_cotieres_csv_map = 'projet_python/data/map_communes_cotieres_csv.html'):
    """
        fonction de représentation des communes cotières
        Deux cartes sont prduites à partir de folium:
        - une a partir d'un fichier csv récupéré sur internet
        - une autre à partir du fichier SHP

        fichier_communes_cotieres_csv (str): localisation fichier communes cotieres en csv
        fichier_communes_cotieres_shp (str): localisation fichier communes cotieres en shp
        communes_cotieres_shp_map (str): localisation carte communes cotieres issues du shp
        communes_cotieres_csv_map (str): localisation carte communes cotieres issues du csv
    """

    print("représentation des communes cotieres")

    communes_cotieres_shp = gpd.read_file(fichier_communes_cotieres_shp)
    
    print(communes_cotieres_shp)

    df_csv = pd.read_csv(fichier_communes_cotieres_csv, delimiter = ';')

    #transformation de la géométrie en wkt
    df_csv['geometry'] = df_csv['geometry'].apply(wkt.loads)

    gdf_csv = gpd.GeoDataFrame(df_csv, geometry=df_csv['geometry'])

    map_shp = folium.Map(location=[48, 2], zoom_start=10)
    map_csv = folium.Map(location=[48, 2], zoom_start=10)

    # Add GeoDataFrame as GeoJSON to the Folium map
    folium.GeoJson(communes_cotieres_shp).add_to(map_shp)

    #reprojection des données issues du csv en Lambert 93
    gdf_csv = gdf_csv.set_crs(epsg=4326)
    gdf_csv = gdf_csv.to_crs(epsg=2154)

    folium.GeoJson(gdf_csv).add_to(map_csv)  

    map_shp.save(communes_cotieres_shp_map)
    map_csv.save(communes_cotieres_csv_map)


def get_zones_inondables():
    """
        récupérer la liste des départements cotiers
        télécharger les départements cotiers
        sélectionner la couche du scénario fort
        faire le plot des zones inondables sur la carte des gradients de prix
    """

    gdf_communes_cotieres = gpd.read_file("projet_python/data/communes_cotieres/communes_cotieres.shp")

    #print(gdf_communes_cotieres)

    liste_departements_cotiers = gdf_communes_cotieres['NumDep'].unique()

    liste_departements_cotiers_sans_Nan = [x for x in liste_departements_cotiers if x is not None]
    liste_departements_cotiers_sans_Nan.sort()

    for departement in liste_departements_cotiers_sans_Nan:
        
        #URL du fichier à télécharger
        url = f"https://files.georisques.fr/di_2020/tri_2020_sig_di_{departement}.zip"

        # Nom du fichier local
        fichier_zones_inondables = f"projet_python/data/zones_inondables/tri_2020_sig_di_{departement}.zip"

        # Exécuter la fonction de téléchargement asynchrone
        asyncio.run(telechargement_fichier(url, fichier_zones_inondables))

        #extraction du fichier zip et suppression de l'archive
        dossier_zones_inondables = "projet_python/data/zones_inondables/"

        extraction_suppression_zip(fichier_zones_inondables, dossier_zones_inondables)


def fusion_fichiers_inondations(nomenclature_zones_inondables = "iso_ht_03_01for_s_"):
    """
        Fonction de fusion des zones inondables
        fichier zones inondables = **iso_ht_03_01for_s_{departement}.shp

        TODO: lister tous les fichiers shp dans un répertoire 
        les charger dans un dataframe
        generalisation cartographique
        export en shp
    """

    # Lister tous les fichiers et dossiers dans le répertoire   
    fichiers_zones_inondables = glob.glob(os.path.join("projet_python/data/zones_inondables/**/**/", "*"+nomenclature_zones_inondables+"*.shp"))
    print(len(fichiers_zones_inondables))

    #suppression des fichiers shp qui ne sont pas utilisés pour la fusion
    fichiers_shp_a_supprimer = glob.glob(os.path.join("projet_python/data/zones_inondables/**/**/", "*.shp"))
    for f in fichiers_shp_a_supprimer:
        if f not in fichiers_zones_inondables:
            os.remove(f)

    gdf_liste = []
    for fichier_shp in fichiers_zones_inondables:
        departement = fichier_shp.split('.')[0][-2:]
        gdf = gpd.read_file(fichier_shp)
        gdf['dept'] = departement
        #print(gdf)
        gdf_liste.append(gdf[['id', 'dept', 'id_tri', 'geometry']])

    gdf_combine = pd.concat(gdf_liste, ignore_index=True)

    #généralisation cartographique avec l'algorithme Douglas-Peucker
    gdf_combine['geometry'] = gdf_combine['geometry'].simplify(tolerance=5)

    print("export du geodataframe des zones inondables en shp")
    output_shp = "projet_python/data/zones_inondables/zones_inondables.shp"
    gdf_combine.to_file(output_shp)

def edition_carte_zones_inondables(fichier_shp_zones_inondables = "projet_python/data/zones_inondables/zones_inondables.shp"):
    """
        fonction d'édition des zones inondables
    """

    print("edition de la carte des zones inondables")
    gdf = gpd.read_file(fichier_shp_zones_inondables)
    
    #print(gdf)

    map = folium.Map(location=[48, 2], zoom_start=10)

    #print(gdf)

    folium.GeoJson(gdf.loc[gdf['dept'] == '06']).add_to(map)
    map.save("projet_python/data/carte_zones_inondables_risque_fort.html")


if __name__ == "__main__":
    #get_communes_france()

    #get_communes_cotieres()
    #show_communes_cotieres()

    get_zones_inondables()

    fusion_fichiers_inondations()
    
    edition_carte_zones_inondables()
