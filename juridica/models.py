from django.db import models
from django.utils import timezone
from django.utils.text import slugify
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
    respuesta = models.TextField(blank=True)
    asignaciones = models.JSONField(default=list, blank=True)
    terminado = models.BooleanField(default=False)
    

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
