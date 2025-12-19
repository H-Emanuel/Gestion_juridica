from django.urls import path
from juridica import views,api

urlpatterns = [
    path("", views.lista_registros, name="lista_registros"),
    path("crear/", views.crear_registro, name="crear_registro"),
    path("editar/<int:id>/", views.editar_registro, name="editar_registro"),
    path("eliminar/<int:id>/", views.eliminar_registro, name="eliminar_registro"),
    path("reiterar_oficio/<int:id>/", views.reiterar_oficio, name="reiterar_oficio"),
    path("api/registros/", api.RegistroJuridico_list, name="api_registros"),
    path("api/historico/", api.RegistroJuridico_terminado_list, name="api_historico"),

    path("api/respondido/<int:id>/", api.oficio_respodido, name="oficio_respodido"),
    path("login/", views.login, name="login"),


]
