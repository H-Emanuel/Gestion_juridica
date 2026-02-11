from django.db import models
from django.utils import timezone
from django.utils.text import slugify,get_valid_filename
import os
import uuid

def _get_registro_from_instance(instance):
    """
    Intenta obtener el RegistroJuridico desde cualquier instancia.
    - Si tiene .registro, listo.
    - Si tiene .respuesta_juridica.registro, etc., puedes ampliar reglas.
    """
    if hasattr(instance, "registro") and instance.registro_id:
        return instance.registro

    # Si algún día tienes modelos que apunten a RespuestaJuridica en vez de RegistroJuridico:
    if hasattr(instance, "respuesta_juridica") and getattr(instance.respuesta_juridica, "registro_id", None):
        return instance.respuesta_juridica.registro

    return None


def archivo_upload_to(instance, filename):
    """
    MEDIA_ROOT/
      Registro_Juridico.<folio_slug>/
        <modelo_slug>/
          <uuid>_<filename>
    """
    filename = os.path.basename(filename)

    registro = _get_registro_from_instance(instance)
    folio = getattr(registro, "folio", None) if registro else None
    safe_folio = slugify(folio) if folio else "sin-folio"

    # Subcarpeta por modelo para ordenar
    model_folder = slugify(instance.__class__.__name__)  # "respuestajuridica" / "documento"

    # Evita colisiones si suben mismo nombre 2 veces
    unique_prefix = uuid.uuid4().hex[:10]
    final_name = f"{unique_prefix}_{filename}"

    return os.path.join(f"Registro_Juridico.{safe_folio}", model_folder, final_name)



class RegistroJuridico(models.Model):
    folio = models.CharField(max_length=50)
    oficio = models.CharField(max_length=100)
    materia = models.TextField()
    fecha_oficio = models.DateField()
    fecha_respuesta = models.DateField(null=True, blank=True)
    asignaciones = models.JSONField(default=list, blank=True)
    terminado = models.BooleanField(default=False)
    dirigido_a = models.CharField(max_length=100, blank=True)
    cc = models.CharField(max_length=255, blank=True)
    respuesta = models.TextField(blank=True)


    def __str__(self):
        return f"{self.folio} - {self.oficio}"

    @property
    def dias_transcurridos(self):
        """Días entre fecha de oficio y fecha de respuesta o hoy"""
        if self.fecha_respuesta:
            return (self.fecha_respuesta - self.fecha_oficio).days
        return (timezone.now().date() - self.fecha_oficio).days

    @property
    def requiere_alerta(self):
        """Retorna True si han pasado 3 días sin respuesta"""
        return not self.fecha_respuesta and self.dias_transcurridos >= 3




class RespuestaJuridica(models.Model):
    registro = models.OneToOneField(
        RegistroJuridico,
        related_name="respuesta_juridica",
        on_delete=models.CASCADE
    )
    respuesta = models.TextField()
    fecha_termino = models.DateField()
    archivo = models.FileField(upload_to=archivo_upload_to, null=True, blank=True)

    def __str__(self):
        return f"Respuesta - {self.registro.folio}"


class Documento(models.Model):
    registro = models.ForeignKey(
        RegistroJuridico,
        related_name="documentos",
        on_delete=models.CASCADE
    )
    archivo = models.FileField(upload_to=archivo_upload_to)
    nombre = models.CharField(max_length=255, blank=True)
    fecha_subida = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.nombre or os.path.basename(self.archivo.name)

    def save(self, *args, **kwargs):
        # Si no se indicó nombre, usar el nombre del archivo subido
        if not self.nombre and self.archivo:
            self.nombre = os.path.basename(self.archivo.name)
        super().save(*args, **kwargs)


def _get_registro_from_instance(instance):
    """
    Devuelve el RegistroSumario asociado, tanto si instance es el registro
    como si es un modelo relacionado (ej: Documento).
    """
    if isinstance(instance, RegistroSumario):
        return instance
    return getattr(instance, "sumario", None)


def archivo_upload_to_sumario(instance, filename):
    """
    MEDIA_ROOT/
      sumario.<folio_slug o id>/
        <model_slug>/
          <uuid>_<filename>
    """
    filename = get_valid_filename(os.path.basename(filename))

    registro = _get_registro_from_instance(instance)
    pk = getattr(registro, "pk", None) if registro else None

    # Si ya hay PK, la usamos; si no, carpeta temporal
    safe_folio = slugify(str(pk)) if pk else f"tmp-{uuid.uuid4().hex[:8]}"

    # Subcarpeta por modelo (estable en Django)
    model_folder = slugify(instance._meta.model_name)

    unique_prefix = uuid.uuid4().hex[:10]
    final_name = f"{unique_prefix}_{filename}"

    return os.path.join(f"sumario.{safe_folio}", model_folder, final_name)


class RegistroSumario(models.Model):
    id = models.AutoField(primary_key=True)
    Fecha_creacion = models.DateField()

    n_da = models.TextField()
    fecha_da = models.DateField()
    fiscal_acargo = models.CharField(max_length=100)
    grado_fiscal = models.CharField(max_length=50)

    materia = models.TextField()

    nombre_apellido_grado_imputado = models.JSONField(default=list, blank=True)

    oficio_fiscalia = models.CharField(max_length=100)
    fecha_fiscalia = models.DateField()
    adjunto_fiscalia = models.FileField(upload_to=archivo_upload_to_sumario, null=True, blank=True)
   
    oficio_juridico = models.CharField(max_length=100)
    fecha_juridico = models.DateField()
    adjunto_juridico = models.FileField(upload_to=archivo_upload_to_sumario, null=True, blank=True)

    sancion = models.CharField(max_length=100, blank=True)
    adjunto_sancion = models.FileField(upload_to=archivo_upload_to_sumario, null=True, blank=True)

    fecha_contrata = models.DateField(null=True, blank=True)

    finalizado = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        """
        Evita que los adjuntos se guarden en 'sin-id' / tmp cuando el registro aún no tiene PK.
        1) Guardamos sin archivos para obtener PK
        2) Reasignamos archivos y guardamos de nuevo
        """
        if self.pk is None and (self.adjunto_fiscalia or self.adjunto_juridico):
            af = self.adjunto_fiscalia
            aj = self.adjunto_juridico

            self.adjunto_fiscalia = None
            self.adjunto_juridico = None
            super().save(*args, **kwargs)  # crea PK

            self.adjunto_fiscalia = af
            self.adjunto_juridico = aj
            return super().save(update_fields=["adjunto_fiscalia", "adjunto_juridico"])

        return super().save(*args, **kwargs)


class DocumentoSumario(models.Model):
    sumario = models.ForeignKey(
        RegistroSumario,
        related_name="documentos_sumario",
        on_delete=models.CASCADE
    )
    archivo = models.FileField(upload_to=archivo_upload_to_sumario)
    nombre = models.CharField(max_length=255, blank=True)
    fecha_subida = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.nombre or os.path.basename(self.archivo.name)

    def save(self, *args, **kwargs):
        # Si no se indicó nombre, usar el nombre ORIGINAL del archivo subido (no el path con uuid)
        if not self.nombre and self.archivo and getattr(self.archivo, "file", None):
            self.nombre = os.path.basename(getattr(self.archivo.file, "name", self.archivo.name))
        super().save(*args, **kwargs)
