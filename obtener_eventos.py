
import cv2 as cv
import numpy as np
from Codigo import funciones


def segmentar(img_color, hsv_color):
    img_color = cv.cvtColor(img_color, cv.COLOR_BGR2HSV)
    hsv_bajo = hsv_color[0]
    hsv_alto = hsv_color[1]
    mask = cv.inRange(img_color, hsv_bajo, hsv_alto)
    return mask


def detectar_dias_del_evento(mask_marca, mat_con_dias, pos_cols, pos_filas):
    dias_evento = []
    # recorro cada posicion guardada
    for fila, p_fila in enumerate(pos_filas):
        for col, p_col in enumerate(pos_cols):
            # si esa posicion y un entorno alrededor cae dentro de la marca, guardo el día
            # if mask_marca[p_fila, p_col] == 255: # guardar este día
            if np.any(mask_marca[p_fila - 15: p_fila + 15, p_col - 15: p_col + 15] == 255):  # guardar este día
                dia = mat_con_dias[fila, col]
                dias_evento.append(dia)
    return dias_evento


def obtener_eventos(mat_con_dias, pos_cols, pos_filas, img_mes_color_sin_tit, mes):

    ###### 1. Definir los umbrales hsv de cada uno de los colores para segmentar
    colores = []        # lista donde se guardarán los ditintos colores/eventos
    hsv_colores = []    # lista donde se guardarán los umbrales hsv de cada color
    # para segmentar amarillo
    colores.append('amarillo')
    hsv_bajo = (26, 70, 0)      # umbral bajo hsv
    hsv_alto = (40, 255, 255)   # umbral alto hsv
    hsv_amarillo = [hsv_bajo, hsv_alto]
    # para segmentar celeste
    colores.append('celeste')
    hsv_bajo = (85, 40, 50)
    hsv_alto = (100, 255, 255)
    hsv_celeste = [hsv_bajo, hsv_alto]
    # para segmentar fucsia
    colores.append('fucsia')
    hsv_bajo = (128, 38, 50)
    hsv_alto = (150, 255, 255)
    hsv_fucsia = [hsv_bajo, hsv_alto]
    # agregar todos a la lista hsv_colores
    hsv_colores.append(hsv_amarillo)
    hsv_colores.append(hsv_celeste)
    hsv_colores.append(hsv_fucsia)

    ###### 2. Por cada uno de los colores segmentar para obtener las marcas, y luego registrar los eventos
    eventos = []  # lista de cada evento, donde cada uno posee columnas de: [nro_mes, tipo_evento, dias]
    for color, hsv_color in zip(colores, hsv_colores):

        ###### Segmentar color segun hsv
        mask = segmentar(img_mes_color_sin_tit, hsv_color)
        # cv.imshow('img_mes_color_sin_tit',img_mes_color_sin_tit)
        # cv.imshow('mask', mask)

        # eliminar algunas impuresas de la segmentacion, haciendo operacion de cierre de apertura
        mask = funciones.filtro_mediana(mask, 9)

        # unificar puntos de una misma mascara
        kn = cv.getStructuringElement(cv.MORPH_RECT, (5, 5))
        mask = cv.dilate(mask, kn, iterations=6)
        # kn = cv.getStructuringElement(cv.MORPH_RECT, (3, 3))
        mask = cv.erode(mask, kn, iterations=6)
        # cv.imshow('mask limpia', mask)

        ###### Cada marca que aparece en la mascara, es un evento distinto pero del mismo tipo.
        # Fijarse qué dias corresponden a cada marca/evento

        # Detectar las posiciones de las marcas/eventos
        marcas = funciones.detectar_bloques(mask)

        # Por cada marca, hacer negro el resto de la imagen y analizar sobre qué dias esta dicha marca
        for marca in marcas:
            # donde no está la marca, hacer cero, así analizamos marca por marca
            mask_marca = np.zeros_like(mask)
            x, y, w, h = marca
            mask_marca[y:y + h, x:x + w] = mask[y:y + h, x:x + w]

            dias_evento = detectar_dias_del_evento(mask_marca, mat_con_dias, pos_cols, pos_filas)
            eventos.append([mes, color, dias_evento])
        # cv.waitKey()

    return eventos


def main():
    pass


if __name__ == '__main__':
    main()

