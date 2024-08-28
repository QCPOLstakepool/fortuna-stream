import subprocess

class Process:
    @staticmethod
    def run(process: list[str], input=None) -> str:
        completed_command = subprocess.run(process, capture_output=True, text=True, input=input)

        if not completed_command.returncode == 0:
            return ""

        return completed_command.stdout.strip()
