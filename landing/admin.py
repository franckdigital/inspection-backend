from django.contrib import admin
from .models import (
    NewsArticle, FAQ, ResourceDocument, Testimonial,
    Campaign, PressRelease, PressAttachment, ContactMessage,
    InspectionOffice, AIKeywordResponse
)


@admin.register(NewsArticle)
class NewsArticleAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'author', 'published_at', 'is_featured', 'views')
    list_filter = ('category', 'is_featured', 'published_at')
    search_fields = ('title', 'content', 'author')
    prepopulated_fields = {'slug': ('title',)}
    date_hierarchy = 'published_at'


@admin.register(FAQ)
class FAQAdmin(admin.ModelAdmin):
    list_display = ('question', 'category', 'order', 'is_active')
    list_filter = ('category', 'is_active')
    search_fields = ('question', 'answer')
    list_editable = ('order', 'is_active')


@admin.register(ResourceDocument)
class ResourceDocumentAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'file_size', 'downloads', 'published_at', 'is_active')
    list_filter = ('category', 'is_active', 'published_at')
    search_fields = ('title', 'description')
    readonly_fields = ('file_size', 'downloads')


@admin.register(Testimonial)
class TestimonialAdmin(admin.ModelAdmin):
    list_display = ('author_name', 'author_role', 'rating', 'published_at', 'is_approved')
    list_filter = ('is_approved', 'rating', 'published_at')
    search_fields = ('author_name', 'content')
    list_editable = ('is_approved',)


@admin.register(Campaign)
class CampaignAdmin(admin.ModelAdmin):
    list_display = ('title', 'start_date', 'end_date', 'is_active')
    list_filter = ('is_active', 'start_date', 'end_date')
    search_fields = ('title', 'description')


class PressAttachmentInline(admin.TabularInline):
    model = PressAttachment
    extra = 1


@admin.register(PressRelease)
class PressReleaseAdmin(admin.ModelAdmin):
    list_display = ('title', 'contact_person', 'published_at', 'is_active')
    list_filter = ('is_active', 'published_at')
    search_fields = ('title', 'content', 'contact_person')
    inlines = [PressAttachmentInline]


@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'subject', 'is_read', 'is_replied', 'created_at')
    list_filter = ('is_read', 'is_replied', 'created_at')
    search_fields = ('name', 'email', 'subject', 'message')
    list_editable = ('is_read', 'is_replied')
    readonly_fields = ('name', 'email', 'phone', 'subject', 'message', 'created_at')


@admin.register(InspectionOffice)
class InspectionOfficeAdmin(admin.ModelAdmin):
    list_display = ('name', 'type', 'region', 'city', 'phone', 'is_active')
    list_filter = ('type', 'region', 'is_active')
    search_fields = ('name', 'region', 'city', 'address')


@admin.register(AIKeywordResponse)
class AIKeywordResponseAdmin(admin.ModelAdmin):
    list_display = ('keyword', 'question_example', 'priority', 'is_active', 'updated_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('keyword', 'question_example', 'response')
    list_editable = ('priority', 'is_active')
    fieldsets = (
        ('Mot-clé', {
            'fields': ('keyword', 'question_example')
        }),
        ('Réponse', {
            'fields': ('response',)
        }),
        ('Configuration', {
            'fields': ('priority', 'is_active')
        }),
    )
