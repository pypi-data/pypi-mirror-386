from django.db import models


class WhatsAppContact(models.Model):
    wa_id = models.CharField(max_length=32, unique=True, db_index=True)
    profile_name = models.CharField(max_length=255, null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = "django_whatsapp_api_wrapper"
        verbose_name = "WhatsApp Contact"
        verbose_name_plural = "WhatsApp Contacts"

    def __str__(self) -> str:
        return f"{self.profile_name or ''} ({self.wa_id})".strip()


class ConversationInfo(models.Model):
    conversation_id = models.CharField(max_length=64, unique=True, db_index=True)
    origin_type = models.CharField(max_length=64, null=True, blank=True)
    expiration_timestamp = models.DateTimeField(null=True, blank=True)
    pricing_model = models.CharField(max_length=32, null=True, blank=True)
    category = models.CharField(max_length=64, null=True, blank=True)
    billable = models.BooleanField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = "django_whatsapp_api_wrapper"
        verbose_name = "Conversation Info"
        verbose_name_plural = "Conversation Infos"

    def __str__(self) -> str:
        return self.conversation_id


class WebhookEvent(models.Model):
    KIND_MESSAGE = "message"
    KIND_STATUS = "status"
    KIND_UNKNOWN = "unknown"
    KIND_CHOICES = [
        (KIND_MESSAGE, "Message"),
        (KIND_STATUS, "Status"),
        (KIND_UNKNOWN, "Unknown"),
    ]

    # Common envelope fields
    object = models.CharField(max_length=64, null=True, blank=True)
    entry_id = models.CharField(max_length=128, null=True, blank=True)
    field = models.CharField(max_length=64, null=True, blank=True)

    phone_number_id = models.CharField(max_length=64, null=True, blank=True, db_index=True)
    display_phone_number = models.CharField(max_length=32, null=True, blank=True)

    # Event identifiers
    event_kind = models.CharField(max_length=16, choices=KIND_CHOICES, db_index=True)
    subtype = models.CharField(max_length=32, null=True, blank=True, db_index=True)
    wamid = models.CharField(max_length=128, null=True, blank=True, db_index=True)
    from_wa_id = models.CharField(max_length=32, null=True, blank=True, db_index=True)

    event_timestamp = models.DateTimeField(null=True, blank=True, db_index=True)
    webhook_received_at = models.DateTimeField(auto_now_add=True)

    raw_payload = models.JSONField()

    class Meta:
        app_label = "django_whatsapp_api_wrapper"
        verbose_name = "Webhook Event"
        verbose_name_plural = "Webhook Events"
        indexes = [
            models.Index(fields=["wamid"]),
            models.Index(fields=["event_kind", "subtype"]),
            models.Index(fields=["event_timestamp"]),
            models.Index(fields=["phone_number_id"]),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["wamid", "event_kind", "subtype"],
                name="uniq_event_wamid_kind_subtype",
                deferrable=models.Deferrable.DEFERRED,
            )
        ]

    def __str__(self) -> str:
        return f"{self.event_kind}:{self.subtype or '-'}:{self.wamid or '-'}"


class MessageText(models.Model):
    event = models.OneToOneField(WebhookEvent, on_delete=models.CASCADE, related_name="message_text")
    body = models.TextField()

    class Meta:
        app_label = "django_whatsapp_api_wrapper"
        verbose_name = "Message Text"
        verbose_name_plural = "Message Texts"


class MessageReaction(models.Model):
    event = models.OneToOneField(WebhookEvent, on_delete=models.CASCADE, related_name="message_reaction")
    reacted_message_id = models.CharField(max_length=128)
    emoji = models.CharField(max_length=32)

    class Meta:
        app_label = "django_whatsapp_api_wrapper"
        verbose_name = "Message Reaction"
        verbose_name_plural = "Message Reactions"


