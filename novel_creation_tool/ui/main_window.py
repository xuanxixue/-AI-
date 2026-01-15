import os
import sys
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QStackedWidget, QMenuBar, QStatusBar, QToolBar, QAction, 
    QMessageBox, QLabel, QFileDialog
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon, QFont

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from project_manager import ProjectManager
from ui.project_list import ProjectListWidget
from ui.function_panel import FunctionPanelWidget


class MainWindow(QMainWindow):
    """
    主窗口类
    """
    
    def __init__(self):
        """初始化主窗口"""
        super().__init__()
        
        # 初始化工程文件管理器
        self.project_manager = ProjectManager()
        self.current_project_path = None
        
        self.setup_ui()
        self.setup_menu_bar()
        self.setup_toolbar()
        self.setup_status_bar()
        
        # 连接信号和槽
        self.connect_signals()
    
    def setup_ui(self):
        """设置主界面"""
        self.setWindowTitle("小说创作辅助工具")
        self.setGeometry(100, 100, 1200, 800)
        
        # 创建中央部件和堆叠窗口
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QHBoxLayout(central_widget)
        
        # 创建堆叠窗口用于切换不同视图
        self.stacked_widget = QStackedWidget()
        
        # 创建工程文件列表界面
        self.project_list_widget = ProjectListWidget(self.project_manager)
        self.stacked_widget.addWidget(self.project_list_widget)
        
        # 创建功能面板界面
        self.function_panel_widget = FunctionPanelWidget()
        self.stacked_widget.addWidget(self.function_panel_widget)
        
        # 默认显示工程文件列表
        self.stacked_widget.setCurrentWidget(self.project_list_widget)
        
        main_layout.addWidget(self.stacked_widget)
    
    def setup_menu_bar(self):
        """设置菜单栏"""
        menubar = self.menuBar()
        
        # 文件菜单
        file_menu = menubar.addMenu('文件(&F)')
        
        new_project_action = QAction('新建工程文件(&N)', self)
        new_project_action.setShortcut('Ctrl+N')
        new_project_action.triggered.connect(self.create_new_project)
        file_menu.addAction(new_project_action)
        
        open_project_action = QAction('打开工程文件(&O)', self)
        open_project_action.setShortcut('Ctrl+O')
        open_project_action.triggered.connect(self.open_project_dialog)
        file_menu.addAction(open_project_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction('退出(&X)', self)
        exit_action.setShortcut('Ctrl+Q')
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # 编辑菜单
        edit_menu = menubar.addMenu('编辑(&E)')
        
        refresh_action = QAction('刷新列表(&R)', self)
        refresh_action.setShortcut('F5')
        refresh_action.triggered.connect(self.refresh_project_list)
        edit_menu.addAction(refresh_action)
        
        # 帮助菜单
        help_menu = menubar.addMenu('帮助(&H)')
        
        about_action = QAction('关于(&A)', self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
    
    def setup_toolbar(self):
        """设置工具栏"""
        toolbar = self.addToolBar('工具栏')
        
        # 新建工程文件按钮
        new_project_btn = QAction(QIcon(), '新建工程文件', self)
        new_project_btn.setToolTip('新建工程文件 (Ctrl+N)')
        new_project_btn.triggered.connect(self.create_new_project)
        toolbar.addAction(new_project_btn)
        
        # 打开工程文件按钮
        open_project_btn = QAction(QIcon(), '打开工程文件', self)
        open_project_btn.setToolTip('打开工程文件 (Ctrl+O)')
        open_project_btn.triggered.connect(self.open_project_dialog)
        toolbar.addAction(open_project_btn)
        
        toolbar.addSeparator()
        
        # 刷新按钮
        refresh_btn = QAction(QIcon(), '刷新', self)
        refresh_btn.setToolTip('刷新工程文件列表 (F5)')
        refresh_btn.triggered.connect(self.refresh_project_list)
        toolbar.addAction(refresh_btn)
    
    def setup_status_bar(self):
        """设置状态栏"""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        
        # 添加状态标签
        self.status_label = QLabel('就绪')
        self.status_bar.addWidget(self.status_label)
        
        # 添加项目数量标签
        self.project_count_label = QLabel('')
        self.status_bar.addPermanentWidget(self.project_count_label)
        
        self.update_status_bar()
    
    def connect_signals(self):
        """连接信号和槽"""
        # 连接工程文件列表的信号
        self.project_list_widget.project_open_requested.connect(self.open_project)
        self.project_list_widget.project_delete_requested.connect(self.on_project_deleted)
        self.project_list_widget.project_created.connect(self.on_project_created)
        
        # 连接功能面板的信号
        self.function_panel_widget.back_to_project_list.connect(self.show_project_list)
    
    def create_new_project(self):
        """创建新工程文件"""
        # 委托给工程文件列表组件处理
        self.project_list_widget.create_new_project()
    
    def open_project_dialog(self):
        """通过对话框打开工程文件"""
        project_dir = os.path.join(os.getcwd(), 'projects')
        if not os.path.exists(project_dir):
            os.makedirs(project_dir)
        
        project_path = QFileDialog.getExistingDirectory(
            self,
            "选择工程文件",
            project_dir,
            QFileDialog.ShowDirsOnly | QFileDialog.DontResolveSymlinks
        )
        
        if project_path:
            self.open_project(project_path)
    
    def open_project(self, project_path):
        """打开指定工程文件"""
        try:
            # 尝试打开工程文件
            project_info = self.project_manager.open_project(project_path)
            
            if project_info:
                # 设置当前工程文件路径
                self.current_project_path = project_path
                
                # 切换到功能面板
                self.stacked_widget.setCurrentWidget(self.function_panel_widget)
                
                # 更新状态栏
                self.status_label.setText(f'正在编辑: {project_info["name"]}')
                
                # 更新功能面板的工程文件路径
                self.function_panel_widget.set_current_project(project_path)
                
                print(f"成功打开工程文件: {project_path}")
            else:
                QMessageBox.warning(
                    self,
                    "警告",
                    "无法打开选定的工程文件，可能不是有效的工程文件目录。"
                )
                
        except Exception as e:
            QMessageBox.critical(
                self,
                "错误",
                f"打开工程文件时发生错误: {str(e)}"
            )
    
    def close_project(self):
        """关闭当前工程文件"""
        self.current_project_path = None
        self.show_project_list()
        self.status_label.setText('已关闭工程文件')
    
    def show_project_list(self):
        """显示工程文件列表"""
        self.stacked_widget.setCurrentWidget(self.project_list_widget)
        self.status_label.setText('工程文件列表')
    
    def refresh_project_list(self):
        """刷新工程文件列表"""
        self.project_list_widget.refresh_projects()
        self.update_status_bar()
    
    def on_project_deleted(self, project_path):
        """当工程文件被删除时的回调"""
        # 如果删除的是当前打开的工程文件，则关闭它
        if self.current_project_path == project_path:
            self.close_project()
        
        self.update_status_bar()
    
    def on_project_created(self):
        """当工程文件被创建时的回调"""
        self.update_status_bar()
    
    def update_status_bar(self):
        """更新状态栏信息"""
        # 获取工程文件数量
        projects = self.project_manager.list_projects()
        self.project_count_label.setText(f'工程文件数量: {len(projects)}')
    
    def show_about(self):
        """显示关于对话框"""
        QMessageBox.about(
            self,
            "关于小说创作辅助工具",
            "小说创作辅助工具 v1.0\n\n"
            "这是一个帮助作家进行小说创作的辅助工具，"
            "提供了大纲理解、想法提取、大纲生成、章节生成等功能。\n\n"
            "作者: 动慢工具\n"
            "联系方式: example@example.com"
        )
    
    def closeEvent(self, event):
        """关闭事件处理"""
        # 关闭数据库连接
        self.project_manager.close()
        
        # 接受关闭事件
        event.accept()


def main():
    """主函数"""
    app = QApplication(sys.argv)
    
    # 设置应用属性
    app.setApplicationName("小说创作辅助工具")
    app.setApplicationVersion("1.0")
    
    # 创建并显示主窗口
    window = MainWindow()
    window.show()
    
    # 运行应用
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()