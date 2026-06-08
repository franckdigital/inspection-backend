"""
Transcription + traduction des déclarations vocales via OpenAI Whisper et GPT.
Lancé en arrière-plan (thread) après chaque soumission audio.
"""
import threading
import logging

logger = logging.getLogger(__name__)

# Correspondance langue app → code ISO Whisper
# Whisper supporte nativement le français ; Bambara/Dioula via "bm" ;
# pour les autres langues ivoiriennes on laisse Whisper détecter.
WHISPER_LANG_MAP = {
    'FRENCH':  'fr',
    'DIOULA':  'bm',   # Bambara (proche du Dioula, mutuellement intelligible)
    'BAOULE':  None,   # Pas de code ISO supporté → auto-détection
    'BETE':    None,
    'SENOUFO': None,
    'ANYIN':   None,
    'OTHER':   None,
}


def _run_transcription(complaint_id: int) -> None:
    """Transcrit et traduit une VoiceComplaint. Appelé dans un thread séparé."""
    from django.conf import settings
    from domestic.models import VoiceComplaint

    api_key = getattr(settings, 'OPENAI_API_KEY', '')
    if not api_key:
        logger.warning('OPENAI_API_KEY non configurée — transcription ignorée.')
        return

    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key)
    except ImportError:
        logger.error('Librairie openai non installée (pip install openai).')
        return

    try:
        vc = VoiceComplaint.objects.get(id=complaint_id)
    except VoiceComplaint.DoesNotExist:
        return

    # Marquer "en cours"
    vc.transcription_status = 'PROCESSING'
    vc.save(update_fields=['transcription_status'])

    try:
        # ── 1. Transcription Whisper ─────────────────────────────────────────
        lang_key = vc.selected_language or vc.detected_language or ''
        whisper_lang = WHISPER_LANG_MAP.get(lang_key)

        with vc.audio_file.open('rb') as audio_f:
            kwargs = {'model': 'whisper-1', 'file': audio_f}
            if whisper_lang:
                kwargs['language'] = whisper_lang
            transcript = client.audio.transcriptions.create(**kwargs)

        original_text = transcript.text.strip()
        vc.transcription_original = original_text

        # ── 2. Traduction GPT si pas en français ─────────────────────────────
        lang_display_map = dict(VoiceComplaint.LANGUAGE_CHOICES)
        lang_display = lang_display_map.get(lang_key, 'langue locale')

        if lang_key not in ('FRENCH', '') and original_text:
            response = client.chat.completions.create(
                model='gpt-3.5-turbo',
                temperature=0.2,
                max_tokens=1200,
                messages=[
                    {
                        'role': 'system',
                        'content': (
                            'Tu es un traducteur expert en langues ivoiriennes (Dioula, Baoulé, Bété, '
                            'Sénoufo, Anyin) vers le français. Traduis fidèlement le message suivant en '
                            'français courant. Ne rajoute aucun commentaire ni note, seulement la traduction. '
                            'Si certains mots restent incompréhensibles, laisse-les entre crochets [mot].'
                        ),
                    },
                    {
                        'role': 'user',
                        'content': (
                            f'Message en {lang_display} :\n\n{original_text}'
                        ),
                    },
                ],
            )
            vc.transcription_french = response.choices[0].message.content.strip()
        else:
            # Déjà en français : la transcription est la traduction
            vc.transcription_french = original_text

        vc.transcription_status = 'DONE'
        vc.save(update_fields=[
            'transcription_original', 'transcription_french', 'transcription_status'
        ])
        logger.info(f'Transcription réussie pour VoiceComplaint {complaint_id}')

    except Exception as exc:
        logger.error(f'Transcription échouée pour VoiceComplaint {complaint_id}: {exc}')
        try:
            vc.transcription_status = 'FAILED'
            vc.save(update_fields=['transcription_status'])
        except Exception:
            pass


def start_transcription_async(complaint_id: int) -> None:
    """Lance la transcription dans un thread daemon (non-bloquant)."""
    t = threading.Thread(
        target=_run_transcription,
        args=(complaint_id,),
        daemon=True,
        name=f'transcription-{complaint_id}',
    )
    t.start()
