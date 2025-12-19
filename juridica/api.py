from .models import *
from django.db.models import Q
from django.core.paginator import Paginator
from datetime import date
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from datetime import date, timedelta
import requests

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
            "materia",
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
                Q(materia__icontains=search_value) |
                Q(asignacion__icontains=search_value)
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
            if r.fecha_oficio:
                base = r.fecha_respuesta or date.today()
                dias = 0
                current = r.fecha_oficio

                while current < base:
                    # solo lunes-viernes y NO feriado
                    if current.weekday() < 5 and current.strftime("%Y-%m-%d") not in holidays:
                        dias += 1

                    # SIEMPRE avanzar 1 día
                    current += timedelta(days=1)
            else:
                dias = None


            data.append({
                "id": r.id,
                "folio": r.folio,
                "oficio": r.oficio,
                "materia": r.materia,  # truncamos en el frontend
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
            "materia",
            "fecha_oficio",
            "fecha_respuesta",
            "asignacion",
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
                Q(materia__icontains=search_value) |
                Q(asignacion__icontains=search_value)
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
                base = r.fecha_respuesta or date.today()
                dias = (base - r.fecha_oficio).days
            else:
                dias = None

            data.append({
                "id": r.id,
                "folio": r.folio,
                "oficio": r.oficio,
                "materia": r.materia,  # truncamos en el frontend
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
        return JsonResponse({
                "folio": registro.folio,
                "oficio": registro.oficio,

            })
    except RegistroJuridico.DoesNotExist:
        return JsonResponse({"error": "Registro no encontrado."}, status=404)