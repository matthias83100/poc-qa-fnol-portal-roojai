import os
import json
import datetime
from django.core.management.base import BaseCommand
from django.utils import timezone
from qa_dashboard.models import CallReport, Utterance, QACategory, QAQuestion

class Command(BaseCommand):
    help = 'Loads real calls from JSON files into the database'

    def add_arguments(self, parser):
        parser.add_argument('--folders', type=str, nargs='+', help='Paths to the folders containing JSON files', default=[
            r'c:\Users\matthias.sto\OneDrive - Roojai THAILAND\Desktop\QA-Portal-FNOL-POC\OneDrive_1_4-10-2026\EN',
            r'c:\Users\matthias.sto\OneDrive - Roojai THAILAND\Desktop\QA-Portal-FNOL-POC\OneDrive_1_4-10-2026\TH'
        ])

    def handle(self, *args, **options):
        folders = options['folders']
        today = timezone.now()
        calls_created = 0

        for folder in folders:
            if not os.path.exists(folder):
                self.stdout.write(self.style.WARNING(f"Folder not found: {folder}. Skipping."))
                continue

            for filename in os.listdir(folder):
                if not filename.endswith('.json'):
                    continue

                filepath = os.path.join(folder, filename)
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"Error reading {filename}: {e}"))
                    continue

                orig_filename = data.get('filename', filename)
                
                # We use today's date so it shows up in real time on the dashboard
                date_processed = today

                # Avoid duplicates
                if CallReport.objects.filter(filename=orig_filename).exists():
                    self.stdout.write(self.style.WARNING(f"Call with filename {orig_filename} already exists. Skipping."))
                    continue

                duration_seconds = data.get('duration', 0)
                td = datetime.timedelta(seconds=int(duration_seconds))
                # Add .000 to the string formatted timedelta
                duration_str = f"0{td}.000" if td.seconds < 36000 else f"{td}.000"
                # For hour >= 10, timedelta string is hh:mm:ss. If < 10, it's h:mm:ss. Zeros padded by 0.
                if len(str(td)) == 7: # h:mm:ss
                   duration_str = f"0{td}.000"
                elif len(str(td)) == 8: # hh:mm:ss
                   duration_str = f"{td}.000"

                prompt_tokens = data.get('usage', {}).get('qa', [0, 0])[0]
                candidates_tokens = data.get('usage', {}).get('qa', [0, 0])[1] if len(data.get('usage', {}).get('qa', [])) > 1 else 0

                call_report = CallReport.objects.create(
                    agent_name=data.get('agent', 'Unknown Agent'),
                    manager_name='System', # Not present in JSON
                    filename=orig_filename,
                    duration=duration_str,
                    system_processing_time=data.get('process_time', 0.0),
                    prompt_tokens=prompt_tokens,
                    candidates_tokens=candidates_tokens,
                    cost_thb=0.0, # Placeholder or calculation
                    queue=data.get('queue', 'Unknown Queue'),
                    overall_score=0.0 # We will update this later
                )
                # Overwrite auto_now_add
                CallReport.objects.filter(id=call_report.id).update(date_processed=date_processed)


                qa_json_raw = data.get('qa_json', {})
                if isinstance(qa_json_raw, list) and len(qa_json_raw) > 0:
                    qa_json = qa_json_raw[0]
                else:
                    qa_json = qa_json_raw

                categories = []
                if isinstance(qa_json, dict):
                    categories = qa_json.get('categories', [])
                
                for cat_data in categories:
                    cat_name = cat_data.get('category_name', 'Unnamed Category')
                    db_category = QACategory.objects.create(
                        call_report=call_report,
                        category_name=cat_name
                    )

                    for q_data in cat_data.get('questions', []):
                        answer = q_data.get('answer', 'NA')
                        if answer == 'None' or answer is None:
                            answer = 'NA'
                        elif answer not in ['Yes', 'No', 'NA']:
                            answer = 'NA'

                        QAQuestion.objects.create(
                            qa_category=db_category,
                            question_id=q_data.get('id', '0'),
                            question=q_data.get('question', ''),
                            criteria=q_data.get('criteria', ''),
                            answer=answer,
                            evidence=q_data.get('evidence', 'N/A'),
                            explanation=q_data.get('explanation', '')
                        )

                # Initialize Utterances
                transcript_json = data.get('transcript_json', [])
                if isinstance(transcript_json, dict):
                    transcript = transcript_json.get('transcript', [])
                else:
                    transcript = transcript_json

                for i, utt_data in enumerate(transcript):
                    Utterance.objects.create(
                        call_report=call_report,
                        timestamp=utt_data.get('timestamp', '00:00:00.000'),
                        speaker=utt_data.get('speaker', 'Unknown'),
                        text=utt_data.get('text', ''),
                        emotion=utt_data.get('emotion', 'neutral'),
                        language=utt_data.get('language', 'unknown'),
                        order=i + 1
                    )

                # Calculate final score based on relations
                call_report.refresh_from_db()
                new_score = call_report.calculate_score()
                CallReport.objects.filter(id=call_report.id).update(overall_score=new_score)

                calls_created += 1
                self.stdout.write(self.style.SUCCESS(f"Successfully loaded call {orig_filename}"))

        self.stdout.write(self.style.SUCCESS(f"Done loading {calls_created} real calls!"))
