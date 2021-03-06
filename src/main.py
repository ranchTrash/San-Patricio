# -*- coding: utf-8 -*-

from flask import Flask, render_template, request, redirect, url_for, session
import mysql.connector
import os
app = Flask(__name__)
app.secret_key = os.urandom(16)

mydb = mysql.connector.connect(
    host="localhost", ## Escribir aqui tu host (localhost por defecto)
    user="root", # Escribir aqui tu usuario
    passwd="3_99SA.17*Pc#2", # Escribir aqui tu contraseña
    database = "sanpatricio", # Escribir aqui el nombre de la base de datos
    auth_plugin='mysql_native_password' # Dejar esta propiedad asi
)

cur = mydb.cursor()
curpGlobal = ""

@app.route('/')
def cargar_principal():
    if 'sesion' in session:
        usuario = session['usuario']
        print("LOGIN: ", usuario)
        return render_template('menu_responsive.html')
    return redirect(url_for('cargar_login'))

@app.route('/login', methods=['GET', 'POST'])
def cargar_login():
    if 'sesion' in session:
        return redirect(url_for('cargar_principal'))

    if request.method == "POST":
        detalles = request.form
        _usuario = detalles['username']

        query = "select exists(select user_usu from usuario where user_usu='" + _usuario + "')"
        cur.execute(query)
        existeUsuario = cur.fetchall()[0]

        if not existeUsuario[0]:
            return redirect(url_for('cargar_login'))

        _contrasenia = detalles['password']

        query = "select cve_usu from usuario where user_usu='" + _usuario + "'"
        cur.execute(query)
        claveUsuario = cur.fetchall()[0]

        query = "select strcmp((select pass_usu from usuario where cve_usu=" + str(claveUsuario[0]) + "), sha2('" + str(_contrasenia) + "', 224))"
        cur.execute(query)
        contraseniaCorrecta = cur.fetchall()[0]

        if contraseniaCorrecta[0] != 0:
            return redirect(url_for('cargar_login'))

        rol = "persona"
        rolEmpleado = ""

        query = "select exists(select u.curp_per from usuario u join empleado e on u.curp_per=e.curp_per where u.cve_usu=" + str(claveUsuario[0]) + ")"
        cur.execute(query)
        esEmpleado = cur.fetchall()[0]

        if esEmpleado[0]:
            rol = "empleado"

            query = "select concat(puesto, '') from usuario u join empleado e on u.curp_per=e.curp_per where user_usu='" + str(_usuario) + "'"
            cur.execute(query)
            resultado = cur.fetchall()[0]
            rolEmpleado = resultado[0]
            print(rolEmpleado)

        query = "select exists(select u.curp_per from usuario u join alumno a on u.curp_per=a.curp_per where u.cve_usu=" + str(claveUsuario[0]) + ")"
        cur.execute(query)
        esAlumno = cur.fetchall()[0]

        if esAlumno[0]:
            rol = "alumno"

        query = "select curp_per from usuario where user_usu='" + str(_usuario) + "'"
        cur.execute(query)
        resultado = cur.fetchall()[0]

        print(resultado[0])

        curpGlobal = str(resultado[0])

        session['usuario'] = detalles['username']
        session['rol'] = rol
        session['sesion'] = True
        session['rolEmpleado'] = rolEmpleado
        return redirect(url_for('cargar_principal'))
    return render_template('Login.html')

@app.route('/logout')
def logout():
   session.pop('usuario', None) 
   session.pop('sesion', None) 
   return redirect(url_for('cargar_login'))

@app.route('/menu/')
def cargar_menu():
    return render_template('menu.html')

# /menu-responsive/
@app.route('/menu-responsive')
def cargar_menu_responsive():
    return render_template('menu_responsive.html')

# --------------------- datosPersonales --------------------- ## --------------------- v_datosPersonales --------------------- #

@app.route('/datos-personales')
def cargar_vista_datosPersonales():
    query = "select * from persona where curp_per='" + str(curpGlobal) + "'"
    cur.execute(query)
    datosPersonales = cur.fetchall()

    print(curpGlobal)

    return render_template('vista_datosPersonales.html', datosPersonales = datosPersonales)

# --------------------- AREAS --------------------- ## --------------------- s_AREAS --------------------- #

@app.route('/areas/')
def cargar_areas():
    query = "select a.cve_are, nombre_are from area a join grupo g on a.cve_are=g.cve_are where curdate() between fechaini_gru and fechafin_gru group by cve_are"
    cur.execute(query)
    areasOcupadas = cur.fetchall()

    query = "select a.cve_are, nombre_are from area a join grupo g on a.cve_are=g.cve_are where curdate() not between fechaini_gru and fechafin_gru group by cve_are"
    cur.execute(query)
    areasLibres = cur.fetchall()

    return render_template('areas.html', areasOcupadas = areasOcupadas, areasLibres = areasLibres)

@app.route('/area', methods=['POST'])
def area():
    data = request.form

    query = "select cve_are, nombre_are, concat(tipo_are, '') as tipo, concat(ancho_are, ' x ', largo_are, ' ', umedida_are) as medidas, detalles_are from area where cve_are=" + str(data['clave'])
    cur.execute(query)
    resultados = cur.fetchall()

    area = resultados[0]

    query = "select g.*, a.nom_act, concat(p.nom_per, ' ', p.ap_per, ' ', p.am_per) from grupo g join actividad a on g.cve_act=a.cve_act join empleado e on g.cve_emp=e.cve_emp join persona p on e.curp_per=p.curp_per where g.cve_are=" + data['clave']
    cur.execute(query)
    grupos = cur.fetchall()

    grupos_dict = []

    for grupo in grupos:
        grupo_dict = {
            "turno": str(grupo[1]) + " a " + str(grupo[2]),
            "lapso": str(grupo[3]) + " - " + str(grupo[4]),
            "minmaxalum": str(grupo[6]) + "/" + str(grupo[5]),
            "act": grupo[10],
            "emp": grupo[11]
        }
        grupos_dict.append(grupo_dict)

    tupla = {
        "area": [
            { "clave": area[0], "nombre": area[1], "tipo": area[2], "medidas": area[3], "detalles": area[4] }
        ],
        "grupos": grupos_dict
    }

    return tupla

