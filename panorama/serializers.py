from django.core.files.storage import default_storage
from rest_framework import serializers

from .models import Panorama


def _asset_url(context, name: str) -> str | None:
    if not name:
        return None
    url = default_storage.url(name)
    request = context.get("request")
    return request.build_absolute_uri(url) if request else url


class PanoramaListSerializer(serializers.ModelSerializer):
    """列表项：卡片所需（缩略图 + 状态 + 尺寸），不含取片模板等重字段。"""

    thumb_url = serializers.SerializerMethodField()
    preview_url = serializers.SerializerMethodField()

    class Meta:
        model = Panorama
        fields = [
            "id", "title", "description", "order", "is_published", "status",
            "width", "height", "origin", "device_model", "capture_heading",
            "thumb_url", "preview_url", "created_at", "updated_at",
        ]
        read_only_fields = fields

    def get_thumb_url(self, obj):
        return _asset_url(self.context, obj.thumb_name)

    def get_preview_url(self, obj):
        return _asset_url(self.context, obj.preview_name)


class PanoramaDetailSerializer(serializers.ModelSerializer):
    """详情：额外给出取片模板、层级表与原始参数（前端据此建 Marzipano 场景）。

    可写字段只有「人调得着」的那些（标题 / 描述 / 排序 / 公开 / 初始视角）；
    尺寸、元数据、瓦片产物一律只读——它们由切片流水线写。
    """

    thumb_url = serializers.SerializerMethodField()
    preview_url = serializers.SerializerMethodField()
    source_url = serializers.SerializerMethodField()
    tile_url_template = serializers.SerializerMethodField()

    class Meta:
        model = Panorama
        fields = [
            "id", "title", "description", "order", "is_published",
            "status", "error", "origin", "device_model", "metadata",
            "width", "height", "projection", "source_name", "source_bytes",
            "initial_yaw", "initial_pitch", "initial_fov", "capture_heading",
            "tile_size", "tile_levels", "tile_url_template",
            "preview_url", "thumb_url", "source_url",
            "created_by", "created_at", "updated_at",
        ]
        read_only_fields = [
            "status", "error", "origin", "device_model", "metadata",
            "width", "height", "projection", "source_name", "source_bytes",
            "capture_heading", "tile_size", "tile_levels", "tile_url_template",
            "preview_url", "thumb_url", "source_url",
            "created_by", "created_at", "updated_at",
        ]

    def get_thumb_url(self, obj):
        return _asset_url(self.context, obj.thumb_name)

    def get_preview_url(self, obj):
        return _asset_url(self.context, obj.preview_name)

    def get_tile_url_template(self, obj):
        return _asset_url(self.context, obj.tile_dir and f"{obj.tile_dir}/{{z}}/{{y}}/{{x}}.jpg")

    def get_source_url(self, obj):
        """原图（5~8MB）是受限读：只给持管理权限的人，避免公网白拿大文件。

        这是字段掩码（可见性轴的收窄），不是访问控制——写入仍由
        ``CanManagePanorama`` 门禁（ADR-0005 决策 1 / 8）。
        """
        request = self.context.get("request")
        user = getattr(request, "user", None)
        if not (
            user
            and user.is_authenticated
            and user.has_perm("panorama.manage_panoramas")
        ):
            return None
        return _asset_url(self.context, obj.source.name)
