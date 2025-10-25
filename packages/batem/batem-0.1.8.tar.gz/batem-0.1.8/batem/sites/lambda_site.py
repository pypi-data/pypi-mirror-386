"""
This code has been written by stephane.ploix@grenoble-inp.fr
It is protected under GNU General Public License v3.0
"""


# configuration of the lambda house
from __future__ import annotations
import batem.core.lambdahouse
import batem.core.weather
import batem.core.library
import batem.core.solar
import configparser
import time
import sys


config = configparser.ConfigParser()
config.read('setup.ini')
weather_file_name = None

# weather_file: str = 'campus_transition.json'
# location: str = 'Forges'
# weather_year = 2019
# latitude_north_deg, longitude_east_deg = 48.419742, 2.962580

# weather_file: str = 'Grenoble.json'
# location: str = 'Grenoble'
# weather_year = 2022
# latitude_north_deg, longitude_east_deg = 45.19154994547585, 5.722065312331381

# weather_file: str = 'saint-nazaire.json'
# location: str = 'Saint-Nazaire'
# weather_year = 2022
# latitude_north_deg, longitude_east_deg = 47.271497, -2.208271

# weather_file: str = 'le_caire.json'
# location: str = 'Le Caire'
# weather_year = 2022
# latitude_north_deg, longitude_east_deg = 30.088719, 31.235820

# weather_file: str = 'briancon.json'
# location: str = 'Briançon'
# weather_year = 2022
# latitude_north_deg, longitude_east_deg = 44.901334, 6.644723

# weather_file: str = 'tirana.json'
# location: str = 'Tirana'
# weather_year = 2022
# latitude_north_deg, longitude_east_deg = 41.33480772491761, 19.821014460650115

# weather_file: str = 'kigali.json'
# location: str = 'kigali'
# weather_year = 2023
# latitude_north_deg, longitude_east_deg = -1.9632023804126906, 30.081752323270084

# weather_file: str = 'narbonne.json'
# location: str = 'narbonne'
# weather_year = 2023
# latitude_north_deg, longitude_east_deg = 43.185457207892796, 3.0031356684177566

weather_file: str = 'saint-honore1500.json'
location: str = 'saint-honore1500'
weather_year = 2023
latitude_north_deg, longitude_east_deg = 44.97234276373383, 5.8243913845702595

# weather_file: str = 'bruxelles.json'
# location: str = 'bruxelles'
# weather_year = 2023
# latitude_north_deg, longitude_east_deg = 50.84899842366747, 4.353543283688299

# weather_file: str = 'liege.json
# location: str = 'liege'
# weather_year = 2023
# latitude_north_deg, longitude_east_deg = 50.63809597884662, 5.5748852887240945

# weather_file: str = 'coimbra.json'
# location: str = 'Coimbra'
# weather_year = 2022
# latitude_north_deg, longitude_east_deg = 40.206317, -8.428578

# weather_file: str = 'refuge_des_bans.json'
# location: str = 'Refuge des Bans'
# weather_year = 2022
# latitude_north_deg, longitude_east_deg = 44.83460591359195, 6.361240519353813

# weather_file: str = 'barcelonnette.json'
# location: str = 'Barcelonnette'
# weather_year = 2022
# latitude_north_deg, longitude_east_deg = 44.387127, 6.652518

# location: str = 'Crolles'
# weather_year = 2022
# latitude_north_deg, longitude_east_deg = 45.284790, 5.885759

# location: str = 'Assouan'
# weather_year = 2022
# latitude_north_deg, longitude_east_deg = 24.02769921861417, 32.87455490478971

# location: str = 'Cayenne'
# weather_year = 2023
# latitude_north_deg, longitude_east_deg = 4.924435336591809, -52.31276008988111

# location: str = 'RefugeDeLaPilatte'
# weather_year = 2023
# latitude_north_deg, longitude_east_deg = 44.870439591344194, 6.331864347312895

