import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("Mark", "0001_initial"),
        ("Papers", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name="markingtask",
            name="paper",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE, to="Papers.paper"
            ),
        ),
        migrations.AddField(
            model_name="annotation",
            name="task",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to="Mark.markingtask",
            ),
        ),
        migrations.AddField(
            model_name="markingtasktag",
            name="task",
            field=models.ManyToManyField(to="Mark.markingtask"),
        ),
        migrations.AddField(
            model_name="markingtasktag",
            name="user",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to=settings.AUTH_USER_MODEL,
            ),
        ),
    ]
