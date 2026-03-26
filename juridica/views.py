from django.shortcuts import render, redirect, get_object_or_404
from .models import *
from django.db import transaction
from django.views.decorators.csrf import csrf_exempt
from datetime import date, datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import smtplib
from .function import enviar_correo_smtp,obtener_perfil_usuario
from django.contrib import messages
from django.db.models import Max
from django.contrib.auth import authenticate, login as auth_login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import JsonResponse
import json

@login_required(login_url='login')




@login_required(login_url='login')
def lista_registros(request):
    query = request.GET.get("q")
    usuario = request.user
    perfiles = obtener_perfil_usuario(usuario)

    perfiles_nombres = list(perfiles.values_list("perfil__nombre", flat=True))

    perfil = perfiles_nombres[0] if perfiles_nombres else None

    if query:
        registros = RegistroJuridico.objects.filter(materia__icontains=query)
    else:
        registros = RegistroJuridico.objects.all()

    return render(request, "lista.html", {"registros": registros, "perfil": perfil})

ASIGNACIONES = [
    "Administración Municipal",
    "Alcaldía",
    "Delegación territorial",
    "Dirección de Administración y Finanzas",
    "Dirección de Asesoría Jurídica",
    "Dirección de Desarrollo Comunitario",
    "Dirección de Desarrollo Cultural",
    "Dirección de Género, Mujeres y Diversidades",
    "Dirección de Medioambiente",
    "Dirección de Obras Municipales",
    "Dirección de Operaciones",
    "Dirección de Seguridad Ciudadana",
    "Dirección de Tránsito y Transporte públicos",
    "Dirección de Vivienda, Barrio y Territorio",
    "Dirección desarrollo Económico y Cooperación Internacional",
    "Gabinete",
    "Juzgados",
    "SECPLA",
    "Otro",
]


@login_required(login_url='login')
def crear_registro(request):
    usuario = request.user

    if request.method == "POST":
        try:
            with transaction.atomic():
                # 1) Crear el registro jurídico
                # Determinar el valor de asignacion
                
                # Validar que el folio no exista (ignorando formato)
                folio_input = request.POST.get("folio", "").strip()
                
                # Extraer solo la primera parte del folio (antes del guión o espacio)
                if folio_input:
                    # Tomar solo los números/caracteres antes del primer guión o espacio
                    folio_principal = folio_input.split('-')[0].split()[0].strip()
                    folio_normalizado = ''.join(c for c in folio_principal if c.isalnum()).lower()

                    print(f"Validando folio: input={folio_input!r} principal={folio_principal!r} normalizado={folio_normalizado!r}")
                    
                    folio_existente = RegistroJuridico.objects.filter(folio__isnull=False)
                    for reg in folio_existente:
                        # Extraer la parte principal del folio en BD también
                        folio_db_principal = reg.folio.split('-')[0].split()[0].strip()
                        folio_db_normalizado = ''.join(c for c in folio_db_principal if c.isalnum()).lower()
                        if folio_normalizado == folio_db_normalizado:
                            messages.error(request, f"El folio {folio_principal} ya existe en el sistema.")
                            return render(request, "formulario.html", {"asignaciones": ASIGNACIONES, "error": f"El folio {folio_principal} ya existe en el sistema."})
                
                registro = RegistroJuridico.objects.create(
                    folio=folio_input,
                    oficio=request.POST.get("oficio", "").strip(),
                    materia=request.POST.get("materia", "").strip(),
                    fecha_oficio=request.POST.get("fecha_oficio"),
                    fecha_respuesta=request.POST.get("fecha_respuesta") or None,
                )

                asignaciones = request.POST.getlist("asignacion[]")
                otro = request.POST.get("asignacion_otro", "").strip()

                if otro:
                    asignaciones.append(otro)

                registro.asignaciones = asignaciones
                registro.save()

                # 2) Obtener TODOS los archivos enviados en "archivos"
                archivos = request.FILES.getlist("archivos")

                print("Archivos recibidos:", archivos)

                for archivo in archivos:
                    Documento.objects.create(
                        registro=registro,
                        archivo=archivo,
                        # nombre se autocompleta en el save() si lo dejas vacío
                    )

            return redirect("lista_registros")

        except Exception as e:
            # si quieres, puedes mandar mensaje de error al template
            # o usar messages.error(...)
            print("Error al crear registro o documentos:", e)
            return render(request, "formulario.html", {
                "error": "Ocurrió un problema al guardar el registro."
            })

    return render(request, "formulario.html", {
            "asignaciones": ASIGNACIONES,

        })

