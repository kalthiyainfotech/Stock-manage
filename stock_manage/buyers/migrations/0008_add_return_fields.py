from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('buyers', '0007_add_return_statuses'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='return_reason',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='order',
            name='return_requested_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]

