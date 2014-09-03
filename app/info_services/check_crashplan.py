import os


class CheckCrashPlan(object):
    def __init__(self, filepath):
        assert os.path.exists(filepath)
        self.filepath = filepath

    def status(self):
        items_to_keep = ['scanning', 'backupenabled']
        with open(self.filepath, 'r') as f:
            items = [line.lower().split() for line in f.readlines() for x in items_to_keep if x in line.lower()]
        # remove "=" from list
        for item in items:
            item.remove('=')
        items_values = [True if item[1] == 'true' else False for item in items]
        if all(items_values):
            return 'active'
        elif any(items_values):
            return 'waiting'
        else:
            return False

