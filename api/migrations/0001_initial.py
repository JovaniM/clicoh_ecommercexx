# Generated by Django 4.0.6 on 2022-07-08 01:05

import api.validators
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Order',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='created_at')),
                ('movement_type', models.CharField(choices=[('INGRESS', 'INGRESS'), ('EGRESS', 'EGRESS')], db_index=True, default='INGRESS', max_length=10)),
                ('status', models.CharField(choices=[('CANCELLED', 'CANCELLED'), ('DRAFT', 'DRAFT'), ('PROCESSED', 'PROCESSED')], default='DRAFT', max_length=10)),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='updated_at')),
            ],
        ),
        migrations.CreateModel(
            name='Product',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('available', models.BooleanField(default=False, verbose_name='available')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='created_at')),
                ('name', models.CharField(max_length=256, verbose_name='name')),
                ('price', models.FloatField(default=0, validators=[api.validators.greater_equal_than_zero], verbose_name='price')),
                ('stock', models.IntegerField(default=0, verbose_name='stock')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='updated_at')),
            ],
        ),
        migrations.CreateModel(
            name='OrderDetail',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='created_at')),
                ('quantity', models.IntegerField(validators=[api.validators.greater_equal_than_zero], verbose_name='quantity')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='updated_at')),
                ('order_id', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='api.order')),
                ('product_id', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='api.product')),
            ],
        ),
    ]
