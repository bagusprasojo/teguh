# Generated manually for per-record public UUIDs.
import uuid

from django.db import migrations, models


MODEL_NAMES = [
    "UserAccess",
    "Voucher",
    "Video",
    "CBT",
    "Question",
    "Choice",
    "CBTAttempt",
    "CBTAttemptAnswer",
    "UserPreference",
]


def populate_uuids(apps, schema_editor):
    for model_name in MODEL_NAMES:
        model = apps.get_model("learning", model_name)
        for obj in model.objects.filter(uuid__isnull=True):
            obj.uuid = uuid.uuid4()
            obj.save(update_fields=["uuid"])


class Migration(migrations.Migration):
    dependencies = [
        ("learning", "0002_userpreference"),
    ]

    operations = [
        migrations.AddField(
            model_name="useraccess",
            name="uuid",
            field=models.UUIDField(blank=True, null=True, editable=False),
        ),
        migrations.AddField(
            model_name="voucher",
            name="uuid",
            field=models.UUIDField(blank=True, null=True, editable=False),
        ),
        migrations.AddField(
            model_name="video",
            name="uuid",
            field=models.UUIDField(blank=True, null=True, editable=False),
        ),
        migrations.AddField(
            model_name="cbt",
            name="uuid",
            field=models.UUIDField(blank=True, null=True, editable=False),
        ),
        migrations.AddField(
            model_name="question",
            name="uuid",
            field=models.UUIDField(blank=True, null=True, editable=False),
        ),
        migrations.AddField(
            model_name="choice",
            name="uuid",
            field=models.UUIDField(blank=True, null=True, editable=False),
        ),
        migrations.AddField(
            model_name="cbtattempt",
            name="uuid",
            field=models.UUIDField(blank=True, null=True, editable=False),
        ),
        migrations.AddField(
            model_name="cbtattemptanswer",
            name="uuid",
            field=models.UUIDField(blank=True, null=True, editable=False),
        ),
        migrations.AddField(
            model_name="userpreference",
            name="uuid",
            field=models.UUIDField(blank=True, null=True, editable=False),
        ),
        migrations.RunPython(populate_uuids, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="useraccess",
            name="uuid",
            field=models.UUIDField(default=uuid.uuid4, unique=True, editable=False),
        ),
        migrations.AlterField(
            model_name="voucher",
            name="uuid",
            field=models.UUIDField(default=uuid.uuid4, unique=True, editable=False),
        ),
        migrations.AlterField(
            model_name="video",
            name="uuid",
            field=models.UUIDField(default=uuid.uuid4, unique=True, editable=False),
        ),
        migrations.AlterField(
            model_name="cbt",
            name="uuid",
            field=models.UUIDField(default=uuid.uuid4, unique=True, editable=False),
        ),
        migrations.AlterField(
            model_name="question",
            name="uuid",
            field=models.UUIDField(default=uuid.uuid4, unique=True, editable=False),
        ),
        migrations.AlterField(
            model_name="choice",
            name="uuid",
            field=models.UUIDField(default=uuid.uuid4, unique=True, editable=False),
        ),
        migrations.AlterField(
            model_name="cbtattempt",
            name="uuid",
            field=models.UUIDField(default=uuid.uuid4, unique=True, editable=False),
        ),
        migrations.AlterField(
            model_name="cbtattemptanswer",
            name="uuid",
            field=models.UUIDField(default=uuid.uuid4, unique=True, editable=False),
        ),
        migrations.AlterField(
            model_name="userpreference",
            name="uuid",
            field=models.UUIDField(default=uuid.uuid4, unique=True, editable=False),
        ),
    ]
