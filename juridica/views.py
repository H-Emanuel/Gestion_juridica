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

@csrf_exempt
def editar_registro(request, id):
    registro = get_object_or_404(RegistroJuridico, id=id)

    if request.method == "POST":
        try:
            with transaction.atomic():
                registro.folio = request.POST.get("folio", "").strip()
                registro.oficio = request.POST.get("oficio", "").strip()
                registro.materia = request.POST.get("materia", "").strip()
                registro.fecha_oficio = request.POST.get("fecha_oficio")
                registro.fecha_respuesta = request.POST.get("fecha_respuesta") or None
                registro.respuesta = request.POST.get("respuesta", "").strip()
                registro.asignacion = request.POST.get("asignacion", "").strip()
                registro.save()

                ids_eliminar = request.POST.getlist("eliminar_docs")  # vienen como strings

                for doc_id in ids_eliminar:
                    try:
                        doc = Documento.objects.get(id=doc_id, registro=registro)
                        doc.archivo.delete(save=False)  # borra el archivo físico
                        doc.delete()
                    except Documento.DoesNotExist:
                        pass

                archivos_nuevos = request.FILES.getlist("archivos")
                for archivo in archivos_nuevos:
                    Documento.objects.create(
                        registro=registro,
                        archivo=archivo
                    )

            return redirect("lista_registros")

        except Exception as e:
            print("Error al editar registro:", e)
            return render(request, "editar.html", {
                "registro": registro,
                "error": "Ocurrió un problema al actualizar el registro."
            })

    # GET → mostrar formulario de edición
    return render(request, "editar.html", {
        "registro": registro
        # no hace falta pasar documentos, se acceden como registro.documentos.all
    })


@csrf_exempt
def reiterar_oficio(request, id):
    registro = get_object_or_404(RegistroJuridico, id=id)
    
    if request.method == "POST":
        try:
            with transaction.atomic():
                print( "Procesando formulario de reiterar_oficio..." )
                usuario = request.POST.get("usuario", "").strip()
                contraseña = request.POST.get("contraseña", "").strip()
                dirigido = request.POST.get("dirigido", "").strip()
                copia = request.POST.get("copia", "").strip()
                respuesta = request.POST.get("respuesta", "").strip()

                archivos = request.FILES.getlist("archivos")

                destinatarios = [e.strip() for e in dirigido.split(",") if e.strip()]
                cc = [e.strip() for e in copia.split(",") if e.strip()] if copia else []

                enviar_correo_smtp(
                    usuario=usuario,
                    contraseña=contraseña,
                    asunto="Respuesta a Oficio Jurídico",
                    cuerpo=respuesta,
                    destinatarios=destinatarios,
                    cc=cc,
                    archivos=archivos
                )

                return redirect("lista_registros")

        except Exception as e:
            messages.error(request, f"Error al enviar correo: {e}")
            return redirect("lista_registros")

    
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