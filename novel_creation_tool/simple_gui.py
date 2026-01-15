"""
使用tkinter创建的小说创作辅助工具简单界面
作为PyQt5的替代方案
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import os
import json
import shutil
from datetime import datetime
from database import ProjectDatabase, init_main_database
from ui.function_panel import FunctionPanelWidget


class SimpleProjectManager:
    """
    简化的工程文件管理器
    """
    
    def __init__(self, base_path=None):
        if base_path is None:
            self.base_path = os.path.join(os.getcwd(), 'projects')
        else:
            self.base_path = base_path
        
        os.makedirs(self.base_path, exist_ok=True)
        self.main_db = init_main_database()
    
    def create_project(self, name):
        try:
            clean_name = "".join(c for c in name if c.isalnum() or c in (' ', '-', '_', '.')).rstrip()
            if not clean_name:
                raise ValueError("工程文件名不合法")
            
            project_path = os.path.join(self.base_path, clean_name)
            counter = 1
            original_path = project_path
            while os.path.exists(project_path):
                project_path = f"{original_path}_{counter}"
                counter += 1
            
            os.makedirs(project_path, exist_ok=True)
            
            project_db_path = os.path.join(project_path, 'project.db')
            project_db = ProjectDatabase(project_db_path)
            project_db.close()
            
            config_path = os.path.join(project_path, 'config.json')
            config_data = {
                'name': clean_name,
                'path': project_path,
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat(),
                'version': '1.0'
            }
            
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, ensure_ascii=False, indent=2)
            
            insert_query = '''
                INSERT INTO projects (name, path, created_at, updated_at)
                VALUES (?, ?, ?, ?)
            '''
            project_id = self.main_db.execute_query(
                insert_query,
                (clean_name, project_path, datetime.now(), datetime.now())
            )
            
            return project_path
        except Exception as e:
            print(f"创建工程文件失败: {str(e)}")
            return None
    
    def delete_project(self, project_path):
        try:
            if not os.path.exists(project_path):
                return False
            
            delete_query = "DELETE FROM projects WHERE path = ?"
            self.main_db.execute_query(delete_query, (project_path,))
            
            shutil.rmtree(project_path)
            
            return True
        except Exception as e:
            print(f"删除工程文件失败: {str(e)}")
            return False
    
    def list_projects(self):
        try:
            query = "SELECT * FROM projects ORDER BY updated_at DESC"
            rows = self.main_db.execute_query(query)
            
            projects = []
            for row in rows:
                project_info = {
                    'id': row['id'],
                    'name': row['name'],
                    'path': row['path'],
                    'created_at': row['created_at'],
                    'updated_at': row['updated_at']
                }
                projects.append(project_info)
            
            return projects
        except Exception as e:
            print(f"获取工程文件列表失败: {str(e)}")
            return []


class ProjectListFrame(ttk.Frame):
    """
    工程文件列表界面
    """
    
    def __init__(self, parent, project_manager, app_instance=None):
        super().__init__(parent)
        
        self.project_manager = project_manager
        self.parent_app = parent
        self.app_instance = app_instance
        
        self.setup_ui()
        self.refresh_projects()
    
    def setup_ui(self):
        # 标题
        title_label = ttk.Label(self, text="工程文件列表", font=("Arial", 16, "bold"))
        title_label.pack(pady=10)
        
        # 新建工程文件按钮
        new_project_btn = ttk.Button(
            self, 
            text="+ 新建工程文件", 
            command=self.create_new_project
        )
        new_project_btn.pack(pady=5)
        
        # 项目列表框架
        list_frame = ttk.Frame(self)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 创建Treeview来显示项目列表
        columns = ('ID', '名称', '路径', '创建时间')
        self.tree = ttk.Treeview(list_frame, columns=columns, show='headings', height=15)
        
        # 定义列标题
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=150)
        
        # 滚动条
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 绑定双击事件
        self.tree.bind('<Double-1>', self.on_item_double_click)
        
        # 删除按钮
        delete_btn = ttk.Button(self, text="删除选中项目", command=self.delete_selected_project)
        delete_btn.pack(pady=5)
        
        # 打开按钮
        open_btn = ttk.Button(self, text="打开选中项目", command=self.open_selected_project)
        open_btn.pack(pady=5)
    
    def refresh_projects(self):
        # 清空现有项目
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # 获取项目列表并插入到Treeview中
        projects = self.project_manager.list_projects()
        
        for project in projects:
            self.tree.insert('', tk.END, values=(
                project['id'],
                project['name'],
                project['path'],
                project['created_at'].split('.')[0] if project['created_at'] else ''
            ))
    
    def create_new_project(self):
        # 创建一个简单的输入对话框
        dialog = NewProjectDialog(self)
        self.wait_window(dialog)
        
        if dialog.result:
            project_path = self.project_manager.create_project(dialog.result)
            
            if project_path:
                self.refresh_projects()
                messagebox.showinfo("成功", f"工程文件 '{dialog.result}' 创建成功！")
            else:
                messagebox.showerror("错误", f"创建工程文件 '{dialog.result}' 失败！")
    
    def delete_selected_project(self):
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("警告", "请选择要删除的工程文件")
            return
        
        item = self.tree.item(selection[0])
        values = item['values']
        project_id = values[0]
        project_name = values[1]
        project_path = values[2]
        
        if messagebox.askyesno("确认删除", f"确定要删除工程文件 '{project_name}' 吗？\n此操作将永久删除该工程文件及其所有数据。"):
            success = self.project_manager.delete_project(project_path)
            
            if success:
                self.refresh_projects()
                messagebox.showinfo("成功", f"工程文件 '{project_name}' 已被删除。")
            else:
                messagebox.showerror("错误", f"删除工程文件 '{project_name}' 失败！")
    
    def on_item_double_click(self, event):
        self.open_selected_project()
    
    def open_selected_project(self):
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("警告", "请选择要打开的工程文件")
            return
        
        item = self.tree.item(selection[0])
        values = item['values']
        project_path = values[2]
        project_name = values[1]
        
        # 使用传递的应用实例切换到功能面板
        if self.app_instance and hasattr(self.app_instance, 'show_function_panel_with_project'):
            self.app_instance.show_function_panel_with_project(project_path, project_name)


class NewProjectDialog(tk.Toplevel):
    """
    新建工程文件对话框
    """
    
    def __init__(self, parent):
        super().__init__(parent)
        self.result = None
        
        self.title("新建工程文件")
        self.geometry("300x100")
        self.resizable(False, False)
        
        # 居中显示
        self.transient(parent)
        self.grab_set()
        
        frame = ttk.Frame(self)
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 输入框
        ttk.Label(frame, text="工程文件名称:").pack(anchor=tk.W)
        self.entry = ttk.Entry(frame, width=30)
        self.entry.pack(pady=5)
        self.entry.focus()
        
        # 按钮框架
        btn_frame = ttk.Frame(frame)
        btn_frame.pack(pady=10)
        
        ttk.Button(btn_frame, text="确定", command=self.ok).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="取消", command=self.cancel).pack(side=tk.LEFT, padx=5)
        
        # 绑定回车键
        self.entry.bind('<Return>', lambda e: self.ok())
        
        # 窗口关闭事件
        self.protocol("WM_DELETE_WINDOW", self.cancel)
    
    def ok(self):
        name = self.entry.get().strip()
        if name:
            self.result = name
        self.destroy()
    
    def cancel(self):
        self.result = None
        self.destroy()


class FunctionPanelFrame(ttk.Frame):
    """
    功能面板界面
    """
    
    def __init__(self, parent, app_instance=None):
        super().__init__(parent)
        
        self.app_instance = app_instance
        self.project_path = None
        self.project_name = None
        self.setup_ui()
    
    def setup_ui(self):
        # 清空当前内容
        for widget in self.winfo_children():
            widget.destroy()
        
        # 创建FunctionPanelWidget实例
        self.function_panel = FunctionPanelWidget(self)
        self.function_panel.pack(fill=tk.BOTH, expand=True)
        
        # 设置返回回调
        self.function_panel.set_back_callback(self.go_back)
    
    def set_project_info(self, project_path, project_name):
        """设置工程文件信息"""
        self.project_path = project_path
        self.project_name = project_name
        if hasattr(self, 'function_panel') and self.function_panel:
            self.function_panel.set_current_project(project_path)
    
    def go_back(self):
        # 使用传递的应用实例切换回项目列表
        if self.app_instance and hasattr(self.app_instance, 'show_project_list'):
            self.app_instance.show_project_list()


class NovelCreationApp:
    """
    小说创作辅助工具主应用
    """
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("小说创作辅助工具")
        self.root.geometry("800x600")
        self.root.minsize(600, 400)
        
        self.project_manager = SimpleProjectManager()
        
        # 创建主框架
        self.main_frame = ttk.Frame(self.root)
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 当前显示的框架
        self.current_frame = None
        
        # 显示项目列表
        self.show_project_list()
    
    def show_project_list(self):
        """显示工程文件列表"""
        if self.current_frame:
            self.current_frame.destroy()
        
        self.current_frame = ProjectListFrame(self.main_frame, self.project_manager, self)
        self.current_frame.pack(fill=tk.BOTH, expand=True)
    
    def show_function_panel_with_project(self, project_path, project_name):
        """显示带有所选工程文件的功能面板"""
        if self.current_frame:
            self.current_frame.destroy()
        
        # 创建功能面板并传入工程文件信息
        self.current_frame = FunctionPanelFrame(self.main_frame, self)
        self.current_frame.set_project_info(project_path, project_name)
        
        self.current_frame.pack(fill=tk.BOTH, expand=True)
    
    def show_function_panel(self):
        """显示功能面板（暂时保留此方法，但不直接使用）"""
        pass
    
    def run(self):
        """运行应用"""
        self.root.mainloop()


def main():
    """主函数"""
    app = NovelCreationApp()
    app.run()


if __name__ == '__main__':
    main()