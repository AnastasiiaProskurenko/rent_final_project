from django.contrib import admin
from django.utils import timezone
from .models import Payment, Refund


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'booking', 'amount', 'method', 'status', 'transaction_id', 'created_at')
    list_filter = ('method', 'status', 'created_at')
    search_fields = ('user__username', 'booking__id', 'transaction_id')
    readonly_fields = ('created_at', 'updated_at')
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Payment Details', {
            'fields': ('booking', 'user', 'amount', 'method', 'status')
        }),
        ('Transaction Info', {
            'fields': ('transaction_id', 'payment_details'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    actions = ['mark_as_completed', 'mark_as_failed']
    
    def mark_as_completed(self, request, queryset):
        queryset.update(status='completed')
        self.message_user(request, f'{queryset.count()} payments marked as completed.')
    mark_as_completed.short_description = "Mark selected payments as completed"
    
    def mark_as_failed(self, request, queryset):
        queryset.update(status='failed')
        self.message_user(request, f'{queryset.count()} payments marked as failed.')
    mark_as_failed.short_description = "Mark selected payments as failed"


@admin.register(Refund)
class RefundAdmin(admin.ModelAdmin):
    list_display = ('id', 'payment', 'amount', 'status', 'processed_by', 'processed_at', 'created_at')
    list_filter = ('status', 'created_at', 'processed_at')
    search_fields = ('payment__transaction_id', 'reason', 'processed_by__username')
    readonly_fields = ('created_at', 'updated_at')
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Refund Details', {
            'fields': ('payment', 'amount', 'reason', 'status')
        }),
        ('Processing', {
            'fields': ('processed_by', 'processed_at'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    actions = ['approve_refunds', 'reject_refunds']
    
    def approve_refunds(self, request, queryset):
        queryset.update(status='approved', processed_by=request.user, processed_at=timezone.now())
        self.message_user(request, f'{queryset.count()} refunds approved.')
    approve_refunds.short_description = "Approve selected refunds"
    
    def reject_refunds(self, request, queryset):
        queryset.update(status='rejected', processed_by=request.user, processed_at=timezone.now())
        self.message_user(request, f'{queryset.count()} refunds rejected.')
    reject_refunds.short_description = "Reject selected refunds"