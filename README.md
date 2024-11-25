# projet_python

But : évaluer l'effet de la hausse des zones à risque sur la valeur immobilière
Les risques climatiques chroniques incluent la montée du niveau de la mer et le risque d'inondation et de submersion
Ces risques peuvent être modélisées par les données de géo-risques
https://api.gouv.fr/documentation/api-georisques

On pourra regarder dans un premier temps :
- les Opérations sur les Territoires à Risques importants d'Inondation (TRI)
- Puis éventuellement dans un 2ème temps :
- les zones argileuses (Retrait gonflement des argiles)

Données mobilisées :
- Les "Données de valeur foncière" (DVF) regroupent l'ensemble des transactions immobilières notariéesde 2019 à 2024.
La base est publiée et produit par la direction générale des finances publiques (DGFiP) permet de connaître les transactions immobilières intervenues au cours des cinq dernières années sur le territoire métropolitain et les DOM-TOM, à l’exception de l’Alsace, de la Moselle et de Mayotte. Les données contenues sont issues des actes notariés et des informations cadastrales

Une base augmentée est "géolocalisée", c'est-à-dire que les transactions répertoriées sont situées en latitude et en longitude
https://www.data.gouv.fr/fr/datasets/demandes-de-valeurs-foncieres-geolocalisees/

Il est également produit par la DGFiP

Les données climatiques viendront du portail géo-risques

Modèle : le projet vise à déterminer un effet causal des risques climatiques sur les prix immobiliers
Dans un premier temps, les transactions seront cartographiées sur une carte de France incluant les zones à risque
Une méthode de clustering permettra de sélectionner les transactions dans une zone à risque, puis des transactions limitrophes de cette zone
Afin d'estimer au mieux les effets, un modèle de régression économétriques pourra estimer le niveau des prix selon les caractéristiques observables
(type de bien, nombre de pièces, proximité du centre ville, proximité géographique des services)

Eventuellement un appariemment avec la base DPE de l'ADEME pourra être tenté pour observer les caractéristiques de eprformance énergétique et énvironnementale

Décomposition du code :
- construction_dvf.ipynb : crée la base des transactions dans les communes cotières
- geolocalisation_actifs.ipynb : géolocalise les transactions non renseignées
- geolocalisation_risque.ipynb : demande à l'API géorisque si le bien est en zone inondable
- construction_tri.ipynb : crée la base .parquet des zones inondables
- visualisation_cotieres.ipynb : crée une carte de chaleur dans des grandes villes
- modele_gradient_ipynb : estime l'effet d'être en zone inondable
