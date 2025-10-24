
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name='JiraTicketStatus',
            fields=[
                (
                    'id',
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name='ID',
                    ),
                ),
                ('is_deleted', models.BooleanField(default=False)),
                ('deleted_at', models.DateTimeField(blank=True, null=True)),
                (
                    'created_at',
                    models.DateTimeField(auto_now_add=True, verbose_name='created at'),
                ),
                (
                    'updated_at',
                    models.DateTimeField(auto_now=True, verbose_name='updated at'),
                ),
                ('key', models.CharField(db_index=True, max_length=255, unique=True)),
                ('status', models.CharField(max_length=255)),
            ],
            options={
                'abstract': False,
            },
        ),
    ]
