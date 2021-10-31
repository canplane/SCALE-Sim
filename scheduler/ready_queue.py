class ReadyQueue:
    def __init__(self, algorithm_name: str):
        self.li = []

    def get_list(self) -> list:
        return self.li
    
    def push(self, task_id: int):
        self.li.append(task_id)

    def pop(self) -> int:
        return self.li.pop(0)