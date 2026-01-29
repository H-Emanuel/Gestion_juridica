from django.urls import path
from juridica import views,api

urlpatterns = [
    path("", views.lista_registros, name="lista_registros"),
    path("crear/", views.crear_registro, name="crear_registro"),
    path("crear_2/", views.crear_registro_2, name="crear_registro_2"),

    path("editar/<int:id>/", views.registro_editar, name="editar_registro"),
    path("eliminar/<int:id>/", views.eliminar_registro, name="eliminar_registro"),
    path("reiterar_oficio/<int:id>/", views.reiterar_oficio, name="reiterar_oficio"),
    path("documento/<int:doc_id>/eliminar/", views.documento_eliminar, name="documento_eliminar"),


    path("api/registros/", api.RegistroJuridico_list, name="api_registros"),
    path("api/historico/", api.RegistroJuridico_terminado_list, name="api_historico"),
    path("api/respondido/<int:id>/", api.oficio_respodido, name="oficio_respodido"),
    path("api/registro/<int:pk>/detalle/", api.registro_detalle_api, name="registro_detalle_api"),


    path("login/", views.login, name="login"),


]
