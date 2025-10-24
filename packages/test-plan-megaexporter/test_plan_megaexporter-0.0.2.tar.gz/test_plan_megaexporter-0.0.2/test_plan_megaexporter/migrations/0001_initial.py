

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name='DocumentRequest',
            fields=[
                ('is_deleted', models.BooleanField(default=False)),
                ('deleted_at', models.DateTimeField(blank=True, null=True)),
                (
                    'created_at',
                    models.DateTimeField(
                        auto_now_add=True, verbose_name='created at'),
                ),
                (
                    'updated_at',
                    models.DateTimeField(
                        auto_now=True, verbose_name='updated at'),
                ),
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('user_id', models.IntegerField()),
                (
                    'document_type',
                    models.CharField(
                        choices=[
                            ('testplan', 'Test Plan'),
                            ('testreport', 'Test Report'),
                        ],
                        max_length=20,
                    ),
                ),
                (
                    'status',
                    models.CharField(
                        choices=[
                            ('PENDING', 'Pending'),
                            ('IN_PROGRESS', 'In Progress'),
                            ('DONE', 'Done'),
                            ('FAILED', 'Failed'),
                        ],
                        default='PENDING',
                        max_length=20,
                    ),
                ),
                ('request_params', models.JSONField(default=dict)),
                ('file_path', models.CharField(
                    blank=True, max_length=255, null=True)),
                ('file_name', models.CharField(
                    blank=True, max_length=255, null=True)),
                ('error_message', models.TextField(blank=True, null=True)),
                ('completed_at', models.DateTimeField(blank=True, null=True)),
            ],
            options={
                'verbose_name': 'Document Request',
                'verbose_name_plural': 'Document Requests',
                'ordering': ['-created_at'],
            },
        ),
    ]
