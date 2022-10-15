import calendar


import numpy as np
import cv2 as cv
from calendar import monthrange
import datetime
import pytesseract

from Codigo import inicializar, funciones


def recortar_días_de_la_semana(img_bin):
    ###### Recortar días de la semana: lu, ma, mi, ju, vi, sa, do
    # Para lograr esto, se recorre desde arriba de la imagen (desde fila 0) y se mira todas las columnas de dicha fila
    # si no hay nada es xq no empezó el calendario, si encuentra algo es xq comienzan a aparecer los días lu, ma, ....
    ya_inicio = False  # bandera que indica que empezaron a aparecer las letras: lu, ma, ...
    ya_termino = False  # bandera que indica que terminaron
    fila = 0  # variable usada para iterar
    fila_inicio = 0  # fila donde comienzan las letras
    fila_fin = 0  # fila donde terminan las letras
    while not ya_termino:
        todos_ceros = np.all(img_bin[fila, :] == 0)  # si todos son iguales a cero
        if not todos_ceros and not ya_inicio:
            ya_inicio = True
            fila_inicio = fila
        if todos_ceros and ya_inicio:
            ya_termino = True
            fila_fin = fila
        fila += 1

    img_letras = img_bin[fila_inicio - 1: fila_fin + 1, :]  # imagen alargada: lu, ma, mi, ju, vi, sa, do
    return img_letras


def calendario_lu_o_dom(img_bin):
    """ Esta función actualiza la variable global inicializar.lunes_o_domingo con
        el día (lunes o domingo) en que comienzan los meses del calendario """

    img_letras = recortar_días_de_la_semana(img_bin)

    if inicializar.lunes_o_domingo != -1 : # quiere decir que ya se detectó para otro mes con cual de los días comienza
        return inicializar.lunes_o_domingo

    else: # encontrarlo y actualizar
        img_letras_copia = img_letras.copy()

        img_letras_copia = np.concatenate((img_letras_copia, img_letras_copia), axis=1) # mientras más letras mejor
        # cv.imshow('img_letras', img_letras)

        # Elimino subrayado si es que hay para detectar mejor
        kn = cv.getStructuringElement(cv.MORPH_RECT, (35, 1))
        lineaH = cv.erode(img_letras_copia, kn)  # para sacar el subrayado en algunas letras
        lineaH = cv.dilate(lineaH, kn)
        img_letras_copia = img_letras_copia - lineaH
        img_letras_copia = funciones.filtro_mediana(img_letras_copia, 5)
        # cv.imshow('letras', img_letras)

        img_letras_copia = 255 - img_letras_copia
        # cv.imshow('letras', img_letras)

        img_letras_copia = cv.copyMakeBorder(img_letras_copia, 100, 100, 100, 100, cv.BORDER_REPLICATE) # mejora la detección
        # pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe' # Sin esta linea tira error la libreria con respecto al PATH
        text = pytesseract.image_to_string(img_letras_copia)
        if len(text) == 0:
            return -1 # los return no los usamos para nada ahora. usamos la variable global inicializar.lunes_o_domingo

        # si la primer letra es D o S ---> entonces comienza con domingo
        if text[0].capitalize() == "D" or text[0].capitalize() == "S" or text[0].capitalize() == "0" \
                or text[0].capitalize() == "O" or text[0].capitalize() == "J":
            inicializar.lunes_o_domingo = 6
            return 6  # esto xq a veces se confunde la D con el 0 o la O

        # si la primer letra es L o M ---> entonces comienza con lunes
        elif text[0].capitalize() == "L" or text[0].capitalize() == "M" or text[0].capitalize() == "T":
            inicializar.lunes_o_domingo = 0
            return 0 # la t es xq se confunde con la L a veces

        else:
            return -1



def descartar_nombre_mes(img_bin, img_color):
    """ Devuelve una imagen mas chica ya que se recorta el nombre del mes """
    img_copia = img_bin.copy()

    ## Operacion de apertura para unir en un bloque el nombre del mes y eliminarlo, xq no lo necesitamos
    kn = cv.getStructuringElement(cv.MORPH_ELLIPSE, (3, 3))
    img_copia = cv.dilate(img_copia, kn, iterations=7)  # la cantidad de dilataciones en este caso la sabemos xq tenemos prefijado el tamaño de la imagen
    # cv.imshow('Dilatada', img_bin); cv.waitKey()

    rectangulo = funciones.detectar_bloques(img_copia)
    # El título va a ser el bloque que se encuentra más arriba de todo, o con el menor y
    miny = np.argmin( rectangulo[:, 1] )    # menor y
    x, y, w, h = rectangulo[miny, :]
    # mostrar_detectados(img_copia, [[x, y, w, h]] ) # mostrar el título que voy a borrar

    # Recortamos el título
    img_bin = img_bin[ y + h : , : ]
    img_color = img_color[ y + h : , : ]
    return img_bin, img_color


