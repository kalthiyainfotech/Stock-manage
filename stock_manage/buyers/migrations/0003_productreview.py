from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('buyers', '0002_order_payment_status_order_razorpay_order_id_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='ProductReview',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('rating', models.PositiveIntegerField(default=5)),
                ('comment', models.TextField()),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('buyer', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='reviews', to='buyers.buyer')),
                ('variant', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='reviews', to='admin_panel.productvariant')),
            ],
            options={
                'ordering': ['-created_at'],
                'unique_together': {('buyer', 'variant')},
            },
        ),
    ]