# /registro-areas
@app.route('/areas/registrar', methods=['GET', 'POST'])
def cargar_areas_registro():
    if request.method == "POST":
        detalles = request.form
        _nombre = detalles['nombre']
        _tipo = detalles['tipo']
        _ancho = detalles['ancho']
        _largo = detalles['largo']
        _umedida = detalles['umedida']
        _detalles = detalles['detalles']

        query = "insert into area values(%s, %s, %s, %s, %s, %s, %s)"
        values = (None, _nombre, _tipo, _ancho, _largo, _umedida, _detalles)

        cur.execute(query, values)
        mydb.commit()

        print("INSERCION EXITOSA")

        #######################

        # cur.execute("select * from test")
        # data = cur.fetchall()

        # print(str(data))


        # _ancho = detalles['ancho']

        # query = "insert into test values(%s, %s)"
        # values = (None, _ancho)

        # cur.execute(query, values)
        # mydb.commit()

        # print("insertado exitosamente")

        pass

    return render_template('areas_registro.html')

# --------------------- ACTIVIDADES --------------------- ## --------------------- s_ACTIVIDADES --------------------- #

# Ventana principal de actividades
@app.route('/actividades/')
def cargar_actividades():
    query = "select * from actividad where tipo_act='Deportiva' order by nom_act"
    cur.execute(query)
    actividadesDeportivas = cur.fetchall()

    query = "select * from actividad where tipo_act='Artistica' order by nom_act"
    cur.execute(query)
    actividadesArtisticas = cur.fetchall()

    return render_template('actividades.html', actividadesDeportivas = actividadesDeportivas, actividadesArtisticas = actividadesArtisticas)

@app.route('/actividad', methods=['POST'])
def actividad():
    data = request.form
    query = "select * from actividad where cve_act=" + data['clave']
    cur.execute(query)
    _actividad = cur.fetchall()

    actividad = _actividad[0]

    _tipo = None

    for i in actividad[2]:
        _tipo = i

    # query = "select g.*, a.nom_act, concat(p.nom_per, ' ', p.ap_per, ' ', p.am_per) from grupo g join actividad a on g.cve_act=a.cve_act join empleado e on g.cve_emp=e.cve_emp join persona p on e.curp_per=p.curp_per where g.cve_act=" + data['clave']
    query = "select g.*, a.nombre_are, concat(p.nom_per, ' ', p.ap_per, ' ', p.am_per) from grupo g join area a on g.cve_are=a.cve_are join empleado e on g.cve_emp=e.cve_emp join persona p on e.curp_per=p.curp_per where g.cve_act=" + data['clave']
    cur.execute(query)
    grupos = cur.fetchall()

    grupos_dict = []

    for grupo in grupos:
        grupo_dict = {
            "turno": str(grupo[1]) + " a " + str(grupo[2]),
            # "horaent": str(grupo[1]),
            # "horasali": str(grupo[2]),
            "lapso": str(grupo[3]) + " - " + str(grupo[4]),
            # "fechaini": str(grupo[3]),
            # "fechafin": str(grupo[4]),
            "minmaxalum": str(grupo[6]) + "/" + str(grupo[5]),
            # "maxalumnos": grupo[5],
            # "minalumnos": grupo[6],
            "are": grupo[10],
            "emp": grupo[11]
        }
        grupos_dict.append(grupo_dict)

    tupla = {
        "actividad": [
            { "clave": actividad[0], "nom": actividad[1], "tipo": _tipo, "descrip": actividad[3] }
        ],
        "grupos": grupos_dict
    }

    return tupla

# /registro-actividades
@app.route('/actividades/registrar', methods=['GET', 'POST'])
def cargar_actividades_registro():
    if request.method == "POST":
        detalles = request.form
        _nombre = detalles['nombre']
        _tipo = detalles['tipo']
        _descripcion = detalles['descripcion']

        query = "insert into actividad values(%s, %s, %s, %s)"
        values = (None, _nombre, _tipo, _descripcion)

        cur.execute(query, values)
        mydb.commit()

        print("INSERCION EXITOSA")
        return redirect(url_for('cargar_actividades'))

    return render_template('actividades_registro.html')

# --------------------- GRUPOS --------------------- ## --------------------- s_GRUPOS --------------------- #

# Ventana principal de grupos
@app.route('/grupos/')
def cargar_grupos():
    query = "select cve_gru, nom_act from grupo g join actividad a on g.cve_act=a.cve_act where curdate() between fechaini_gru and fechafin_gru"
    cur.execute(query)
    gruposActivos = cur.fetchall()

    query = "select cve_gru, nom_act from grupo g join actividad a on g.cve_act=a.cve_act where curdate() not between fechaini_gru and fechafin_gru"
    cur.execute(query)
    gruposInactivos = cur.fetchall()

    return render_template('grupos.html', gruposActivos = gruposActivos, gruposInactivos = gruposInactivos)

