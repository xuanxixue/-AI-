import os
import sys
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QListWidget, 
    QListWidgetItem, QLabel, QPushButton, QMenu, QAction, 
    QMessageBox, QFrame, QScrollArea, QAbstractItemView
)
from PyQt5.QtCore import Qt, QSize, QPoint, pyqtSignal
from PyQt5.QtGui import QPixmap, QIcon, QFont, QPainter, QColor


class ProjectCardWidget(QFrame):
    """
    工程文件卡片组件
    """
    
    # 自定义信号
    double_clicked = pyqtSignal(str)  # 双击信号，传递工程文件路径
    right_clicked = pyqtSignal(str, QPoint)  # 右键点击信号，传递工程文件路径和位置
    
    def __init__(self, project_info):
        """
        初始化工程文件卡片
        
        Args:
            project_info (dict): 工程文件信息，包含id, name, path, created_at等
        """
        super().__init__()
        
        self.project_info = project_info
        self.setup_ui()
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_context_menu)
    
    def setup_ui(self):
        """设置UI界面"""
        self.setFixedSize(200, 120)
        self.setFrameShape(QFrame.StyledPanel)
        self.setLineWidth(1)
        
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        
        # 创建图标
        icon_label = QLabel()
        pixmap = self.create_project_icon()
        icon_label.setPixmap(pixmap)
        icon_label.setAlignment(Qt.AlignCenter)
        icon_label.setFixedSize(48, 48)
        
        # 工程文件名称
        name_label = QLabel(self.project_info['name'])
        name_label.setWordWrap(True)
        name_label.setFont(QFont("Microsoft YaHei", 10, QFont.Bold))
        name_label.setStyleSheet("color: #333;")
        
        # 创建时间
        time_label = QLabel(f"创建: {self.format_datetime(self.project_info['created_at'])}")
        time_label.setFont(QFont("Microsoft YaHei", 8))
        time_label.setStyleSheet("color: #888;")
        
        layout.addWidget(icon_label, alignment=Qt.AlignCenter)
        layout.addWidget(name_label)
        layout.addWidget(time_label)
        
        self.setLayout(layout)
        
        # 连接鼠标事件
        self.mouseDoubleClickEvent = self.on_double_click
        self.mousePressEvent = self.on_mouse_press
    
    def create_project_icon(self):
        """创建工程文件图标"""
        pixmap = QPixmap(48, 48)
        pixmap.fill(Qt.transparent)
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # 绘制文件夹图标
        painter.setBrush(QColor(70, 130, 180))  # SteelBlue
        painter.setPen(QColor(50, 100, 150))
        
        # 文件夹主体
        painter.drawRect(5, 15, 38, 28)
        
        # 文件夹顶部
        painter.drawPolygon([
            QPoint(5, 15),
            QPoint(15, 5),
            QPoint(35, 5),
            QPoint(43, 15)
        ])
        
        painter.end()
        
        return pixmap
    
    def format_datetime(self, datetime_str):
        """格式化日期时间字符串"""
        if not datetime_str:
            return ""
        
        # 尝试解析ISO格式的时间字符串
        try:
            dt = datetime.fromisoformat(datetime_str.replace('Z', '+00:00'))
            return dt.strftime("%Y-%m-%d %H:%M")
        except:
            return datetime_str
    
    def on_double_click(self, event):
        """处理双击事件"""
        self.double_clicked.emit(self.project_info['path'])
    
    def on_mouse_press(self, event):
        """处理鼠标按下事件"""
        if event.button() == Qt.RightButton:
            self.right_clicked.emit(self.project_info['path'], event.globalPos())
        super().mousePressEvent(event)
    
    def show_context_menu(self, pos):
        """显示右键菜单"""
        menu = QMenu()
        delete_action = menu.addAction("删除工程文件")
        
        action = menu.exec_(self.mapToGlobal(pos))
        if action == delete_action:
            # 发射右键点击信号，让父组件处理删除操作
            self.right_clicked.emit(self.project_info['path'], pos)


