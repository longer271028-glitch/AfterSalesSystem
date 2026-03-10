# Generated manually

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('logistics', '0003_add_api_config_fields'),
    ]

    operations = [
        migrations.AlterField(
            model_name='logisticschannel',
            name='api_type',
            field=models.CharField(
                choices=[('kuaidi100', '快递100'), ('kuaidi', '快递鸟'), ('tencent', '腾讯云'), ('tencent_market', '腾讯云市场'), ('custom', '自定义')],
                default='kuaidi100',
                help_text='',
                max_length=20,
                verbose_name='API类型'
            ),
        ),
        migrations.AddField(
            model_name='logisticschannel',
            name='secret_id',
            field=models.CharField(blank=True, help_text='腾讯云市场API Secret ID', max_length=200, verbose_name='Secret ID'),
        ),
        migrations.AddField(
            model_name='logisticschannel',
            name='secret_key_market',
            field=models.CharField(blank=True, help_text='腾讯云市场API Secret Key', max_length=200, verbose_name='Secret Key'),
        ),
        migrations.AddField(
            model_name='logisticschannel',
            name='market_api_url',
            field=models.CharField(
                blank=True,
                default='https://ap-beijing.cloudmarket-apigw.com/service-2r11e3tz/point-list',
                help_text='',
                max_length=200,
                verbose_name='API地址'
            ),
        ),
    ]
