import wda

class Helper:

    def __init__(self):
        self.client = None
        self.bundle_id = None
        self.arguments = None
        self.environment = None
        self.session = None

    def start_app(self, *args, **env):
        """

        required:
        - bundle_id(string): app bundle id
        """
        self.client = wda.Client()
        self.session = self.client.session(
            bundle_id=self.bundle_id,
            arguments=self.arguments,
            environment=self.environment)

    def stop_app(self):
        self.session.close()
