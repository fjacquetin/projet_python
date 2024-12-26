import requests
import geopandas as gpd
import pandas as pd
import os
import folium
import zipfile
import glob
from PIL import Image
import io
import shutil


def get_communes_france(url_communes='https://raw.githubusercontent.com/gregoiredavid/france-geojson/master/communes.geojson', fichier_sortie_communes_france = 'data/communes_france/communes_france.shp'):

    """
        fonction de téléchargement des communes françaises à partir d'un fichier geojson
        et export dans un fichier shp

        url_communes (str): localisation fichier des communes en geojson
        sortie_fichier_communes_france_shp (str): localisation fichier de sortie des communes en shapefile
    """

    print("Récupération des communes francaises")

    response_commune = requests.get(url_communes)
    communes_geojson = response_commune.json()

    # Charger le GeoJSON dans un GeoDataFrame
    gdf_communes = gpd.GeoDataFrame.from_features(communes_geojson['features'])

    #reprojection en Lambert 93
    gdf_communes = gdf_communes.set_crs(epsg=4326)
    gdf_communes = gdf_communes.to_crs(epsg=2154)

    #export des communes en Shapefile
    gdf_communes.to_file(fichier_sortie_communes_france)

def get_communes_cotieres(fichier_communes_france = "data/communes_france/communes_france.shp", fichier_trait_de_cote = "data/trait_de_cote/TCH_FRA_V2/Shapefile/TCH.shp",\
     fichier_sortie_communes_cotieres="data/communes_cotieres/communes_cotieres.shp"):
    """
        Fonction de récupération des communes cotières en France à partir d'une jointure spatiale
    
        fichier_communes_france (str): localisation fichier des communes shp
        fichier_trait_de_cote (str): localisation fichier trait de cote shp
        fichier_sortie_communes_cotieres (str): localisation fichier communes côtieres shp
    """

    #chargement des communes et du trait de côte
    gdf_communes = gpd.read_file(fichier_communes_france)
    gdf_trait_cote = gpd.read_file(fichier_trait_de_cote)

    #jointure spatiale pour récupérer les communes cotières
    gdf_communes_cotieres = gpd.sjoin(gdf_communes, gdf_trait_cote, how='inner', predicate='intersects')
    repertoire_communes_cotieres = "data/communes_cotieres"
    
    if os.path.exists(repertoire_communes_cotieres):
        if os.path.isdir(repertoire_communes_cotieres):
            # Enregistrer le fichier .shp dans le répertoire existant
            gdf_communes_cotieres.to_file(fichier_sortie_communes_cotieres)
        else:
        # Si c'est un fichier mais pas un répertoire, le supprimer et recréer le répertoire
            os.remove(repertoire_communes_cotieres)
            os.makedirs(repertoire_communes_cotieres)
            gdf_communes_cotieres.to_file(fichier_sortie_communes_cotieres)
    else:
        # Si le répertoire n'existe pas, le créer
        os.makedirs(repertoire_communes_cotieres)
        gdf_communes_cotieres.to_file(fichier_sortie_communes_cotieres)
    

def show_communes_cotieres(fichier_communes_cotieres_shp="data/communes_cotieres/communes_cotieres.shp", 
                           communes_cotieres_shp_map='data/map_communes_cotieres_shp.html'
                           ):
    """
    Fonction de représentation des communes côtières
    Une carte est produite à partir du fichier SHP (Folium)

    fichier_communes_cotieres_csv (str): localisation fichier communes côtières en CSV
    fichier_communes_cotieres_shp (str): localisation fichier communes côtières en SHP
    communes_cotieres_shp_map (str): localisation carte communes côtières issues du SHP
    communes_cotieres_csv_map (str): localisation carte communes côtières issues du CSV
    """
    # Charger les données géospatiales
    communes_cotieres_shp = gpd.read_file(fichier_communes_cotieres_shp)

    # Créer la carte Folium pour le SHP
    map_shp = folium.Map(location=[46, 3], zoom_start=5)
    
    # Ajouter le GeoDataFrame SHP à la carte Folium
    folium.GeoJson(communes_cotieres_shp).add_to(map_shp)
    
    # Sauvegarder la carte dans un fichier HTML
    map_shp.save(communes_cotieres_shp_map)
    
    # Capturer une image de la carte SHP
    img_data_shp = map_shp._to_png(5)
    img_shp = Image.open(io.BytesIO(img_data_shp))
    img_shp.save('maps/communes_cotieres_shp.png')  # Sauvegarder l'image SHP
    
    return img_shp


# Fonction de téléchargement du fichier (sauf téléchargement asynchrone)
def telechargement_fichier(url, chemin_local):
    """Télécharge un fichier depuis une URL et le sauvegarde à un emplacement local."""
    try:
        response = requests.get(url)
        if response.status_code == 200:
            with open(chemin_local, 'wb') as f:
                f.write(response.content)

    except Exception as e:
        print(f"Erreur lors du téléchargement de {url}: {e}")

