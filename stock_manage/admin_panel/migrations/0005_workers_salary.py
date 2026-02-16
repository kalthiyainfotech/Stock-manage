from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('admin_panel', '0004_contact'),
    ]

    operations = [
        migrations.AddField(
            model_name='workers',
            name='salary',
            field=models.DecimalField(max_digits=10, decimal_places=2, default=0),
        ),
    ]
