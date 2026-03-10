# Generated migration

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('logistics', '0002_remove_logisticsrecord_last_update_time_and_more'),
    ]

    operations = [
        migrations.AddField('logisticschannel', 'app_id', models.CharField(blank=True, max_length=100)),
        migrations.AddField('logisticschannel', 'app_key', models.CharField(blank=True, max_length=100)),
        migrations.AddField('logisticschannel', 'secret_key', models.CharField(blank=True, max_length=100)),
        migrations.AddField('logisticschannel', 'api_url', models.CharField(blank=True, max_length=200)),
        migrations.AlterField(
            model_name='logisticschannel',
            name='api_type',
            field=models.CharField(choices=[('custom', '自定义'), ('kuaidi', '快递鸟'), ('kuaidi100', '快递100'), ('tencent', '腾讯云')], max_length=20),
        ),
        migrations.AddField('logisticsrecord', 'is_completed', models.BooleanField(default=False)),
        migrations.AddField('logisticsrecord', 'last_query_time', models.DateTimeField(blank=True, null=True)),
        migrations.AddField('logisticsrecord', 'query_count_today', models.IntegerField(default=0)),
        migrations.AddField('logisticsrecord', 'query_date', models.DateField(blank=True, null=True)),
        migrations.AddField('logisticsrecord', 'updated_at', models.DateTimeField(auto_now=True)),
    ]
