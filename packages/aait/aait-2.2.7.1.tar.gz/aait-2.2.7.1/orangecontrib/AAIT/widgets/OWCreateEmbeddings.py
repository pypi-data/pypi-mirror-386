import os
import sys

import Orange.data
from AnyQt.QtWidgets import QApplication
from Orange.widgets import widget
from Orange.widgets.utils.signals import Input, Output
from sentence_transformers import SentenceTransformer

if "site-packages/Orange/widgets" in os.path.dirname(os.path.abspath(__file__)).replace("\\", "/"):
    from Orange.widgets.orangecontrib.AAIT.llm import embeddings
    from Orange.widgets.orangecontrib.AAIT.utils import thread_management
    from Orange.widgets.orangecontrib.AAIT.utils.import_uic import uic
    from Orange.widgets.orangecontrib.AAIT.utils.initialize_from_ini import apply_modification_from_python_file
else:
    from orangecontrib.AAIT.llm import embeddings
    from orangecontrib.AAIT.utils import thread_management
    from orangecontrib.AAIT.utils.import_uic import uic
    from orangecontrib.AAIT.utils.initialize_from_ini import apply_modification_from_python_file


@apply_modification_from_python_file(filepath_original_widget=__file__)
class OWCreateEmbeddings(widget.OWWidget):
    name = "Create Embeddings"
    description = "Create embeddings on the column 'content' of a Table"
    category = "AAIT - LLM INTEGRATION"
    icon = "icons/owembeddings.svg"
    if "site-packages/Orange/widgets" in os.path.dirname(os.path.abspath(__file__)).replace("\\", "/"):
        icon = "icons_dev/owembeddings.svg"
    gui = os.path.join(os.path.dirname(os.path.abspath(__file__)), "designer/owembeddings.ui")
    want_control_area = False
    priority = 1060

    class Inputs:
        data = Input("Data", Orange.data.Table)
        model = Input("Model", SentenceTransformer, auto_summary=False)

    class Outputs:
        data = Output("Data", Orange.data.Table)

    @Inputs.data
    def set_data(self, in_data):
        if in_data is None:
            self.Outputs.data.send(None)
            return
        self.data = in_data
        if self.autorun:
            self.run()

    @Inputs.model
    def set_model(self, in_model):
        self.model = in_model
        if self.autorun:
            self.run()

    def __init__(self):
        super().__init__()
        # Qt Management
        self.setFixedWidth(470)
        self.setFixedHeight(300)
        uic.loadUi(self.gui, self)

        # Data Management
        self.data = None
        self.model = None
        self.thread = None
        self.autorun = True
        self.result = None
        self.post_initialized()

    def run(self):
        # if thread is running quit
        if self.thread is not None:
            self.thread.safe_quit()

        if self.data is None:
            return

        if self.model is None:
            return

        # Verification of in_data
        self.error("")
        try:
            self.data.domain["content"]
        except KeyError:
            self.error('You need a "content" column in input data')
            return

        if type(self.data.domain["content"]).__name__ != 'StringVariable':
            self.error('"content" column needs to be a Text')
            return

        # Start progress bar
        self.progressBarInit()

        # Connect and start thread : main function, progress, result and finish
        # --> progress is used in the main function to track progress (with a callback)
        # --> result is used to collect the result from main function
        # --> finish is just an empty signal to indicate that the thread is finished
        self.thread = thread_management.Thread(embeddings.create_embeddings, self.data, self.model)
        self.thread.progress.connect(self.handle_progress)
        self.thread.result.connect(self.handle_result)
        self.thread.finish.connect(self.handle_finish)
        self.thread.start()

    def handle_progress(self, value: float) -> None:
        self.progressBarSet(value)

    def handle_result(self, result):
        try:
            self.result = result
            self.Outputs.data.send(result)
        except Exception as e:
            print("An error occurred when sending out_data:", e)
            self.Outputs.data.send(None)
            return

    def handle_finish(self):
        print("Embeddings finished")
        self.progressBarFinished()

    def post_initialized(self):
        pass

if __name__ == "__main__":
    app = QApplication(sys.argv)
    my_widget = OWCreateEmbeddings()
    my_widget.show()
    if hasattr(app, "exec"):
        app.exec()
    else:
        app.exec_()
