# Generated manually to remove DiscountCampaign and POSSession models

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('sales', '0001_initial'),
    ]

    operations = [
        # Delete the models
        migrations.DeleteModel(
            name='DiscountCampaign',
        ),
        migrations.DeleteModel(
            name='POSSession',
        ),
    ]
