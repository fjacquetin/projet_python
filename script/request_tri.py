import time
import requests

def check_inondable(lat, lon, timeout=3):
    """
    Vérifie si une localisation est dans une zone inondable via l'API Georisques (tri_zonage).
    Si le nombre de résultats est 1, retourne directement l'identifiant TRI, le libellé du type d'inondation,
    et le code du scénario.

    Args:
        lat (float): Latitude de la localisation.
        lon (float): Longitude de la localisation.
        commune (str, optional): Nom de la commune (pour les logs).
        timeout (int, optional): Temps maximum d'attente pour la requête en secondes. Par défaut : 3.

    Returns:
        tuple: (nombre de résultats, identifiant TRI, libellé type inondation, code scénario)
    """
    url = "https://georisques.gouv.fr/api/v1/tri_zonage"  # URL de l'API
    params = {
        'latlon': f"{lon},{lat}"  # Latlon dans le format: 'longitude,latitude'
    }
    
    try:
        response = requests.get(url, params=params, timeout=timeout)

        if response.status_code == 200:
            data = response.json()
            results = data.get('results', 0)
            
            if results == 1:
                # Extraction des informations spécifiques si 1 résultat est trouvé
                tri_data = data['data'][0]  # Le premier résultat

                # Identifiants et informations sur l'inondation
                identifiant_tri = tri_data.get('identifiant_tri', None)
                libelle_type_inondation = tri_data['typeInondation'].get('libelle', None)
                code_scenario = tri_data['scenario'].get('code', None)

                # Retourner les informations directement
                return results, identifiant_tri, libelle_type_inondation, code_scenario
            else:
                # Si aucun ou plus d'un résultat, retourne juste le nombre de résultats
                return results, None, None, None
        else:
            # print(f"Erreur API ({response.status_code}) pour la commune '{commune}' (lat: {lat}, lon: {lon}).")
            return 0, None, None, None

    except requests.exceptions.Timeout:
        # print(f"Requête expirée pour la commune '{commune}' (lat: {lat}, lon: {lon}).")
        return 0, None, None, None
    except requests.exceptions.RequestException:
        # print(f"Erreur de connexion pour la commune '{commune}' (lat: {lat}, lon: {lon}): {e}")
        return 0, None, None, None
    
def check_inondable_parallel(args):
    """
    Vérifie si un point géographique (latitude, longitude) est situé dans une zone inondable
    en utilisant une fonction externe `check_inondable`. La fonction inclut une gestion des erreurs
    et des tentatives multiples avec temporisation.

    Args:
        args (tuple): Un tuple contenant la latitude et la longitude du point (latitude, longitude).

    Returns:
        str: Résultat de la fonction `check_inondable` si la requête réussit.
        None: Si toutes les tentatives échouent.
    """
    latitude, longitude = args
    attempts = 2  # Nombre maximum de tentatives en cas d'échec
    for _ in range(attempts):
        try:
            return check_inondable(latitude, longitude)
        except requests.exceptions.RequestException:
            # Temporisation pour gérer les erreurs de connexion
            time.sleep(2)  
    # Retourne None si toutes les tentatives échouent
    return None