class ProjectListWidget(QWidget):
    """
    工程文件列表组件
    """
    
    # 信号
    project_open_requested = pyqtSignal(str)  # 请求打开工程文件
    project_delete_requested = pyqtSignal(str)  # 请求删除工程文件
    project_created = pyqtSignal()  # 工程文件创建完成信号
    
    def __init__(self, project_manager):
        """
        初始化工程文件列表
        
        Args:
            project_manager (ProjectManager): 工程文件管理器实例
        """
        super().__init__()
        
        self.project_manager = project_manager
        self.projects = []
        
        self.setup_ui()
        self.refresh_projects()
    
    def setup_ui(self):
        """设置UI界面"""
        layout = QVBoxLayout()
        
        # 顶部标题和新建按钮
        header_layout = QHBoxLayout()
        
        title_label = QLabel("工程文件")
        title_label.setFont(QFont("Microsoft YaHei", 14, QFont.Bold))
        title_label.setStyleSheet("color: #333; padding: 10px;")
        
        new_project_btn = QPushButton("+ 新建工程文件")
        new_project_btn.setFont(QFont("Microsoft YaHei", 10))
        new_project_btn.setStyleSheet(
            """
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                min-width: 120px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            """
        )
        new_project_btn.clicked.connect(self.create_new_project)
        
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        header_layout.addWidget(new_project_btn)
        
        # 工程文件列表容器
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        # 创建内容容器
        self.content_widget = QWidget()
        self.grid_layout = QGridLayout(self.content_widget)
        self.grid_layout.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        
        # 设置间距
        self.grid_layout.setSpacing(20)
        self.grid_layout.setContentsMargins(20, 20, 20, 20)
        
        self.scroll_area.setWidget(self.content_widget)
        
        layout.addLayout(header_layout)
        layout.addWidget(self.scroll_area)
        
        self.setLayout(layout)
    
    def refresh_projects(self):
        """刷新工程文件列表"""
        # 清空现有项目
        self.clear_projects()
        
        # 获取工程文件列表
        self.projects = self.project_manager.list_projects()
        
        if not self.projects:
            # 如果没有工程文件，显示提示信息
            hint_label = QLabel("还没有工程文件，点击上方“新建工程文件”开始创作")
            hint_label.setAlignment(Qt.AlignCenter)
            hint_label.setFont(QFont("Microsoft YaHei", 12))
            hint_label.setStyleSheet("color: #888;")
            self.grid_layout.addWidget(hint_label, 0, 0, 1, 1)
        else:
            # 计算每行列数（根据窗口宽度动态调整）
            items_per_row = max(1, self.width() // 220)  # 每个项目占用约220像素宽度
            
            for i, project in enumerate(self.projects):
                row = i // items_per_row
                col = i % items_per_row
                
                # 创建工程文件卡片
                card = ProjectCardWidget(project)
                card.double_clicked.connect(self.open_project)
                card.right_clicked.connect(self.on_project_right_click)
                
                self.grid_layout.addWidget(card, row, col)
    
    def clear_projects(self):
        """清空工程文件列表"""
        # 移除所有子控件
        for i in reversed(range(self.grid_layout.count())):
            widget = self.grid_layout.itemAt(i).widget()
            if widget is not None:
                widget.setParent(None)
    
    def create_new_project(self):
        """创建新工程文件"""
        from PyQt5.QtWidgets import QInputDialog
        
        project_name, ok = QInputDialog.getText(
            self,
            "新建工程文件",
            "请输入工程文件名称:",
            text="新工程文件"
        )
        
        if ok and project_name.strip():
            # 创建工程文件
            project_path = self.project_manager.create_project(project_name.strip())
            
            if project_path:
                # 刷新列表
                self.refresh_projects()
                self.project_created.emit()
                
                QMessageBox.information(
                    self,
                    "成功",
                    f"工程文件 '{project_name}' 创建成功！"
                )
            else:
                QMessageBox.critical(
                    self,
                    "错误",
                    f"创建工程文件 '{project_name}' 失败！"
                )
    
    def open_project(self, project_path):
        """打开工程文件"""
        self.project_open_requested.emit(project_path)
    
    def delete_project(self, project_path):
        """删除工程文件"""
        # 获取工程文件名称
        project_info = None
        for proj in self.projects:
            if proj['path'] == project_path:
                project_info = proj
                break
        
        if project_info:
            reply = QMessageBox.question(
                self,
                "确认删除",
                f"确定要删除工程文件 '{project_info['name']}' 吗？\n此操作将永久删除该工程文件及其所有数据。",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                # 删除工程文件
                success = self.project_manager.delete_project(project_path)
                
                if success:
                    # 刷新列表
                    self.refresh_projects()
                    
                    QMessageBox.information(
                        self,
                        "成功",
                        f"工程文件 '{project_info['name']}' 已被删除。"
                    )
                    
                    self.project_delete_requested.emit(project_path)
                else:
                    QMessageBox.critical(
                        self,
                        "错误",
                        f"删除工程文件 '{project_info['name']}' 失败！"
                    )
    
    def on_project_right_click(self, project_path, pos):
        """处理工程文件右键点击"""
        # 将局部坐标转换为全局坐标
        global_pos = self.mapToGlobal(pos)
        
        # 显示上下文菜单
        menu = QMenu()
        delete_action = menu.addAction("删除工程文件")
        
        action = menu.exec_(global_pos)
        if action == delete_action:
            self.delete_project(project_path)
    
    def resizeEvent(self, event):
        """重写resize事件，调整网格布局"""
        super().resizeEvent(event)
        # 在大小改变时重新计算列数
        self.refresh_projects()