from django.db import migrations, models
from django.db.models import Count, Min


def consolidate_duplicate_unreads(apps, schema_editor):
    unreads = apps.get_model("comics", "UnreadStrip").objects.using(
        schema_editor.connection.alias
    )
    duplicates = (
        unreads.order_by()
        .values("user_id", "strip_id")
        .annotate(first_id=Min("id"), total=Count("id"))
        .filter(total__gt=1)
    )
    for duplicate in duplicates.iterator(chunk_size=1000):
        unreads.filter(
            user_id=duplicate["user_id"], strip_id=duplicate["strip_id"]
        ).exclude(pk=duplicate["first_id"]).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("comics", "0014_alter_comic_last_image"),
    ]

    operations = [
        migrations.AddField(
            model_name="strip",
            name="unreads_distributed",
            field=models.BooleanField(db_index=True, default=True),
        ),
        migrations.AlterField(
            model_name="strip",
            name="unreads_distributed",
            field=models.BooleanField(db_index=True, default=False),
        ),
        migrations.RunPython(
            consolidate_duplicate_unreads, reverse_code=migrations.RunPython.noop
        ),
        migrations.AddConstraint(
            model_name="unreadstrip",
            constraint=models.UniqueConstraint(
                fields=("user", "strip"), name="unique_user_unread_strip"
            ),
        ),
    ]
