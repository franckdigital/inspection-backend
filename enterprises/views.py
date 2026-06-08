from rest_framework import viewsets, filters, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from .models import Enterprise, EnterpriseBranch, EnterpriseDocument, EnterpriseHistory
from .serializers import (
    EnterpriseSerializer, EnterpriseDetailSerializer, EnterpriseBranchSerializer,
    EnterpriseDocumentSerializer, EnterpriseHistorySerializer
)


class EnterpriseViewSet(viewsets.ModelViewSet):
    queryset = Enterprise.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['sector', 'city', 'risk_level', 'is_active', 'is_verified']
    search_fields = ['name', 'rccm', 'nif', 'email']
    ordering_fields = ['name', 'created_at', 'compliance_score', 'employee_count']

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return EnterpriseDetailSerializer
        return EnterpriseSerializer

    @action(detail=True, methods=['get'])
    def branches(self, request, pk=None):
        enterprise = self.get_object()
        branches = enterprise.branches.all()
        serializer = EnterpriseBranchSerializer(branches, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def documents(self, request, pk=None):
        enterprise = self.get_object()
        documents = enterprise.documents.all()
        serializer = EnterpriseDocumentSerializer(documents, many=True, context={'request': request})
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def history(self, request, pk=None):
        enterprise = self.get_object()
        history = enterprise.history.all()
        serializer = EnterpriseHistorySerializer(history, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def update_score(self, request, pk=None):
        enterprise = self.get_object()
        enterprise.update_compliance_score()
        return Response({
            'compliance_score': enterprise.compliance_score,
            'risk_level': enterprise.risk_level
        })


class EnterpriseBranchViewSet(viewsets.ModelViewSet):
    queryset = EnterpriseBranch.objects.all()
    serializer_class = EnterpriseBranchSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['enterprise', 'city', 'is_active']
    search_fields = ['name', 'city', 'manager_name']


class EnterpriseDocumentViewSet(viewsets.ModelViewSet):
    queryset = EnterpriseDocument.objects.all()
    serializer_class = EnterpriseDocumentSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['enterprise', 'document_type', 'is_verified']


class EnterpriseHistoryViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = EnterpriseHistory.objects.all()
    serializer_class = EnterpriseHistorySerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['enterprise', 'event_type']
