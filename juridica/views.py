from django.shortcuts import render, redirect, get_object_or_404
from .models import *
from django.db import transaction
from django.views.decorators.csrf import csrf_exempt
from datetime import date, datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import smtplib
from .function import enviar_correo_smtp
from django.contrib import messages

def lista_registros(request):
    query = request.GET.get("q")
    
    if query:
        registros = RegistroJuridico.objects.filter(materia__icontains=query)
    else:
        registros = RegistroJuridico.objects.all()

    return render(request, "lista.html", {"registros": registros})

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

@csrf_exempt
def crear_registro(request):
    if request.method == "POST":
        try:
            with transaction.atomic():
                # 1) Crear el registro jurídico
                # Determinar el valor de asignacion
                
                registro = RegistroJuridico.objects.create(
                    folio=request.POST.get("folio", "").strip(),
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
            "asignaciones": ASIGNACIONES
        })

def crear_registro_2(request):


    return render(request, "formulario_2.html")

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

def documento_eliminar(request, doc_id):
    doc = get_object_or_404(Documento, pk=doc_id)
    reg_id = doc.registro_id

    # opcional: borrar archivo físico
    if doc.archivo:
        doc.archivo.delete(save=False)

    doc.delete()
    messages.success(request, "Documento eliminado.")
    return redirect("registro_editar", pk=reg_id)


@csrf_exempt
def reiterar_oficio(request, id):
    registro = get_object_or_404(RegistroJuridico, id=id)

    if request.method == "POST":
        usuario = request.POST.get("usuario", "").strip()
        contraseña = request.POST.get("contraseña", "").strip()
        dirigido = request.POST.get("dirigido", "").strip()
        copia = request.POST.get("copia", "").strip()
        respuesta = request.POST.get("respuesta", "").strip()
        archivos = request.FILES.getlist("adjuntos")

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
            # 1) Guarda cambios en DB rápido
            with transaction.atomic():
                registro.dirigido_a = dirigido
                registro.cc = copia
                registro.respuesta = respuesta
                registro.save()

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

            messages.success(request, "Correo enviado correctamente.")
            return redirect("lista_registros")

        except Exception as e:
            # No ocultar el error con redirect ciego
            print(f"[reiterar_oficio] ERROR correo: {repr(e)}")
            messages.error(request, f"Error al enviar correo: {e}")
            return render(request, "reiterar.html", {"registro": registro})

    return render(request, "reiterar.html", {"registro": registro})


@csrf_exempt
def eliminar_registro(request, id):
    registro = get_object_or_404(RegistroJuridico, id=id)
    registro.delete()
    return redirect("lista_registros")

@csrf_exempt
def login(request):
    print("Login view accessed")
    if request.method == "POST":
        print("Login view accessed")

        return redirect("lista_registros")

    return render(request, "login.html")