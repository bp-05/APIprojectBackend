from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name='Company',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200)),
                ('address', models.CharField(max_length=255)),
                ('management_address', models.CharField(blank=True, default='', max_length=255)),
                ('spys_responsible_name', models.CharField(max_length=200)),
                ('email', models.EmailField(max_length=254)),
                ('phone', models.CharField(max_length=50)),
                ('employees_count', models.PositiveIntegerField(default=0)),
                ('sector', models.CharField(max_length=100)),
                ('api_type', models.PositiveSmallIntegerField(choices=((1, 'Type 1'), (2, 'Type 2'), (3, 'Type 3')), default=1)),
            ],
            options={'ordering': ('name',)},
        ),
    ]

