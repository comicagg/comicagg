from django.core import signing

from .models import Subscription, UnreadStrip

SALT = "comics.read-snapshot.v1"


class InvalidReadSnapshot(ValueError):
    pass


def make_snapshot(
    user_id: int, subscriptions: list[Subscription], unreads: list[UnreadStrip]
) -> str:
    boundaries: dict[int, int] = {}
    for unread in unreads:
        boundaries[unread.comic_id] = max(
            boundaries.get(unread.comic_id, 0), unread.read_sequence
        )
    return signing.dumps(
        {
            "user": user_id,
            "boundaries": [
                [
                    subscription.pk,
                    subscription.comic_id,
                    boundaries.get(subscription.comic_id, 0),
                ]
                for subscription in subscriptions
            ],
        },
        salt=SALT,
        compress=True,
    )


def load_snapshot(snapshot: str, user_id: int) -> list[list[int]]:
    try:
        payload = signing.loads(snapshot, salt=SALT)
    except signing.BadSignature as exc:
        raise InvalidReadSnapshot("Invalid read snapshot; reload the reader.") from exc
    if not isinstance(payload, dict) or payload.get("user") != user_id:
        raise InvalidReadSnapshot("The read snapshot belongs to another user.")
    boundaries = payload.get("boundaries")
    if not isinstance(boundaries, list) or any(
        not isinstance(row, list)
        or len(row) != 3
        or any(type(value) is not int or value < 0 for value in row)
        for row in boundaries
    ):
        raise InvalidReadSnapshot("Invalid read snapshot boundaries.")
    return boundaries