def pre_procesar_mes(img_mes):
    """ El tamanio dejarlo en 500, aunque más grande es mejor.. si se mueve, ajustar parámetro de descartar_titulo()
            cuanto se tiene que dilatar  """

    # se procesará todo en imagen binarizada, por eso se lee en escala de gris
    img = cv.cvtColor(img_mes, cv.COLOR_BGR2GRAY)
    # agrandamos todas las imágenes de manera proporcional a un tamaño de ancho 500
    tamanio = 500
    img = funciones.resize(img, ancho=tamanio)
    img_color = funciones.resize(img_mes, ancho=tamanio)

    ###### 1. Binarizar
    # por ahora para probar este binarizado sirve para este tipo de calendario
    # _, img_bin = cv.threshold(img, 180, 255, cv.THRESH_BINARY_INV)
    _, img_bin = cv.threshold(img, 0, 255, cv.THRESH_BINARY_INV | cv.THRESH_OTSU)
    # pasar filtro de mediana para eliminar puntos espureos
    img_bin = funciones.filtro_mediana(img_bin, 3)

    ###### 2. Descartar el nombre del mes (Enero, Febrero, ...)
    img_bin, img_color_sin_titulo = descartar_nombre_mes(img_bin, img_color)

    return img_bin, img_color_sin_titulo


def obtener_anio_calendario(img, pos_cols, nro_mes, tipo_lu_do):
    columna = 0  # columna en donde se encuentra el primer dia del mes
    for col, pos_col in enumerate(pos_cols):
        seccion_img = img[:, pos_col-5: pos_col+5]  # el -+5 se lo puso a ojo, mas o menos (total esta prefijado el ancho de la imagen)
        if np.any( seccion_img == 255 ):
            columna = col
            break

    ## Puede haber muchos años que tal mes comience tal dia, entonces retornamos los meses posibles de 20 años antes y 20 despues del actual
    ## En realidad se analizó.. y cada 5 o 6 años se repite el calendario..
    anio_actual = int(datetime.datetime.now().year)
    posibles_anios = []
    for anio in range(anio_actual-20, anio_actual+20):
        primer_dia, _ = calendar.monthrange(anio, nro_mes)
        # primer día indica el número del primer día del mes contando desde el lunes (Ej: si es 2, primer día es miercoles)
        if tipo_lu_do == 6:  # si la semana comienza en domingo
            primer_dia = (primer_dia + 1) % 7  # Correr todos los días, 1 día a la derecha
        if primer_dia == columna:
            posibles_anios.append(anio)

    ## De los meses posibles, quedarme con el más cercano al actual
    dif0 = abs(posibles_anios[0] - anio_actual)  # diferencia entre el posible y el actual
    anio_calendario = posibles_anios[0]  # anio a retornar
    for anio in posibles_anios:
        dif1 = abs(anio - anio_actual)
        if dif1 <= dif0: # igual xq se prefiere un año futuro en vez de uno pasado
            anio_calendario = anio
            dif0 = dif1
    inicializar.anio_calendario = anio_calendario
    return anio_calendario



