from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('reviews', '0003_alter_review_rating'),
    ]

    operations = [
        migrations.AddField(
            model_name='review',
            name='title',
            field=models.CharField(default='', max_length=120),
        ),
        migrations.AlterField(
            model_name='review',
            name='comment',
            field=models.TextField(default=''),
        ),
    ]