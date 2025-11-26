from tortoise import Model, fields


class BotUser(Model):
    id = fields.BigIntField(primary_key=True, description="ID пользователя в Telegram")
    language_code = fields.CharField(max_length=10, description="Язык пользователя (ISO 639-1)")
    username = fields.CharField(max_length=32, null=True, description="@Username пользователя")
    full_name = fields.CharField(max_length=128, description="Полное имя пользователя")

    is_banned = fields.BooleanField(default=False, description="Забанен ли пользователь")
    
    created_at = fields.DatetimeField(
        auto_now_add=True, description="Дата регистрации пользователя"
    )
    updated_at = fields.DatetimeField(
        auto_now=True, description="Дата последнего изменения пользователя"
    )

    class Meta:
        table = "users"
        table_description = "Пользователи бота"
        indexes = (
            ("username",),
            ("is_banned",),  # Индекс для быстрой фильтрации при рассылках
        )

    def __str__(self):
        return f"BotUser(id={self.id}, username={self.username}, full_name={self.full_name})"