from django.contrib import admin
from .models import Post


class PostModelAdmin(admin.ModelAdmin):
    # admin画面で確認できる項目の羅列
    list_display = ["title", "updated", "timestamp"]

    # コラムへのリンクを貼る
    list_display_links = ["updated"]

    # リストを変更可能にする
    list_editable = ["title"]

    # フィルターを掛ける
    list_filter = ["updated", "timestamp"]

    # 検索可能にする
    search_fields = ["title", "content"]

    # このクラスはPost Modelを扱うよという宣言
    class Meta:
        model = Post

admin.site.register(Post, PostModelAdmin)