def logout_view(request):
    from django.contrib.auth import logout
    logout(request)
    return redirect("login")
    

@csrf_exempt
def registro_editar(request, id):
    registro = get_object_or_404(RegistroJuridico, id=id)
    


    if request.method == "POST":
        # campos simples
        registro.folio = request.POST.get("folio", "").strip()
        registro.oficio = request.POST.get("oficio", "").strip()
        registro.materia = request.POST.get("materia", "").strip()
        registro.fecha_oficio = request.POST.get("fecha_oficio") or None
        registro.fecha_respuesta = request.POST.get("fecha_respuesta") or None
        registro.dirigido_a = request.POST.get("dirigido_a", "").strip()
        registro.cc = request.POST.get("cc", "").strip()
        registro.respuesta = request.POST.get("respuesta", "").strip()

        # asignaciones (JSON)
        asignaciones = request.POST.getlist("asignacion[]")
        otro = request.POST.get("asignacion_otro", "").strip()
        if otro:
            # si marcaron "Otro" pero escribieron, guarda el texto como asignación real
            asignaciones = [a for a in asignaciones if a != "Otro"]
            asignaciones.append(otro)
        else:
            # si dejaron "Otro" marcado pero vacío, saca "Otro" para no guardar basura
            asignaciones = [a for a in asignaciones if a != "Otro"]

        # dedupe manteniendo orden
        seen = set()
        asignaciones = [a for a in asignaciones if a and (a not in seen and not seen.add(a))]

        registro.asignaciones = asignaciones

        # terminado (si lo editas en form con checkbox)
        registro.terminado = request.POST.get("terminado") == "on"

        # agregar nuevos documentos (NO se pueden “precargar”, solo agregar)
        nuevos_archivos = request.FILES.getlist("archivos")

        with transaction.atomic():
            registro.save()

            for f in nuevos_archivos:
                Documento.objects.create(
                    registro=registro,
                    archivo=f,
                    nombre=f.name
                )

        messages.success(request, "Registro actualizado.")
        return redirect("editar_registro", id=registro.id)

    # GET: precargar
    asignaciones_seleccionadas = registro.asignaciones or []
    # si hay una asignación que no está en lista, se considera “otro”
    set_base = set([a for a in ASIGNACIONES if a != "Otro"])
    otros = [a for a in asignaciones_seleccionadas if a not in set_base]
    otro_texto = ", ".join(otros) if otros else ""

    return render(request, "editar.html", {
        "registro": registro,
        "asignaciones": ASIGNACIONES,
        "asignaciones_seleccionadas": asignaciones_seleccionadas,
        "asignacion_otro_texto": otro_texto,
        "documentos": registro.documentos.all().order_by("-fecha_subida"),
    })

@login_required(login_url='login')
def documento_eliminar(request, doc_id):
    doc = get_object_or_404(Documento, pk=doc_id)
    reg_id = doc.registro_id

    # opcional: borrar archivo físico
    if doc.archivo:
        doc.archivo.delete(save=False)

    doc.delete()
    messages.success(request, "Documento eliminado.")
    return redirect("registro_editar", pk=reg_id)