@app.route('/grupo', methods=['POST'])
def grupo():
    data = request.form

    query = "select cve_gru, concat(horaent_gru, ' - ', horasali_gru) as turno, concat(fechaini_gru, ' / ', fechafin_gru) as periodo, concat(minalumnos_gru, '/', maxalumnos_gru) as minmax, concat(nom_act, ' - ', tipo_act) as actividad, concat(nombre_are, ' - ', tipo_are) as area, concat(nom_per, ' ', ap_per, ' ', am_per) as docente from grupo g join actividad a on g.cve_act=a.cve_act join area ar on g.cve_are=ar.cve_are join empleado e on g.cve_emp=e.cve_emp join persona p on e.curp_per=p.curp_per where cve_gru=" + data['clave']
    cur.execute(query)
    resultados = cur.fetchall()

    grupo = resultados[0]

    cur.callproc('sp_getListaGrupo', [ data['clave'], ])

    alumnos = []

    for resultado in cur.stored_results():
        listaAlumnos = resultado.fetchall()
        # if (listaAlumnos):
        #     alumnos = listaAlumnos

        for alumno in listaAlumnos:
            alumno_dict = {
                "curp": alumno[0],
                "nombre": alumno[1]
            }
            alumnos.append(alumno_dict)

        # print(listaAlumnos)
        # for alumno in listaAlumnos:
        #     print(alumno)

    # print(alumnos)

    # print(alumnos)

    tupla = {
        "grupo": [
            { "clave": grupo[0], "turno": grupo[1], "periodo": grupo[2], "minmax": grupo[3], "act": grupo[4], "are": grupo[5], "docente": grupo[6] }
        ],
        "alumnos": alumnos
    }

    return tupla

#/registro-grupos
@app.route('/grupos/registrar', methods=['GET', 'POST'])
def cargar_grupos_registro():
    if request.method == "GET":
        query = "select cve_act, nom_act from actividad"     
        cur.execute(query)
        actividades = cur.fetchall()

        query = "select cve_are, nombre_are from area"
        cur.execute(query)
        areas = cur.fetchall()

        query = "select cve_emp, rfc_emp, concat(fechain_emp, ' / ', fechafin_emp), concat(nom_per, ' ', ap_per, ' ', am_per) as nombre from empleado e join persona p on e.curp_per=p.curp_per where puesto='Docente' and curdate() between fechain_emp and fechafin_emp"  
        cur.execute(query)
        empleados = cur.fetchall()

        return render_template('grupos_registro.html', actividades = actividades, areas = areas, empleados = empleados)

    if request.method == "POST":
        detalles = request.form
        _horaent = detalles['horaent']
        _horasali = detalles['horasali']
        _fechaini = detalles['fechaini']
        _fechafin = detalles['fechafin']
        _minalumnos = detalles['minalumnos']
        _maxalumnos = detalles['maxalumnos']
        _actividad = detalles['actividad']
        _area = detalles['area']
        _empleado = detalles['empleado']

        query = "insert into grupo values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
        values = (None, _horaent, _horasali, _fechaini, _fechafin, _maxalumnos, _minalumnos, _actividad, _area, _empleado)

        cur.execute(query, values)
        mydb.commit()

        print("INSERCION EXITOSA")
        pass

    return render_template('grupos_registro.html')

# --------------------- EMPLEADOS --------------------- ## --------------------- s_EMPLEADOS --------------------- #

# Ventana principal de empleados
@app.route('/empleados/')
def cargar_empleados():
    # if 'sesion' not in session:
    #     return redirect(url_for('cargar_login'))

    queryAux = "select cve_emp, puesto, concat(ap_per, ' ', am_per, ' ', nom_per) as nombre from empleado e join persona p on e.curp_per=p.curp_per where puesto="
    
    query = queryAux + "'Administrador' order by nombre"
    cur.execute(query)
    administradores = cur.fetchall()

    query = queryAux + "'Docente' order by nombre"
    cur.execute(query)
    docentes = cur.fetchall()

    query = queryAux + "'Limpieza' order by nombre"
    cur.execute(query)
    limpieza = cur.fetchall()

    query = queryAux + "'Velador' order by nombre"
    cur.execute(query)
    veladores = cur.fetchall()

    query = queryAux + "'Director' order by nombre"
    cur.execute(query)
    directores = cur.fetchall()
    return render_template('empleados.html', administradores = administradores, docentes = docentes, limpieza = limpieza, veladores = veladores, directores = directores)

@app.route('/empleado', methods=['POST'])
def empleado():
    data = request.form
    # print(data)
    # print(data['clave'])

    query = "select * from empleado e join persona p on e.curp_per=p.curp_per where cve_emp=" + data['clave']
    cur.execute(query)
    resultado = cur.fetchall()

    # print(type(resultado))
    # print(type(resultado[0]))
    # print(resultado)

    datosEmpleado = resultado[0]

    _puesto = None
    _genero = None
    _orient = None

    for x in datosEmpleado[4]: # Esta es la unica forma de acceder a un elemento de un set(conjunto)
        _puesto = x

    for x in datosEmpleado[12]:
        _genero = x

    for x in datosEmpleado[15]:
        _orient = x

    query = "select * from grupo where cve_emp=" + str(datosEmpleado[0])
    cur.execute(query)
    grupos = cur.fetchall()
    # print(grupos)
    # print(type(grupos))
    # print(type(grupos[0]))

    gruposDict = [] # Diccionario de grupos

    for grupo in grupos: # Esta es la forma mas sencilla de generar un JSON para retornar una respuesta
        grupoDict = {
            "clave": grupo[0],
            'horaent': str(grupo[1]),
            "horasali": str(grupo[2]),
            "fechaini": str(grupo[3]),
            "fechafin": str(grupo[4]),
            "maxalumnos": grupo[5],
            "minalumnos": grupo[6],
            "act": grupo[7],
            "are": grupo[8]
        }
        gruposDict.append(grupoDict)

    query = "select dia_diahor, horaent_diahor, horasal_diahor from diahora dh join horario h on dh.cve_hor=h.cve_hor where cve_emp=" + str(datosEmpleado[0])
    cur.execute(query)
    horarios = cur.fetchall()

    horariosDict = []
    for horario in horarios:
        horarioDict = {
            "dia": entero_a_dia(horario[0]),
            "horaent": str(horario[1]),
            "horasal": str(horario[2])
        }
        horariosDict.append(horarioDict)

    tupla = { 
        "laborales": [
            { "clave": datosEmpleado[0], "rfc": datosEmpleado[1], "fechain": str(datosEmpleado[2]), "fechafin": str(datosEmpleado[3]), "puesto": _puesto }
        ],
        "personales": [
            { "curp": datosEmpleado[5], "nombre": datosEmpleado[7] + " " + datosEmpleado[8] + " " + datosEmpleado[9], "tel": datosEmpleado[10],
            "fechanac": str(datosEmpleado[11]), "genero": _genero, 
            "domicilio": datosEmpleado[13] + " " + _orient + " " + str(datosEmpleado[14]) }
        ],
        "grupos": gruposDict,
        "horarios": horariosDict
    }

    # print(tupla)
    # print("tupla = ", type(tupla))

    # print(tupla.laborales)

    return tupla

