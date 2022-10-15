
# How do I share global variables across modules?
# The canonical way to share information across modules within a single program is to create a special module
# (often called config or cfg). Just import the config module in all modules of your application;
# the module then becomes available as a global name. Because there is only one instance of each module,
# any changes made to the module object get reflected everywhere.

# En este caso, el modulo config, se llamará inicializar.py

# por el momento, xq se necesitaba, sólo esta variable se levanta, pero se puede levantar las imágenes y todo
anio_calendario = 0

# esta variable contiene 6 si comienza en domingo, 0 en lunes o -1 cuando todavía no se detectó en ninguno de los meses
# cuál es el día con el que comienza
lunes_o_domingo = -1

nombre_meses = ['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio', 'Julio',
                    'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre']


