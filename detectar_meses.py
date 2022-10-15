
import sys

import numpy as np
import cv2 as cv

from Codigo import funciones


def ordenar_meses(rectangulos):
    """ Esta función ordena los rectangulos según la posicion del calendario,
        poniendo primero el mes de Enero, luego Febrero, Marzo, ...."""
    # Tomo el de menor y, que sería la primer fila de los meses de arriba del calendario.
    # Para después definir una franja (+y -y) en donde encontrar los meses de la misma fila..
    # El orden va de izquierda a derecha, asique de menor a mayor pos en x
    aprom = np.mean(rectangulos[:, 3], dtype=int)  # altura promedio de todos los meses

    pos_xy = rectangulos[:, 0:2]  # posicion x e y de cada bloque

    miny = min(pos_xy[:, 1])  # menor y
    franja = [miny + aprom * 0.1, miny - aprom * 0.1]  # +- 10%
    cond1 = np.logical_and(pos_xy[:, 1] > franja[1], pos_xy[:, 1] < franja[0])
    rectangulos_f1 = rectangulos[cond1]  # rectangulos de primer fila.. Enero, febrero, marzo, abril

    maxy = max(pos_xy[:, 1])  # mayor y
    franja = [maxy + aprom * 0.1, maxy - aprom * 0.1]  # +- 10%
    cond2 = np.logical_and(pos_xy[:, 1] > franja[1], pos_xy[:, 1] < franja[0])
    rectangulos_f3 = rectangulos[cond2]  # rect ultima fila.. sept, oct, nov, dic

    cond3 = np.logical_and(np.invert(cond1), np.invert(cond2))
    rectangulos_f2 = rectangulos[cond3]  # moyo, junio, julio, agosto

    ###### 6. Ordenar cada fila de menor a mayor para retornar cada mes en orden creciente
    # Primeros 4 meses
    pos_x = rectangulos_f1[:, 0]  # posiciones en x
    indx = np.argsort(pos_x)  # indices de menor a mayor
    rectangulos_f1 = rectangulos_f1[indx]  # ordenados por mes

    # Segundos 4 meses
    pos_x = rectangulos_f2[:, 0]  # posiciones en x
    indx = np.argsort(pos_x)  # indices de menor a mayor
    rectangulos_f2 = rectangulos_f2[indx]  # ordenados por mes

    # Terceros 4 meses
    pos_x = rectangulos_f3[:, 0]  # posiciones en x
    indx = np.argsort(pos_x)  # indices de menor a mayor
    rectangulos_f3 = rectangulos_f3[indx]  # ordenados por mes

    # juntar de nuevo en un mismo array
    rectangulos_ordenados = np.append(rectangulos_f1, rectangulos_f2, axis=0)
    rectangulos_ordenados = np.append(rectangulos_ordenados, rectangulos_f3, axis=0)
    return rectangulos_ordenados


def descartar_no_mes(img_bin, rectangulos):
    """ Retorna los rectangulos que no se descartan por las condiciones de relacion aspecto y area
        no_descartados es una lista donde cada elemento posee información de: x, y, w, h de cada uno de ellos """

    relacion_wh = np.maximum(rectangulos[:,2] / rectangulos[:,3] , rectangulos[:,3] / rectangulos[:,2]) # relacion-aspecto de cada bloque
    area = rectangulos[:,2] * rectangulos[:,3]  # area de cada bloque

    ### Comprobacion 1:  1 < relacion_aspecto < 1.4
    cond = np.logical_and(relacion_wh > 1, relacion_wh < 1.4)
    rectangulo1 = rectangulos[cond]  # se tiene los que pasaron primera condicion
    area = area[cond]

    # mostrar_detectados(img_bin, rectangulo1)
    rect_descartados1 = rectangulos[np.invert(cond)]  # los que se descartaron por cond 1

    ### Comprobación 2: aMin < area < aMax   ...   amax = a_total/12   ,   amin = 0.3 * amax
    rows, cols = img_bin.shape
    amax = rows * cols / 12  # se supone que no pueden entrar mas de 12 meses
    amin = amax * 0.3  # como mínimo deben ser el 30% del tamaño maximo
    cond = np.logical_and(area > amin, area < amax)
    # print('Descarte por area: ',cond)
    no_descartados = rectangulo1[cond]  # se tiene los que pasaron primera y segunda condicion

    # mostrar_detectados(img_bin, no_descartados)
    rect_descartados2 = rectangulo1[np.invert(cond)]  # los que se descartaron por cond 2

    # De todos los descartados que están dentro de alguno más grande y tengan mayor altura, modificar el más grande
    # con la altura del que está adentro, de esta manera se contempla las columnas que están adentro..
    # Este proceso consume cpu y demora, pero es un parche que surgió en el momento para solucionar este problema
    descartados = np.vstack((rect_descartados1, rect_descartados2))  # todos los que se descartaron
    for rect2 in descartados:  # por cada uno de los rectangulos descartados
        for i, rect1 in enumerate(no_descartados):  # por cada uno de los rectángulos no descartados
            x, y, w, h = rect1[:]
            nuevo_h = (rect2[1] + rect2[3]) - y
            if (x < rect2[0] + rect2[2] < x + w) and (y < rect2[1] < y + h) and ( nuevo_h > h):  # si la esquina está dentro del rectángulo no descartado
                no_descartados[i, 3] = nuevo_h  # modificarle la altura para que contemple la columna
    funciones.mostrar_detectados(img_bin, no_descartados)

    return no_descartados


