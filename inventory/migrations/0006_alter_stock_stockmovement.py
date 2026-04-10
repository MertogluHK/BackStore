# Manual migration for Stock and StockMovement model changes
# Changes ForeignKey relationships to CharField (barcode and store_code)

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0005_userprofile_user_id_code'),
    ]

    operations = [
        # Remove ForeignKey constraints for Stock model
        migrations.RemoveField(
            model_name='stock',
            name='product',
        ),
        migrations.RemoveField(
            model_name='stock',
            name='store',
        ),
        # Add CharField fields to Stock
        migrations.AddField(
            model_name='stock',
            name='barcode',
            field=models.CharField(default='', max_length=50, verbose_name='Barkod'),
        ),
        migrations.AddField(
            model_name='stock',
            name='store_code',
            field=models.CharField(default='', max_length=10, verbose_name='Mağaza Kodu'),
        ),
        # Update unique_together constraint
        migrations.AlterUniqueTogether(
            name='stock',
            unique_together={('barcode', 'store_code')},
        ),
        # Remove old indexes and add new ones
        migrations.RemoveIndex(
            model_name='stock',
            name='inventory_s_product_store_idx',
        ),
        migrations.AddIndex(
            model_name='stock',
            index=models.Index(fields=['barcode', 'store_code'], name='inventory_s_barcode_store_code_idx'),
        ),
        
        # Same changes for StockMovement model
        migrations.RemoveField(
            model_name='stockmovement',
            name='product',
        ),
        migrations.RemoveField(
            model_name='stockmovement',
            name='store',
        ),
        migrations.AddField(
            model_name='stockmovement',
            name='barcode',
            field=models.CharField(default='', max_length=50, verbose_name='Barkod'),
        ),
        migrations.AddField(
            model_name='stockmovement',
            name='store_code',
            field=models.CharField(default='', max_length=10, verbose_name='Mağaza Kodu'),
        ),
        # Remove old indexes and add new ones
        migrations.RemoveIndex(
            model_name='stockmovement',
            name='inventory_s_product_store_idx',
        ),
        migrations.AddIndex(
            model_name='stockmovement',
            index=models.Index(fields=['barcode', 'store_code'], name='inventory_s_barcode_store_code_idx'),
        ),
    ]
