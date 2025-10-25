from django.contrib import admin
from .models import (
    WebhookEvent,
    WhatsAppContact,
    ConversationInfo,
    MessageText,
    MessageReaction,
    MessageMedia,
    MessageLocation,
    MessageContacts,
    MessageSystem,
    MessageOrder,
    MessageUnknown,
    StatusUpdate,
)


@admin.register(WebhookEvent)
class WebhookEventAdmin(admin.ModelAdmin):
    list_display = ("event_kind", "subtype", "wamid", "from_wa_id", "phone_number_id", "event_timestamp")
    list_filter = ("event_kind", "subtype", "phone_number_id")
    search_fields = ("wamid", "from_wa_id")
    readonly_fields = ("raw_payload",)


@admin.register(StatusUpdate)
class StatusUpdateAdmin(admin.ModelAdmin):
    list_display = ("status", "recipient_id", "error_code")
    list_filter = ("status",)
    search_fields = ("recipient_id",)


admin.site.register(WhatsAppContact)
admin.site.register(ConversationInfo)
admin.site.register(MessageText)
admin.site.register(MessageReaction)
admin.site.register(MessageMedia)
admin.site.register(MessageLocation)
admin.site.register(MessageContacts)
admin.site.register(MessageSystem)
admin.site.register(MessageOrder)
admin.site.register(MessageUnknown)