# location: str = 'Giens'
# weather_year = 2023
# latitude_north_deg, longitude_east_deg = 43.05173789891146, 6.132881864519103

# location: str = 'AutransMeaudre'
# weather_year = 2023
# latitude_north_deg, longitude_east_deg = 45.175560185534195, 5.5427723689148065

# location: str = 'la-cote-saint-andre'
# weather_year = 2022
# latitude_north_deg, longitude_east_deg = 45.393775, 5.260494

# location: str = 'Meolans'
# weather_year = 2022
# latitude_north_deg, longitude_east_deg = 44.399190, 6.497175

# location: str = "Saint-Germain-au-Mont-d'Or"
# weather_year = 2022
# latitude_north_deg, longitude_east_deg = 45.884843, 4.801576

# location: str = "Ardennes"
# weather_year = 2022
# latitude_north_deg, longitude_east_deg = 49.81357529876085, 4.74266551569724

# location: str = "Liege"
# weather_year = 2022
# latitude_north_deg, longitude_east_deg = 50.63809597884662, 5.5748852887240945

# location: str = "Grenoble_campus"
# weather_year = 2022
# latitude_north_deg, longitude_east_deg = 45.191135, 5.764832

# location: str = "Rotterdam"
# weather_year = 2023
# latitude_north_deg, longitude_east_deg = 51.932723048945405, 4.469347589348471

# location: str = "Liège"
# weather_year = 2023
# latitude_north_deg, longitude_east_deg = 50.63809597884662, 5.5748852887240945

# location: str = "Nagada"
# weather_year = 2023
# latitude_north_deg, longitude_east_deg = 25.90082736144239, 32.72443181962625

# location: str = "Novara"
# weather_year = 2023
# latitude_north_deg, longitude_east_deg = 45.453333753154936, 8.62274742072009

# location: str = "DahammaMahi"
# weather_year = 2023
# latitude_north_deg, longitude_east_deg = 47.777145, 3.169911

# location: str = "Mens"
# weather_year = 2023
# latitude_north_deg, longitude_east_deg = 44.816667, 5.750000

# latitude_north_deg, longitude_east_deg = 45.39394199789429, 5.259668832483038
# location: str = "La-cote-saint-andre"
# weather_year = 2022

# latitude_north_deg, longitude_east_deg = 45.216719, 5.577455
# location: str = "projet_vercors"
# weather_year = 2022

# location: str = 'Carqueiranne'
# weather_year = 2023
# latitude_north_deg, longitude_east_deg = 43.08933178200723, 6.072235955304281

# location: str = 'Saint-Julien-en-Saint-Alban'
# weather_year = 2023
# latitude_north_deg, longitude_east_deg = 44.71407488275519, 4.633318302898348

#########################################################################

if weather_file_name is None:
    weather_file_name = location

batem.core.library.properties.load('polystyrene2', 'thermal', 170)
batem.core.library.properties.load('straw', 'thermal', 261)


class MyConfiguration(batem.core.lambdahouse.LambdaParametricData):

    def __init__(self, location: str, latitude: float, longitude: float, weather_year: int, albedo: float = 0.1, pollution: float = 0.1) -> None:
        swd_builder = batem.core.weather.SWDbuilder(location, latitude, longitude)
        super().__init__(swd_builder, weather_year, albedo, pollution)


configuration: MyConfiguration = MyConfiguration(location=location, weather_year=weather_year, latitude=latitude_north_deg, longitude=longitude_east_deg)

on_screen = False
analysis: batem.core.lambdahouse.Analyzes = batem.core.lambdahouse.Analyzes(configuration, on_screen=on_screen)

print(configuration)
tstart: float = time.time()
analysis.climate()
analysis.evolution()
analysis.solar()
analysis.house()
analysis.neutrality()
analysis.close(pdf=True)
print(f'duration {round((time.time() - tstart)/60, 1)} min', file=sys.stderr)