# @app.route('/signUp')
# def signUp():
#     return render_template('signUp.html')

# @app.route('/signUpUser', methods=['POST'])
# def signUpUser():
#     print(request.form)
#     user =  request.form['username']
#     password = request.form['password']
#     return json.dumps({'status':'OK','user':user,'pass':password})

# Registro de empleados
@app.route('/empleados/registrar', methods=['GET', 'POST'])
def cargar_empleados_registro():
    if request.method == "POST":
        detalles = request.form
        _curp = detalles['curp']
        _nombre = detalles['nombre']
        _ap = detalles['ap']
        _am = detalles['am']
        _tel = detalles['tel']
        _fechanac = detalles['fechanac']
        _genero = detalles['genero']
        _calle = detalles['calle']
        _num = detalles['num']
        _orient = detalles['orient']
        _entrecalles = detalles['entrecalles']
        _col = detalles['col']

        query = "insert into persona values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
        values = (_curp, _nombre, _ap, _am, _tel, _fechanac, _genero, _calle, _num, _orient, _entrecalles, _col)

        cur.execute(query, values)

        _rfc = detalles['rfc']
        _fechain = detalles['fechain']
        _fechafin = detalles['fechafin']
        _puesto = detalles['puesto']

        query = "insert into empleado values (%s, %s, %s, %s, %s, %s)" 
        values = (None, _rfc, _fechain, _fechafin, _puesto, _curp)

        cur.execute(query, values)
        # mydb.commit()

        # detalles = request.form
        # print(detalles)

        _monto = detalles['monto']
        _modo = detalles['modo']

        query = "insert into pagoempleado values(%s, now(), %s, %s, (select max(cve_emp) from empleado))"
        values = (None, _monto, _modo)
        cur.execute(query, values)

        query = "insert into horario values(null, curdate(), (select max(cve_emp) from empleado))"
        cur.execute(query)

        dias = detalles.getlist('dia')
        hsinicio = detalles.getlist('hinicio')
        hsfinal = detalles.getlist('hfinal')

        # print(dias)
        # print(hsinicio)
        # print(hsfinal)

        if detalles['horario'] == "Fijo":
            for i in range(len(dias)):
                print("%s (%s) - %s - %s" % ( dias[i], dia_a_entero(dias[i]), hsinicio[0], hsfinal[0] ))
                query = "insert into diahora values(%s, %s, %s, %s, (select max(cve_hor) from horario))"
                values = ( None, dia_a_entero(dias[i]), hsinicio[0], hsfinal[0] )
                cur.execute(query, values)
        else:
            for i in range(len(dias)):
                print(dias[i], "(", dia_a_entero(dias[i]), ") - ", hsinicio[i], " - ", hsfinal[i])
                # query = "insert into "


        mydb.commit()

        print("INSERION EXITOSA")
        return redirect(url_for('cargar_empleados'))
        # pass

    query = "select * from colonia"
    cur.execute(query)
    colonias = cur.fetchall()

    return render_template('empleados_registro.html', colonias = colonias)

def dia_a_entero(dia):
    if dia == "Lunes":
        return 1
    elif dia == "Martes":
        return 2
    elif dia == "Miercoles":
        return 3
    elif dia == "Jueves":
        return 4
    elif dia == "Viernes":
        return 5
    elif dia == "Sabado":
        return 6
    elif dia == "Domingo":
        return 7

def entero_a_dia(n):
    if n == 1:
        return "Lunes"
    if n == 2:
        return "Martes"
    if n == 3:
        return "Miércoles"
    if n == 4:
        return "Jueves"
    if n == 5:
        return "Viernes"
    if n == 6:
        return "Sábado"
    if n == 7:
        return "Domingo"

# --------------------- ALUMNOS --------------------- ## --------------------- s_ALUMNOS --------------------- #

