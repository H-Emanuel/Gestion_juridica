from juridica.views import ETAPAS

from .models import *
from django.db.models import Q
from django.core.paginator import Paginator
from datetime import date
from django.views.decorators.csrf import csrf_exempt
from datetime import date, timedelta
import requests
from django.http import JsonResponse
from django.shortcuts import get_object_or_404

@csrf_exempt
def registro_detalle_api(request, pk):
    r = get_object_or_404(RegistroJuridico, pk=pk)

    # RespuestaJuridica: puede no existir (OneToOne)
    try:
        resp = r.respuesta_juridica
        respuesta_data = {
            "id": resp.id,
            "respuesta": resp.respuesta,
            "fecha_termino": resp.fecha_termino.isoformat() if resp.fecha_termino else None,
            "archivo": resp.archivo.url if resp.archivo else None,
        }
    except RespuestaJuridica.DoesNotExist:
        respuesta_data = None

    # ReiterarJuridica: puede no existir (FK)
    reiteraciones = []
    for reitero in r.reiteraciones.all().order_by("-fecha_de_envio"):
        reitero_data = {
            "respuesta": reitero.respuesta,
            "correos": reitero.correos,
            "copias_correos": reitero.copias_correos,
            "fecha_de_envio": reitero.fecha_de_envio.isoformat() if reitero.fecha_de_envio else None,
            "archivos": [
                {
                    "id": archivo.id,
                    "archivo": archivo.archivo.url if archivo.archivo else None,
                } for archivo in reitero.archivos_reitero.all()
            ]
        }
        reiteraciones.append(reitero_data)

    # Documentos: puede ser lista vacía (FK)
    documentos = []
    for d in r.documentos.all().order_by("-fecha_subida"):
        documentos.append({
            "id": d.id,
            "nombre": d.nombre,
            "fecha_subida": d.fecha_subida.isoformat() if d.fecha_subida else None,
            "archivo": d.archivo.url if d.archivo else None,
        })

    data = {
        "id": r.id,
        "folio": r.folio,
        "oficio": r.oficio,
        "materia": r.materia,
        "fecha_oficio": r.fecha_oficio.isoformat() if r.fecha_oficio else None,
        "fecha_respuesta": r.fecha_respuesta.isoformat() if r.fecha_respuesta else None,
        "asignaciones": r.asignaciones or [],
        "terminado": r.terminado,
        "dirigido_a": r.dirigido_a,
        "cc": r.cc,
        "respuesta": r.respuesta,
        "dias_transcurridos": r.dias_transcurridos,
        "requiere_alerta": r.requiere_alerta,
        "respuesta_juridica": respuesta_data,   # null si no hay
        "documentos": documentos,               # [] si no hay
        "reiteraciones": reiteraciones,          # [] si no hay
    }

    return JsonResponse(data, json_dumps_params={"ensure_ascii": False})

