import folium
from folium.plugins import HeatMap

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