@login_required(login_url='login')
@csrf_exempt
def reiterar_oficio(request, id):
    registro = get_object_or_404(RegistroJuridico, id=id)

    if request.method == "POST":
        usuario = request.POST.get("usuario", "").strip()
        contraseña = request.POST.get("contraseña", "").strip()
        dirigido = request.POST.get("dirigido", "").strip()
        copia = request.POST.get("copia", "").strip()
        respuesta = request.POST.get("respuesta", "").strip()
        archivos = request.FILES.getlist("archivos")

        # Validaciones mínimas (evita intentar SMTP con vacío)
        if not usuario or not contraseña:
            messages.error(request, "Falta usuario o contraseña.")
            return render(request, "reiterar.html", {"registro": registro})

        if not dirigido:
            messages.error(request, "Falta el/los destinatarios (Dirigido a).")
            return render(request, "reiterar.html", {"registro": registro})

        destinatarios = [e.strip() for e in dirigido.split(",") if e.strip()]
        cc = [e.strip() for e in copia.split(",") if e.strip()] if copia else []

        try:

            # 2) Envía correo fuera de la transacción
            print(f"[reiterar_oficio] Enviando correo. to={len(destinatarios)} cc={len(cc)} adj={len(archivos)} usuario={usuario!r}")
            enviar_correo_smtp(
                usuario=usuario,
                contraseña=contraseña,
                asunto="Respuesta a Oficio Jurídico",
                cuerpo=respuesta,
                destinatarios=destinatarios,
                cc=cc,
                archivos=archivos
            )
            print("[reiterar_oficio] Correo enviado OK")

            # 3) Mensaje Guardar el registro

            reitero = ReiterarJuridica.objects.create(
                registro=registro,
                respuesta=respuesta,
                correos=dirigido,
                copias_correos=copia
            )
            reitero.save()
            Archivo_reitero_Adjunto.objects.bulk_create([
                Archivo_reitero_Adjunto(reitero=reitero, archivo=f) for f in archivos
            ])


            messages.success(request, "Correo enviado correctamente.")
            return redirect("lista_registros")

        except Exception as e:
            # No ocultar el error con redirect ciego
            print(f"[reiterar_oficio] ERROR correo: {repr(e)}")
            messages.error(request, f"Error al enviar correo: {e}")
            return render(request, "reiterar.html", {"registro": registro})

    return render(request, "reiterar.html", {"registro": registro})

@login_required(login_url='login')
def eliminar_registro(request, id):
    registro = get_object_or_404(RegistroJuridico, id=id)
    registro.delete()
    return redirect("lista_registros")

# SUMARIOS
ETAPAS = [
    "1.- indagatoria o investigativo.",
    "2.- formulación de cargos o etapa acusatoria",
    "3.- periodo de descargos y/o periodo de prueba",
    "4.- informe del fiscal",
    "5.- Terminado",
]

SACCIONES = [
    "1.- Censura",
    "2.- Multa",
    "3.- Suspensión del empleo desde treinta Dias a tres meses",
    "4.- Destitución",
    "5.- Sobre Seguimiento"
]

@login_required(login_url='login')
def crear_registro_2(request):
    next_id = (RegistroSumario.objects.aggregate(m=Max("id"))["m"] or 0) + 1

    context = {
        "SACCIONES": SACCIONES,
        "registro_id": next_id,
    }
    if request.method == "POST":

        etapa_index = int(request.POST.getlist("sancion")[0]) - 1 if request.POST.getlist("sancion") else 0
        sancion = SACCIONES[etapa_index] if 0 <= etapa_index < len(SACCIONES) else ""

        registro = RegistroSumario.objects.create(
            Fecha_creacion=request.POST.get("fecha_creacion") or None,
            n_da=request.POST.get("n_da", "").strip(),
            fecha_da=request.POST.get("fecha_da") or None,
            fiscal_acargo=request.POST.get("fiscal", "").strip(),
            grado_fiscal=request.POST.get("grado_fiscal", "").strip(),

            materia=request.POST.get("materia", "").strip(),



            #vistal_fical
            oficio_fiscalia=request.POST.get("oficio_vista_fiscal", "").strip(),
            fecha_fiscalia=request.POST.get("fecha_vista_fiscal") or None,
            adjunto_fiscalia=request.FILES.get("adjunto_fiscalia"),


            #Notificacion fical

            fecha_notificacion_fiscal=request.POST.get("fecha_notificacion_fiscal") or None,
            adjunto_not_fiscalia=request.FILES.get("adjunto_not_fiscalia"),

            #Informe DAJ

            fecha_daj=request.POST.get("fecha_daj") or None,
            adjunto_daj=request.FILES.get("adjunto_daj"),
            
            # ------------------------------------

            sancion=sancion,
            adjunto_sancion=request.FILES.get("adjunto_sancion"),
            fecha_contrata=request.POST.get("fecha_contrata") or None,
            
            etapa = ETAPAS[0]
        )

        nombres = request.POST.getlist("nombre[]")
        grado = request.POST.getlist("grado[]")

        registro.nombre_apellido_grado_imputado = [
            {"nombre": n, "grado": g} for n, g in zip(nombres, grado)
        ]

        registro.save()
        return redirect("lista_registros")



    return render(request, "formulario_2.html", context)


