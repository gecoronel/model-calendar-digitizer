
import numpy as np
import cv2 as cv
from skimage.filters import threshold_yen
from skimage.exposure import rescale_intensity
from Codigo import inicializar
import math
from collections import Counter


def restaurar(img):
    yen_threshold = threshold_yen(img) + 15
    bright = rescale_intensity(img, (0, yen_threshold), (0, 255))
    # cv.imshow('bright', bright)

    bright = filtro_non_local_mean(bright)
    bright = filtro_mediana(bright, 3)
    return bright

def resize(img, ancho, interpolacion=cv.INTER_LINEAR):
    """Cambia tamaño imagen según el parámetro ancho (en píxeles) manteniendo relacion aspecto de la imagen"""
    factor = ancho / img.shape[1]
    alto = int(img.shape[0] * factor)
    return cv.resize(img, (ancho, alto), interpolation=interpolacion)

def nothing(x): pass

def mostrar_detectados(img_bin, rectangulos):
    bloques_detectados = img_bin.copy()
    bloques_detectados = cv.cvtColor(bloques_detectados, cv.COLOR_GRAY2BGR)
    for rect in rectangulos:
        (x, y, w, h) = rect[:]
        cv.rectangle(bloques_detectados, (x, y), (x + w, y + h), (0, 255, 0), 1)
    # cv.imshow('contornos', bloques_detectados)
    # cv.waitKey()

def detectar_bloques(img_bin):
    contours, _ = cv.findContours(img_bin, mode=cv.RETR_EXTERNAL, method=cv.CHAIN_APPROX_NONE)
    bloques = []  # lista con los bloques detectados
    for contour in contours:
        (x, y, w, h) = cv.boundingRect(contour)  # Draw the bounding rectangle
        bloques.append([x, y, w, h])
    # mostrar_detectados(img_bin, bloques)
    # Convertir las listas en numpy para trabajar mejor
    bloques = np.array(bloques)
    return bloques

def filtro_mediana(img, tam_kn):
    out = img.copy()
    # out = cv.medianBlur(out, tam_kn)
    # return cv.medianBlur(np.float32(out), tam_kn)  # la funcion dice que recive CV_32F
    return cv.medianBlur(out, tam_kn)  # la funcion dice que recive CV_32F

def filtro_non_local_mean(img):
    # los parametros predefinidos son recomendados de la página oficial
    # https://docs.opencv.org/3.4/d1/d79/group__photo__denoise.html#ga4c6b0031f56ea3f98f768881279ffe93
    return cv.fastNlMeansDenoising(img, dst=None, h=10, templateWindowSize=7, searchWindowSize=21)

def nothing(x): pass

def filtrar(img,kernel):
    ker=np.ones((kernel,kernel))/(kernel*kernel)
    res=cv.filter2D(img,-1,ker)
    return res

def rotate(img, angle):
    """Rotación de la imagen sobre el centro"""
    r = cv.getRotationMatrix2D((img.shape[1] / 2, img.shape[0] / 2), angle, 1.0)
    return cv.warpAffine(img, r, (img.shape[1],img.shape[0]))

def houghComun(imgOr,bin=1,umbral1=100,umbral2=150,thresh=80):
    imgC=np.copy(imgOr)
    if (bin==1):
        imgG= cv.cvtColor(imgC,cv.COLOR_BGR2GRAY)
    else:
        imgG=np.copy(imgOr)
    img= imgG[:,:]/255
    H,W=img.shape
    aux = img.copy()*0

    #1. Calcular el gradiente de la imagen 
    edges= cv.Canny(imgG,umbral1,umbral2)
    #2. umbralizar el resultado. Hecho en Canny

    #3. HoughLines
    lines= cv.HoughLines(edges,1,np.pi/180,thresh)
    #agregar lineas Hough
    for rho,theta in lines[:,0]:
        a = np.cos(theta)
        b = np.sin(theta)
        x0 = a*rho
        y0 = b*rho
        x1 = int(x0 + 1000*(-b))
        y1 = int(y0 + 1000*(a))
        x2 = int(x0 - 1000*(-b))
        y2 = int(y0 - 1000*(a))

        cv.line(aux,(x1,y1),(x2,y2),255,2)
    return aux,lines

def detectarBlur(img,thresh = 100):
    data = img.copy()
    data_gray = cv.cvtColor(data, cv.COLOR_BGR2GRAY)
    fm_vec = cv.Laplacian(data_gray, cv.CV_64F)
    fm = fm_vec.var()
    if (fm < thresh):
        print('Imagen Desenfocada')
        return True
    else:
        return False