# Fonction de suppression et d'extraction du zip
def extraction_suppression_zip(fichier_zip, dossier_destination):
    """Extrait un fichier zip et supprime l'archive."""
    if os.path.exists(fichier_zip):  # Vérifie si le fichier zip existe avant de tenter l'extraction
        with zipfile.ZipFile(fichier_zip, 'r') as zip_ref:
            zip_ref.extractall(dossier_destination)
        os.remove(fichier_zip)

# Fonction de traitement de chaque département
def telecharger_et_traiter_departement(departement, dossier_zones_inondables):
    """Télécharge et traite les données pour un département spécifique."""
    url = f"https://files.georisques.fr/di_2020/tri_2020_sig_di_{departement}.zip"
    fichier_zones_inondables = os.path.join(dossier_zones_inondables, f"tri_2020_sig_di_{departement}.zip")

    # Vérification si le fichier existe déjà
    if not os.path.exists(fichier_zones_inondables):
        telechargement_fichier(url, fichier_zones_inondables)  # Télécharger le fichier si nécessaire
        extraction_suppression_zip(fichier_zones_inondables, dossier_zones_inondables)
    else:
        extraction_suppression_zip(fichier_zones_inondables, dossier_zones_inondables)

# Fonction principale pour récupérer les zones inondables
def get_zones_inondables():
    """
    Récupérer la liste des départements côtiers, télécharger et traiter les fichiers associés.
    """
    gdf_communes_cotieres = gpd.read_file("data/communes_cotieres/communes_cotieres.shp")

    liste_departements_cotiers = gdf_communes_cotieres['NumDep'].unique()
    liste_departements_cotiers_sans_Nan = [x for x in liste_departements_cotiers if x is not None]
    liste_departements_cotiers_sans_Nan.sort()

    # Créer une boucle et télécharger les fichiers pour chaque département
    dossier_zones_inondables = "data/zones_inondables/"
    for departement in liste_departements_cotiers_sans_Nan:
        telecharger_et_traiter_departement(departement, dossier_zones_inondables)

def fusion_fichiers_inondations(nomenclature_zones_inondables="iso_ht_03_01for_s_"):
    """
    Fusionner les fichiers shapefiles des zones inondables, enregistrer le résultat,
    et supprimer les répertoires commençant par 'tri' dans data/zones_inondables.
    """
    # Recherche des fichiers shapefiles correspondant à la nomenclature
    fichiers_zones_inondables = glob.glob(
        os.path.join("data/zones_inondables/**/**/", f"*{nomenclature_zones_inondables}*.shp"), 
        recursive=True
    )
    print(f"Nombre de fichiers trouvés : {len(fichiers_zones_inondables)}")

    gdf_liste = []
    for fichier_shp in fichiers_zones_inondables:
        departement = fichier_shp.split('.')[-2][-2:]  # Extraire le département
        gdf = gpd.read_file(fichier_shp)
        gdf['dept'] = departement
        gdf_liste.append(gdf[['id', 'dept', 'id_tri', 'geometry']])

    # Fusionner tous les shapefiles
    gdf_combine = pd.concat(gdf_liste, ignore_index=True)

    # Simplification géométrique
    gdf_combine['geometry'] = gdf_combine['geometry'].simplify(tolerance=5)

    print("Export du geodataframe des zones inondables en shapefile...")
    output_shp = "data/zones_inondables/zones_inondables.shp"
    gdf_combine.to_file(output_shp)

    # Suppression des répertoires commençant par "tri"
    tri_dirs = glob.glob(os.path.join("data/zones_inondables/", "tri*"))
    for tri_dir in tri_dirs:
        shutil.rmtree(tri_dir, ignore_errors=True)


def edition_carte_zones_inondables(fichier_shp_zones_inondables="data/zones_inondables/zones_inondables.shp"):
    """
    Fonction d'édition des zones inondables et génération d'une carte.
    Affiche uniquement la carte des zones inondables avec les zones de risque fort.
    
    fichier_shp_zones_inondables (str): localisation du fichier SHP des zones inondables.
    """
    print("Édition de la carte des zones inondables")

    # Charger le fichier SHP
    gdf = gpd.read_file(fichier_shp_zones_inondables)
    
    # Créer la carte avec Folium
    map = folium.Map(location=[43.6, 7.15], zoom_start=11)

    # Ajouter le GeoDataFrame avec les zones de risque fort pour le département 06
    folium.GeoJson(gdf.loc[gdf['dept'] == '06']).add_to(map)
    
    # Sauvegarder la carte sous format HTML
    map.save("data/carte_zones_inondables_risque_fort.html")

    # Capturer l'image de la carte (en PNG)
    img_data = map._to_png(5)  # Ajuster la qualité avec le paramètre (ici 5)
    
    # Convertir l'image en PIL
    img = Image.open(io.BytesIO(img_data))
    
    # Sauvegarder l'image sous format PNG
    img.save('maps/carte_zones_inondables_risque_fort.png')

    return img
