# Generated migration

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0004_add_warehouse_category_model'),
        ('repairs', '0002_repairorder_receive_quantity_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='repairorder',
            name='inbound_warehouse',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='inbound_repairs', to='inventory.warehouse', verbose_name='入库仓库'),
        ),
        migrations.AddField(
            model_name='repairorder',
            name='outbound_warehouse',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='outbound_repairs', to='inventory.warehouse', verbose_name='出库仓库'),
        ),
        migrations.AddField(
            model_name='repairorder',
            name='product',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='repair_orders', to='inventory.product', verbose_name='关联产品'),
        ),
    ]