def detectar_meses(img_cal):
    """
        Entradas:   1- Ruta del calendario retornado por el modulo de pre-procesamiento.
        Salidas:    1- Lista con los meses recortados en orden (enero, febrero, marzo,...)

        Restricciones:  el calendario no debe estar rotado
                        los meses deben estar dispuestos en tres filas por 4 columnas
                        Los calendarios deben ser similares a los 5 que se tiene en la carpeta calendarios

        Los parámetros para jugar son relacion-aspecto y en menor medida (xq anda muy bien), la ecuacion de área.
        Ambos dentro de la funcion: detectar_meses().
    """

    ancho = 2000    # mientras más grande, más nitida la imagen y menos probabilidad de fallar el algoritmo,
                    # pero se pone lento.... quedó 2000 xq es el que me anda, si lo queremos bajar, arreglar donde reviente

    #img = cv.imread(archivo)
    img_color = img_cal.copy() # ya llega redimensionada
    img_color = funciones.resize(img_cal, ancho)
    #img_color = funciones.resize(img, ancho)
    
    ###### restauro NUEVO !!!
    img_color = funciones.restaurar(img_color)


    ###### paso a escala de gris que es con la que voy a trabajar la mayor parte
    img = cv.cvtColor(img_color, cv.COLOR_BGR2GRAY)

    ###### 1. Binarizar la imagen del calendario recibida
    # _, img_bin = cv.threshold(img, 180, 255, cv.THRESH_BINARY_INV)  # 180 es un valor que se probó y anda bien para
    #                                                                 # eliminar las líneas claras del calendario
    #                                                                 # si se tiene más oscuras, pensar en otro preproceso
    _, img_bin = cv.threshold(img, 0, 255, cv.THRESH_BINARY_INV | cv.THRESH_OTSU)

    img_bin_copia = img_bin.copy()  # trabajar sobre una copia

    ###### 2. Operacion de apertura para unir los números y formar bloques
    # ¿Cuánto dilatar? Ir probando hasta encontrar los 12 meses, si no se encuentran, mal tomado el calendario o
    # revisar las condiciones de descarte de bloques: relacion-aspecto y área
    se_encontraron = False
    cant_dilat = 1
    rectangulos_meses = []    # lista donde se irán guardando los rectángulos que rodean a los meses/bloques
    while not se_encontraron:
        kn = cv.getStructuringElement(cv.MORPH_CROSS, (5, 5))
        img_bin_copia = cv.dilate(img_bin_copia, kn, iterations=1)
        # cv.imshow('dilatada', img_bin)
        # cv.waitKey()

        ###### 3. Detectar los bloques formados
        bloques = funciones.detectar_bloques(img_bin_copia)

        ###### 4. Descartar los bloques/rectángulos que no son mes de acuerdo a su relacion_aspecto y tamaño
        rectangulos_meses = descartar_no_mes(img_bin_copia, bloques)

        if len(rectangulos_meses) == 12: # si se encontraron los 12 meses
            se_encontraron = True
        if len(rectangulos_meses) < 12 and len(bloques) < 12:
            print('No se pudieron detectar los meses, usar otro calendario o ajustar algún parámetro de descarte')
            sys.exit(1)

        cant_dilat += 1

    ###### 5. Ordenar los rectángulos segun posicion, de esquina superior izquierda a inferior derecha
    rectangulos_ordenados = ordenar_meses(rectangulos_meses)

    ###### 7. Recortar los meses del calendario
    meses_recortados = [] # lista de imagenes de los meses
    for indx, rect in enumerate(rectangulos_ordenados):
        area_crop = img_color[rect[1]:rect[1]+rect[3], rect[0]:rect[0]+rect[2]]
        meses_recortados.append(area_crop)
        # cv.imshow('mes',area_crop)
        # cv.waitKey()

    return meses_recortados


def main():
    pass


if __name__ == '__main__':

    main()


