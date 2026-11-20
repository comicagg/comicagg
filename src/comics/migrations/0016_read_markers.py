from django.db import migrations, models
from django.db.models import Count, F, Max, OuterRef, Subquery, Value
from django.db.models.functions import Coalesce


def initialize_read_markers(apps, schema_editor):
    using = schema_editor.connection.alias
    unreads = apps.get_model("comics", "UnreadStrip").objects.using(using)
    comics = apps.get_model("comics", "Comic").objects.using(using)
    subscriptions = apps.get_model("comics", "Subscription").objects.using(using)
    unreads.update(read_sequence=F("pk"))
    maximum = (
        unreads.filter(comic_id=OuterRef("pk"))
        .order_by()
        .values("comic_id")
        .annotate(maximum=Max("read_sequence"))
        .values("maximum")
    )
    comics.update(unread_sequence=Coalesce(Subquery(maximum), Value(0)))
    duplicates = (
        subscriptions.order_by()
        .values("user_id", "comic_id")
        .annotate(total=Count("pk"))
        .filter(total__gt=1)
    )
    for duplicate in duplicates.iterator(chunk_size=1000):
        matching = subscriptions.filter(
            user_id=duplicate["user_id"], comic_id=duplicate["comic_id"]
        )
        keep = matching.order_by("position", "pk").values_list("pk", flat=True).first()
        matching.exclude(pk=keep).delete()


class Migration(migrations.Migration):
    dependencies = [("comics", "0015_deferred_strip_distribution")]

    operations = [
        migrations.AddField(
            model_name="comic",
            name="unread_sequence",
            field=models.PositiveBigIntegerField(default=0, editable=False),
        ),
        migrations.AddField(
            model_name="subscription",
            name="read_through",
            field=models.PositiveBigIntegerField(default=0, editable=False),
        ),
        migrations.AddField(
            model_name="unreadstrip",
            name="read_sequence",
            field=models.PositiveBigIntegerField(default=0, editable=False),
        ),
        migrations.RunPython(initialize_read_markers, migrations.RunPython.noop),
        migrations.AddConstraint(
            model_name="subscription",
            constraint=models.UniqueConstraint(
                fields=("user", "comic"), name="unique_user_comic_subscription"
            ),
        ),
        migrations.AddIndex(
            model_name="unreadstrip",
            index=models.Index(
                fields=["user", "comic", "read_sequence"],
                name="unread_user_comic_sequence",
            ),
        ),
    ]