# Ventana principal de alumnos
@app.route('/alumnos/')
def cargar_alumnos():
    query = "select a.cve_alu, concat(nom_per, ' ', ap_per, ' ', am_per) from grupo g join registroinscripcion ri on g.cve_gru=ri.cve_gru join folio f on ri.folio_insc=f.folio_fol join alumno a on f.cve_alu=a.cve_alu join persona p on a.curp_per=p.curp_per where curdate() between fechaini_gru and fechafin_gru"
    cur.execute(query)
    inscritos = cur.fetchall()

    # query = "select a.cve_alu, concat(nom_per, ' ', ap_per, ' ', am_per) from folio f join alumno a on f.cve_alu=a.cve_alu join persona p on a.curp_per=p.curp_per where not exists(select folio_fol, folio_insc from folio f, registroinscripcion ri where folio_fol=folio_insc)"
    # query = "select a.cve_alu, concat(nom_per, ' ', ap_per, ' ', am_per) from folio f join registroinscripcion ri on f.folio_fol!=ri.folio_insc join alumno a on f.cve_alu=a.cve_alu join persona p on a.curp_per=p.curp_per"
    query = "select f.cve_alu, concat(nom_per, ' ', ap_per, ' ', am_per), folio_fol from folio f join alumno a on f.cve_alu=a.cve_alu join persona p on a.curp_per=p.curp_per where not exists(select folio_insc from registroInscripcion ri where ri.folio_insc=f.folio_fol)"
    cur.execute(query)
    noInscritos = cur.fetchall()

    # query = "select cve_gru, concat(horaent_gru, ' - ', horasali_gru), concat(fechaini_gru, ' a ', fechafin_gru), nom_act, nombre_are, concat(nom_per, " ", ap_per, " ", am_per) from grupo g join actividad a on g.cve_act=a.cve_act join area ar on g.cve_are=ar.cve_are join empleado e on g.cve_emp=e.cve_emp join persona p on e.curp_per=p.curp_per where curdate() between fechaini_gru and fechafin_gru"
    query = "select g.cve_gru, concat(horaent_gru, ' - ', horasali_gru) as turno, concat(fechaini_gru, ' a ', fechafin_gru) as periodo, nom_act, nombre_are, concat(nom_per, ' ', ap_per, ' ', am_per) as docente, count(folio_insc) as cuenta, maxalumnos_gru as maxalumnos from grupo g join registroInscripcion ri on g.cve_gru=ri.cve_gru join actividad a on g.cve_act=a.cve_act join area ar on g.cve_are=ar.cve_are join empleado e on g.cve_emp=e.cve_emp join persona p on e.curp_per=p.curp_per where curdate() between fechaini_gru and fechafin_gru group by g.cve_gru having cuenta<=maxalumnos"
    cur.execute(query)
    gruposNoVacios = cur.fetchall()

    # select cve_gru from grupo where cve_gru not in (select cve_gru from registroinscripcion) AGREGA ESTOOOOOOOOOOOOOOOOOOOOOOOO
    # select cve_gru, concat(horaent_gru, ' - ', horasali_gru) as turno, concat(fechaini_gru, ' a ', fechafin_gru) as periodo, nom_act, nombre_are, concat(nom_per, ' ', ap_per, ' ', am_per) as docente, maxalumnos_gru from grupo g join actividad a on g.cve_act=a.cve_act join area ar on g.cve_are=ar.cve_are join empleado e on g.cve_emp=e.cve_emp join persona p on e.curp_per=p.curp_per where g.cve_gru not in (select cve_gru from registroinscripcion)
    # query = "select g.cve_gru, concat(horaent_gru, ' - ', horasali_gru) as turno, concat(fechaini_gru, ' a ', fechafin_gru) as periodo, nom_act, nombre_are, concat(nom_per, ' ', ap_per, ' ', am_per) as docente, maxalumnos_gru from grupo g join registroInscripcion ri on g.cve_gru!=ri.cve_gru join actividad a on g.cve_act=a.cve_act join area ar on g.cve_are=ar.cve_are join empleado e on g.cve_emp=e.cve_emp join persona p on e.curp_per=p.curp_per where curdate() between fechaini_gru and fechafin_gru"
    query = "select cve_gru, concat(horaent_gru, ' - ', horasali_gru) as turno, concat(fechaini_gru, ' a ', fechafin_gru) as periodo, nom_act, nombre_are, concat(nom_per, ' ', ap_per, ' ', am_per) as docente, maxalumnos_gru from grupo g join actividad a on g.cve_act=a.cve_act join area ar on g.cve_are=ar.cve_are join empleado e on g.cve_emp=e.cve_emp join persona p on e.curp_per=p.curp_per where g.cve_gru not in (select cve_gru from registroinscripcion)"
    cur.execute(query)
    gruposVacios = cur.fetchall()

    return render_template('alumnos.html', inscritos = inscritos, noInscritos = noInscritos, gruposNoVacios = gruposNoVacios, gruposVacios = gruposVacios)

@app.route('/alumno', methods=['POST'])
def alumno():
    data = request.form

    query = "select a.*, concat(p.nom_per, ' ', ap_per, ' ', am_per) as nombre, p.tel_per, p.fechanac_per, p.genero_per, concat(p.calle_per, ' ', p.orient_per, ' ', p.numero_per) as direccion from alumno a join persona p on a.curp_per=p.curp_per where a.cve_alu=" + data['clave']
    cur.execute(query)
    _alumno = cur.fetchall()

    alumno = _alumno[0]

    _genero = None

    for i in alumno[7]:
        _genero = i

    query = "select f.*, ac.nom_act from folio f join alumno a on f.cve_alu=a.cve_alu join actividad ac on f.cve_act=ac.cve_act where f.cve_alu=" + data['clave'] + " order by fecha_fol limit 1"
    cur.execute(query)
    folio = cur.fetchall()

    # query = "select cve_gru, concat(horaent_gru, ' - ', horasali_gru), concat(fechaini_gru, ' a ', fechafin_gru) from grupo where curdate() between fechaini_gru and fechafin_gru"
    # cur.execute(query)
    # grupos = cur.fetchall()

    print("folio = ", folio)

    tupla = {
        "alumno": [
            { "clave": alumno[0], "estatura": alumno[1], "peso": alumno[2] }
        ],
        "personales": [
            { "curp": alumno[3], "nombre": alumno[4], "tel": alumno[5], "fechanac": str(alumno[6]), "genero": _genero, "domicilio": alumno[8] }
        ],
        "folio": folio
    }

    # print(tupla)
    return tupla

@app.route('/alumnoInscribir', methods=['POST'])
def alumnoInscribir():
    detalles = request.form
    _folio = detalles['folio']
    _grupo = detalles['grupo']
    _fecha = detalles['fecha']
    _importe = detalles['importe']

    # print("detalles = ", detalles)

    query = "insert into registroInscripcion values(%s, %s, %s, %s, %s)"
    values = (_folio, _fecha, _importe, _importe, _grupo)

    # query = "insert into registroinscripcion values(%s, %s, %s, %s, %s)"
    # values = (data['folio'], data['fecha'], data['importe'], data['importe'], data['grupo'])

    cur.execute(query, values)
    mydb.commit()

    return "OK"

import time

