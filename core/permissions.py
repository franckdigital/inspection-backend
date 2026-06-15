"""
Permissions RBAC centralisées — Plateforme e-Inspection du Travail
Chaque classe couvre un niveau hiérarchique ou un rôle fonctionnel.
"""
from rest_framework.permissions import BasePermission, SAFE_METHODS

# ─── Groupes de rôles ────────────────────────────────────────────────────────
INSPECTION_ROLES   = {'INSPECTEUR', 'CHEF_INSPECTION', 'DIRECTEUR_REGIONAL', 'DIRECTEUR_GENERAL', 'ADMIN'}
HIERARCHY_ROLES    = {'CHEF_INSPECTION', 'DIRECTEUR_REGIONAL', 'DIRECTEUR_GENERAL', 'ADMIN'}
MANAGEMENT_ROLES   = {'DIRECTEUR_REGIONAL', 'DIRECTEUR_GENERAL', 'ADMIN'}
DIRECTION_ROLES    = {'DIRECTEUR_GENERAL', 'ADMIN'}
WORKER_ROLES       = {'EMPLOYE', 'EMPLOYE_MAISON'}
ALL_STAFF_ROLES    = INSPECTION_ROLES | {'EMPLOYEUR'}


# ─── Permissions atomiques ────────────────────────────────────────────────────

class IsAdmin(BasePermission):
    """Uniquement l'administrateur système."""
    message = "Accès réservé aux administrateurs."

    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.user_type == 'ADMIN'


class IsDirecteurGeneral(BasePermission):
    """Directeur Général ou Admin."""
    message = "Accès réservé à la Direction Générale."

    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.user_type in DIRECTION_ROLES


class IsDirecteur(BasePermission):
    """Directeur Régional, DG ou Admin."""
    message = "Accès réservé aux directeurs."

    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.user_type in MANAGEMENT_ROLES


class IsChefInspection(BasePermission):
    """Chef d'Inspection et niveaux supérieurs."""
    message = "Accès réservé aux Chefs d'Inspection et à la hiérarchie."

    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.user_type in HIERARCHY_ROLES


class IsInspecteur(BasePermission):
    """Inspecteur du Travail et niveaux supérieurs."""
    message = "Accès réservé aux Inspecteurs du Travail."

    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.user_type in INSPECTION_ROLES


class IsEmployeur(BasePermission):
    """Employeur uniquement."""
    message = "Accès réservé aux employeurs."

    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.user_type == 'EMPLOYEUR'


class IsEmploye(BasePermission):
    """Employé salarié ou employé de maison."""
    message = "Accès réservé aux employés."

    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.user_type in WORKER_ROLES


class IsEmployeMaison(BasePermission):
    """Travailleur domestique uniquement."""
    message = "Accès réservé aux employés de maison."

    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.user_type == 'EMPLOYE_MAISON'


# ─── Permissions mixtes ───────────────────────────────────────────────────────

class IsInspecteurOrEmploye(BasePermission):
    """Inspecteurs ET employés (lecture employés, écriture inspecteurs)."""
    message = "Accès non autorisé."

    def has_permission(self, request, view):
        return request.user.is_authenticated and (
            request.user.user_type in INSPECTION_ROLES or
            request.user.user_type in WORKER_ROLES
        )


class IsInspecteurOrEmployeur(BasePermission):
    """Inspecteurs ET employeurs."""
    message = "Accès réservé aux inspecteurs ou employeurs."

    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.user_type in (
            INSPECTION_ROLES | {'EMPLOYEUR'}
        )


class IsOwnerOrInspecteur(BasePermission):
    """L'objet appartient à l'utilisateur, ou c'est un inspecteur+."""
    message = "Accès non autorisé à cette ressource."

    def has_object_permission(self, request, view, obj):
        if request.user.user_type in INSPECTION_ROLES:
            return True
        # Essaie plusieurs attributs d'appartenance
        for attr in ('user', 'complainant', 'worker'):
            if hasattr(obj, attr) and getattr(obj, attr) == request.user:
                return True
        return False


class IsInspecteurReadOnly(BasePermission):
    """Lecture pour tous les authentifiés, écriture pour les inspecteurs+."""
    message = "Modification réservée aux Inspecteurs du Travail."

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        if request.method in SAFE_METHODS:
            return True
        return request.user.user_type in INSPECTION_ROLES


class IsAdminOrReadOnly(BasePermission):
    """Lecture pour tous les authentifiés, écriture pour l'admin."""
    message = "Modification réservée à l'administrateur."

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        if request.method in SAFE_METHODS:
            return True
        return request.user.user_type == 'ADMIN'
