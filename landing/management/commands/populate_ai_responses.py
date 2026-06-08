from django.core.management.base import BaseCommand
from landing.models import AIKeywordResponse


class Command(BaseCommand):
    help = 'Populate AI keyword responses with initial data'

    def handle(self, *args, **kwargs):
        # Données initiales pour l'assistant IA
        initial_responses = [
            {
                'keyword': 'plainte',
                'question_example': 'Comment déposer une plainte ?',
                'response': "Pour déposer une plainte, vous devez créer un compte sur notre plateforme, puis accéder à la section 'Mes Plaintes' et cliquer sur 'Nouvelle Plainte'. Vous serez guidé à travers le processus de dépôt. Vous devrez fournir des informations sur votre employeur, la nature du problème et toute preuve que vous avez.",
                'priority': 1,
            },
            {
                'keyword': 'licenciement',
                'question_example': 'Quels sont mes droits en cas de licenciement ?',
                'response': "En cas de licenciement, vous avez droit à un préavis selon votre ancienneté. Un employeur doit avoir un motif valable pour licencier (faute grave, raisons économiques, etc.). Si vous estimez votre licenciement abusif, vous pouvez déposer une plainte auprès de l'inspection du travail dans un délai de 2 mois.",
                'priority': 2,
            },
            {
                'keyword': 'préavis',
                'question_example': 'Quelle est la durée du préavis ?',
                'response': "La durée du préavis dépend de votre ancienneté :\n• Moins de 5 ans : 1 mois de préavis\n• Entre 5 et 10 ans : 2 mois de préavis\n• Plus de 10 ans : 3 mois de préavis\n\nCe délai peut être réduit en cas de faute grave ou d'accord entre les parties.",
                'priority': 3,
            },
            {
                'keyword': 'heures supplémentaires',
                'question_example': 'Comment sont payées les heures supplémentaires ?',
                'response': "Les heures supplémentaires sont les heures travaillées au-delà de 40h par semaine. Elles doivent être rémunérées avec une majoration :\n• +15% pour les 8 premières heures supplémentaires\n• +50% au-delà de 8 heures supplémentaires\n• +75% pour le travail de nuit (21h-5h)\n• +100% pour le travail le dimanche et jours fériés",
                'priority': 4,
            },
            {
                'keyword': 'salaire',
                'question_example': 'Quel est le salaire minimum en Côte d\'Ivoire ?',
                'response': "Le salaire minimum garanti (SMIG) en Côte d'Ivoire est de 75 000 FCFA par mois pour 173,33 heures de travail. Votre employeur doit vous payer au moins ce montant. Les retenues sur salaire sont strictement encadrées par la loi et ne peuvent excéder le tiers du salaire brut.",
                'priority': 5,
            },
            {
                'keyword': 'congés',
                'question_example': 'Combien de jours de congés ai-je droit ?',
                'response': "Vous avez droit à 2 jours ouvrables de congés payés par mois de travail effectif, soit 24 jours par an (environ 26 jours calendaires). Les congés ne peuvent être remplacés par une indemnité compensatrice sauf en cas de rupture du contrat. L'employeur fixe les dates de congés après consultation du salarié.",
                'priority': 6,
            },
            {
                'keyword': 'contrat',
                'question_example': 'Quels sont les types de contrats de travail ?',
                'response': "Il existe principalement 3 types de contrats en Côte d'Ivoire :\n• CDI (Contrat à Durée Indéterminée) : sans date de fin\n• CDD (Contrat à Durée Déterminée) : durée maximale de 2 ans, renouvelable une fois\n• Contrat d'essai : 1 à 6 mois selon la qualification\n\nLe contrat doit être écrit et signé par les deux parties.",
                'priority': 7,
            },
            {
                'keyword': 'démission',
                'question_example': 'Comment démissionner ?',
                'response': "Pour démissionner, vous devez :\n1. Envoyer une lettre de démission écrite à votre employeur\n2. Respecter le préavis (selon votre ancienneté)\n3. Vous pouvez négocier une dispense de préavis avec l'employeur\n\nAttention : la démission est définitive et ne donne pas droit aux allocations chômage.",
                'priority': 8,
            },
            {
                'keyword': 'discrimination',
                'question_example': 'Je subis une discrimination au travail',
                'response': "La discrimination au travail est strictement interdite (origine, sexe, religion, opinion politique, etc.). Si vous êtes victime de discrimination :\n1. Rassemblez des preuves (emails, témoins, etc.)\n2. Déposez une plainte sur notre plateforme\n3. Contactez l'inspection du travail\n4. Vous pouvez également saisir le tribunal du travail",
                'priority': 9,
            },
            {
                'keyword': 'harcèlement',
                'question_example': 'Je suis victime de harcèlement au travail',
                'response': "Le harcèlement (moral ou sexuel) est un délit pénal. Si vous êtes victime :\n1. Notez les faits avec dates et témoins\n2. Informez votre employeur par écrit\n3. Déposez une plainte sur notre plateforme\n4. Contactez l'inspection du travail\n5. Vous pouvez porter plainte au commissariat\n\nVous êtes protégé contre toute mesure de rétorsion.",
                'priority': 10,
            },
            {
                'keyword': 'default',
                'question_example': 'Question par défaut',
                'response': "Merci pour votre question. Pour des informations précises sur le droit du travail en Côte d'Ivoire, je vous recommande de :\n• Consulter notre centre de ressources\n• Contacter directement l'inspection du travail\n• Poser une question plus spécifique en utilisant des mots-clés comme : plainte, licenciement, salaire, congés, etc.\n\nVous pouvez également déposer une plainte en ligne si vous rencontrez un problème avec votre employeur.",
                'priority': 999,
            },
        ]

        created_count = 0
        updated_count = 0

        for data in initial_responses:
            obj, created = AIKeywordResponse.objects.update_or_create(
                keyword=data['keyword'],
                defaults={
                    'question_example': data['question_example'],
                    'response': data['response'],
                    'priority': data['priority'],
                    'is_active': True,
                }
            )
            if created:
                created_count += 1
            else:
                updated_count += 1

        self.stdout.write(
            self.style.SUCCESS(
                f'✅ Données IA créées avec succès !\n'
                f'   Créées: {created_count}\n'
                f'   Mises à jour: {updated_count}\n'
                f'   Total: {len(initial_responses)}'
            )
        )
