"""Script que ejecuta el proceso completo de extraccion y exportacion de vuelos de Despegar.
"""

import time
from datetime import datetime
from despegar.scraper import Despegar
from bcrp.utilidades import obtener_logger

# Logs
logger = obtener_logger('IAE170_2150_DespegarOnpremise')

# Parametros
# destinos = ['IQT','CUN']
destinos = ['MAD', 'BCN', 'SCL', 'BUE', 'MIA', 'BOG', 'CTG', 'MEX', 'PUJ', 'CUN', 'CUZ', 'JUL', 'CJA', 'TBP', 'TRU',
            'AQP', 'PEM', 'PIU', 'CIX', 'IQT']


def main():
    # Extraccion de vuelos
    inicio = time.time()
    scraper = Despegar(destinos)
    scraper.extraer_data()
    scraper.extraer_data_perdida()
    fecha = (datetime.now()).strftime('%Y-%m-%d')
    scraper.guardar_archivo(fecha)
    fin = time.time()
    print('Tiempo de ejecucion: ' + str(round((fin - inicio) / 3600, 2)))


if __name__ == '__main__':
    main()
