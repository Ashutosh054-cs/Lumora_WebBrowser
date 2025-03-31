import sys
import json
from datetime import datetime
from pathlib import Path
from PyQt6.QtCore import (
    QUrl, Qt, QPropertyAnimation, QEasingCurve, QSize, 
    QParallelAnimationGroup, QTimer, QPoint, QStandardPaths,
    QRectF
)
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QHBoxLayout,
    QLineEdit, QPushButton, QTabWidget, QWidget, QToolBar,
    QLabel, QGraphicsOpacityEffect, QGraphicsDropShadowEffect,
    QSizePolicy, QStackedWidget, QMenu, QFileDialog,
    QGraphicsScene, QGraphicsView, QGraphicsItem
)
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtGui import (
    QPalette, QColor, QPainter, QPixmap, QIcon, 
    QAction, QGuiApplication, QColorConstants, QLinearGradient,
    QBrush, QPen, QFont, QPainterPath
)
import random
import math

# ----------------------------
# 1. INTERACTIVE LANDING PAGE
# ----------------------------
class Particle:
    def __init__(self, scene):
        self.scene = scene
        self.reset()
        self.item = scene.addEllipse(
            self.x, self.y, self.size, self.size,
            QPen(Qt.PenStyle.NoPen),
            QBrush(QColor(255, 255, 255, self.alpha))
        )

    def reset(self):
        self.x = random.randint(0, 800)
        self.y = random.randint(0, 600)
        self.size = random.randint(2, 8)
        self.speed = random.uniform(0.5, 2)
        self.direction = random.uniform(0, 2 * math.pi)
        self.alpha = random.randint(50, 150)

    def update(self):
        self.x += math.cos(self.direction) * self.speed
        self.y += math.sin(self.direction) * self.speed
        
        # Wrap around screen edges
        if self.x > 800: self.x = 0
        if self.x < 0: self.x = 800
        if self.y > 600: self.y = 0
        if self.y < 0: self.y = 600
        
        self.item.setRect(self.x, self.y, self.size, self.size)
        self.item.setBrush(QColor(255, 255, 255, self.alpha))

class LandingPage(QGraphicsView):
    def __init__(self):
        super().__init__()
        self.scene = QGraphicsScene()
        self.setScene(self.scene)
        self.setStyleSheet("background: transparent; border: none;")
        
        # Gradient background
        gradient = QLinearGradient(0, 0, 0, 600)
        gradient.setColorAt(0, QColor(30, 30, 50))
        gradient.setColorAt(1, QColor(10, 10, 20))
        self.scene.setBackgroundBrush(QBrush(gradient))
        
        # Particles
        self.particles = [Particle(self.scene) for _ in range(50)]
        self.timer = QTimer()
        self.timer.timeout.connect(self.animate_particles)
        self.timer.start(30)
        
        # Clock
        self.clock = QLabel()
        self.clock.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.clock.setStyleSheet("""
            font-size: 48px; 
            color: white;
            font-weight: light;
        """)
        clock_proxy = self.scene.addWidget(self.clock)
        clock_proxy.setPos(300, 200)
        
        # Greeting
        self.greeting = QLabel()
        self.greeting.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.greeting.setStyleSheet("""
            font-size: 24px; 
            color: #aaa;
            font-weight: light;
        """)
        greeting_proxy = self.scene.addWidget(self.greeting)
        greeting_proxy.setPos(300, 260)
        
        # Search box
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("Search or enter website...")
        self.search_box.setStyleSheet("""
            QLineEdit {
                background: rgba(255, 255, 255, 0.2);
                color: white;
                border: 1px solid rgba(255, 255, 255, 0.3);
                border-radius: 20px;
                padding: 10px 20px;
                font-size: 16px;
                min-width: 400px;
            }
        """)
        search_proxy = self.scene.addWidget(self.search_box)
        search_proxy.setPos(200, 320)
        
        # Update time
        self.update_time()
        self.clock_timer = QTimer()
        self.clock_timer.timeout.connect(self.update_time)
        self.clock_timer.start(1000)
    
    def update_time(self):
        now = datetime.now()
        self.clock.setText(now.strftime("%H:%M"))
        
        hour = now.hour
        if 5 <= hour < 12:
            greeting = "Good Morning"
        elif 12 <= hour < 18:
            greeting = "Good Afternoon"
        else:
            greeting = "Good Evening"
        self.greeting.setText(greeting)
    
    def animate_particles(self):
        for particle in self.particles:
            particle.update()

