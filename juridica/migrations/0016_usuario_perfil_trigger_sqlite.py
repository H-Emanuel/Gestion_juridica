from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('juridica', '0015_perfil_usuarioperfil'),
    ]

    operations = [
        migrations.RunSQL(
            sql="""
                CREATE OR REPLACE FUNCTION juridica_set_usuario_perfil_default()
                RETURNS TRIGGER AS $$
                BEGIN
                    INSERT INTO juridica_usuarioperfil (usuario_id, perfil_id, fecha_asignacion)
                    VALUES (
                        NEW.id,
                        (SELECT id FROM juridica_perfil WHERE nombre = 'Usuario Normal' LIMIT 1),
                        CURRENT_TIMESTAMP
                    )
                    ON CONFLICT (usuario_id, perfil_id) DO NOTHING;
                    RETURN NEW;
                END;
                $$ LANGUAGE plpgsql;

                DROP TRIGGER IF EXISTS juridica_set_usuario_perfil_default_trigger ON auth_user;
                
                CREATE TRIGGER juridica_set_usuario_perfil_default_trigger
                AFTER INSERT ON auth_user
                FOR EACH ROW
                EXECUTE FUNCTION juridica_set_usuario_perfil_default();
            """,
            reverse_sql="""
                DROP TRIGGER IF EXISTS juridica_set_usuario_perfil_default_trigger ON auth_user;
                DROP FUNCTION IF EXISTS juridica_set_usuario_perfil_default();
            """,
        ),
    ]