@login_required(login_url='login')
@csrf_exempt
def editar_sumario(request, id):
    sumario = get_object_or_404(RegistroSumario, id=id)

    if request.method == "POST":
        etapa_index = int(request.POST.getlist("sancion")[0]) - 1 if request.POST.getlist("sancion") else -1
        sancion = SACCIONES[etapa_index] if 0 <= etapa_index < len(SACCIONES) else sumario.sancion

        sumario.Fecha_creacion = request.POST.get("fecha_creacion") or None
        sumario.n_da = request.POST.get("n_da", "").strip()
        sumario.fecha_da = request.POST.get("fecha_da") or None
        sumario.fiscal_acargo = request.POST.get("fiscal", "").strip()
        sumario.grado_fiscal = request.POST.get("grado_fiscal", "").strip()
        sumario.materia = request.POST.get("materia", "").strip()
        sumario.oficio_fiscalia = request.POST.get("oficio_vista_fiscal", "").strip()
        sumario.fecha_fiscalia = request.POST.get("fecha_vista_fiscal") or None
        sumario.fecha_notificacion_fiscal = request.POST.get("fecha_notificacion_fiscal") or None
        sumario.fecha_daj = request.POST.get("fecha_daj") or None
        sumario.sancion = sancion

        if request.FILES.get("adjunto_fiscalia"):
            sumario.adjunto_fiscalia = request.FILES.get("adjunto_fiscalia")
        if request.FILES.get("adjunto_not_fiscalia"):
            sumario.adjunto_not_fiscalia = request.FILES.get("adjunto_not_fiscalia")
        if request.FILES.get("adjunto_daj"):
            sumario.adjunto_daj = request.FILES.get("adjunto_daj")
        if request.FILES.get("adjunto_sancion"):
            sumario.adjunto_sancion = request.FILES.get("adjunto_sancion")

        nombres = request.POST.getlist("nombre[]")
        grados = request.POST.getlist("grado[]")
        sumario.nombre_apellido_grado_imputado = [
            {"nombre": n, "grado": g} for n, g in zip(nombres, grados)
        ]

        sumario.save()
        messages.success(request, "Sumario actualizado.")
        return redirect("editar_sumario", id=sumario.id)

    # GET: determine sancion index for pre-selection (1-based)
    sancion_index = None
    if sumario.sancion:
        try:
            sancion_index = SACCIONES.index(sumario.sancion) + 1
        except ValueError:
            sancion_index = None

    return render(request, "formulario_2.html", {
        "instance": sumario,
        "SACCIONES": SACCIONES,
        "sancion_index": sancion_index,
        "registro_id": sumario.id,
        "inculpados_json": json.dumps(sumario.nombre_apellido_grado_imputado or []),
    })


@login_required(login_url='login')
def eliminar_sumario(request, id):
    registro = get_object_or_404(RegistroSumario, id=id)
    registro.delete()
    return redirect("lista_registros")

def sumario_etapa(request, id):
    registro = get_object_or_404(RegistroJuridico, id=id)

    if request.method == "POST":
        usuario = request.POST.get("usuario", "").strip()
        contraseña = request.POST.get("contraseña", "").strip()
        dirigido = request.POST.get("dirigido", "").strip()
        copia = request.POST.get("copia", "").strip()
        respuesta = request.POST.get("respuesta", "").strip()
        archivos = request.FILES.getlist("archivos")

        # Validaciones mínimas (evita intentar SMTP con vacío)
        if not usuario or not contraseña:
            messages.error(request, "Falta usuario o contraseña.")
            return render(request, "reiterar.html", {"registro": registro})

        if not dirigido:
            messages.error(request, "Falta el/los destinatarios (Dirigido a).")
            return render(request, "reiterar.html", {"registro": registro})

        destinatarios = [e.strip() for e in dirigido.split(",") if e.strip()]
        cc = [e.strip() for e in copia.split(",") if e.strip()] if copia else []

        try:

            # 2) Envía correo fuera de la transacción
            print(f"[reiterar_oficio] Enviando correo. to={len(destinatarios)} cc={len(cc)} adj={len(archivos)} usuario={usuario!r}")
            enviar_correo_smtp(
                usuario=usuario,
                contraseña=contraseña,
                asunto="Respuesta a Oficio Jurídico",
                cuerpo=respuesta,
                destinatarios=destinatarios,
                cc=cc,
                archivos=archivos
            )
            print("[reiterar_oficio] Correo enviado OK")

            # 3) Mensaje Guardar el registro

            reitero = ReiterarJuridica.objects.create(
                registro=registro,
                respuesta=respuesta,
                correos=dirigido,
                copias_correos=copia
            )
            reitero.save()
            Archivo_reitero_Adjunto.objects.bulk_create([
                Archivo_reitero_Adjunto(reitero=reitero, archivo=f) for f in archivos
            ])


            messages.success(request, "Correo enviado correctamente.")
            return redirect("lista_registros")

        except Exception as e:
            # No ocultar el error con redirect ciego
            print(f"[reiterar_oficio] ERROR correo: {repr(e)}")
            messages.error(request, f"Error al enviar correo: {e}")
            return render(request, "reiterar.html", {"registro": registro})

    return render(request, "reiterar.html", {"registro": registro})

