import sys
import numpy as np
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.pyplot as plt

class PlotWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Plot App")
        self.is_running = False
        self.x = np.linspace(0, 2 * np.pi, 1000)
        self.count = 0  # Initialize the counter

        # Create a Figure object and a plot
        self.figure = Figure(figsize=(5, 4), dpi=100)
        self.canvas = FigureCanvas(self.figure)
        self.ax = self.figure.add_subplot(111)
        self.line1, = self.ax.plot(self.x, np.sin(self.x), label='Line 1')
        self.line2, = self.ax.plot(self.x, np.cos(self.x), label='Line 2')
        self.ax.legend()

        # Create buttons
        start_button = QPushButton("Start", self)
        start_button.clicked.connect(self.start_plot)
        stop_button = QPushButton("Stop", self)
        stop_button.clicked.connect(self.stop_plot)
        clear_button = QPushButton("Clear", self)
        clear_button.clicked.connect(self.clear_plot)

        # Set up the layout
        layout = QVBoxLayout()
        layout.addWidget(self.canvas)
        layout.addWidget(start_button)
        layout.addWidget(stop_button)
        layout.addWidget(clear_button)

        # Create a central widget to hold the layout
        central_widget = QWidget()
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)

    def start_plot(self):
        if not self.is_running:
            self.is_running = True
            self.update_plot()

    def stop_plot(self):
        self.is_running = False

    def clear_plot(self):
        self.ax.clear()
        self.ax.legend()
        self.canvas.draw()

    def update_plot(self):
        if self.is_running:
            # Update the x-axis values
            self.x = np.linspace(0, 2 * np.pi, 1000) + self.count * 0.1

            # Update the line data
            self.line1.set_data(self.x, np.sin(self.x))
            self.line2.set_data(self.x, np.cos(self.x))
            self.ax.relim()
            self.ax.autoscale_view()

            # Redraw the canvas
            self.canvas.draw_idle()

            # Schedule the next update
            QApplication.instance().processEvents()
            if self.is_running:
                self.count += 1
                self.update_plot()
        else:
            self.count = 0

# Create the PyQt application
app = QApplication(sys.argv)

# Create the main window
window = PlotWindow()
window.show()

# Start the PyQt event loop
sys.exit(app.exec_())
