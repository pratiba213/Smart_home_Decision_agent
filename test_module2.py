from simulation.environment import Room
from temporary_fake_agent import FakeAgent
from dashboard.app import Dashboard

room = Room()
agent = FakeAgent()
dashboard = Dashboard(room, agent)
dashboard.run()