@csrf_exempt
def asignar_usuario(request, id=None):
    if request.method != "POST":
        return JsonResponse({"ok": False, "error": "Método no permitido"}, status=405)

    try:
        data = json.loads(request.body.decode("utf-8")) if request.body else {}
    except json.JSONDecodeError:
        data = {}

    registro_id = data.get("registro_id") or id or request.POST.get("registro_id")
    usuario_id = data.get("usuario_id") or request.POST.get("usuario_id")

    if not registro_id or not usuario_id:
        return JsonResponse({"ok": False, "error": "Faltan registro_id o usuario_id"}, status=400)

    try:
        registro = RegistroJuridico.objects.get(id=registro_id)
        usuario = User.objects.get(id=usuario_id)
    except RegistroJuridico.DoesNotExist:
        return JsonResponse({"ok": False, "error": "Registro no encontrado"}, status=404)
    except User.DoesNotExist:
        return JsonResponse({"ok": False, "error": "Usuario no encontrado"}, status=404)

    registro.funcionario_asignado = usuario
    registro.save(update_fields=["funcionario_asignado"])

    return JsonResponse(
        {"ok": True, "message": f"Usuario {usuario.username} asignado.", "registro_id": registro.id}
    )

def reiterar_sumario(request, id):
    sumario = get_object_or_404(RegistroSumario, id=id)

    if request.method == "POST":
        usuario = request.POST.get("usuario", "").strip()
        contraseña = request.POST.get("contraseña", "").strip()
        dirigido = request.POST.get("dirigido", "").strip()
        copia = request.POST.get("copia", "").strip()
        respuesta = request.POST.get("respuesta", "").strip()
        archivos = request.FILES.getlist("archivos")

        # Validaciones mínimas (evita intentar SMTP con vacío)
        if not usuario or not contraseña:
            messages.error(request, "Falta usuario o contraseña.")
            return render(request, "reiterar.html", {"sumario": sumario})

        if not dirigido:
            messages.error(request, "Falta el/los destinatarios (Dirigido a).")
            return render(request, "reiterar.html", {"sumario": sumario})

        destinatarios = [e.strip() for e in dirigido.split(",") if e.strip()]
        cc = [e.strip() for e in copia.split(",") if e.strip()] if copia else []

        try:

            # 2) Envía correo fuera de la transacción
            print(f"[reiterar_oficio] Enviando correo. to={len(destinatarios)} cc={len(cc)} adj={len(archivos)} usuario={usuario!r}")
            enviar_correo_smtp(
                usuario=usuario,
                contraseña=contraseña,
                asunto="Estado de Sumario Administrativo",
                cuerpo=respuesta,
                destinatarios=destinatarios,
                cc=cc,
                archivos=archivos
                
            )
            print("[reiterar_oficio] Correo enviado OK")

            # 3) Mensaje Guardar el registro

            reitero = ReiterarSumario.objects.create(
                sumario=sumario,
                respuesta=respuesta,
                correos=dirigido,
                copias_correos=copia,
                etapa = sumario.etapa
            )
            reitero.save()
            Archivo_reitero_sumario_Adjunto.objects.bulk_create([
                Archivo_reitero_sumario_Adjunto(reitero=reitero, archivo=f) for f in archivos
            ])


            messages.success(request, "Correo enviado correctamente.")
            return redirect("lista_registros")

        except Exception as e:
            # No ocultar el error con redirect ciego
            print(f"[reiterar_oficio] ERROR correo: {repr(e)}")
            messages.error(request, f"Error al enviar correo: {e}")
            return render(request, "reiterar.html", {"sumario": sumario})

    return render(request, "reiterar.html", {"sumario": sumario})

@csrf_exempt
def login(request):
    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "").strip()
        
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            auth_login(request, user)
            return redirect("lista_registros")
        else:
            messages.error(request, "Usuario o contraseña inválidos.")
            return render(request, "login.html")
    
    return render(request, "login.html")