import sys

import cv2 as cv

from Codigo import funciones, detectar_meses, inicializar, detectar_dias, obtener_eventos


def main():
    """
        Esta función permite probar la detección de eventos sobre 5 calendarios que se encuentran en la carpeta
        calendarios_marcados. Debe moverse la barra para elegir el calendario y luego apretar una tecla para procesar
    """

    cv.namedWindow("Digitalizador")
    cv.createTrackbar('calendario', 'Digitalizador', 8, 19, funciones.nothing)  # la numero 8 revienta


    while 1: # iterar hasta presionar escape o letra Q

        print('\n\n\n-Elija el calendario y presione la tecla espacio para procesar.')
        print('-Para finalizar presione la letra Q o escape.\n\n')
        while 1: # tecla enter
            nro_cal = cv.getTrackbarPos('calendario', 'Digitalizador') + 1

            ###### Cargar y mostrar calendario
            img_cal = cv.imread( 'calendarios/calendario' + str(nro_cal) + '.jpg' )
            img_cal_aux = funciones.resize(img_cal, 700) # para poder verlo

            cv.imshow('Digitalizador', img_cal_aux)
            k = cv.waitKey(1) & 0xFF
            if k == 32: # espacio
                break
            elif k == 27 or k == 113 or k == 81: # tecla escape, q o Q
                print('\nPrograma finalizado.')
                exit(1)
        print('... Espere unos segundos. Procesando ...\n')


        if funciones.detectarBlur(img_cal_aux):
            print("Imagen Desenfocada. Vuelva a tomar la foto.")
            sys.exit(1)
        # if funciones.detectarBrilloMedio(img_cal_aux) == 1:
            # print("Supera el brillo estipulado.")
        elif funciones.detectarBrilloMedio(img_cal_aux) == -1:
            print("No supera el brillo estipulado.")
            sys.exit(1)
        elif funciones.detectarBrilloMedio(img_cal_aux) == 0:
            value = 20
            img_cal[:,:] += value

        img_cal = funciones.recortarCalendario(img_cal, img_cal_aux)
        img_cal_recortado_chico = funciones.resize(img_cal, 700)  # para poder verlo


        ###### Separar meses
        meses_recortados = detectar_meses.detectar_meses(img_cal)

        ###### Recorrer los meses en busca de con qué día de la semana comienzan y actualizar la variable global inicializar.lunes_o_domingo
        inicializar.lunes_o_domingo = -1  # indica que todavía no se sabe si los días de la semana empiezan en lu o dom
        meses_recortados_pre_procesados = [] # ajustados en tamaño, binarizados y sin el título (enero, febrero,)
        meses_recortados_pre_procesados_color = [] # los mismos que antes procesados pero en color

        for img_mes in meses_recortados:

            ####### Ajustar el tamaño, binarizar y quitarle el título a los meses
            img_bin, img_color_sin_titulo = detectar_dias.pre_procesar_mes(img_mes)
            # los guardo en una lista porque servirán para más adelante
            meses_recortados_pre_procesados.append(img_bin)
            meses_recortados_pre_procesados_color.append(img_color_sin_titulo)

            ####### Encontrar si comienza en lunes o domingo, si no se encuentra, seguir con los proximos meses hasta encontrar 1
            detectar_dias.calendario_lu_o_dom(img_bin) # actualiza la variable global inicializar.lunes_o_domingo

        if inicializar.lunes_o_domingo == -1: # no se pudo detectar en ninguno de los meses en qué dia comienza la semana
            print('En ninguno de los meses se pudo detectar si la semana comienza en lunes o domingo')
            sys.exit(1)


        print('----------------------')

        ###### Detectar matrices de los días y posiciones de cada mes para luego obtener los eventos
        ###### Obtener los eventos del mes

        for nro_mes, (mes_bin, mes_color) in enumerate(zip(meses_recortados_pre_procesados, meses_recortados_pre_procesados_color)):

            mat_con_dias, pos_cols, pos_filas = detectar_dias.detectar_dias_posiciones(mes_bin, nro_mes+1)
            eventos = obtener_eventos.obtener_eventos(mat_con_dias, pos_cols, pos_filas, mes_color, nro_mes+1)

            if len(eventos) != 0: # si se encontraron eventos en este mes
                print('\n-- Eventos del mes de:', inicializar.nombre_meses[nro_mes], ' --')
                [print(ev) for ev in eventos]



        print('\nAÑO DEL CALENDARIO: ', inicializar.anio_calendario, '\n\n----------------------')



if __name__ == '__main__':

    main()


