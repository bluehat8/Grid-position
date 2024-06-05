import requests
import math
import sys
import json
import warnings

def haversine(lat1, lon1, lat2, lon2):
    R = 6371  # Radio de la Tierra en km
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)
    a = math.sin(delta_phi / 2)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    distance = R * c
    return distance

def generar_cuadricula(lat_central, lon_central, incremento_lat, incremento_lon, tamano=5):
    medio = tamano // 2
    for i in range(-medio, medio + 1):
        for j in range(-medio, medio + 1):
            yield (lat_central + (i * incremento_lat), lon_central + (j * incremento_lon))

def buscar_negocio(lat_central, lon_central, busqueda_maps, api_key):
    incremento_lat = 0.0158
    incremento_lon = 0.0206
    puntos = generar_cuadricula(lat_central, lon_central, incremento_lat, incremento_lon, tamano=5)
    negocios = {}
    negocios_trasnformados = []

    for lat, lon in puntos:
        if len(negocios) >= 23:  # Verifica si ya se han encontrado 21 negocios únicos
            break
        url_base = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
        parametros = {
            "key": api_key,
            "location": f"{lat},{lon}",
            "radius": 12000,  # Ajuste para la búsqueda
            "keyword": busqueda_maps
        }
        response = requests.get(url_base, params=parametros)
        if response.status_code == 200:
            resultados = response.json()
            for index, lugar in enumerate(resultados["results"], start=1):
                nombre = lugar['name']
                nombre_corto = nombre[:20]
                if nombre_corto not in negocios:
                    negocios[nombre_corto] = {'posiciones': [], 'reseñas': lugar.get('user_ratings_total', 0),
                                                'valoración': lugar.get('rating', 'N/A'),
                                                'categoría': lugar['types'][0] if lugar['types'] else 'N/A',
                                                'lat_lng': [], 'distancias': [], 'direccion': lugar.get('vicinity', 'No disponible')}
                negocios[nombre_corto]['posiciones'].append(index)
                negocios[nombre_corto]['lat_lng'].append((lugar['geometry']['location']['lat'], lugar['geometry']['location']['lng']))
                negocios[nombre_corto]['distancias'].append(haversine(lat_central, lon_central, lugar['geometry']['location']['lat'], lugar['geometry']['location']['lng']))
        else:
            print("Error en la solicitud a la API.")

    # Ordenar negocios por posición media y calcular latitud, longitud promedio y distancia media
    negocios_ordenados = sorted(negocios.items(), key=lambda x: sum(x[1]['posiciones']) / len(x[1]['posiciones']))

    # print("Nombre del Negocio | Posición Media | Veces Listado | Reseñas | Valoración | Categoría | Distancia Media (km) | Latitud y Longitud Promedio")
    # print("-" * 160)
    for nombre, info in negocios_ordenados:
        posicion_media = sum(info['posiciones']) / len(info['posiciones']) if info['posiciones'] else 'N/A'
        distancia_media = sum(info['distancias']) / len(info['distancias']) if info['distancias'] else 0
        lat_prom, lng_prom = tuple(sum(coords) / len(coords) for coords in zip(*info['lat_lng'])) if info[
            'lat_lng'] else ('N/A', 'N/A')
        # print(
        #     f"{nombre:<20} | {posicion_media:<14.2f} | {len(info['posiciones']):<12} | {info['reseñas']:<7} | {info['valoración']:<10} | {info['categoría']:<15} | {distancia_media:<20.2f} | ({lat_prom:.4f}, {lng_prom:.4f})")
        negocios_trasnformados.append({
                        "rango": f"{posicion_media:.2f}",
                        "nombre": nombre,
                        "direccion": info['direccion'],
                        "latitud": lat_prom,
                        "longitud": lng_prom
                    })
    return negocios_trasnformados



if __name__ == "__main__":
    lat_central = float(sys.argv[1])
    lon_central = float(sys.argv[2])
    busqueda_maps = sys.argv[3]
    api_key = sys.argv[4]

    # Captura de advertencias y ejecución del script
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        resultados = buscar_negocio(lat_central, lon_central, busqueda_maps, api_key)
    
    # Imprime los resultados

    print(json.dumps(resultados, ensure_ascii=False));
