from django.db import models
from django.conf import settings

class FloodReport(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="flood_reports", null=True, blank=True)
    rainfall = models.FloatField()
    river_level = models.FloatField()
    area_type = models.CharField(max_length=20)
    risk = models.CharField(max_length=10)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.risk} risk - {self.created_at:%Y-%m-%d %H:%M}"


class Conversation(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="chat_conversation",
    )
    title = models.CharField(max_length=120, default="My flood assistant")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user} - {self.title}"


class ChatMessage(models.Model):
    ROLE_CHOICES = (
        ("user", "User"),
        ("assistant", "Assistant"),
    )

    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE,
        related_name="messages",
    )
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at", "id"]

    def __str__(self):
        return f"{self.role} message at {self.created_at:%Y-%m-%d %H:%M}"


class DeletedAccount(models.Model):
    username = models.CharField(max_length=150)
    email = models.EmailField(blank=True)
    deleted_at = models.DateTimeField(auto_now_add=True)
    deleted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="account_deletions",
    )

    class Meta:
        ordering = ["-deleted_at"]

    def __str__(self):
        return f"{self.username} deleted at {self.deleted_at:%Y-%m-%d %H:%M}"