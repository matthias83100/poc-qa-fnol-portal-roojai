from django.core.management.base import BaseCommand
from qa_dashboard.models import CallReport, Utterance, QACategory, QAQuestion
from django.utils import timezone
import random
from datetime import timedelta

class Command(BaseCommand):
    help = 'Generates diverse mock data for fnol_qa without Users'

    def handle(self, *args, **kwargs):
        self.stdout.write("Cleaning up existing data...")
        Utterance.objects.all().delete()
        QAQuestion.objects.all().delete()
        QACategory.objects.all().delete()
        CallReport.objects.all().delete()

        # 1. Define Agent/Manager structure
        teams = {
            'Manager 1': ['Agent 1', 'Agent 2', 'Agent 3'],
            'Manager 2': ['Agent 4', 'Agent 5']
        }
        
        all_agents = []
        for manager, agents in teams.items():
            for agent in agents:
                all_agents.append((agent, manager))

        # 2. Scenarios
        scenarios = [
            {
                'name': 'Standard Claim',
                'customer_emotions': ['neutral', 'neutral', 'satisfied'],
                'agent_emotions': ['professional'],
                'qa_success_rate': 0.8,
                'weight': 40
            },
            {
                'name': 'Frustrated Customer',
                'customer_emotions': ['frustrated', 'frustrated', 'anxious', 'neutral'],
                'agent_emotions': ['professional', 'professional', 'neutral'],
                'qa_success_rate': 0.6,
                'weight': 15
            },
            {
                'name': 'Positive Interaction',
                'customer_emotions': ['satisfied', 'satisfied', 'satisfied'],
                'agent_emotions': ['professional', 'professional'],
                'qa_success_rate': 0.95,
                'weight': 25
            },
            {
                'name': 'Anxious Reporter',
                'customer_emotions': ['anxious', 'anxious', 'neutral', 'satisfied'],
                'agent_emotions': ['professional', 'professional'],
                'qa_success_rate': 0.75,
                'weight': 20
            }
        ]

        scenario_list = []
        for s in scenarios:
            scenario_list.extend([s] * s['weight'])

        # 3. Generate Calls
        now = timezone.now()
        today = now.date()
        self.stdout.write(f"Generating 100 calls for the last 7 days...")
        
        # Ensure EVERY agent has at least 2 calls TODAY for the demo
        for agent_name, manager_name in all_agents:
            for i in range(2):
                hour = random.randint(8, 10)
                minute = random.randint(0, 59)
                call_date = timezone.make_aware(timezone.datetime.combine(today, timezone.datetime.min.time())) + timedelta(hours=hour, minutes=minute)
                
                scenario = random.choice(scenario_list)
                call = CallReport.objects.create(
                    agent_name=agent_name,
                    manager_name=manager_name,
                    filename=f"DEMO-{agent_name.replace(' ', '')}-{i}_{scenario['name'].replace(' ', '_')}.wav",
                    duration=f"00:0{random.randint(3,8)}:{random.randint(10,59)}.000",
                    system_processing_time=random.uniform(5.5, 45.2),
                    prompt_tokens=random.randint(1000, 4000),
                    candidates_tokens=random.randint(100, 1200),
                    cost_thb=random.uniform(0.3, 3.5),
                    queue=random.choice(['RJI', 'Thai', 'English']),
                    overall_score=random.uniform(60, 100) # Simplified for mock
                )
                # Overwrite auto_now_add
                CallReport.objects.filter(id=call.id).update(date_processed=call_date)
                self._generate_call_details(call, scenario)

        # Generate remaining random calls
        for i in range(80):
            agent_name, manager_name = random.choice(all_agents)
            scenario = random.choice(scenario_list)
            
            days_ago = random.randint(0, 7)
            hours_ago = random.randint(0, 23)
            call_date = now - timedelta(days=days_ago, hours=hours_ago)
            
            call = CallReport.objects.create(
                agent_name=agent_name,
                manager_name=manager_name,
                filename=f"CLA-{20240000 + i}_{scenario['name'].replace(' ', '_')}.wav",
                duration=f"00:0{random.randint(3,8)}:{random.randint(10,59)}.000",
                system_processing_time=random.uniform(5.5, 45.2),
                prompt_tokens=random.randint(1000, 4000),
                candidates_tokens=random.randint(100, 1200),
                cost_thb=random.uniform(0.3, 3.5),
                queue=random.choice(['RJI', 'Thai', 'English']),
                overall_score=random.uniform(60, 100)
            )
            CallReport.objects.filter(id=call.id).update(date_processed=call_date)
            self._generate_call_details(call, scenario)

        self.stdout.write(self.style.SUCCESS(f"Successfully generated 100 calls without User models!"))

    def _generate_call_details(self, call, scenario):
        num_utts = random.randint(5, 12)
        for j in range(num_utts):
            is_agent = (j % 2 == 0)
            speaker = "AGENT" if is_agent else "CUSTOMER"
            emotion = random.choice(scenario['agent_emotions'] if is_agent else scenario['customer_emotions'])
            
            Utterance.objects.create(
                call_report=call,
                timestamp=f"00:00:{j*5:02d}.000",
                speaker=speaker,
                text=f"Sample text for {speaker} in {scenario['name']} scenario.",
                emotion=emotion,
                language=random.choice(['thai', 'thai', 'thai', 'english', 'mixed']),
                order=j+1
            )

        categories = [
            ('call_procedure', ["Recording Consent", "Agent Introduction", "Closing Statement"]),
            ('information_gathering', ["Car Plate Verification", "Location Details", "Injury Report"]),
            ('customer_experience', ["Politeness", "Clear Explanation", "Empathy"])
        ]

        for cat_name, questions in categories:
            cat = QACategory.objects.create(call_report=call, category_name=cat_name)
            for q_text in questions:
                answer = 'Yes' if random.random() < scenario['qa_success_rate'] else 'No'
                if random.random() < 0.05: answer = 'NA' 
                
                QAQuestion.objects.create(
                    qa_category=cat,
                    question_id=str(random.randint(100, 999)),
                    question=q_text,
                    criteria=f"Criteria for {q_text}",
                    answer=answer,
                    explanation=f"Agent performed with {answer} for {q_text}."
                )
