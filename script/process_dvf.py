import pandas as pd

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