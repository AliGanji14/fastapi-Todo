from locust import HttpUser, task, between


class QuickstartUser(HttpUser):
    @task
    def tasks_list(self):
        self.client.get("/tasks")

    @task
    def fetch_weather(self):
        self.client.get("/fetch-current-weather")

    @task
    def initiate_task(self):
        self.client.get("/initiate-task")

    @task
    def not_found(self):
        self.client.get("/not-found")
