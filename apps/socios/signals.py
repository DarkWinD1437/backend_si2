# signals.py (crear este archivo nuevo)
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.mail import send_mail
from django.conf import settings
from .models import Socio

@receiver(post_save, sender=Socio)
def enviar_email_bienvenida(sender, instance, created, **kwargs):
    if created and instance.usuario.email:
        subject = 'Bienvenido/a como Socio'
        message = f'''
        Hola {instance.usuario.get_full_name()},
        
        Te damos la bienvenida como socio {instance.get_tipo_socio_display().lower()}.
        
        Tus datos:
        - DNI: {instance.dni}
        - Tipo: {instance.get_tipo_socio_display()}
        - Fecha de ingreso: {instance.fecha_ingreso}
        
        ¡Gracias por unirte a nuestra comunidad!
        '''
        
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [instance.usuario.email],
            fail_silently=True,
        )