# Generated by Django 3.1.7 on 2021-02-26 12:24

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('books', '0008_auto_20210226_1321'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='userfollows',
            unique_together={('user', 'followed_user')},
        ),
        migrations.CreateModel(
            name='Ticket2',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=128, unique=True)),
                ('description', models.TextField(blank=True, max_length=2048)),
                ('time_created', models.DateTimeField(auto_now_add=True)),
                ('image', models.ImageField(blank=True, null=True, upload_to='images/')),
                ('completed', models.BooleanField(default=False)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