# ----------------------------
# 2. MAIN BROWSER CLASS (UPDATED)
# ----------------------------
class DarkBrowser(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("DarkMin Browser")
        self.setMinimumSize(1000, 700)
        
        # Create landing page
        self.landing_page = LandingPage()
        
        # Tab system
        self.tabs = QTabWidget()
        self.tabs.setTabsClosable(True)
        self.tabs.tabCloseRequested.connect(self.close_tab)
        
        # Stacked widget to switch between landing and tabs
        self.stack = QStackedWidget()
        self.stack.addWidget(self.landing_page)
        self.stack.addWidget(self.tabs)
        self.stack.setCurrentIndex(1)  # Start with browser
        
        # Setup UI
        self.init_ui()
        
        # Connect landing page search
        self.landing_page.search_box.returnPressed.connect(
            lambda: self.navigate(self.landing_page.search_box.text(), new_tab=True)
        )

    def init_ui(self):
        # Central widget
        self.setCentralWidget(self.stack)
        
        # Toolbar
        self.toolbar = QToolBar()
        self.addToolBar(Qt.ToolBarArea.TopToolBarArea, self.toolbar)
        
        # Home button to toggle landing page
        self.home_btn = QPushButton("⌂")
        self.home_btn.setFixedSize(30, 30)
        self.home_btn.clicked.connect(self.toggle_home)
        self.toolbar.addWidget(self.home_btn)
        
        # Navigation buttons
        self.back_btn = QPushButton("←")
        self.forward_btn = QPushButton("→")
        self.refresh_btn = QPushButton("↻")
        
        for btn in [self.back_btn, self.forward_btn, self.refresh_btn]:
            btn.setFixedSize(30, 30)
            self.toolbar.addWidget(btn)
        
        # URL bar
        self.url_bar = QLineEdit()
        self.url_bar.setPlaceholderText("Search or enter URL...")
        self.toolbar.addWidget(self.url_bar)
        
        # New tab button
        self.new_tab_btn = QPushButton("+")
        self.new_tab_btn.setFixedSize(30, 30)
        self.toolbar.addWidget(self.new_tab_btn)
        
        # Connect signals
        self.back_btn.clicked.connect(lambda: self.current_browser().back())
        self.forward_btn.clicked.connect(lambda: self.current_browser().forward())
        self.refresh_btn.clicked.connect(lambda: self.current_browser().reload())
        self.url_bar.returnPressed.connect(lambda: self.navigate(self.url_bar.text()))
        self.new_tab_btn.clicked.connect(self.add_new_tab)
        
        # Add first tab
        self.add_new_tab("https://www.google.com", "Google")

    def toggle_home(self):
        if self.stack.currentIndex() == 0:
            self.stack.setCurrentIndex(1)
        else:
            self.stack.setCurrentIndex(0)
            self.landing_page.search_box.setFocus()

    def current_browser(self):
        return self.tabs.currentWidget()

    def add_new_tab(self, url=None, title="New Tab"):
        tab = QWebEngineView()
        tab.setUrl(QUrl(url if url else "about:blank"))
        index = self.tabs.addTab(tab, title)
        self.tabs.setCurrentIndex(index)
        tab.urlChanged.connect(self.update_url)
        tab.titleChanged.connect(lambda t, tab=tab: self.update_tab_title(tab, t))
        return tab

    def close_tab(self, index):
        if self.tabs.count() > 1:
            self.tabs.removeTab(index)

    def update_url(self, url):
        self.url_bar.setText(url.toString())
        # Switch to browser view if on landing page
        if self.stack.currentIndex() == 0:
            self.stack.setCurrentIndex(1)

    def update_tab_title(self, tab, title):
        index = self.tabs.indexOf(tab)
        self.tabs.setTabText(index, title[:15] + "..." if len(title) > 15 else title)

    def navigate(self, url, new_tab=False):
        if not url.startswith(("http://", "https://")):
            url = "https://" + url
        
        if new_tab:
            self.add_new_tab(url)
        else:
            self.current_browser().setUrl(QUrl(url))

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # Dark theme
    palette = QPalette()
    palette.setColor(QPalette.ColorRole.Window, QColor(30, 30, 30))
    palette.setColor(QPalette.ColorRole.WindowText, QColor(255, 255, 255))
    app.setPalette(palette)
    
    browser = DarkBrowser()
    browser.show()
    sys.exit(app.exec())