# def detectar_dias_posiciones(archivo, anio, nro_mes):
def detectar_dias_posiciones(img_bin, nro_mes):
    ###### 3. Detectar el arreglo en donde se dispondrán los números del mes.

    tot_rows, tot_cols = img_bin.shape

    ###### Recortar días de la semana: lu, ma, mi, ju, vi, sa, do

    # Para lograr esto, se recorre desde arriba de la imagen (desde fila 0) y se mira todas las columnas de dicha fila
    # si no hay nada es xq no empezó el calendario, si encuentra algo es xq comienzan a aparecer los días lu, ma, ....
    ya_inicio = False  # bandera que indica que empezaron a aparecer las letras: lu, ma, ...
    ya_termino = False  # bandera que indica que terminaron
    fila = 0  # variable usada para iterar
    fila_inicio = 0  # fila donde comienzan las letras
    fila_fin = 0  # fila donde terminan las letras
    while not ya_termino:
        todos_ceros = np.all(img_bin[fila, :] == 0)  # si todos son iguales a cero
        if not todos_ceros and not ya_inicio:
            ya_inicio = True
            fila_inicio = fila
        if todos_ceros and ya_inicio:
            ya_termino = True
            fila_fin = fila
        fila += 1

    ###### Detectar si comienza en lunes o domingo
    # Para ello, recortar imagen un cuarto mas de alto y de bajo (esto soluciona el subrayado de las letras)..
    # para pasar dicha sección a la función lu_o_dom que se encarga de detectar cual es el primer día de la semana
    alto_letra = fila_fin - fila_inicio
    if fila_inicio - alto_letra // 4 < 0:
        corte = 0  # este if-else soluciona un problema que no interesa pensar tanto
    else:
        corte = fila_inicio - alto_letra // 4

    img_letras = img_bin[fila_inicio - 1: fila_fin + 1, :]  # imagen alargada: lu, ma, mi, ju, vi, sa, do

    # tipo_lu_do = funciones.lu_o_dom(img_letras)  # esta función devuelve 0 si es lunes o 6 si es domingo

    ### -------------------------------------------------   todo lo anterior ya se está haciendo en otra funcion



    ###### Encontrar las posiciones de las columnas, para ello dilato la imagen de las letras antes recortadas
    # hasta encontrar los 7 objetos (lu, ma, mi, ...). Luego, el centro de cada uno, son las posiciones de las cols
    bloques = funciones.detectar_bloques(img_letras)
    cant_bloques = len(bloques)
    kn = cv.getStructuringElement(cv.MORPH_ELLIPSE, (3, 3))
    while cant_bloques > 7:
        img_letras = cv.dilate(img_letras, kn, iterations=1)
        bloques = funciones.detectar_bloques(img_letras)
        cant_bloques = len(bloques)

    if cant_bloques != 7:  # quiere decir que la imagen recortada de los días no es la correcta
        print('---- LA IMAGEN RECORTADA DE LAS LETRAS DE LOS DIAS NO ES CORRECTA ')
        print('---- mirar funcion recortar titulo, puede estar mal la cant de dilataciones debido al tamanio de la imagen')
        cv.imshow('imagen mes sin el título',img_bin)
        cv.imshow('imagen recortada de las letras',img_bin[fila_inicio - 1: fila_fin + 1, :])
        cv.imshow('luego de dilatar', img_letras)
        cv.waitKey()
        exit(1)

    # El centro de cada uno es la posicion de las columnas
    pos_cols = []
    for bloque in bloques:
        centro = (bloque[0] + bloque[0] + bloque[2]) // 2
        pos_cols.append(centro)
    pos_cols.sort()  # las ordeno de izquierda a derecha: lu, ma, mi, ...

    ##### Obtener pocision de las filas
    img_bin_sin_letras = img_bin
    img_bin_sin_letras[corte: fila_fin + alto_letra // 4, :] = 0

    # se procede con la misma lógica en que se encontraron las letras: lu, ma, mi, recorriendo cada fila y analizando
    # todas las columnas de cada fila. (Si hay una marca de un evento que une dos filas, caga el algoritmo)
    pos_filas = []
    ya_inicio = False
    ya_termino = False
    alto_numeros = 0
    cant_filas = 0
    for fila in range(tot_rows):
        vfila = img_bin_sin_letras[fila, :]  # vector fila
        todos_ceros = np.all(vfila == 0)  # si todos son iguales a cero
        if not todos_ceros and not ya_inicio:
            ya_inicio = True
            fila_inicio = fila
        if todos_ceros and ya_inicio:
            ya_termino = True
            fila_fin = fila
        if ya_inicio and ya_termino:
            if (
                    fila_fin - fila_inicio) < 20:  # (fila_fin-fila_inicio)<20 es por si hay algun puntito blanco que quedó y no es un número
                ya_inicio = False
                ya_termino = False
            else:
                cant_filas += 1
                centro = (fila_inicio + fila_fin) // 2
                alto_numeros = fila_fin - fila_inicio
                pos_filas.append(centro)
                ya_inicio = False
                ya_termino = False

    # -----------------------------------------------------------------------------------------

    ###### Estimar el anio del calendario, sabiendo cual es el mes, el primer dia y si comienza en do o lu
    img_primeros_dias_mes = img_bin_sin_letras[pos_filas[0] - alto_numeros // 2: pos_filas[0] + alto_numeros // 2, :]
    # cv.imshow('primer_fila', img_primeros_dias_mes)
    # cv.waitKey()
    nro_anio = obtener_anio_calendario(img_primeros_dias_mes, pos_cols, nro_mes, inicializar.lunes_o_domingo)

    # -----------------------------------------------------------------------------------------

    ##### Poner en una matriz, los días del mes, colocalndo -1 donde no se encuentran días
    mat_con_dias1 = np.ones(7 * cant_filas, dtype=int) * (-1)  # primero la lleno de -1

    primer_dia, cant_dias_mes = monthrange(nro_anio, nro_mes)
    # primer día indica el número del primer día del mes contando desde el lunes (Ej: si es 2, primer día es miercoles)
    if inicializar.lunes_o_domingo == 6:  # si la semana comienza en domingo
        primer_dia = (primer_dia + 1) % 7  # Correr todos los días, 1 día a la derecha

    dias = np.arange(cant_dias_mes, dtype=int) + 1  # +1 está xq arange devuelve desde el día 0 y no incluye el último
    fin = primer_dia + len(dias)  # ultima posición dentro del calendario que corresponde al último día del mes
    mat_con_dias1[primer_dia: fin] = dias
    mat_con_dias = np.reshape(mat_con_dias1, (cant_filas, 7))

    return mat_con_dias, pos_cols, pos_filas



def main():
    pass


if __name__ == '__main__':

    main()



