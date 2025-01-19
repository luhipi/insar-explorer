from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar


class CustomToolbar(NavigationToolbar):
    def __init__(self, canvas, parent):
        super().__init__(canvas, parent)
        self.setStyleSheet("""
            QToolBar {
                background: #f0f0f0;
                border: 1px solid #dcdcdc;
                min-height: 20px;
                max-height: 20px;
            }
            QToolButton {
                background: #e0e0e0;
                border: 1px solid #b0b0b0;
                padding: 0px;
                margin: 0px;
            }
            QToolButton:pressed {
                background: #d0d0d0;
            }
        """)

        right_actions = ['Subplots', 'Customize']
        right_action_objects = []
        left_action_objects = []

        for action in self.actions():
            if action.text() in right_actions:
                right_action_objects.append(action)
            else:
                left_action_objects.append(action)

        for action in self.actions():
            if action.text() in right_actions:
                right_action_objects.append(action)
            else:
                left_action_objects.append(action)

        for action in self.actions():
            self.removeAction(action)

        for action in left_action_objects:
            self.addAction(action)

        self.addSeparator()

        for action in right_action_objects:
            self.addAction(action)

        items_to_remove = ['Save']
        for action in self.actions():
            if action.text() in items_to_remove:
                self.removeAction(action)
