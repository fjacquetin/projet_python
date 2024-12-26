## Projet Python : La décote immobilière sur les littoraux  
**Auteurs** : Florian Jacquetin & Philémon Pensier, Groupe 8  

---

## Sommaire  
1. [Introduction](#1-introduction)  
2. [Résultats-clés](#2-résultats-clés)  
3. [Source des données](#3-source-des-données)  
4. [Présentation du dépôt](#4-présentation-du-dépôt)  
5. [Contributions](#5-contributions)  
6. [Auteurs](#6-auteurs)  

---

## 1. Introduction  
La décote littorale représente la dépréciation des valeurs immobilières en raison des risques côtiers tels que la montée des eaux, les submersions et l'érosion.  
Ce projet utilise les données de transactions immobilières recensées par **DVF (2023)** et les informations de l'application **Géorisques** pour construire un modèle hédonique et spatial.  

---

## 2. Résultats-clés  
- **Appartements exposés** : Décote estimée à **8%**.  
- **Maisons exposées** : Pas d’effet significatif détecté, traduisant une possible **myopie des acheteurs** face aux risques.  

---

## 3. Source des données  
L'ensemble des données utilisées est soit directement disponible via des API open-source, soit via des bases de données publiques soumises à des licences ouvertes.

Les données reposent sur les sources suivantes :  
- Les Demandes de Valeurs Foncières géolocalisées (DVF) : https://www.data.gouv.fr/fr/datasets/demandes-de-valeurs-foncieres-geolocalisees  
- Les fichiers géographiques français, mis à disposition par Grégoire David (https://github.com/gregoiredavid/france-geojson)  
- La Base de Données Nationales des Bâtiments (BDNB) : https://www.data.gouv.fr/fr/datasets/base-de-donnees-nationale-des-batiments  
- L'API Géorisques : https://www.georisques.gouv.fr/doc-api  
- L'API Adresse : https://adresse.data.gouv.fr/api-doc/adresse  
- L'API Overpass, via le module overpy de Python  

---

## 4. Présentation du dépôt  
Notre production est essentiellement localisée dans deux versions d'un fichier `main.ipynb` :

- **Version 1** : Contient uniquement le code non exécuté et les commentaires entre les cellules.  
- **Version 2** : Contient le code préalablement exécuté pour présenter les résultats même en cas d'inaccessibilité temporaire des sources.  

C'est cette version exécutée qui tient lieu de rapport final.  

**Organisation des fichiers et dossiers :**  
- `data` : Copie locale de certaines données issues de nos sources.  
- `scripts` : Contient des fonctions utiles pour rendre le code plus lisible et maintenable.  
- `maps` : Cartes des communes côtières retenues, avec gradients de prix et zones inondables "fortes".  
- `requirements.txt` : Contient la liste des dépendances nécessaires à installer avec `pip`.  

**Instructions :**  
1. Assurez-vous d’avoir Python 3.x installé.  
2. Lancez le notebook principal (sans résultats enregistrés) : `main.ipynb`.  

---

## 5. Contributions  
Les contributions sont les bienvenues. Merci de soumettre vos propositions via une pull request en respectant les bonnes pratiques de développement.  

---

## 6. Auteurs  
- **Florian Jacquetin**  
- **Philémon Pensier**  

Ce projet est réalisé par Florian Jacquetin et Philémon Pensier dans le cadre du cours _Python pour la Data Science_ de 2ème année à l'ENSAE, réalisé par Lino Galiana, et encadré au sein du groupe 8 par Daniel Marin.  