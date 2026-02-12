from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('buyers', '0006_alter_order_payment_method'),
    ]

    operations = [
        migrations.AlterField(
            model_name='order',
            name='status',
            field=models.CharField(
                max_length=20,
                choices=[
                    ('pending', 'Pending'),
                    ('processing', 'Processing'),
                    ('shipped', 'Shipped'),
                    ('delivered', 'Delivered'),
                    ('return_requested', 'Return Requested'),
                    ('returned', 'Returned'),
                    ('cancelled', 'Cancelled'),
                ],
                default='pending',
            ),
        ),
    ]

