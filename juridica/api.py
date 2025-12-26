from .models import *
from django.db.models import Q
from django.core.paginator import Paginator
from datetime import date
from django.http import JsonResponse
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
        ]

        if order_column_index < 0 or order_column_index >= len(columns):
            order_column_index = 0

        order_column = columns[order_column_index]
        if order_dir == "desc":
            order_column = f"-{order_column}"

        registros = RegistroJuridico.objects.filter(terminado=False)

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
                dias = 0
                current = r.fecha_respuesta

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
                "folio": r.folio,
                "oficio": r.oficio,
                "asignaciones": r.asignaciones,  # truncamos en el frontend
                "fecha_oficio": r.fecha_oficio.strftime("%d-%m-%Y") if r.fecha_oficio else "",
                "fecha_respuesta": r.fecha_respuesta.strftime("%d-%m-%Y") if r.fecha_respuesta else "—",
                "dias_transcurridos": dias,
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
        ]

        if order_column_index < 0 or order_column_index >= len(columns):
            order_column_index = 0

        order_column = columns[order_column_index]
        if order_dir == "desc":
            order_column = f"-{order_column}"

        registros = RegistroJuridico.objects.filter(terminado=True)

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
def oficio_respodido(request, id):
    try:
        registro = RegistroJuridico.objects.get(id=id)
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