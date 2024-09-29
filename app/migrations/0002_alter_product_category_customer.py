# Generated by Django 5.0.7 on 2024-08-08 08:35

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("app", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AlterField(
            model_name="product",
            name="category",
            field=models.CharField(
                choices=[
                    ("PY", "Primary"),
                    ("SY", "Secondary"),
                    ("TY", "Tertiary"),
                    ("IL", "Inspirational"),
                    ("SL", "Spiritual"),
                    ("OT", "Others"),
                ],
                max_length=2,
            ),
        ),
        migrations.CreateModel(
            name="Customer",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("name", models.CharField(max_length=200)),
                ("locality", models.CharField(max_length=200)),
                ("city", models.CharField(max_length=50)),
                ("mobile", models.IntegerField(default=0)),
                ("zipcode", models.IntegerField()),
                (
                    "state",
                    models.CharField(
                        choices=[
                            ("Abia", "Abia"),
                            ("Adamawa", "Adamawa"),
                            ("Akwa Ibom", "Akwa Ibom"),
                            ("Anambra", "Anambra"),
                            ("Bauchi", "Bauchi"),
                            ("Bayelsa", "Bayelsa"),
                            ("Benue", "Benue"),
                            ("Borno", "Borno"),
                            ("Cross River", "Cross River"),
                            ("Delta", "Delta"),
                            ("Ebonyi", "Ebonyi"),
                            ("Edo", "Edo"),
                            ("Ekiti", "Ekiti"),
                            ("Enugu", "Enugu"),
                            ("Gombe", "Gombe"),
                            ("Imo", "Imo"),
                            ("Jigawa", "Jigawa"),
                            ("Kaduna", "Kaduna"),
                            ("Kano", "Kano"),
                            ("Katsina", "Katsina"),
                            ("Kebbi", "Kebbi"),
                            ("Kogi", "Kogi"),
                            ("Kwara", "Kwara"),
                            ("Lagos", "Lagos"),
                            ("Nasarawa", "Nasarawa"),
                            ("Niger", "Niger"),
                            ("Ogun", "Ogun"),
                            ("Ondo", "Ondo"),
                            ("Osun", "Osun"),
                            ("Oyo", "Oyo"),
                            ("Plateau", "Plateau"),
                            ("Rivers", "Rivers"),
                            ("Sokoto", "Sokoto"),
                            ("Taraba", "Taraba"),
                            ("Yobe", "Yobe"),
                            ("Zamfara", "Zamfara"),
                        ],
                        max_length=100,
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
        ),
    ]
