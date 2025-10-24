from models.vehicule import Vehicule
from models.route import Route
from models.reseau import Reseau
from core.config_loader import ConfigurationLoader
import os

def main():
    print("=== Simulateur de Trafic - Version Réseau avec Changements de Routes ===\n")
    
    # Chemin vers le fichier de configuration
    script_dir = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(script_dir, 'data', 'config_reseau.json')
    
    print(f"Recherche du fichier de configuration: {config_path}")
    reseau = ConfigurationLoader.creer_reseau_depuis_config(config_path)
    print(f"Réseau chargé: {reseau.nom}")
    print(f"Nombre de routes: {len(reseau.routes)}")
    print(f"Véhicules de Route A1: {[v.identifiant for v in reseau.routes['A1'].vehicules]}")
    print(f"Les connexions sont: {reseau.connections}")

    print("\n=== État initial du réseau ===")
    for nom_route, route in reseau.routes.items():
        print(f"\nRoute {nom_route} (longueur: {route.longueur}):")
        for vehicule in route.vehicules:
            print(f"  {vehicule.identifiant} - Position: {vehicule.position}, Vitesse: {vehicule.vitesse}")

    # Simulation de quelques pas de temps
    print("\n=== Simulation en cours ===")
    for pas in range(15):
        print(f"\n{'='*50}")
        print(f"--- Pas de temps {pas + 1} ---")
        
        # Afficher l'état avant mise à jour
        print("État avant mise à jour:")
        for nom_route, route in reseau.routes.items():
            if route.vehicules:
                vehicules_info = [f"{v.identifiant}({v.position:.1f})" for v in route.vehicules]
                print(f"  {nom_route}: {vehicules_info}")
        
        # Mettre à jour le réseau
        reseau.mettre_a_jour_reseau()
        
        # Afficher l'état après mise à jour
        print("État après mise à jour:")
        for nom_route, route in reseau.routes.items():
            if route.vehicules:
                vehicules_info = [f"{v.identifiant}({v.position:.1f})" for v in route.vehicules]
                print(f"  {nom_route}: {vehicules_info}")
        
        # Afficher les statistiques
        stats = reseau.obtenir_statistiques()
        print(f"Véhicules actifs: {stats['total_vehicules_actifs']}, Véhicules sortis: {stats['vehicules_sortis']}")
        
        # Arrêter si plus de véhicules
        if stats['total_vehicules_actifs'] == 0:
            print("\n🏁 Tous les véhicules ont quitté le réseau!")
            break

    # Statistiques finales
    print(f"\n{'='*50}")
    print("=== Statistiques finales ===")
    stats = reseau.obtenir_statistiques()
    for key, value in stats.items():
        print(f"{key}: {value}")
    
    # Statistiques des véhicules sortis
    if reseau.vehicules_sortis:
        print("\n=== Véhicules qui ont quitté le réseau ===")
        for vehicule in reseau.vehicules_sortis:
            vehicule_stats = vehicule.obtenir_statistiques()
            print(f"{vehicule.identifiant}:")
            print(f"  - Distance totale: {vehicule_stats['distance_totale_parcourue']}")
            print(f"  - Routes visitées: {vehicule_stats['routes_visitees']}")
            print(f"  - Historique: {vehicule_stats['historique_routes']}")

if __name__ == "__main__":
    main()