class MessageMedia(models.Model):
    TYPE_IMAGE = "image"
    TYPE_AUDIO = "audio"
    TYPE_VIDEO = "video"
    TYPE_DOCUMENT = "document"
    TYPE_STICKER = "sticker"
    TYPE_CHOICES = [
        (TYPE_IMAGE, "Image"),
        (TYPE_AUDIO, "Audio"),
        (TYPE_VIDEO, "Video"),
        (TYPE_DOCUMENT, "Document"),
        (TYPE_STICKER, "Sticker"),
    ]

    event = models.OneToOneField(WebhookEvent, on_delete=models.CASCADE, related_name="message_media")
    media_type = models.CharField(max_length=16, choices=TYPE_CHOICES)
    media_id = models.CharField(max_length=128)
    mime_type = models.CharField(max_length=64, null=True, blank=True)
    sha256 = models.CharField(max_length=128, null=True, blank=True)
    caption = models.TextField(null=True, blank=True)

    class Meta:
        app_label = "django_whatsapp_api_wrapper"
        verbose_name = "Message Media"
        verbose_name_plural = "Message Media"


class MessageLocation(models.Model):
    event = models.OneToOneField(WebhookEvent, on_delete=models.CASCADE, related_name="message_location")
    latitude = models.DecimalField(max_digits=9, decimal_places=6)
    longitude = models.DecimalField(max_digits=9, decimal_places=6)
    name = models.CharField(max_length=255, null=True, blank=True)
    address = models.CharField(max_length=512, null=True, blank=True)

    class Meta:
        app_label = "django_whatsapp_api_wrapper"
        verbose_name = "Message Location"
        verbose_name_plural = "Message Locations"


class MessageContacts(models.Model):
    event = models.OneToOneField(WebhookEvent, on_delete=models.CASCADE, related_name="message_contacts")
    contacts = models.JSONField()

    class Meta:
        app_label = "django_whatsapp_api_wrapper"
        verbose_name = "Message Contacts"
        verbose_name_plural = "Message Contacts"


class MessageSystem(models.Model):
    event = models.OneToOneField(WebhookEvent, on_delete=models.CASCADE, related_name="message_system")
    system_type = models.CharField(max_length=64)
    body = models.TextField(null=True, blank=True)
    new_wa_id = models.CharField(max_length=32, null=True, blank=True)

    class Meta:
        app_label = "django_whatsapp_api_wrapper"
        verbose_name = "Message System"
        verbose_name_plural = "Message Systems"


class MessageOrder(models.Model):
    event = models.OneToOneField(WebhookEvent, on_delete=models.CASCADE, related_name="message_order")
    order = models.JSONField()

    class Meta:
        app_label = "django_whatsapp_api_wrapper"
        verbose_name = "Message Order"
        verbose_name_plural = "Message Orders"


class MessageUnknown(models.Model):
    event = models.OneToOneField(WebhookEvent, on_delete=models.CASCADE, related_name="message_unknown")
    errors = models.JSONField(null=True, blank=True)

    class Meta:
        app_label = "django_whatsapp_api_wrapper"
        verbose_name = "Message Unknown"
        verbose_name_plural = "Message Unknown"


class StatusUpdate(models.Model):
    STATUS_SENT = "sent"
    STATUS_DELIVERED = "delivered"
    STATUS_READ = "read"
    STATUS_FAILED = "failed"
    STATUS_CHOICES = [
        (STATUS_SENT, "Sent"),
        (STATUS_DELIVERED, "Delivered"),
        (STATUS_READ, "Read"),
        (STATUS_FAILED, "Failed"),
    ]

    event = models.OneToOneField(WebhookEvent, on_delete=models.CASCADE, related_name="status_update")
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, db_index=True)
    recipient_id = models.CharField(max_length=32, null=True, blank=True, db_index=True)

    # Error details for failed statuses
    error_code = models.IntegerField(null=True, blank=True)
    error_title = models.CharField(max_length=255, null=True, blank=True)
    error_message = models.CharField(max_length=512, null=True, blank=True)
    error_details = models.JSONField(null=True, blank=True)

    # Conversation / pricing info
    conversation = models.ForeignKey(ConversationInfo, on_delete=models.SET_NULL, null=True, blank=True, related_name="status_updates")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = "django_whatsapp_api_wrapper"
        verbose_name = "Status Update"
        verbose_name_plural = "Status Updates"


