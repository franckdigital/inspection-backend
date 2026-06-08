from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone

from .models import DocumentCategory, Document, DocumentVersion, DocumentAccess, Archive
from .serializers import (
    DocumentCategorySerializer, DocumentSerializer, DocumentVersionSerializer,
    DocumentAccessSerializer, ArchiveSerializer
)


class DocumentCategoryViewSet(viewsets.ModelViewSet):
    queryset = DocumentCategory.objects.all()
    serializer_class = DocumentCategorySerializer
    permission_classes = [permissions.IsAuthenticated]


class DocumentViewSet(viewsets.ModelViewSet):
    queryset = Document.objects.all()
    serializer_class = DocumentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    @action(detail=True, methods=['post'])
    def archive(self, request, pk=None):
        """Archiver un document"""
        document = self.get_object()
        document.status = 'ARCHIVED'
        document.archived_at = timezone.now()
        document.save()

        return Response({'message': 'Document archivé'})

    @action(detail=True, methods=['post'])
    def restore(self, request, pk=None):
        """Restaurer un document archivé"""
        document = self.get_object()
        document.status = 'ACTIVE'
        document.archived_at = None
        document.save()

        return Response({'message': 'Document restauré'})

    @action(detail=True, methods=['get'])
    def download(self, request, pk=None):
        """Télécharger un document"""
        document = self.get_object()

        # Logger l'accès
        DocumentAccess.objects.create(
            document=document,
            user=request.user,
            action='DOWNLOAD',
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )

        return Response({
            'file_url': document.file.url,
            'filename': document.file.name
        })

    @action(detail=False, methods=['get'])
    def search(self, request):
        """Recherche fulltext"""
        query = request.query_params.get('q', '')
        if query:
            documents = Document.objects.filter(
                title__icontains=query
            ) | Document.objects.filter(
                description__icontains=query
            )
        else:
            documents = Document.objects.all()

        serializer = self.get_serializer(documents[:50], many=True)
        return Response(serializer.data)


class DocumentVersionViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = DocumentVersion.objects.all()
    serializer_class = DocumentVersionSerializer
    permission_classes = [permissions.IsAuthenticated]


class DocumentAccessViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = DocumentAccess.objects.all()
    serializer_class = DocumentAccessSerializer
    permission_classes = [permissions.IsAuthenticated]


class ArchiveViewSet(viewsets.ModelViewSet):
    queryset = Archive.objects.all()
    serializer_class = ArchiveSerializer
    permission_classes = [permissions.IsAuthenticated]
