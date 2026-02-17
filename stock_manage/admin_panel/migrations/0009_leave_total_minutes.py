from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('admin_panel', '0008_leave_category_leave_end_time_leave_start_time'),
    ]

    operations = [
        migrations.AddField(
            model_name='leave',
            name='total_minutes',
            field=models.IntegerField(default=0),
        ),
    ]