# /registro-alumnos
@app.route('/alumnos/registrar', methods=['GET', 'POST'])
def cargar_alumnos_registro():
    if request.method == "POST":
        detalles = request.form
        _curp = detalles['curp']
        _nombre = detalles['nombre']
        _ap = detalles['ap']
        _am = detalles['am']
        _tel = detalles['tel']
        _fechanac = detalles['fechanac']
        _genero = detalles['genero']
        _calle = detalles['calle']
        _num = detalles['num']
        _orient = detalles['orient']
        _entrecalles = detalles['entrecalles']
        _col = detalles['col']

        query = "insert into persona values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
        values = (_curp, _nombre, _ap, _am, _tel, _fechanac, _genero, _calle, _num, _orient, _entrecalles, _col)

        cur.execute(query, values)

        _estatura = detalles['estatura']
        _peso = detalles['peso']

        query = "insert into alumno values (%s, %s, %s, %s)"
        values = (None, _estatura, _peso, _curp)

        cur.execute(query, values)
        # mydb.commit()

        _costo = detalles['costo']
        _act = detalles['act']

        query = "select max(cve_alu) from alumno"
        cur.execute(query)
        _alumno = cur.fetchall()

        alumno = _alumno[0]

        query = "insert into folio values(%s, %s, %s, %s, %s)"
        values = (None, time.strftime('%Y-%m-%d %H:%M:%S'), _costo, alumno[0], _act)

        cur.execute(query, values)
        mydb.commit()

        return redirect(url_for('cargar_alumnos'))

    query = "select * from colonia"
    cur.execute(query)
    colonias = cur.fetchall()

    query = "select cve_act, concat(nom_act, ' - ', tipo_act) from actividad"
    cur.execute(query)
    actividades = cur.fetchall()

    return render_template('alumnos_registro.html', colonias = colonias, actividades = actividades)

# --------------------- PROVEEDORES --------------------- ## --------------------- S_PROVEEDORES --------------------- #

# Ventana principal de proveedores
@app.route('/proveedores/')
def cargar_proveedores():
    query = "select * from proveedor"
    cur.execute(query)
    proveedores = cur.fetchall()

    return render_template('proveedores.html', proveedores = proveedores)

@app.route('/proveedor', methods=['POST'])
def proveedor():
    data = request.form

    query = "select cve_prov, empresa_prov, concat(calle_prov, ' ', orient_prov, ' ', num_prov) as domicilio, tel_prov, cve_col from proveedor where cve_prov=" + data['clave']
    cur.execute(query)
    _proveedor = cur.fetchall()

    proveedor = _proveedor[0]

    tupla = {
        "general": [
            { "clave": proveedor[0], "empresa": proveedor[1], "domicilio": proveedor[2], "tel": proveedor[3], "col": proveedor[4] }
        ]
    }

    return tupla

@app.route('/proveedores/registrar', methods=['GET', 'POST'])
def cargar_proveedores_registro():
    if request.method == "POST":
        detalles = request.form
        _empresa = detalles['empresa']
        _tel = detalles['tel']
        _calle = detalles['calle']
        _num = detalles['num']
        _orient = detalles['orient']
        _entrecalles = detalles['entrecalles']
        _col = detalles['col']

        query = "insert into proveedor values(%s, %s, %s, %s, %s, %s, %s, %s)"
        values = (None, _empresa, _calle, _num, _orient, _entrecalles, _tel, _col)

        cur.execute(query, values)
        mydb.commit()

        print("INSERCION EXITOSA")
        return redirect(url_for('cargar_proveedores'))

    query = "select * from colonia"
    cur.execute(query)
    colonias = cur.fetchall()

    return render_template('proveedores_registro.html', colonias = colonias)

# --------------------- MATERIALES --------------------- ## --------------------- S_MATERIALES --------------------- #

# Ventana principal de materiales
@app.route('/materiales/')
def cargar_materiales():
    query = "select * from material"
    cur.execute(query)
    materiales = cur.fetchall()
    return render_template('materiales.html', materiales = materiales)

@app.route('/material', methods=['POST'])
def material():
    data = request.form

    query = "select m.*, a.nom_act from material m join actividad a on m.cve_act=a.cve_act where m.cve_mat=" + data['clave']
    cur.execute(query)
    _material = cur.fetchall()

    material = _material[0]

    tupla = {
        "material": [
            { "clave": material[0], "nombre": material[1], "marca": material[2], "precio": material[3], "descripcion": material[4],
            "act": material[7]  }
        ]
    }

    return tupla

# /registro-materiales
@app.route('/materiales/registrar', methods=['GET', 'POST'])
def cargar_materiales_registro():
    if request.method == "POST":
        detalles = request.form
        _nombre = detalles['nombre']
        _marca = detalles['marca']
        _precio = detalles['precio']
        _actividad = detalles['actividad']
        _descripcion = detalles['descripcion']

        query = "insert into material values (%s, %s, %s, %s, %s, %s, %s)"
        values = (None, _nombre, _marca, _precio, _descripcion, "Prestable", _actividad)

        cur.execute(query, values)
        mydb.commit()

        print("INSERCION EXITOSA")
        pass

    query = "select cve_act, nom_act from actividad"
    cur.execute(query)
    
    actividades = cur.fetchall()

    return render_template('materiales_registro.html', actividades = actividades)

