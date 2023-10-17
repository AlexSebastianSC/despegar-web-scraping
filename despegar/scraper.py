import concurrent.futures
import json
import logging
import pandas as pd
from datetime import date, datetime, timedelta
from random import randint
from time import sleep, perf_counter
from seleniumwire import webdriver
from seleniumwire.utils import decode
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException, TimeoutException, WebDriverException, \
    ElementClickInterceptedException
from selenium.common.exceptions import ElementNotInteractableException
from bcrp.utilidades import obtener_driver, obtener_fecha_uid

# Logs
logger = logging.getLogger('IAE170_2150_DespegarOnpremise')


class Despegar:

    def __init__(self, destinos):
        self.destinos = destinos
        self.totales = 0
        self.missing_links = []
        self.vuelos = {
            "Fecha Extraccion": [],
            "Fecha Vuelo": [],
            "Origen": [],
            "Destino": [],
            "Duracion de viaje": [],
            "Escalas": [],
            "Mochila o cartera": [],
            "Equipaje de mano": [],
            "Equipaje para documentar": [],
            "Precio": [],
            "Impuesto": [],
            "Precio Final": [],
            "Aeropuerto de salida": [],
            "Aeropuerto de destino": [],
            "Aerolinea 1": [],
            "ID de vuelo 1": [],
            "Modelo avion 1": [],
            "Hora de salida 1": [],
            "Lugar de salida 1": [],
            "Aeropuerto de salida 1": [],
            "Duracion de vuelo hacia escala 1": [],
            "Hora de llegada a la escala 1": [],
            "Aeropuerto de llegada 1": [],
            "Lugar de llegada tramo 1": [],  # cancelacion
            # "Cancelacion 1":[],
            # "Costo cancelacion 1":[],
            # "Cambios 1":[],
            # "Costo cambios 1":[],

            "Aerolinea 2": [],
            "ID de vuelo 2": [],
            "Modelo avion 2": [],
            "Hora de salida 2": [],
            "Lugar de salida 2": [],
            "Aeropuerto de salida 2": [],
            "Duracion de vuelo hacia escala 2": [],
            "Hora de llegada a la escala 2": [],
            "Aeropuerto de llegada 2": [],
            "Lugar de llegada tramo 2": [],  # escala 2
            # "Cancelacion 2":[],
            # "Costo cancelacion 2":[],
            # "Cambios 2":[],
            # "Costo cambios 2":[],

            "Aerolinea 3": [],
            "ID de vuelo 3": [],
            "Modelo avion 3": [],
            "Hora de salida 3": [],
            "Lugar de salida 3": [],
            "Aeropuerto de salida 3": [],
            "Duracion de vuelo hacia escala 3": [],
            "Hora de llegada a la escala 3": [],
            "Aeropuerto de llegada 3": [],
            "Lugar de llegada tramo 3": []
        }

    def generar_links(self):
        urls = []
        dias = [(datetime.now() + timedelta(i)).strftime('%Y-%m-%d') for i in range(1, 31)]  # 1-31
        for destino in self.destinos:
            for dia in dias:
                url = 'https://www.despegar.com.pe/shop/flights/results/oneway/LIM/' + destino + '/' + dia + '/1/0/0/NA/NA/NA/NA?from=SB&di=1-0#showModal'
                urls.append(url)
        return urls

    def obtener_datos(self, url):
        logger.info(url)

        try:
            aux = self.vuelos
            driver = obtener_driver(wire=True)
            wait = WebDriverWait(driver, 10)
            dia = url[64:74]
            driver.get(url)
            sleep(3)
            # driver.save_screenshot(f'screenshots/inicio_{obtener_fecha_uid()}.png')
        except Exception as err:
            logger.info(err)

        items_totales = []
        data_referencial = {
            'aircrafts': {},
            'airlines': {},
            'airports': {},
            'cities': {},
            'citiesCodeByAirport': {}
        }

        try:
            # driver.maximize_window()
            cookies = wait.until(ec.presence_of_element_located((By.XPATH, "//em[contains( text(),'Entendí')]")))
            cookies.click()
            wait.until(ec.element_to_be_clickable((By.XPATH, '(//*[@class="modal-header login-aggressive--header"])')))

            try:
                popup = driver.find_element(By.XPATH, '(//*[@class="modal-header login-aggressive--header"])/i')
                popup.click()
            except Exception as err:
                popups = driver.find_elements(By.XPATH,'(//*[@class="login-aggressive--button login-aggressive--button-close shifu-3-btn-ghost"])')
                for popup in popups:
                    popup.click()
                    sleep(0.5)
                # no quiero beneficios!!!!!!!!!!!!!!
                close_buttons = driver.find_elements(By.XPATH, "//em[contains( text(),'No quiero beneficios')]")
                for close_button in close_buttons:
                    close_button.click()
                    sleep(0.5)
                sleep(2)
        except (ElementNotInteractableException, TimeoutException, WebDriverException) as err:
            try:
                wait.until(ec.presence_of_element_located((By.XPATH, "//em[contains( text(),'Comprar')]")))
            except TimeoutException:
                logger.info('Esta demorando en cargar mas de 20 seg')
                sleep(10)
                pass
        except Exception as err:
            pass


        finding_click = False
        reached_page_end = False
        today = date.today()

        # vuelos = self.crear_diccionario()

        new_height = driver.get_window_size()['height']

        # driver.save_screenshot(f'screenshots/scraping_{obtener_fecha_uid()}.png')

        try:
            while finding_click is False:
                try:
                    ec.element_to_be_clickable(
                        (By.XPATH, "//em[contains(@class,'btn-text') and .//text()='Ver más vuelos']"))
                    boton = driver.find_element(
                        By.XPATH, "//em[contains(@class,'btn-text') and .//text()='Ver más vuelos']")
                    boton.click()
                    sleep(2)

                except NoSuchElementException or ElementClickInterceptedException:
                    driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.PAGE_DOWN)
                    sleep(randint(2, 3))  # 2-3

                try:
                    driver.execute_script(
                        "document.querySelector('modal-header login-aggresive--header',':before').click();")
                except Exception:
                    pass

                page_height = driver.execute_script("return document.body.scrollHeight")
                total_scrolled_height = driver.execute_script("return window.pageYOffset + window.innerHeight")

                if (page_height - 1) <= total_scrolled_height:
                    # print("pass")
                    break
                else:
                    pass
                    # print("Bajando")

            try:
                req = driver.requests
                # print(len(req))
                for request in req:
                    if request.response:
                        if 'search?' in request.url:
                            body = decode(request.response.body,
                                          request.response.headers.get('Content-Encoding', 'identity'))
                            decoded_body = body.decode('utf-8')
                            try:
                                json_data = json.loads(decoded_body)
                                items = json_data['items']

                                # print(len(items))
                                # print('OK')
                                for i in range(0, len(items)):
                                    items_totales.append(items[i])

                                reference_data = json_data['referenceData']
                                # print(reference_data) print('--------------------') data_referencial['aircrafts'] =
                                # data_referencial['aircrafts'] | reference_data['aircrafts']
                                data_referencial['aircrafts'].update(reference_data['aircrafts'])
                                data_referencial['airlines'].update(reference_data['airlines'])
                                data_referencial['airports'].update(reference_data['airports'])
                                data_referencial['cities'].update(reference_data['cities'])
                                data_referencial['citiesCodeByAirport'].update(reference_data['citiesCodeByAirport'])

                            # except json.decoder.JSONDecodeError:
                            #    print('Error en el decode json')
                            except Exception as err:
                                try:
                                    data_referencial['airlines'].update(reference_data['airlines'])
                                    data_referencial['airports'].update(reference_data['airports'])
                                    data_referencial['cities'].update(reference_data['cities'])
                                    data_referencial['citiesCodeByAirport'].update(
                                        reference_data['citiesCodeByAirport'])
                                except Exception as err:
                                    logger.info('Error al armar diccionario de campos 1')
                                    logger.info(err)
                                    self.missing_links.append(url)
                                    logger.info(f'Fecha perdida: {dia}')
                                    logger.info(f'URL perdido: {url}')
                                    return
            except Exception as err:
                logger.info('Error al decodificar')
                logger.info(err)
                self.missing_links.append(url)
                logger.info(f'Fecha perdida: {dia}')
                logger.info(f'URL perdido: {url}')
                return

        except Exception as err:
            try:
                actualizar = driver.find_element(By.XPATH, '//div[@class="error-session-expired -eva-3-"]/div[4]/div')
                if actualizar:
                    actualizar.click()
            except Exception:
                pass

        # cerrar navegador
        # driver.save_screenshot(f'screenshots/fin_{obtener_fecha_uid()}.png')
        driver.quit()

        # print('Cantidad de items: '+str(len(items_totales))+' ################')
        # print(data_referencial['aircrafts'])

        hoy = str(date.today())
        contador = 0

        for item in items_totales:
            if item['itemType'] == 'BIG_CLUSTER':
                rutas = item['item']['routeChoices'][0]['routes']
                for ruta in rutas:
                    self.vuelos['Fecha Extraccion'].append(hoy)
                    self.vuelos['Fecha Vuelo'].append(dia)

                    try:
                        self.vuelos['Precio'].append(item['item']['priceDetail']['items'][0]['amount'])
                        # print(item['item']['priceDetail']['items'][0]['amount'])
                        self.vuelos['Impuesto'].append(item['item']['priceDetail']['items'][1]['amount'])
                        # print(item['item']['priceDetail']['items'][1]['amount'])
                        self.vuelos['Precio Final'].append(item['item']['priceDetail']['totalFare']['amount'])
                        # print(self.vuelos['Precio Final'][-1])
                    except Exception:
                        self.vuelos['Precio'].append(item['item']['priceDetail']['mainFare']['amount'])
                        # print(self.vuelos['Precio'][-1])
                        self.vuelos['Impuesto'].append(0)
                        # print(self.vuelos['Impuesto'][-1])
                        self.vuelos['Precio Final'].append(item['item']['priceDetail']['mainFare']['amount'])
                        # print(self.vuelos['Precio Final'][-1])

                    self.vuelos['Origen'].append(data_referencial['cities'][data_referencial['citiesCodeByAirport'][
                        ruta['departure']['airportCode']]])  # Partida y aeropuerto
                    # print(data_referencial['cities'][data_referencial['citiesCodeByAirport'][ruta['departure']['airportCode']]])
                    destino = data_referencial['cities'][
                        data_referencial['citiesCodeByAirport'][ruta['arrival']['airportCode']]]
                    self.vuelos['Destino'].append(destino)  # Destino y aeropuerto
                    # print(data_referencial['cities'][data_referencial['citiesCodeByAirport'][ruta['arrival']['airportCode']]])
                    self.vuelos['Aeropuerto de salida'].append(
                        data_referencial['airports'][ruta['departure']['airportCode']])  # Partida y aeropuerto
                    # print(data_referencial['airports'][ruta['departure']['airportCode']])
                    self.vuelos['Aeropuerto de destino'].append(
                        data_referencial['airports'][ruta['arrival']['airportCode']])  # Destino y aeropuerto
                    # print(data_referencial['airports'][ruta['arrival']['airportCode']])

                    self.vuelos['Duracion de viaje'].append(ruta['totalDuration'])  # duracion vuelo
                    # ruta['departure']['date'] #fecha y hora de partida----
                    # ruta['arrival']['date'] #fecha y hora de llegada----
                    self.vuelos['Escalas'].append(ruta['stopsCount'])  # escalas

                    if 'NOT_INCLUDED' in ruta['baggageInfo']['backpackType']:
                        self.vuelos['Mochila o cartera'].append('FALSE')
                    else:
                        self.vuelos['Mochila o cartera'].append('TRUE')  # mochila

                    if 'NOT_INCLUDED' in ruta['baggageInfo']['carryonType']:
                        self.vuelos['Equipaje de mano'].append('FALSE')
                    else:
                        self.vuelos['Equipaje de mano'].append('TRUE')  # maleta

                    if 'NOT_INCLUDED' in ruta['baggageInfo']['baggageInfoType']:
                        self.vuelos['Equipaje para documentar'].append('FALSE')
                    else:
                        self.vuelos['Equipaje para documentar'].append('TRUE')  # equipaje

                    try:
                        self.vuelos['Aerolinea 1'].append(
                            data_referencial['airlines'][ruta['segments'][0]['airlineCode']])
                        self.vuelos['ID de vuelo 1'].append(ruta['segments'][0]['flightId'])  # idVuelo
                        try:
                            self.vuelos['Modelo avion 1'].append(
                                data_referencial['aircrafts'][ruta['segments'][0]['equipmentCode']][
                                    'manufacturer'] + ' ' +
                                data_referencial['aircrafts'][ruta['segments'][0]['equipmentCode']][
                                    'model'])  # manufaturer - airbus
                            # print(data_referencial['aircrafts'][ruta['segments'][0]['equipmentCode']][
                            # 'manufacturer']+' '+data_referencial['aircrafts'][ruta['segments'][0][
                            # 'equipmentCode']]['model'])
                        except Exception:
                            self.vuelos['Modelo avion 1'].append('n.d.')  # manufaturer - airbus
                            # print(self.vuelos['Modelo avion 1'][-1])

                        hora_salida_1 = ruta['segments'][0]['departure']['date']
                        self.vuelos['Hora de salida 1'].append(hora_salida_1[11:])  # fecha y hora de partida----

                        self.vuelos['Lugar de salida 1'].append(data_referencial['cities'][
                                                                    data_referencial['citiesCodeByAirport'][
                                                                        ruta['segments'][0]['departure'][
                                                                            'airportCode']]])
                        self.vuelos['Aeropuerto de salida 1'].append(
                            data_referencial['airports'][ruta['segments'][0]['departure']['airportCode']])
                        self.vuelos['Duracion de vuelo hacia escala 1'].append(
                            ruta['segments'][0]['duration'])  # duracion vuelo
                        hora_llegada_1 = ruta['segments'][0]['arrival']['date']
                        self.vuelos['Hora de llegada a la escala 1'].append(hora_llegada_1[11:])
                        self.vuelos['Aeropuerto de llegada 1'].append(
                            data_referencial['airports'][ruta['segments'][0]['arrival']['airportCode']])
                        self.vuelos['Lugar de llegada tramo 1'].append(data_referencial['cities'][
                                                                           data_referencial['citiesCodeByAirport'][
                                                                               ruta['segments'][0]['arrival'][
                                                                                   'airportCode']]])
                    except Exception as err:
                        logger.info('Primer tramos del pueblo errado')
                        logger.info(f"Unexpected {err=}, {type(err)=}")
                        # self.missing_links.append(url)
                        # print(f'Fecha perdida: {dia}')
                        # print(f'Destino perdido: {destino}')

                    # raise

                    try:
                        self.vuelos['Aerolinea 2'].append(
                            data_referencial['airlines'][ruta['segments'][1]['airlineCode']])
                        self.vuelos['ID de vuelo 2'].append(ruta['segments'][1]['flightId'])  # idVuelo

                        try:
                            self.vuelos['Modelo avion 2'].append(
                                data_referencial['aircrafts'][ruta['segments'][1]['equipmentCode']][
                                    'manufacturer'] + ' ' +
                                data_referencial['aircrafts'][ruta['segments'][1]['equipmentCode']][
                                    'model'])  # manufaturer - airbus
                            # print(data_referencial['aircrafts'][ruta['segments'][1]['equipmentCode']][
                            # 'manufacturer']+' '+data_referencial['aircrafts'][ruta['segments'][1][
                            # 'equipmentCode']]['model'])
                        except Exception:
                            self.vuelos['Modelo avion 2'].append('n.d.')  # manufaturer - airbus
                            # print(self.vuelos['Modelo avion 2'][-1])

                        hora_salida_2 = ruta['segments'][1]['departure']['date']
                        self.vuelos['Hora de salida 2'].append(hora_salida_2[11:])  # fecha y hora de partida----
                        self.vuelos['Lugar de salida 2'].append(data_referencial['cities'][
                                                                    data_referencial['citiesCodeByAirport'][
                                                                        ruta['segments'][1]['departure'][
                                                                            'airportCode']]])
                        self.vuelos['Aeropuerto de salida 2'].append(
                            data_referencial['airports'][ruta['segments'][1]['departure']['airportCode']])
                        self.vuelos['Duracion de vuelo hacia escala 2'].append(
                            ruta['segments'][1]['duration'])  # duracion vuelo
                        hora_llegada_2 = ruta['segments'][1]['arrival']['date']
                        self.vuelos['Hora de llegada a la escala 2'].append(hora_llegada_2[11:])
                        self.vuelos['Aeropuerto de llegada 2'].append(
                            data_referencial['airports'][ruta['segments'][1]['arrival']['airportCode']])
                        self.vuelos['Lugar de llegada tramo 2'].append(data_referencial['cities'][
                                                                           data_referencial['citiesCodeByAirport'][
                                                                               ruta['segments'][1]['arrival'][
                                                                                   'airportCode']]])
                    except Exception:
                        self.vuelos['Aerolinea 2'].append('n.d.')
                        self.vuelos['ID de vuelo 2'].append('n.d.')
                        self.vuelos['Modelo avion 2'].append('n.d.')
                        self.vuelos['Hora de salida 2'].append('n.d.')
                        self.vuelos['Lugar de salida 2'].append('n.d.')
                        self.vuelos['Aeropuerto de salida 2'].append('n.d.')
                        self.vuelos['Duracion de vuelo hacia escala 2'].append('n.d.')
                        self.vuelos['Hora de llegada a la escala 2'].append('n.d.')
                        self.vuelos['Aeropuerto de llegada 2'].append('n.d.')
                        self.vuelos['Lugar de llegada tramo 2'].append('n.d.')

                    try:
                        self.vuelos['Aerolinea 3'].append(
                            data_referencial['airlines'][ruta['segments'][2]['airlineCode']])
                        self.vuelos['ID de vuelo 3'].append(ruta['segments'][2]['flightId'])  # idVuelo

                        try:
                            self.vuelos['Modelo avion 3'].append(
                                data_referencial['aircrafts'][ruta['segments'][2]['equipmentCode']][
                                    'manufacturer'] + ' ' +
                                data_referencial['aircrafts'][ruta['segments'][2]['equipmentCode']][
                                    'model'])  # manufaturer - airbus
                            # print(data_referencial['aircrafts'][ruta['segments'][2]['equipmentCode']][
                            # 'manufacturer']+' '+data_referencial['aircrafts'][ruta['segments'][2][
                            # 'equipmentCode']]['model'])
                        except Exception:
                            self.vuelos['Modelo avion 3'].append('n.d.')  # manufaturer - airbus
                            # print(self.vuelos['Modelo avion 3'][-1])

                        hora_salida_3 = ruta['segments'][2]['departure']['date']
                        self.vuelos['Hora de salida 3'].append(hora_salida_3[11:])  # fecha y hora de partida----
                        self.vuelos['Lugar de salida 3'].append(data_referencial['cities'][
                                                                    data_referencial['citiesCodeByAirport'][
                                                                        ruta['segments'][2]['departure'][
                                                                            'airportCode']]])
                        self.vuelos['Aeropuerto de salida 3'].append(
                            data_referencial['airports'][ruta['segments'][2]['departure']['airportCode']])
                        self.vuelos['Duracion de vuelo hacia escala 3'].append(
                            ruta['segments'][2]['duration'])  # duracion vuelo
                        hora_llegada_3 = ruta['segments'][2]['arrival']['date']
                        self.vuelos['Hora de llegada a la escala 3'].append(hora_llegada_3[11:])
                        self.vuelos['Aeropuerto de llegada 3'].append(
                            data_referencial['airports'][ruta['segments'][2]['arrival']['airportCode']])
                        self.vuelos['Lugar de llegada tramo 3'].append(data_referencial['cities'][
                                                                           data_referencial['citiesCodeByAirport'][
                                                                               ruta['segments'][2]['arrival'][
                                                                                   'airportCode']]])
                    except Exception:
                        self.vuelos['Aerolinea 3'].append('n.d.')
                        self.vuelos['ID de vuelo 3'].append('n.d.')
                        self.vuelos['Modelo avion 3'].append('n.d.')
                        self.vuelos['Hora de salida 3'].append('n.d.')
                        self.vuelos['Lugar de salida 3'].append('n.d.')
                        self.vuelos['Aeropuerto de salida 3'].append('n.d.')
                        self.vuelos['Duracion de vuelo hacia escala 3'].append('n.d.')
                        self.vuelos['Hora de llegada a la escala 3'].append('n.d.')
                        self.vuelos['Aeropuerto de llegada 3'].append('n.d.')
                        self.vuelos['Lugar de llegada tramo 3'].append('n.d.')

                    # print('******************')
                    contador += 1
            else:
                pass

        estado = self.validar_data(self.vuelos)
        self.totales += contador

        if self.totales == aux:
            self.missing_links.append(url)
            logger.info(f'Fecha perdida: {dia}')
            logger.info(f'Destino perdido: {destino}')
        else:
            if estado:
                logger.info(f'Fecha de vuelo: {dia}')
                logger.info(f'Destino: {destino}')
                logger.info(f'Cantidad de vuelos: {contador}')
                logger.info('Completo.')
                logger.info('------------------------------------')
            else:
                self.missing_links.append(url)
                self.vuelos = aux
                logger.info(f'Fecha perdida: {dia}')
                logger.info(f'Destino perdido: {destino}')
        return
        # return self.vuelos

    def validar_data(self, dic):
        length_dict = {key: len(value) for key, value in dic.items()}
        # print(length_dict)
        # Flag to check if all elements are same
        res = True
        # extracting value to compare
        test_val = list(length_dict.values())[0]
        # print(test_val)
        for ele in length_dict:
            # print(length_dict[ele])
            # print('------------')
            if length_dict[ele] != test_val:
                logger.info(test_val)
                logger.info(length_dict[ele])
                logger.info('------------')
                indic = max(int(length_dict[ele]), int(test_val))
                res = False
                break
        return res

    def extraer_data_perdida(self):
        urls = self.missing_links
        self.missing_links = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=6) as executor:
            executor.map(self.obtener_datos, urls)
            # executor.shutdown()
        # return self.vuelos

    def extraer_data(self):
        urls = self.generar_links()
        logger.info(f'URLS: {len(urls)}')
        start_time = perf_counter()

        with concurrent.futures.ThreadPoolExecutor(max_workers=6) as executor:
            executor.map(self.obtener_datos, urls)
            # executor.shutdown()

        end_time = perf_counter()

        # return self.vuelos
        logger.info(f'It took {end_time - start_time: 0.2f} second(s) to complete.')

    def limpiar_data(self):
        dataframe = pd.DataFrame.from_dict(self.vuelos)

        df0 = dataframe[dataframe['Precio'] != 'undefined']
        df1 = df0[df0['Precio Final'] != 'undefined']
        df2 = df1[(df1['Destino'] == 'Barcelona') | (df1['Destino'] == 'Bogotá') |
                  (df1['Destino'] == 'Buenos Aires') | (df1['Destino'] == 'Cancún') |
                  (df1['Destino'] == 'Cartagena de Indias') | (df1['Destino'] == 'Ciudad de México') |
                  (df1['Destino'] == 'Madrid') | (df1['Destino'] == 'Miami') |
                  (df1['Destino'] == 'Punta Cana') | (df1['Destino'] == 'Santiago de Chile') |
                  (df1['Destino'] == 'Cusco') | (df1['Destino'] == 'Juliaca') |
                  (df1['Destino'] == 'Cajamarca') | (df1['Destino'] == 'Tumbes') |
                  (df1['Destino'] == 'Trujillo') | (df1['Destino'] == 'Arequipa') |
                  (df1['Destino'] == 'Puerto Maldonado') | (df1['Destino'] == 'Piura') |
                  (df1['Destino'] == 'Iquitos') | (df1['Destino'] == 'Chiclayo')]
        df2.reset_index(drop=True, inplace=True)

        return df2

    def guardar_archivo(self, fecha):
        dataframe = self.limpiar_data()
        logger.info(dataframe)

        try:
            # leer data principal
            data = pd.read_csv("data/Vuelos_completos.csv", sep=';')
            # display(data)
            # display(dataframe)
            logger.info('Despues de combinar:')
            data_final = pd.concat([data, dataframe], axis=0)
            data_final.to_csv('data/Vuelos_completos.csv', index=False, sep=';', encoding="utf-8-sig")
            # sobreescribir data principal dataframe.to_csv('Vuelos_completos_internacionales'+fecha+'.csv',
            # index=False, sep=';',encoding="utf-8-sig")
        except Exception as err:
            logger.info(f"Unexpected {err=}, {type(err)=}")
            # crear data principal
            # dataframe.to_csv('Vuelos_completos.csv',index=False, sep=';',encoding="utf-8-sig")
            dataframe.to_csv('data/Vuelos_completos_' + fecha + '.csv', index=False, sep=';', encoding="utf-8-sig")
            logger.info(self.missing_links)

        logger.info('....Listo!' + fecha)

    # def estadisticas_financieras(self):

    # def limpiar_escalas_nacionales(self):

    # def no_se_que_mas_poner_para_impresionar(self):

    # def jajaja(self):
