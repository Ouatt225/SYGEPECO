from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('SYGEPECO', '0010_userprofile_departement'),
    ]

    operations = [
        # Renommer le modèle (table) Departement → Direction
        migrations.RenameModel(
            old_name='Departement',
            new_name='Direction',
        ),
        # Renommer les champs FK departement → direction
        migrations.RenameField(
            model_name='poste',
            old_name='departement',
            new_name='direction',
        ),
        migrations.RenameField(
            model_name='contractuel',
            old_name='departement',
            new_name='direction',
        ),
        migrations.RenameField(
            model_name='userprofile',
            old_name='departement',
            new_name='direction',
        ),
    ]