# /resurtido-materiales
@app.route('/materiales/suministrar', methods=['GET', 'POST'])
def cargar_materiales_resurtir():
    if request.method == "POST":
        detalles = request.form
        _material = detalles['material']
        _proveedor = detalles['proveedor']
        _cantidad = detalles['cantidad']
        _ppu = detalles['ppu']
        _fechaent = detalles['fechaent']

        query = "insert into entrada values (%s, %s, %s, %s, %s, %s)"
        values = (None, _cantidad, _ppu, _fechaent, _material, _proveedor)

        cur.execute(query, values)
        mydb.commit()

        print("INSERCION EXITOSA")
        pass

    query = "select * from material m join actividad a on m.cve_act=a.cve_act"
    cur.execute(query)
    materiales = cur.fetchall()

    query = "select * from proveedor p join colonia c on p.cve_col=c.cve_col"
    cur.execute(query)
    proveedores = cur.fetchall()

    query = "select nombre_mat, cantidad_ent, preciounidad_ent, empresa_prov, fechaent_ent from material m join entrada e on m.cve_mat=e.cve_mat join proveedor p on e.cve_prov=p.cve_prov order by fechaent_ent limit 5"
    cur.execute(query)
    listaMateriales = cur.fetchall()

    return render_template('materiales_resurtir.html', materiales = materiales, proveedores = proveedores, listaMateriales = listaMateriales)

# --------------------- SOLICITUDES --------------------- ## --------------------- s_SOLICITUDES --------------------- #

@app.route('/solicitudes/')
def cargar_solicitudes():
    query = "select cve_sol, concat(nom_per, ' ', ap_per, ' ', am_per) from solicitud s join persona p on s.curp_per=p.curp_per where cve_sol not in (select cve_pres from prestamo)"
    cur.execute(query)
    solicitudes = cur.fetchall()

    return render_template('solicitudes.html', solicitudes = solicitudes)

@app.route('/solicitud', methods=['POST'])
def solicitud():
    data = request.form

    query = "select cve_sol, concat(nom_per, ' ', ap_per, ' ', am_per), fecha_sol from solicitud s join persona p on s.curp_per=p.curp_per where cve_sol=" + str(data['clave'])
    cur.execute(query)
    resultados = cur.fetchall()

    _solicitud = resultados[0]

    query = "select nombre_mat, cantidad_rensolic from renglonsolicitud rs join material m on rs.cve_mat=m.cve_mat where cve_sol=" + str(data['clave'])
    cur.execute(query)
    solicitudes = cur.fetchall()

    solicitudesDict = []

    for solicitud in solicitudes:
        solicitudDict = {
            "material": solicitud[0],
            "cantidad": solicitud[1]
        }
        solicitudesDict.append(solicitudDict)

    tupla = {
        "solicitud": [
            { "clave": _solicitud[0], "solicitante": _solicitud[1], "fecha": str(_solicitud[2]) }
        ],
        "solicitudes": solicitudesDict
    }

    return tupla

@app.route('/solicitudes/solicitar', methods=['POST','GET'])
def cargar_materiales_solicitar():
    if request.method == "POST":
        detalles = request.form
        _curp = detalles['persona']
        print(detalles)

        cantidades = detalles.getlist('cantidadVal')
        materiales = detalles.getlist('materialVal')

        print(cantidades)
        print(materiales)

        query = "insert into solicitud values(%s, curdate(), %s)"
        values = (None, _curp)
        cur.execute(query, values)

        for i in range(len(materiales)):
            query = "insert into renglonsolicitud values(null, %s, %s, (select max(cve_sol) from solicitud))"
            values = (cantidades[i], materiales[i])
            cur.execute(query, values)

        mydb.commit()
        print("INSERCION EXITOSA")
        return redirect(url_for('cargar_solicitudes'))

        # query = "insert into prestamo values (%s, %s, %s, %s)"

        # consulta = "select p.curp_per from persona p join empleado e on p.curp_per = e.curp_per where cve_emp = %s and puesto = 'Docente' group by p.curp_per" %_docente
        # cur.execute(consulta)
        # resultado = cur.fetchall()

        # for registro in resultado:
        #     _curp = registro[0]

        # values = (None, _fechapres, _curp, _docente)
        # cur.execute(query, values)
        # mydb.commit()
        
        # query = "insert into renglonprestamo values (%s, %s, %s, %s)"
        # consulta = "select max(cve_pres) from prestamo"
        # cur.execute(consulta)
        # result = cur.fetchall()

        # for registro in result:
        #     _prestamo = registro[0]

        # values = (None, _cantidad, _material, _prestamo)
        # cur.execute(query, values)
        # mydb.commit()

    # query = "select e.cve_emp, concat(nom_per, ' ', ap_per, ' ', am_per) as nombre from persona p join empleado e where p.curp_per = e.curp_per and puesto='Docente'"
    query = " select p.curp_per, concat(nom_per, ' ', ap_per, ' ', am_per), concat(calle_per, ' ', orient_per, ' ', numero_per), tel_per, concat(puesto, '') from persona p join empleado e on p.curp_per=e.curp_per"
    cur.execute(query)
    empleados = cur.fetchall()

    query = "select p.curp_per, concat(nom_per, ' ', ap_per, ' ', am_per), concat(calle_per, ' ', orient_per, ' ', numero_per), tel_per from persona p join alumno a on p.curp_per=a.curp_per"
    cur.execute(query)
    alumnos = cur.fetchall()
        
    # query = "select e.cve_mat,  nombre_mat from material m join entrada e where m.cve_mat = e.cve_mat and cantidad_ent >=1 group by nombre_mat"
    query = "select e.cve_mat, nombre_mat, marca_mat, nom_act from material m join entrada e join actividad a on m.cve_act=a.cve_act where m.cve_mat = e.cve_mat and cantidad_ent >=1 group by nombre_mat"
    cur.execute(query)
    materiales = cur.fetchall()

    materialesAux = []
    for i in materiales:
        datos = []
        materialesAux.append(datos)
        for j in i:
            datos.append(j)

        print('materialNombre = ', i[1])
        cur.callproc('sp_materialdisponible', [i[1], ])
        # listaDisp = cur.stored_results()
        # disp = listaDisp[0].fetchall()
        # print("disp = ", disp)
        for resultado in cur.stored_results():
            listaDisp = resultado.fetchall()
            # print("disp = ", disp[0])
            for k in listaDisp[0]:
                datos.append(k)
            # datos.append(resultado.fetchall())

    print("materiales aux = ", materialesAux)

    return render_template('materiales_solicitar.html', empleados = empleados, alumnos = alumnos, materialesAux = materialesAux)

