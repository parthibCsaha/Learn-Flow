from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('courses', '0002_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='lesson',
            name='transcript',
            field=models.TextField(blank=True),
        ),
    ]
