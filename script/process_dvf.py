import pandas as pd
from IPython.display import display

def afficher_tableau_par_id_mutation(df, id_mutation_str):
    """
    Affiche un tableau filtré par id_mutation dans un joli format pour Jupyter Notebook.
    
    Paramètres :
    df (DataFrame) : Le DataFrame contenant les données.
    id_mutation_str (str) : L'ID de mutation sous forme de chaîne à filtrer.
    """
    
    # Vérifier si l'id_mutation existe dans les données
    if 'id_mutation' not in df.columns:
        print("Erreur : la colonne 'id_mutation' n'existe pas dans le DataFrame.")
        return
    
    # Filtrer le DataFrame en fonction de l'id_mutation
    df_filtered = df[df['id_mutation'].astype(str) == id_mutation_str]
    
    # Si aucun résultat n'est trouvé, afficher un message
    if df_filtered.empty:
        print(f"Aucun enregistrement trouvé pour l'id_mutation {id_mutation_str}.")
        return
    
    # Sélectionner les colonnes nécessaires
    colonnes_a_afficher = ['id_mutation', 'valeur_fonciere', 'type_local', 'surface_reelle_bati', 
                           'surface_terrain', 'nature_culture', 'nombre_pieces_principales']
    
    # Vérifier que toutes les colonnes existent
    colonnes_existantes = [col for col in colonnes_a_afficher if col in df.columns]
    df_filtered = df_filtered[colonnes_existantes]
    df_filtered = df_filtered.reset_index(drop=True)

    # Affichage du tableau avec un formatage soigné
    display(df_filtered)

    return None

def process_group(group):
    
    # Filtrer les lignes où 'nature_culture' est différent de vide ou de "sols"
    
    maison_present = 'Maison' in group['type_local'].values
    appart_present = 'Appartement' in group['type_local'].values
    dependance_present = 'Dépendance' in group['type_local'].values
    
    bati_group = group[group['type_local'].isin(['Maison', 'Appartement'])]
    surface_reelle_bati = bati_group['surface_reelle_bati'].fillna(0).sum()
    surface_terrain = group['surface_terrain'].fillna(0).sum()
    
    # Vérifier les colonnes avant d'accéder à leur première valeur
    valeur_fonciere = group['valeur_fonciere'].iloc[0] if not group['valeur_fonciere'].empty else None
    nombre_pieces_principales = group['nombre_pieces_principales'].max() if not group['nombre_pieces_principales'].isna().all() else None
    id_mutation = group['id_mutation'].iloc[0]
    numero_dispositon = group['numero_disposition'].iloc[0]
    # Résultats
    result = {
        'id_mutation' : id_mutation,
        'numero_disposition' : numero_dispositon,
        'valeur_fonciere': valeur_fonciere,
        'surface_reelle_bati': surface_reelle_bati,
        'surface_terrain': surface_terrain,
        'nombre_locaux': len(group),
        'maison_present': maison_present,
        'appart_present': appart_present,
        'dependance': dependance_present,
        'nombre_pieces_principales': nombre_pieces_principales,
    }

    # Ajouter les colonnes supplémentaires (avec vérification)
    for col in group.columns:
        if col not in result:
            result[col] = group[col].iloc[0] if not group[col].empty else None
    
    return pd.Series(result)