# --------------------- PRESTAMOS --------------------- ## --------------------- s_PRESTAMOS --------------------- #

@app.route('/prestamos/')
def cargar_prestamos():
    query = "select cve_pres, concat(nom_per, ' ', ap_per, ' ', am_per) from prestamo pr join persona p on pr.curp_per=p.curp_per where cve_pres not in (select cve_devo from devolucion)"
    cur.execute(query)
    prestamos = cur.fetchall()

    return render_template('prestamos.html', prestamos = prestamos)

@app.route('/pSolicitud', methods=['POST'])
def pSolicitud():
    data = request.form

    query = "select cve_rensolic, cantidad_rensolic, nombre_mat from renglonsolicitud rs join material m on rs.cve_mat=m.cve_mat where cve_sol=" + str(data['clave'])
    cur.execute(query)
    solicitudes = cur.fetchall()

    solicitudesDict = []

    for solicitud in solicitudes:
        solicitudDict = {
            "clave": solicitud[0],
            "cantidad": solicitud[1],
            "material": solicitud[2]
        }
        solicitudesDict.append(solicitudDict)

    tupla = {
        "solicitudes": solicitudesDict
    }

    return tupla

@app.route('/prestamos/prestar', methods=['GET', 'POST'])
def cargar_materiales_prestar():
    if request.method == "POST":
        detalles = request.form
        _solicitud = detalles['solicitud']

        query = "select curp_per from solicitud where cve_sol=" + str(_solicitud)
        cur.execute(query)
        resultados = cur.fetchall()

        solicitud = resultados[0]
        curp = solicitud[0]

        query = "select * from renglonsolicitud where cve_sol=" + str(_solicitud)
        cur.execute(query)
        materialSolicitado = cur.fetchall()

        # print(materialSolicitado)

        query = "insert into prestamo values(%s, curdate(), %s)"
        values = (_solicitud, curp)

        cur.execute(query, values)

        for material in materialSolicitado:
            query = "insert into renglonprestamo values(%s, %s, %s, %s)"
            values = (None, material[1], material[2], _solicitud)
            cur.execute(query, values)

        mydb.commit()
        print("INSERCION EXITOSA")
        return redirect(url_for('cargar_prestamos'))

    query = "select cve_sol, concat(fecha_sol, ''), concat(nom_per, ' ', ap_per, ' ', am_per), s.curp_per from solicitud s join persona p on s.curp_per=p.curp_per where cve_sol not in (select cve_pres from prestamo)"
    cur.execute(query)
    solicitudes = cur.fetchall()

    return render_template('materiales_prestar.html', solicitudes = solicitudes)

# --------------------- NOMINAS --------------------- ## --------------------- s_NOMINAS --------------------- #

@app.route('/nominas/')
def cargar_nominas():
    query = "select cve_retri, fecha_retri from retribucionempleado group by fecha_retri"
    cur.execute(query)
    nominas = cur.fetchall()

    return render_template('nominas.html', nominas = nominas)

@app.route('/nomina', methods=['POST'])
def nomina():
    cur.callproc('sp_pagoTrabajadores')

    for resultado in cur.stored_results():
        lista = resultado.fetchall()
        
        for i in lista:
            query = "insert into retribucionempleado values(%s, now(), %s, %s)"
            values = (None, i[0], i[2])
            cur.execute(query, values)

    mydb.commit()
    return "OK"

@app.route('/test', methods=['GET', 'POST'])
def test():
    if request.method == "POST":
        # detalles = request.form
        # print(detalles)

        # dias = detalles.getlist('dia')
        # hsinicio = detalles.getlist('hinicio')
        # hsfinal = detalles.getlist('hfinal')

        # print(dias)
        # print(hsinicio)
        # print(hsfinal)

        # for i in range(len(dias)):
        #     print(dias[i], " - ", hsinicio[i], " - ", hsfinal[i])

        query = "insert into test values(null, (select max(cve_emp) from empleado), now())"
        # values = (None, "wea")

        cur.execute(query)
        mydb.commit()

    return render_template('test.html')

# --------------------- REPORTES --------------------- ## --------------------- s_REPORTES --------------------- #

@app.route('/reportes/')
def cargar_reportes():
    query = "select cve_repmat, nombre_mat from reportematerial rm join material m on rm.cve_mat=m.cve_mat"
    cur.execute(query)
    materiales = cur.fetchall()

    return render_template('reportes.html', materiales = materiales)

@app.route('/reporte', methods=['POST'])
def reporte():
    data = request.form

    query = "select rm.*, nombre_mat from reportematerial rm join material m on rm.cve_mat=m.cve_mat where cve_repmat=" + str(data['clave'])
    cur.execute(query)
    resultados = cur.fetchall()

    reporte = resultados[0]

    tupla = {
        "reporte": [
            { "clave": reporte[0], "fecha": str(reporte[1]), "cantidad": reporte[2], "causa": reporte[3], "material": reporte[5] }
        ]
    }

    return tupla

@app.route('/reportes/registrar', methods=['GET', 'POST'])
def cargar_reportes_registrar():
    if request.method == "POST":
        detalles = request.form
        _fecha = detalles['fecha']
        _cantidad = detalles['cantidad']
        _causa = detalles['causa']
        _material = detalles['material']

        query = "insert into reportematerial values(%s, %s, %s, %s, %s)"
        values = (None, _fecha, _cantidad, _causa, _material)
        cur.execute(query, values)
        mydb.commit()
        print("INSERCION EXITOSA")
        return redirect(url_for('cargar_reportes'))

    # query = "select * from material m join actividad a on m.cve_act=a.cve_act"
    query = "select m.*, a.nom_act from material m join actividad a on m.cve_act=a.cve_act"
    cur.execute(query)
    materiales = cur.fetchall()

    return render_template('reportes_registrar.html', materiales = materiales)