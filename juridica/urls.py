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

    # FOLIOS
    path("api/registros/", api.RegistroJuridico_list, name="api_registros"),
    path("api/historico/", api.RegistroJuridico_terminado_list, name="api_historico"),
    path("api/registro/<int:pk>/detalle/", api.registro_detalle_api, name="registro_detalle_api"),
    path("api/registro/<int:pk>/respondido/", api.respondido, name="respondido_api"),
    path("api/registro/<int:pk>/rechazado/", api.rechazado, name="rechazado_api"),

    # SUMARIO

    path("editar_sumario/<int:id>/", views.editar_sumario, name="editar_sumario"),
    path("eliminar_sumario/<int:id>/", views.eliminar_sumario, name="eliminar_sumario"),
    path("api/sumario/", api.RegistroSumario_list, name="api_sumario"),
    path("api/historico_sumario/", api.RegistroSumario_terminado_list, name="api_historico_sumario"),
    path("api/sumario/<int:pk>/detalle/", api.sumario_detalle, name="sumario_detalle_api"),
    path("api/sumario/<int:pk>/etapas/", api.sumario_etapa, name="sumario_etapas_api"),
    path("reiterar_sumario/<int:id>/", views.reiterar_sumario, name="reiterar_sumario"),
    path("api/sumario/<int:pk>/etapas/guardar/", api.guardarEtapas, name="guardar_etapas_api"),
    path("api/sumario/<int:id>/finalizar/", api.terminonio_sumario, name="finalizar_sumario_api"),

    # ASIGNAR USUARIOS
    path("api/usuarios/", api.Usuario_list, name="api_usuarios"),
    path("api/asignar/", views.asignar_usuario, name="api_asignar_usuario"),

    # LOGOUT
    path("login/", views.login, name="login"),

    path("logout/", views.logout_view, name="logout"),
]