def detectarBrilloMedio(img):
    data = img.copy()
    data_gray = cv.cvtColor(data, cv.COLOR_BGR2GRAY)
    data_gray = data_gray / 255  # esto xq se supone que  se recive en el rango 0-255
    media = np.mean(data_gray.flatten()) * 255
    if (media>127):
        return 1
    elif ((media>100) and (media<128)):
        return 0
    else: 
        return -1

def rotarCalendario(img_ori, img):
    data = img.copy()
    calendar_gray = cv.cvtColor(data, cv.COLOR_BGR2GRAY)
    ############### ENDEREZAR CON HOUGH ####################
    i=100
    aux,lines=houghComun(calendar_gray,0,100,250,i)
    while lines.shape[0]>10:
        aux,lines=houghComun(calendar_gray,0,100,250,i)
        i=i+1
        # print(i, len(lines))
    # cv.imshow('Hough', aux)
    # cv.waitKey()  # para mostrar
    # cv.destroyAllWindows()
    # Recopilemos qué ángulos ha encontrado la transformada
    # de hough para cada una de las líneas halladas
    angulos = []
    for linea in lines:
        theta = linea[0][1]
        angulos.append(theta * 180 / math.pi)
    # Ahora contemos cuántas veces aparece cada ángulo
    veces = Counter(angulos)
    
    # Y quedémonos con el ángulo que más veces se repite
    angulo = veces.most_common()[0][0]
    
    # Cambiar el sentido de la rotación si el ángulo es mayor de 180º
    if angulo > np.pi/2:
       angulo = -angulo
       angulo = angulo + 90
    else:
       angulo = angulo - 90
    # print("Angulo de rotacion: ", angulo)
    # Ahora enderecemos la imagen, girando (en negativo) el ángulo detectado
    """h, w = data.shape[:2]
    centro = (w // 2, h // 2)
    M = cv.getRotationMatrix2D(centro, -angulo, 1.0)
    calendar_derecho = cv.warpAffine(data, M, (w, h),
                flags=cv.INTER_CUBIC, borderMode=cv.BORDER_REPLICATE)
    """
    calendar_derecho = rotate(img_ori, -angulo)
    """
    cv.imshow('Hough', aux)
    cv.waitKey()  # para mostrar
    cv.destroyAllWindows()
    # DEVOLVER EL ANGULO
    angulo = []
    for c in lines:
        _, theta = c[0]
        angulo.append(theta * 180 / math.pi)
        print(angulo)
    inclinacion = round(statistics.mean(angulo)-90)
    print(inclinacion)
    calendar_derecho = rotate(data, inclinacion)
    """
    return calendar_derecho

def recortarCalendario(img_ori, img):
    data = img.copy()
    data2 = img_ori.copy()

    calendar = rotarCalendario(data2, data)

    calendar_gray = cv.cvtColor(calendar, cv.COLOR_BGR2GRAY)

    calendar_gray = filtrar(calendar_gray,5)

    calendar_bin = cv.threshold(calendar_gray,180,255, 0)[1] #180 es un valor probado
    
    ele = cv.getStructuringElement(cv.MORPH_RECT,(3,3))
    calendarEro = cv.erode(calendar_bin,ele,iterations=3)
    calendarDil = cv.dilate(calendarEro,ele,iterations=3)
    calendarDil = cv.erode(calendarDil,ele,iterations=3)
    calendarDil = cv.dilate(calendarDil,ele,iterations=3)
    calendarDil = cv.erode(calendarDil,ele,iterations=3)
    h,w = calendarDil.shape
    for i in range(w):
        if (calendarDil[int(h/2),i] == 255):
            minHor = i
            break
    for i in range(w):
        if (calendarDil[int(h/2),w-i-1] == 255):
            maxHor = w-i-1
            break
    for i in range(h):
        if (calendarDil[i,int(w/2)] == 255):
            minVer = i
            break
    for i in range(h):
        if (calendarDil[h-i-1,int(w/2)] == 255):
            maxVer = h-i-1
            break
    #print(h,w,minHor, maxHor, minVer, maxVer)
    img_crop = np.zeros((maxVer-minVer, maxHor-minHor), np.uint8)
    img_crop = calendar[minVer:maxVer, minHor:maxHor]

    return img_crop