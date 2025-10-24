from ioo.affichage import simuler_reseau_graphique
from models.vehicule import Vehicule
from models.route import Route
import os

from core.config_loader import ConfigurationLoader



def simulation_reseau():

    """Simulation graphique d'un réseau complet"""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(script_dir, 'data', 'config_reseau.json')
 
    try:
        reseau = ConfigurationLoader.creer_reseau_depuis_config(config_path)
        simuler_reseau_graphique(reseau)
    except Exception as e:
        print(f"Erreur lors du chargement du réseau: {e}")
        print("Utilisation de la simulation simple...")
         

if __name__=="__main__":
 
    simulation_reseau()