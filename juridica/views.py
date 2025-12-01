from django.shortcuts import render, redirect, get_object_or_404
from .models import *
from django.db import transaction

def lista_registros(request):
    query = request.GET.get("q")
    
    if query:
        registros = RegistroJuridico.objects.filter(materia__icontains=query)
    else:
        registros = RegistroJuridico.objects.all()

    return render(request, "lista.html", {"registros": registros})


def crear_registro(request):
    if request.method == "POST":
        try:
            with transaction.atomic():
                # 1) Crear el registro jurídico
                registro = RegistroJuridico.objects.create(
                    folio=request.POST.get("folio", "").strip(),
                    oficio=request.POST.get("oficio", "").strip(),
                    materia=request.POST.get("materia", "").strip(),
                    fecha_oficio=request.POST.get("fecha_oficio"),      # viene como 'YYYY-MM-DD'
                    fecha_respuesta=request.POST.get("fecha_respuesta") or None,
                    respuesta=request.POST.get("respuesta", "").strip(),
                    asignacion=request.POST.get("asignacion", "").strip(),
                )

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

    return render(request, "formulario.html")


def editar_registro(request, id):
    registro = get_object_or_404(RegistroJuridico, id=id)

    if request.method == "POST":
        try:
            with transaction.atomic():
                # 1) Actualizar campos del registro
                registro.folio = request.POST.get("folio", "").strip()
                registro.oficio = request.POST.get("oficio", "").strip()
                registro.materia = request.POST.get("materia", "").strip()
                registro.fecha_oficio = request.POST.get("fecha_oficio")
                registro.fecha_respuesta = request.POST.get("fecha_respuesta") or None
                registro.respuesta = request.POST.get("respuesta", "").strip()
                registro.asignacion = request.POST.get("asignacion", "").strip()
                registro.save()

                # 2) Eliminar documentos marcados
                ids_eliminar = request.POST.getlist("eliminar_docs")  # vienen como strings

                for doc_id in ids_eliminar:
                    try:
                        doc = Documento.objects.get(id=doc_id, registro=registro)
                        doc.archivo.delete(save=False)  # borra el archivo físico
                        doc.delete()
                    except Documento.DoesNotExist:
                        pass

                # 3) Agregar nuevos documentos (si se subieron)
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



def eliminar_registro(request, id):
    registro = get_object_or_404(RegistroJuridico, id=id)
    registro.delete()
    return redirect("lista_registros")
