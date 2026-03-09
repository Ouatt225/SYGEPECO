from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('SYGEPECO', '0007_conge_document_medical'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='permission',
            name='date',
        ),
        migrations.RemoveField(
            model_name='permission',
            name='heure_debut',
        ),
        migrations.RemoveField(
            model_name='permission',
            name='heure_fin',
        ),
        migrations.AddField(
            model_name='permission',
            name='date_debut',
            field=models.DateField(default='2026-01-01'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='permission',
            name='date_fin',
            field=models.DateField(default='2026-01-01'),
            preserve_default=False,
        ),
    ]
