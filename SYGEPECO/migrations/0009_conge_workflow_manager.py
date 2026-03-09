from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('SYGEPECO', '0008_permission_date_range'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='conge',
            name='valide_par_manager',
            field=models.ForeignKey(
                blank=True, null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='conges_valides_manager',
                to=settings.AUTH_USER_MODEL,
                verbose_name='Validé par (manager)',
            ),
        ),
        migrations.AddField(
            model_name='conge',
            name='commentaire_manager',
            field=models.TextField(blank=True, verbose_name='Commentaire manager'),
        ),
        migrations.AlterField(
            model_name='conge',
            name='statut',
            field=models.CharField(
                choices=[
                    ('EN_ATTENTE', 'En attente'),
                    ('VALIDE_MANAGER', 'Validé par le manager'),
                    ('APPROUVE', 'Approuvé'),
                    ('REJETE', 'Rejeté'),
                    ('ANNULE', 'Annulé'),
                ],
                default='EN_ATTENTE',
                max_length=15,
            ),
        ),
    ]
