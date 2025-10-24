
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("test_plan_megaexporter", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="documentrequest",
            name="user_id",
            field=models.IntegerField(db_index=True),
        ),
    ]
