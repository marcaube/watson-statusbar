import re
import subprocess
from datetime import datetime

import rumps
from rumps import MenuItem

STATUS_REGEX = r'Project ([a-zA-Z\-_ \/]+)\s?(?:\[.+\])? started .+\((.+)\)'
DATETIME_FORMAT = '%Y.%m.%d %H:%M:%S%z'

TITLE_DEFAULT = '⏱ Watson'
TITLE_TASK = '⏱ {task_name} {time}'


def get_watson_status():
    print('[-] Retrieving Watson status...')
    output = subprocess.getoutput('watson status')
    matches = re.match(STATUS_REGEX, output)

    if not matches:
        return None, None

    project_name, start_time = matches.groups()
    start_time = datetime.strptime(start_time, DATETIME_FORMAT)

    return project_name, start_time


def get_watson_projects():
    print('[-] Retrieving the list of Watson projects...')
    output = subprocess.getoutput('watson projects')

    return output.splitlines()


projects = get_watson_projects()


class WatsonStatusBar(rumps.App):
    task_started = False
    task_name = None
    task_start_time = None

    def __init__(self):
        super().__init__(TITLE_DEFAULT)

        print('[-] Booting the app...')

        # Check if there's currently a running task
        self.task_name, self.task_start_time = get_watson_status()
        if self.task_name and self.task_start_time:
            self.task_started = True

        # Fill menu items and bind click events
        for project in projects:
            menu_item = MenuItem(project, callback=None if self.task_started else self.project_click)
            self.menu.add(menu_item)

        # Add an empty line before the Quit button
        self.menu.add(None)
        self.menu.add('Stop')

    def project_click(self, sender: MenuItem):
        """
        Handle a click on an existing project in the taskbar menu.
        """
        self.start_project(sender.title)

    def stop_click(self, _):
        """
        Handle a click on the stop button
        """
        self.stop_project(_)

    def start_project(self, project_name: str):
        """
        Start timer for a given project
        """
        print(f'[-] Starting timer for "{project_name}"...')
        output = subprocess.getoutput(f'watson start {project_name}')

        if 'Starting project' in output:
            self.task_name, self.task_start_time = get_watson_status()
            self.task_started = True

            # Disable the menu items for all projects
            for project in projects:
                self.menu[project].set_callback(None)

    def stop_project(self, _):
        """
        Handle a click on the stop button
        """
        print(f'[-] Stopping timer for {self.task_name}...')
        output = subprocess.getoutput('watson stop')

        if 'Stopping project' in output or 'No project started.' in output:
            self.task_started = False

            # Re-enable the menu items for all projects
            projects = get_watson_projects()
            for project in projects:
                self.menu[project].set_callback(self.project_click)

    @rumps.clicked('New Project')
    def new_project(self, _):
        window = rumps.Window(
            title='Enter a project name',
            dimensions=(250, 23),
        )

        if project_name := window.run().text:
            self.start_project(project_name)
            menu_item = MenuItem(project_name, callback=None)
            self.menu.insert_after(projects[-1], menu_item)
            projects.append(project_name)

    @rumps.timer(1)
    def update_title(self, _):
        """
        Update the timer in the taskbar if there's a task running.
        """
        if not self.task_started:
            self.title = TITLE_DEFAULT
            self.menu['Stop'].set_callback(None)
            self.menu['New Project'].set_callback(self.new_project)
            return

        if not self.task_name or not self.task_start_time:
            self.task_name, self.task_start_time = get_watson_status()

        elapsed_time = datetime.now(tz=self.task_start_time.tzinfo) - self.task_start_time
        formatted_time = f'{elapsed_time.seconds // 60:02}:{elapsed_time.seconds % 60:02}'

        self.title = TITLE_TASK.format(task_name=self.task_name, time=formatted_time)
        self.menu['Stop'].set_callback(self.stop_click)
        self.menu['New Project'].set_callback(None)

    @rumps.timer(60)
    def check_if_running(self, _):
        """
        Every minute, check if a task has been started directly from the CLI with watson.
        """
        if not self.task_started:
            return

        self.task_name, self.task_start_time = get_watson_status()
        self.task_started = self.task_name and self.task_start_time

    @rumps.timer(60 * 30)
    def check_if_working(self, _):
        """
        Every 30min, check if I've not forgotten to stop the time.
        """
        if not self.task_started:
            return

        rumps.notification(
            title='Watson Time Tracker',
            message=f'Are you still working on {self.task_name}?',
        )


if __name__ == '__main__':
    WatsonStatusBar().run()
