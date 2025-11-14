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
                ('email', models.EmailField(max_length=254)),
                ('phone', models.CharField(max_length=50)),
                ('employees_count', models.PositiveIntegerField(default=0)),
                ('sector', models.CharField(max_length=100)),
            ],
            options={'ordering': ('name',)},
        ),
    ]
