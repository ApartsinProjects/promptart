from core.paDocs import DocMng


class TaskErrorHandler:
    def __init__(self, db):
        self.db = db

    def transformer_error_handler(self, event: dict, error: str):
        task_id = event["task_id"]
        curr_task = self.db.selectObj("tasks", task_id)
        tasks_to_del = []
        # get all applyTransformer tasks that in any way related to the current task
        while curr_task.get("parent") and curr_task["method"] == "applyTransformer":
            if parent_task := self.db.selectObj("tasks", curr_task["parent"]):
                child_tasks = self.db.findRows("tasks", {"parent": curr_task['parent']})  # change query parameter from string to dict
                tasks_to_del += child_tasks
            curr_task = parent_task

        # if we tried to generate and pay for only one feed, we need to delete the genAndPayFeed task as well
        if curr_task["method"] == "procFeed":
            tasks_to_del.append(curr_task)
            gen_and_pay_feed_task = self.db.selectObj("tasks", curr_task["parent"])
            assert gen_and_pay_feed_task["method"] == "genAndPayFeed"
            proc_feed_tasks = self.db.findRows("tasks", {"parent": gen_and_pay_feed_task['uid']})
            if len(proc_feed_tasks) == 1:
                tasks_to_del.append(gen_and_pay_feed_task)

        doc_mng = DocMng(self.db)
        for task in tasks_to_del:
            if task["did"]:
                doc_mng.delete(task["did"])
            self.db.deleteObj("tasks", task["uid"])

    def handle(self, event: dict, error: str):
        method = event["method"]
        if method == "applyTransformer":
            self.transformer_error_handler(event, error)
        print(f"Error occurred: {error}")

