from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.http import HttpResponseRedirect
from django.contrib import messages
from .models import Video
import os
from django.conf import settings

@admin.register(Video)
class VideoAdmin(admin.ModelAdmin):
    list_display = [
        'id', 
        'title', 
        'file_size_display', 
        'uploaded_at', 
        'storage_location',
        'video_thumbnail',
        'view_video_link',
        'aws_s3_status'
    ]
    list_filter = ['uploaded_at']
    search_fields = ['title', 'description']
    readonly_fields = [
        'uploaded_at', 
        'file_size', 
        'video_player', 
        'aws_s3_url',
        'file_info',
        'storage_location'
    ]
    ordering = ['-uploaded_at']
    list_per_page = 20
    actions = ['migrate_to_s3', 'delete_selected']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'description')
        }),
        ('File Information', {
            'fields': ('video_file', 'file_size', 'uploaded_at', 'file_info'),
            'classes': ('collapse',)
        }),
        ('Storage Details', {
            'fields': ('storage_location', 'aws_s3_url', 'video_player'),
            'classes': ('collapse',)
        }),
    )
    
    def file_size_display(self, obj):
        if obj.file_size:
            size_mb = obj.file_size / (1024 * 1024)
            if size_mb < 1:
                return f"{round(obj.file_size / 1024, 1)} KB"
            else:
                return f"{round(size_mb, 2)} MB"
        return "Unknown"
    file_size_display.short_description = "File Size"
    file_size_display.admin_order_field = 'file_size'
    
    def storage_location(self, obj):
        """Check if file is stored on S3 or locally"""
        if obj.video_file:
            url = obj.video_file.url
            if 's3.amazonaws.com' in url or getattr(settings, 'AWS_STORAGE_BUCKET_NAME', '') in url:
                return format_html(
                    '<span style="color: #28a745; font-weight: bold;">☁️ AWS S3</span>'
                )
            else:
                return format_html(
                    '<span style="color: #ffc107; font-weight: bold;">💾 Local Storage</span>'
                )
        return format_html(
            '<span style="color: #dc3545;">❌ No File</span>'
        )
    storage_location.short_description = "Storage Location"
    
    def aws_s3_url(self, obj):
        if obj.video_file:
            url = obj.video_file.url
            is_s3 = 's3.amazonaws.com' in url or getattr(settings, 'AWS_STORAGE_BUCKET_NAME', '') in url
            
            if is_s3:
                return format_html(
                    '<a href="{}" target="_blank" style="color: #0066cc;">{}</a>',
                    url,
                    url[:60] + '...' if len(url) > 60 else url
                )
            else:
                return format_html(
                    '<span style="color: #ffc107;">⚠️ File stored locally: {}</span>',
                    url[:40] + '...' if len(url) > 40 else url
                )
        return "No file uploaded"
    aws_s3_url.short_description = "File URL"
    
    def video_thumbnail(self, obj):
        if obj.video_file:
            return format_html(
                '<video width="100" height="60" style="border-radius: 4px;">'
                '<source src="{}" type="video/mp4">'
                'Preview not available'
                '</video>',
                obj.video_file.url
            )
        return "No video"
    video_thumbnail.short_description = "Thumbnail"
    
    def video_player(self, obj):
        if obj.video_file:
            url = obj.video_file.url
            is_s3 = 's3.amazonaws.com' in url or getattr(settings, 'AWS_STORAGE_BUCKET_NAME', '') in url
            
            storage_info = "☁️ Stored on AWS S3" if is_s3 else "💾 Stored Locally"
            
            return format_html(
                '''
                <div style="margin-bottom: 10px;">
                    <span style="background: {}; color: white; padding: 4px 8px; border-radius: 4px; font-size: 12px;">
                        {}
                    </span>
                </div>
                <video width="400" controls style="border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
                    <source src="{}" type="video/mp4">
                    Your browser does not support the video tag.
                </video>
                <br><br>
                <a href="{}" target="_blank" class="button" style="margin-top: 10px;">
                    🔗 Open in New Tab
                </a>
                ''',
                '#28a745' if is_s3 else '#ffc107',
                storage_info,
                obj.video_file.url,
                obj.video_file.url
            )
        return "No video available"
    video_player.short_description = "Video Player"
    
    def view_video_link(self, obj):
        if obj.video_file:
            return format_html(
                '<a href="{}" target="_blank" class="button" style="background: #28a745; color: white; padding: 4px 8px; text-decoration: none; border-radius: 3px; font-size: 11px;">▶ View</a>',
                obj.video_file.url
            )
        return "No video"
    view_video_link.short_description = "Actions"
    
    def aws_s3_status(self, obj):
        if obj.video_file:
            url = obj.video_file.url
            is_s3 = 's3.amazonaws.com' in url or getattr(settings, 'AWS_STORAGE_BUCKET_NAME', '') in url
            
            if is_s3:
                return format_html(
                    '<span style="color: #28a745; font-weight: bold;">✓ S3</span>'
                )
            else:
                return format_html(
                    '<span style="color: #ffc107; font-weight: bold;">⚠ Local</span>'
                )
        return format_html(
            '<span style="color: #dc3545; font-weight: bold;">✗ Missing</span>'
        )
    aws_s3_status.short_description = "Status"
    
    def file_info(self, obj):
        if obj.video_file:
            try:
                url = obj.video_file.url
                file_name = url.split('/')[-1]
                is_s3 = 's3.amazonaws.com' in url or getattr(settings, 'AWS_STORAGE_BUCKET_NAME', '') in url
                
                storage_status = "☁️ AWS S3" if is_s3 else "💾 Local Storage"
                storage_color = "#28a745" if is_s3 else "#ffc107"
                
                info = f"""
                <table style="border-collapse: collapse; width: 100%;">
                    <tr><td><strong>File Name:</strong></td><td>{file_name}</td></tr>
                    <tr><td><strong>Size:</strong></td><td>{self.file_size_display(obj)}</td></tr>
                    <tr><td><strong>Uploaded:</strong></td><td>{obj.uploaded_at.strftime('%Y-%m-%d %H:%M:%S')}</td></tr>
                    <tr><td><strong>Storage:</strong></td><td><span style="color: {storage_color}; font-weight: bold;">{storage_status}</span></td></tr>
                    <tr><td><strong>URL:</strong></td><td><a href="{url}" target="_blank" style="word-break: break-all;">{url[:50]}...</a></td></tr>
                </table>
                """
                if not is_s3:
                    info += """
                    <div style="margin-top: 10px; padding: 8px; background: #fff3cd; border-radius: 4px; border-left: 4px solid #ffc107;">
                        <strong>⚠️ Notice:</strong> This file is stored locally. Use the "Migrate to S3" action to move it to AWS S3.
                    </div>
                    """
                
                return mark_safe(info)
            except Exception as e:
                return f"File information not available: {str(e)}"
        return "No file uploaded"
    file_info.short_description = "File Details"
    
    def migrate_to_s3(self, request, queryset):
        """Custom admin action to migrate local files to S3"""
        migrated_count = 0
        error_count = 0
        
        for video in queryset:
            if video.video_file:
                url = video.video_file.url
                is_local = not ('s3.amazonaws.com' in url or getattr(settings, 'AWS_STORAGE_BUCKET_NAME', '') in url)
                
                if is_local:
                    try:
                        # Check if local file exists
                        if hasattr(video.video_file, 'path'):
                            local_path = video.video_file.path
                            if os.path.exists(local_path):
                                # Re-save to trigger S3 upload
                                with open(local_path, 'rb') as f:
                                    video.video_file.save(
                                        os.path.basename(local_path),
                                        f,
                                        save=True
                                    )
                                migrated_count += 1
                            else:
                                error_count += 1
                        else:
                            error_count += 1
                    except Exception as e:
                        error_count += 1
                        self.message_user(
                            request,
                            f"Error migrating {video.title}: {str(e)}",
                            level=messages.ERROR
                        )
        
        if migrated_count > 0:
            self.message_user(
                request,
                f"Successfully migrated {migrated_count} video(s) to AWS S3.",
                level=messages.SUCCESS
            )
        
        if error_count > 0:
            self.message_user(
                request,
                f"Failed to migrate {error_count} video(s). Check if local files exist.",
                level=messages.WARNING
            )
        
        if migrated_count == 0 and error_count == 0:
            self.message_user(
                request,
                "Selected videos are already on S3 or no local files found.",
                level=messages.INFO
            )
    
    migrate_to_s3.short_description = "🔄 Migrate selected videos to AWS S3"
    
    def save_model(self, request, obj, form, change):
        """Override save to ensure new uploads go to S3"""
        super().save_model(request, obj, form, change)
        
        # Check if file was saved to S3
        if obj.video_file:
            url = obj.video_file.url
            is_s3 = 's3.amazonaws.com' in url or getattr(settings, 'AWS_STORAGE_BUCKET_NAME', '') in url
            
            if is_s3:
                messages.success(request, f"✅ Video '{obj.title}' successfully uploaded to AWS S3!")
            else:
                messages.warning(request, f"⚠️ Video '{obj.title}' was saved locally. Check your S3 configuration.")

# Custom admin site titles
admin.site.site_header = "Video Management System"
admin.site.site_title = "Video Admin"
admin.site.index_title = "Welcome to Video Management"