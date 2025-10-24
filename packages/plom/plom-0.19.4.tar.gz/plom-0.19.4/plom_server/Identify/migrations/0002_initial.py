import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("Identify", "0001_initial"),
        ("Papers", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name="idprediction",
            name="paper",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE, to="Papers.paper"
            ),
        ),
        migrations.AddField(
            model_name="idprediction",
            name="user",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AddField(
            model_name="paperidaction",
            name="user",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL
            ),
        ),
        migrations.AddField(
            model_name="paperidtask",
            name="assigned_user",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AddField(
            model_name="paperidtask",
            name="latest_action",
            field=models.OneToOneField(
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to="Identify.paperidaction",
            ),
        ),
        migrations.AddField(
            model_name="paperidtask",
            name="paper",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE, to="Papers.paper"
            ),
        ),
        migrations.AddField(
            model_name="paperidaction",
            name="task",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to="Identify.paperidtask",
            ),
        ),
    ]
