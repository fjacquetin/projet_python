# projet_python

But : �valuer l'effet de la hausse des zones � risque sur la valeur immobili�re
Les risques climatiques chroniques incluent la mont�e du niveau de la mer et le risque d'inondation et de submersion
Ces risques peuvent �tre mod�lis�es par les donn�es de g�o-risques
https://api.gouv.fr/documentation/api-georisques

On pourra regarder dans un premier temps :
- les Op�rations sur les Territoires � Risques importants d'Inondation (TRI)
- Puis �ventuellement dans un 2�me temps :
- les zones argileuses (Retrait gonflement des argiles)

Donn�es mobilis�es :
- Les "Donn�es de valeur fonci�re" (DVF) regroupent l'ensemble des transactions immobili�res notari�esde 2019 � 2024.
La base est publi�e et produit par la direction g�n�rale des finances publiques (DGFiP) permet de conna�tre les transactions immobili�res intervenues au cours des cinq derni�res ann�es sur le territoire m�tropolitain et les DOM-TOM, � l�exception de l�Alsace, de la Moselle et de Mayotte. Les donn�es contenues sont issues des actes notari�s et des informations cadastrales

Une base augment�e est "g�olocalis�e", c'est-�-dire que les transactions r�pertori�es sont situ�es en latitude et en longitude
https://www.data.gouv.fr/fr/datasets/demandes-de-valeurs-foncieres-geolocalisees/

Il est �galement produit par la DGFiP

Les donn�es climatiques viendront du portail g�o-risques

Mod�le : le projet vise � d�terminer un effet causal des risques climatiques sur les prix immobiliers
Dans un premier temps, les transactions seront cartographi�es sur une carte de France incluant les zones � risque
Une m�thode de clustering permettra de s�lectionner les transactions dans une zone � risque, puis des transactions limitrophes de cette zone
Afin d'estimer au mieux les effets, un mod�le de r�gression �conom�triques pourra estimer le niveau des prix selon les caract�ristiques observables
(type de bien, nombre de pi�ces, proximit� du centre ville, proximit� g�ographique des services)

Eventuellement un appariemment avec la base DPE de l'ADEME pourra �tre tent� pour observer les caract�ristiques de eprformance �nerg�tique et �nvironnementale

D�composition du code :
- construction_dvf.ipynb : cr�e la base des transactions dans les communes coti�res
- geolocalisation_actifs.ipynb : g�olocalise les transactions non renseign�es
- geolocalisation_risque.ipynb : demande � l'API g�orisque si le bien est en zone inondable
- construction_tri.ipynb : cr�e la base .parquet des zones inondables
- visualisation_cotieres.ipynb : cr�e une carte de chaleur dans des grandes villes
- modele_gradient_ipynb : estime l'effet d'�tre en zone inondable
