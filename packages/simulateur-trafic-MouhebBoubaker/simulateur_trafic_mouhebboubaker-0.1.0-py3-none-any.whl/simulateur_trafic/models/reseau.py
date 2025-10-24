from typing import Dict, List
from models.route import Route
import json
import random

class Reseau:
    def __init__(self, nom: str = "Reseau_Principal"):
        self.nom = nom
        self.routes: Dict[str, Route] = {}
        self.connections: Dict[str, List[str]] = {}  # route_id -> list of connected route_ids
        self.vehicules_sortis = []  # Véhicules qui ont quitté le réseau
      
    def ajouter_route(self, route: Route):
        """Ajoute une route au réseau"""
        if route.nom not in self.routes:
            self.routes[route.nom] = route
            if route.nom not in self.connections:
                self.connections[route.nom] = []

    def connecter_routes(self, route1_nom: str, route2_nom: str):
        """Connecte deux routes dans le réseau (connexion bidirectionnelle)"""
        if route1_nom in self.routes and route2_nom in self.routes:
            if route2_nom not in self.connections[route1_nom]:
                self.connections[route1_nom].append(route2_nom)
            # if route1_nom not in self.connections[route2_nom]:
            #     self.connections[route2_nom].append(route1_nom)

    def obtenir_routes_connectees(self, route_nom: str) -> List[str]:
        """Retourne la liste des noms des routes connectées à une route donnée"""
        return self.connections.get(route_nom, [])

    def choisir_prochaine_route(self, route_actuelle_nom: str) -> str:
        """Choisit aléatoirement la prochaine route parmi celles connectées"""
        routes_connectees = self.obtenir_routes_connectees(route_actuelle_nom)
        
        if routes_connectees:
            return random.choice(routes_connectees)
        return None

    def gerer_changements_routes(self):
        """Gère les changements de routes pour tous les véhicules"""
        changements_effectues = 0
        
        for route in self.routes.values():
            vehicules_a_changer = route.mettre_a_jour_vehicules()
            
            for vehicule in vehicules_a_changer:
                prochaine_route_nom = self.choisir_prochaine_route(route.nom)
                
                if prochaine_route_nom:
                    prochaine_route = self.routes[prochaine_route_nom]
                    print(f"🚗 {vehicule.identifiant} change de {route.nom} vers {prochaine_route_nom}")
                    vehicule.changer_de_route(prochaine_route)
                    changements_effectues += 1
                else:
                    # Aucune route connectée, le véhicule quitte le réseau
                    print(f"{vehicule.identifiant} quitte le réseau depuis {route.nom}")
                    route.retirer_vehicule(vehicule)
                    self.vehicules_sortis.append(vehicule)
        
        return changements_effectues

    def mettre_a_jour_reseau(self):
        """Met à jour tous les véhicules de toutes les routes du réseau"""
        # D'abord, gérer les mouvements normaux et identifier les changements de route
        changements = self.gerer_changements_routes()
        
        if changements > 0:
            print(f"📊 {changements} changement(s) de route effectué(s)")

    def obtenir_statistiques(self):
        """Retourne les statistiques complètes du réseau"""
        total_vehicules_actifs = sum(len(route.vehicules) for route in self.routes.values())
        total_longueur = sum(route.longueur for route in self.routes.values())
        
        return {
            "nombre_routes": len(self.routes),
            "total_vehicules_actifs": total_vehicules_actifs,
            "vehicules_sortis": len(self.vehicules_sortis),
            "total_longueur": total_longueur,
            "routes": {nom: len(route.vehicules) for nom, route in self.routes.items()},
            "connexions": self.connections
        }

    def charger_depuis_json(self, fichier_config: str):
        """Charge la configuration du réseau depuis un fichier JSON"""
        with open(fichier_config, 'r', encoding='utf-8') as f:
            config = json.load(f)

        # Charger les routes
        for route_config in config.get("routes", []):
            route = Route(
                nom=route_config['nom'],
                longueur=route_config['longueur'],
                limite_vitesse=route_config['limite_vitesse']
            )
            self.ajouter_route(route)
        
        # Charger les connexions
        for connexion in config.get('connexions', []):
            self.connecter_routes(connexion['route1'], connexion['route2'])
        
        return self

    def sauvegarder_vers_json(self, fichier_config: str):
        """Sauvegarde la configuration du réseau vers un fichier JSON"""
        config = {
            "nom_reseau": self.nom,
            "routes": [
                {
                    "nom": route.nom,
                    "longueur": route.longueur,
                    "limite_vitesse": route.limite_vitesse
                }
                for route in self.routes.values()
            ],
            "connexions": [
                {"route1": route_nom, "route2": route_connectee}
                for route_nom, routes_connectees in self.connections.items()
                for route_connectee in routes_connectees
                if route_nom < route_connectee  # Éviter les doublons
            ]
        }
        
        with open(fichier_config, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)