from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('SYGEPECO', '0009_conge_workflow_manager'),
    ]

    operations = [
        migrations.AddField(
            model_name='userprofile',
            name='departement',
            field=models.ForeignKey(
                blank=True, null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='managers',
                to='SYGEPECO.departement',
                verbose_name='Direction (Manager)',
            ),
        ),
    ]
