from django.db import models
from django.utils import timezone
from django.utils.text import slugify
import os

class RegistroJuridico(models.Model):
    folio = models.CharField(max_length=50)
    oficio = models.CharField(max_length=100)
    materia = models.TextField()
    fecha_oficio = models.DateField()
    fecha_respuesta = models.DateField(null=True, blank=True)
    respuesta = models.TextField(blank=True)
    asignacion = models.CharField(max_length=100, blank=True)

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


def archivo_upload_to(instance, filename):
    """
    Guarda el archivo en MEDIA_ROOT/RegistroJuridico.<folio>/<filename>
    Se slugifica el folio para evitar caracteres problemáticos en rutas.
    """
    safe_folio = slugify(instance.registro.folio) if instance.registro and instance.registro.folio else "sin-folio"
    filename = os.path.basename(filename)
    return os.path.join(f"Registro_Juridico.{safe_folio}", filename)


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
