# Generated migration for adding status and task_id fields

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("example_app", "0002_rename_polarity_analysis_confidence_score_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="analysis",
            name="status",
            field=models.CharField(
                choices=[
                    ("pending", "Pending"),
                    ("processing", "Processing"),
                    ("completed", "Completed"),
                    ("failed", "Failed"),
                ],
                default="pending",
                max_length=10,
            ),
        ),
        migrations.AddField(
            model_name="analysis",
            name="task_id",
            field=models.CharField(
                blank=True, db_index=True, max_length=255, null=True
            ),
        ),
        migrations.AddField(
            model_name="analysis",
            name="updated_at",
            field=models.DateTimeField(auto_now=True),
        ),
        migrations.AddIndex(
            model_name="analysis",
            index=models.Index(fields=["status"], name="example_app_status_idx"),
        ),
        migrations.AddIndex(
            model_name="analysis",
            index=models.Index(fields=["created_at"], name="example_app_created_idx"),
        ),
        migrations.AlterField(
            model_name="analysis",
            name="sentiment",
            field=models.CharField(
                blank=True,
                choices=[
                    ("positive", "Positive"),
                    ("negative", "Negative"),
                    ("neutral", "Neutral"),
                ],
                max_length=8,
                null=True,
            ),
        ),
        migrations.AlterModelOptions(
            name="analysis",
            options={
                "ordering": ["-created_at"],
                "verbose_name": "Analysis",
                "verbose_name_plural": "Analyses",
            },
        ),
    ]