@csrf_exempt
def RegistroJuridico_list(request):
    try:
        draw = int(request.GET.get("draw", 1))
        start = int(request.GET.get("start", 0))
        length = int(request.GET.get("length", 10))
        search_value = request.GET.get("search[value]", "")

        order_column_index = int(request.GET.get("order[0][column]", 0))
        order_dir = request.GET.get("order[0][dir]", "asc")

        columns = [
            "folio",
            "oficio",
            "asignaciones",
            "fecha_oficio",
            "fecha_respuesta",
            "asignacion",
            "N° de reiteraciones",
        ]

        if order_column_index < 0 or order_column_index >= len(columns):
            order_column_index = 0

        order_column = columns[order_column_index]
        if order_dir == "desc":
            order_column = f"-{order_column}"

        user = request.user
        
        # Verificar si el usuario es Admin
        try:
            user_perfil = UsuarioPerfil.objects.get(usuario=user)
            es_admin = user_perfil.perfil.nombre == 'admin'
        except UsuarioPerfil.DoesNotExist:
            es_admin = False
        
        if es_admin:
            registros = RegistroJuridico.objects.filter(terminado=False)
        else:
            registros = RegistroJuridico.objects.filter(
            terminado=False,
            funcionario_asignado=user
            )

        if search_value:
            registros = registros.filter(
                Q(folio__icontains=search_value) |
                Q(oficio__icontains=search_value) |
                Q(asignaciones__icontains=search_value)
            )

        total_records = RegistroJuridico.objects.count()
        total_filtered = registros.count()

        registros = registros.order_by(order_column)

        paginator = Paginator(registros, length)
        page_number = (start // length) + 1
        page = paginator.get_page(page_number)

        data = []
        try:
            resp = requests.get("https://api.boostr.cl/holidays.json", timeout=5)
            resp.raise_for_status()
            holidays = {item["date"] for item in resp.json()}  # "YYYY-MM-DD"
        except Exception:
            holidays = set()

        for r in page:
            if r.fecha_respuesta:
                base = date.today()
                days = 0
                current = r.fecha_respuesta

                # fecha_respuesta en el futuro => positivo
                if current > base:
                    while current > base:
                        if current.weekday() < 5 and current.strftime("%Y-%m-%d") not in holidays:
                            days += 1
                        current -= timedelta(days=1)

                # fecha_respuesta en el pasado => negativo
                elif current < base:
                    while current < base:
                        if current.weekday() < 5 and current.strftime("%Y-%m-%d") not in holidays:
                            days -= 1
                        current += timedelta(days=1)

                # fecha_respuesta == hoy
                else:
                    days = 0
            else:
                days = None

            data.append({
                "id": r.id,
                "revision": r.terminado_funcinario,
                "folio": r.folio,
                "oficio": r.oficio,
                "asignaciones": r.asignaciones,  # truncamos en el frontend
                "fecha_oficio": r.fecha_oficio.strftime("%d-%m-%Y") if r.fecha_oficio else "",
                "fecha_respuesta": r.fecha_respuesta.strftime("%d-%m-%Y") if r.fecha_respuesta else "—",
                "dias_transcurridos": days,
                "reiteraciones": r.reiteraciones.count(),
                "funcionario_asignado": r.funcionario_asignado.username if r.funcionario_asignado else "No asignado",
            })

        response = {
            "draw": draw,
            "recordsTotal": total_records,
            "recordsFiltered": total_filtered,
            "data": data,
        }

        return JsonResponse(response, safe=False)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

@csrf_exempt
def RegistroJuridico_terminado_list(request):
    try:
        draw = int(request.GET.get("draw", 1))
        start = int(request.GET.get("start", 0))
        length = int(request.GET.get("length", 10))
        search_value = request.GET.get("search[value]", "")

        order_column_index = int(request.GET.get("order[0][column]", 0))
        order_dir = request.GET.get("order[0][dir]", "asc")

        columns = [
            "folio",
            "oficio",
            "asignaciones",
            "fecha_oficio",
            "fecha_respuesta",
            "N° de reiteraciones",
        ]

        if order_column_index < 0 or order_column_index >= len(columns):
            order_column_index = 0

        order_column = columns[order_column_index]
        if order_dir == "desc":
            order_column = f"-{order_column}"

        user = request.user

        try:
            user_perfil = UsuarioPerfil.objects.get(usuario=user)
            es_admin = user_perfil.perfil.nombre == 'admin'
        except UsuarioPerfil.DoesNotExist:
            es_admin = False
        
        if es_admin:
            registros = RegistroJuridico.objects.filter(terminado=True)
        else:
            registros = RegistroJuridico.objects.filter(
            terminado=True,
            funcionario_asignado=user
            )

        if search_value:
            registros = registros.filter(
                Q(folio__icontains=search_value) |
                Q(oficio__icontains=search_value) |
                Q(asignaciones__icontains=search_value)
                )

        total_records = RegistroJuridico.objects.count()
        total_filtered = registros.count()

        registros = registros.order_by(order_column)

        paginator = Paginator(registros, length)
        page_number = (start // length) + 1
        page = paginator.get_page(page_number)

        data = []
        for r in page:
            if r.fecha_oficio:
                base = date.today()
                dias = (base - r.fecha_oficio).days
            else:
                dias = None

            data.append({
                "id": r.id,
                "folio": r.folio,
                "oficio": r.oficio,
                "asignaciones": r.asignaciones,  # truncamos en el frontend
                "fecha_oficio": r.fecha_oficio.strftime("%d-%m-%Y") if r.fecha_oficio else "",
                "fecha_respuesta": r.fecha_respuesta.strftime("%d-%m-%Y") if r.fecha_respuesta else "—",
                "dias_transcurridos": dias,
                "reiteraciones": r.reiteraciones.count(),

            })

        response = {
            "draw": draw,
            "recordsTotal": total_records,
            "recordsFiltered": total_filtered,
            "data": data,
        }

        return JsonResponse(response, safe=False)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

@csrf_exempt
def oficio_respodido(request, pk):
    
    try:
        registro = RegistroJuridico.objects.get(id=pk)
        registro.terminado = True
        registro.save()

        respuesta_text = request.POST.get("respuesta", "")
        archivo = request.FILES.get("archivo")

        RespuestaJuridica.objects.create(
            registro=registro,
            respuesta=respuesta_text,
            fecha_termino=date.today(),
            archivo=archivo
        )
        return JsonResponse({
                "folio": registro.folio,
                "oficio": registro.oficio,
            })
    except RegistroJuridico.DoesNotExist:
        return JsonResponse({"error": "Registro no encontrado."}, status=404)
    
@csrf_exempt
def RegistroSumario_list(request):
    try:
        draw = int(request.GET.get("draw", 1))
        start = int(request.GET.get("start", 0))
        length = int(request.GET.get("length", 10))
        search_value = request.GET.get("search[value]", "")

        order_column_index = int(request.GET.get("order[0][column]", 0))
        order_dir = request.GET.get("order[0][dir]", "asc")

        columns = [
            "id",
            "Fecha_creacion",
            "n_da",
            "fiscal_acargo",
        ]

        if order_column_index < 0 or order_column_index >= len(columns):
            order_column_index = 0

        order_column = columns[order_column_index]
        if order_dir == "desc":
            order_column = f"-{order_column}"

        registros = RegistroSumario.objects.filter(finalizado=False)

        if search_value:
            registros = registros.filter(
                Q(id__icontains=search_value) |
                Q(Fecha_creacion__icontains=search_value) |
                Q(n_da__icontains=search_value) |
                Q(fiscal_acargo__icontains=search_value)
            )

        total_records = RegistroSumario.objects.count()
        total_filtered = registros.count()

        registros = registros.order_by(order_column)

        paginator = Paginator(registros, length)
        page_number = (start // length) + 1
        page = paginator.get_page(page_number)

        data = []
        try:
            resp = requests.get("https://api.boostr.cl/holidays.json", timeout=5)
            resp.raise_for_status()
            holidays = {item["date"] for item in resp.json()}  # "YYYY-MM-DD"
        except Exception:
            holidays = set()

        for r in page:
            if r.Fecha_creacion:
                base = date.today()
                dias = 0
                current = r.Fecha_creacion

                while current < base:
                    # solo lunes-viernes y NO feriado
                    if current.weekday() < 5 and current.strftime("%Y-%m-%d") not in holidays:
                        dias -= 1

                    # SIEMPRE avanzar 1 día
                    current += timedelta(days=1)
            else:
                dias = None


            data.append({
                "id": r.id,
                "Fecha_creacion": r.Fecha_creacion.strftime("%d-%m-%Y") if r.Fecha_creacion else "",
                "n_da": r.n_da,
                "fiscal_acargo": r.fiscal_acargo,
            })

        response = {
            "draw": draw,
            "recordsTotal": total_records,
            "recordsFiltered": total_filtered,
            "data": data,
        }

        return JsonResponse(response, safe=False)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
    
@csrf_exempt
def respondido(request, pk):
    try:
        registro = RegistroJuridico.objects.get(id=pk)
        registro.terminado_funcinario = True
        registro.save()
        return JsonResponse({
                "id": registro.id,
            })
    except RegistroJuridico.DoesNotExist:
        return JsonResponse({"error": "Registro no encontrado."}, status=404)
    
@csrf_exempt
def rechazado(request, pk):
    try:
        registro = RegistroJuridico.objects.get(id=pk)
        registro.terminado_funcinario = False
        registro.save()
        return JsonResponse({
                "id": registro.id,
            })
    except RegistroJuridico.DoesNotExist:
        return JsonResponse({"error": "Registro no encontrado."}, status=404)

@csrf_exempt
def sumario_detalle(request, pk):
    r = get_object_or_404(RegistroSumario, pk=pk)

    # Reiteraciones: puede ser lista vacía (FK)
    reiteraciones = []
    for reitero in r.reiteraciones_sumario.all().order_by("-fecha_de_envio"):
        reitero_data = {
            "etapa": reitero.etapa,
            "respuesta": reitero.respuesta,
            "correos": reitero.correos,
            "copias_correos": reitero.copias_correos,
            "fecha_de_envio": reitero.fecha_de_envio.isoformat() if reitero.fecha_de_envio else None,
            "documentos": [
                {
                    "id": archivo.id,
                    "archivo": archivo.archivo.url if archivo.archivo else None,
                } for archivo in reitero.documentos_sumario_reitero.all()
            ]
        }
        reiteraciones.append(reitero_data)

    # Documentos: puede ser lista vacía (FK)
    documentos = []
    for d in r.documentos_sumario.all().order_by("-fecha_subida"):
        documentos.append({
            "id": d.id,
            "nombre": d.nombre,
            "fecha_subida": d.fecha_subida.isoformat() if d.fecha_subida else None,
            "archivo": d.archivo.url if d.archivo else None,
        })

    data = {
        "id": r.id,
        "fecha_creacion": r.Fecha_creacion.isoformat() if r.Fecha_creacion else None,
        "n_da": r.n_da,
        "fecha_da": r.fecha_da.isoformat() if r.fecha_da else None,
        "fiscal_acargo": r.fiscal_acargo,
        "grado_fiscal": r.grado_fiscal,
        "materia": r.materia,
        "nombre_apellido_grado_imputado": r.nombre_apellido_grado_imputado or [],
        "oficio_fiscalia": r.oficio_fiscalia,
        "fecha_fiscalia": r.fecha_fiscalia.isoformat() if r.fecha_fiscalia else None,
        "adjunto_fiscalia": r.adjunto_fiscalia.url if r.adjunto_fiscalia else None,
        "oficio_juridico": r.oficio_juridico,
        "fecha_notificacion_fiscal": r.fecha_notificacion_fiscal.isoformat() if r.fecha_notificacion_fiscal else None,
        "adjunto_not_fiscalia": r.adjunto_not_fiscalia.url if r.adjunto_not_fiscalia else None,
        "fecha_daj": r.fecha_daj.isoformat() if r.fecha_daj else None,
        "adjunto_daj": r.adjunto_daj.url if r.adjunto_daj else None,
        "sancion": r.sancion,
        "adjunto_sancion": r.adjunto_sancion.url if r.adjunto_sancion else None,
        "fecha_contrata": r.fecha_contrata.isoformat() if r.fecha_contrata else None,
        "oficio_adjunto": r.oficio_adjunto.url if r.oficio_adjunto else None,
        "oficio_fecha": r.oficio_fecha.isoformat() if r.oficio_fecha else None,
        "etapa": r.etapa,
        "archivo_e_1": r.archivo_e_1.url if r.archivo_e_1 else None,
        "archivo_e_2": r.archivo_e_2,
        "archivo_e_3": r.archivo_e_3,
        "archivo_e_4": r.archivo_e_4.url if r.archivo_e_4 else None,
        "finalizado": r.finalizado,
        "respuesta": r.respuesta,
        "archivo_final": r.archivo_final.url if r.archivo_final else None,
        "reiteraciones": reiteraciones,
        "documentos": documentos,
    }

    return JsonResponse(data, json_dumps_params={"ensure_ascii": False})

@csrf_exempt
def sumario_etapa(request, pk):
    sumario = get_object_or_404(RegistroSumario, pk=pk)

    data = {
        "archivo_1": sumario.archivo_e_1.url if sumario.archivo_e_1 else None,
        "archivo_2": sumario.archivo_e_2,
        "archivo_3": sumario.archivo_e_3,
        "archivo_4": sumario.archivo_e_4.url if sumario.archivo_e_4 else None,
    }
    return JsonResponse(data, json_dumps_params={"ensure_ascii": False})

@csrf_exempt
def guardarEtapas(request, pk):
    if request.method == "POST":
        sumario = get_object_or_404(RegistroSumario, pk=pk)

        # Etapa 1 y 4: archivos
        archivo_1 = request.FILES.get("etapa_1")
        print (f"Archivo etapa 1 recibido: {archivo_1}")
        if archivo_1:
            sumario.archivo_e_1 = archivo_1

        archivo_4 = request.FILES.get("etapa_4")
        print (f"Archivo etapa 4 recibido: {archivo_4}")
        if archivo_4:
            sumario.archivo_e_4 = archivo_4

        # Etapa 2 y 3: booleanos
        etapa_2 = request.POST.get("etapa_2") == "true"
        etapa_3 = request.POST.get("etapa_3") == "true"
        
        sumario.archivo_e_2 = etapa_2
        sumario.archivo_e_3 = etapa_3

        if sumario.archivo_e_1:
            sumario.etapa = ETAPAS[1]

        if etapa_2:
            sumario.etapa = ETAPAS[2]

        if etapa_3:
            sumario.etapa = ETAPAS[3]

        if sumario.archivo_e_4:
            sumario.etapa = ETAPAS[4]

        sumario.save()

        return JsonResponse({"mensaje": "Etapas guardadas exitosamente."})
    else:
        return JsonResponse({"error": "Método no permitido."}, status=405)

@csrf_exempt
def terminonio_sumario(request, id):
    try:
        sumario = RegistroSumario.objects.get(id=id)
        sumario.finalizado = True

        sumario.respuesta = request.POST.get("respuesta", "")
        sumario.archivo_final = request.FILES.get("archivo")
        sumario.save()
        
        return JsonResponse({
                "id": sumario.id,
            })
    except RegistroSumario.DoesNotExist:
        return JsonResponse({"error": "Registro no encontrado."}, status=404)

@csrf_exempt
def Usuario_list(request):
    
    try:
        usuarios = UsuarioPerfil.objects.filter(perfil_id=2)
        data = [
            {
            "id": u.usuario.id,
            "username": u.usuario.username,
            "email": u.usuario.email,
            "perfil": u.perfil.nombre if u.perfil else None,
            "fecha_asignacion": u.fecha_asignacion.isoformat() if u.fecha_asignacion else None,
            }
            for u in usuarios
        ]
       
        return JsonResponse(data, safe=False)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
    

@csrf_exempt
def RegistroSumario_terminado_list(request):
    try:
        draw = int(request.GET.get("draw", 1))
        start = int(request.GET.get("start", 0))
        length = int(request.GET.get("length", 10))
        search_value = request.GET.get("search[value]", "")

        order_column_index = int(request.GET.get("order[0][column]", 0))
        order_dir = request.GET.get("order[0][dir]", "asc")

        columns = [
            "id",
            "Fecha_creacion",
            "n_da",
            "fiscal_acargo",
        ]

        if order_column_index < 0 or order_column_index >= len(columns):
            order_column_index = 0

        order_column = columns[order_column_index]
        if order_dir == "desc":
            order_column = f"-{order_column}"

        registros = RegistroSumario.objects.filter(finalizado=True)

        if search_value:
            registros = registros.filter(
                Q(id__icontains=search_value) |
                Q(Fecha_creacion__icontains=search_value) |
                Q(n_da__icontains=search_value) |
                Q(fiscal_acargo__icontains=search_value)
            )

        total_records = RegistroSumario.objects.count()
        total_filtered = registros.count()

        registros = registros.order_by(order_column)

        paginator = Paginator(registros, length)
        page_number = (start // length) + 1
        page = paginator.get_page(page_number)

        data = []
        try:
            resp = requests.get("https://api.boostr.cl/holidays.json", timeout=5)
            resp.raise_for_status()
            holidays = {item["date"] for item in resp.json()}  # "YYYY-MM-DD"
        except Exception:
            holidays = set()

        for r in page:
            if r.Fecha_creacion:
                base = date.today()
                dias = 0
                current = r.Fecha_creacion

                while current < base:
                    # solo lunes-viernes y NO feriado
                    if current.weekday() < 5 and current.strftime("%Y-%m-%d") not in holidays:
                        dias -= 1

                    # SIEMPRE avanzar 1 día
                    current += timedelta(days=1)
            else:
                dias = None


            data.append({
                "id": r.id,
                "Fecha_creacion": r.Fecha_creacion.strftime("%d-%m-%Y") if r.Fecha_creacion else "",
                "n_da": r.n_da,
                "fiscal_acargo": r.fiscal_acargo,
            })

        response = {
            "draw": draw,
            "recordsTotal": total_records,
            "recordsFiltered": total_filtered,
            "data": data,
        }

        return JsonResponse(response, safe=False)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)