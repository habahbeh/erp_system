# Generated manually

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('hr', '0012_remove_jobgrade_unique_jobgrade_code_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='earlyleave',
            name='notes',
            field=models.TextField(blank=True, verbose_name='ملاحظات'),
        ),
    ]
